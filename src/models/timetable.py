from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from .types import RoomId, StudentId, SubjectId, TeacherId


class Day(Enum):
    MON = "Mon"
    TUE = "Tue"
    WED = "Wed"
    THU = "Thu"
    FRI = "Fri"


@dataclass(frozen=True)
class TimePeriod:
    """Represents a period within a day (e.g., Period 1).

    If precise times are used, start/end must be provided; otherwise
    only the period index is used.
    """

    index: int
    start: Optional[time] = None
    end: Optional[time] = None


@dataclass(frozen=True)
class Lesson:
    """A single lesson instance (subject taught by a teacher in a room).

    Student assignment can be a group identifier or a list of student IDs.
    Keep it minimal for now; expands later as grouping model evolves.
    """

    id: str
    subject_id: SubjectId
    teacher_id: TeacherId
    room_id: RoomId
    student_group: Optional[str] = None
    student_ids: Tuple[StudentId, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LessonPlacement:
    day: Day
    period: int  # 1-based index within the day
    lesson: Lesson


class Timetable:
    """Holds the scheduled lessons and provides basic queries/validation.

    Contract:
    - At most one lesson per (day, period, room).
    - At most one lesson per (day, period, teacher).
    """

    def __init__(
        self,
        periods_per_day: int = 7,
        day_order: Optional[List[Day]] = None,
        period_times: Optional[Dict[int, Tuple[Optional[time], Optional[time]]]] = None,
    ):
        if periods_per_day <= 0:
            raise ValueError("periods_per_day must be > 0")
        self.periods_per_day = periods_per_day
        self.days: List[Day] = day_order or [
            Day.MON,
            Day.TUE,
            Day.WED,
            Day.THU,
            Day.FRI,
        ]

        # (day, period) -> placements
        self._grid: Dict[Tuple[Day, int], List[LessonPlacement]] = {}
        # Fast collision indices
        self._room_busy: Dict[Tuple[Day, int], Set[RoomId]] = {}
        self._teacher_busy: Dict[Tuple[Day, int], Set[TeacherId]] = {}

        # Optional mapping of period index -> (start, end)
        self._period_times: Dict[int, TimePeriod] = {}
        if period_times:
            for idx, (start, end) in period_times.items():
                self._period_times[idx] = TimePeriod(index=idx, start=start, end=end)

    # -------------------------
    # Adding and removing
    # -------------------------
    def add(self, placement: LessonPlacement) -> None:
        self._validate_slot(placement.day, placement.period)
        key = (placement.day, placement.period)

        # Check collisions
        room = placement.lesson.room_id
        teacher = placement.lesson.teacher_id
        if room in self._room_busy.get(key, set()):
            raise ValueError(
                f"Room {room} already occupied on {placement.day.name} P{placement.period}"
            )
        if teacher in self._teacher_busy.get(key, set()):
            raise ValueError(
                f"Teacher {teacher} already assigned on {placement.day.name} P{placement.period}"
            )

        self._grid.setdefault(key, []).append(placement)
        self._room_busy.setdefault(key, set()).add(room)
        self._teacher_busy.setdefault(key, set()).add(teacher)

    def remove(self, placement: LessonPlacement) -> None:
        key = (placement.day, placement.period)
        items = self._grid.get(key)
        if not items or placement not in items:
            return
        items.remove(placement)
        if not items:
            self._grid.pop(key, None)
        # Rebuild indices for that slot
        rooms = {p.lesson.room_id for p in self._grid.get(key, [])}
        teachers = {p.lesson.teacher_id for p in self._grid.get(key, [])}
        self._room_busy[key] = rooms
        self._teacher_busy[key] = teachers

    # -------------------------
    # Queries
    # -------------------------
    def lessons_on(self, day: Day, period: int) -> List[LessonPlacement]:
        self._validate_slot(day, period)
        return list(self._grid.get((day, period), []))

    def lessons_for_subject_on_day(
        self, subject_id: SubjectId, day: Day
    ) -> List[LessonPlacement]:
        results: List[LessonPlacement] = []
        for period in range(1, self.periods_per_day + 1):
            for lp in self._grid.get((day, period), []):
                if lp.lesson.subject_id == subject_id:
                    results.append(lp)
        return results

    def count_subject_on_day(self, subject_id: SubjectId, day: Day) -> int:
        return len(self.lessons_for_subject_on_day(subject_id, day))

    def rooms_used_on_day(self, day: Day) -> Set[RoomId]:
        used: Set[RoomId] = set()
        for period in range(1, self.periods_per_day + 1):
            used |= {lp.lesson.room_id for lp in self._grid.get((day, period), [])}
        return used

    def preferred_room_used_for_subject_on_day(
        self, subject_id: SubjectId, day: Day, preferred_rooms: Set[RoomId]
    ) -> bool:
        placements = self.lessons_for_subject_on_day(subject_id, day)
        if not placements:
            return True  # no lesson → not a violation
        return any(lp.lesson.room_id in preferred_rooms for lp in placements)

    # -------------------------
    # Helpers
    # -------------------------
    def _validate_slot(self, day: Day, period: int) -> None:
        if day not in self.days:
            raise ValueError(f"Unsupported day {day}")
        if not (1 <= period <= self.periods_per_day):
            raise ValueError(f"period must be in 1..{self.periods_per_day}")

    def get_period_time(self, period: int) -> Optional[TimePeriod]:
        return self._period_times.get(period)
