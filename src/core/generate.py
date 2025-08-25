from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.models.curriculum import Subject
from src.models.facilities import Room
from src.models.people import Student, Teacher
from src.models.timetable import Day, Lesson, LessonPlacement, Timetable
from src.models.types import RoomId, StudentId, SubjectId, TeacherId


class HardConstraintViolation(Exception):
    """Raised when a hard constraint is violated and cannot be auto-resolved."""


class TimetableScheduler:
    """Stateful scheduler encapsulating indices, occupancy, and timetable state.

    Designed for iterative improvement: after initial build you can run optimisation
    passes that mutate timetables while consulting stored intermediate data.
    """

    def __init__(
        self,
        subjects: List[Subject],
        teachers: List[Teacher],
        students: List[Student],
        rooms: List[Room],
        periods_per_day: int = 6,
        days: Optional[List[Day]] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.subjects = subjects
        self.teachers = teachers
        self.students = students
        self.rooms = rooms
        self.periods_per_day = periods_per_day
        self.days = days or list(Day)
        self.seed = seed

        # Indices
        self.subject_index: Dict[SubjectId, Subject] = {}
        self.teacher_index: Dict[TeacherId, Teacher] = {}
        self.students_by_subject: Dict[SubjectId, List[Student]] = defaultdict(list)
        self.subject_teachers: Dict[SubjectId, List[Teacher]] = defaultdict(list)

        # Timetables
        self.student_timetables: Dict[StudentId, Timetable] = {}
        self.teacher_timetables: Dict[TeacherId, Timetable] = {}

        # Occupancy (for quick hard constraint checks)
        self.teacher_busy: Dict[TeacherId, set[Tuple[Day, int]]] = defaultdict(set)
        self.room_busy: Dict[RoomId, set[Tuple[Day, int]]] = defaultdict(set)

        # Schedule metrics & bookkeeping
        self.lesson_counter: int = 0
        self.unscheduled: Dict[SubjectId, int] = defaultdict(
            int
        )  # remaining lessons not placed
        self.placed_lessons: int = 0
        self.total_required: int = 0

        self._build_indices()
        self._init_timetables()

    # ------------------ public API ------------------
    def schedule_all(self) -> None:
        """Perform initial naive scheduling honoring hard constraints."""
        # Deterministic ordering: more frequent subjects first
        ordered_subjects = sorted(
            self.subjects, key=lambda s: (-(s.required_per_cycle), s.id)
        )
        for subj in ordered_subjects:
            self.total_required += max(0, subj.required_per_cycle)
            self._schedule_subject(subj)

    def save(self, output_dir: str | Path = "output/timetables") -> None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for sid, tt in self.student_timetables.items():
            self._write_tt(out / f"student_{sid}.json", tt)
        for tid, tt in self.teacher_timetables.items():
            self._write_tt(out / f"teacher_{tid}.json", tt)
        self._write_state(out / "scheduler_state.json")

    def summary(self) -> Dict[str, int | float]:
        return {
            "placed_lessons": self.placed_lessons,
            "total_required": self.total_required,
            "unscheduled_subjects": sum(1 for v in self.unscheduled.values() if v),
            "unscheduled_lessons": sum(self.unscheduled.values()),
            "fill_ratio": (
                (self.placed_lessons / self.total_required)
                if self.total_required
                else 0.0
            ),
        }

    def evaluate_hard_constraints(self) -> Dict[str, int]:
        """Return counts of detected hard constraint violations (should be zero)."""
        violations = {
            "teacher_overlap": 0,
            "room_overlap": 0,
            "student_overlap": 0,
        }
        # Teacher / room overlaps already structurally prevented; we can still scan.
        for tt in self.teacher_timetables.values():
            seen = set()
            for day in self.days:
                for p in range(1, self.periods_per_day + 1):
                    if len(tt.lessons_on(day, p)) > 1:
                        violations["teacher_overlap"] += 1
        for tt in self.student_timetables.values():
            for day in self.days:
                for p in range(1, self.periods_per_day + 1):
                    if len(tt.lessons_on(day, p)) > 1:
                        violations["student_overlap"] += 1
        # Room overlap derivation
        room_slots = defaultdict(list)
        for tt in self.teacher_timetables.values():  # each placement unique per teacher
            for day in self.days:
                for p in range(1, self.periods_per_day + 1):
                    for lp in tt.lessons_on(day, p):
                        room_slots[(day, p, lp.lesson.room_id)].append(lp.lesson.id)
        for key, lessons in room_slots.items():
            if len(lessons) > 1:
                violations["room_overlap"] += 1
        return violations

    # Placeholder for future expansion
    def optimise_soft_constraints(self):  # pragma: no cover - future work
        """Iterative improvement pass (not yet implemented)."""
        pass

    # ------------------ internal helpers ------------------
    def _build_indices(self) -> None:
        self.subject_index = {s.id: s for s in self.subjects}
        self.teacher_index = {t.id: t for t in self.teachers}
        for stu in self.students:
            for sid in stu.subjects:
                if sid in self.subject_index:
                    self.students_by_subject[sid].append(stu)
        for t in self.teachers:
            for sid in t.subjects:
                self.subject_teachers[sid].append(t)

    def _init_timetables(self) -> None:
        self.student_timetables = {
            s.id: Timetable(owner_id=s.id, periods_per_day=self.periods_per_day)
            for s in self.students
        }
        self.teacher_timetables = {
            t.id: Timetable(owner_id=t.id, periods_per_day=self.periods_per_day)
            for t in self.teachers
        }

    def _schedule_subject(self, subj: Subject) -> None:
        remaining = subj.required_per_cycle
        if remaining <= 0:
            return
        enrolled = self.students_by_subject.get(subj.id, [])
        if not enrolled:
            return
        qualified = self.subject_teachers.get(subj.id, [])
        if not qualified:
            self.unscheduled[subj.id] += remaining
            return
        day_pointer = 0
        while remaining > 0:
            day = self.days[day_pointer % len(self.days)]
            placed_this_loop = False
            for period in range(1, self.periods_per_day + 1):
                slot = (day, period)
                teacher = self._pick_teacher(qualified, day, period)
                if teacher is None:
                    continue
                room = self._pick_room(day, period)
                if room is None:
                    continue
                # Student availability check (slot empty)
                if any(
                    self.student_timetables[stu.id].lessons_on(day, period)
                    for stu in enrolled
                ):
                    continue
                self.lesson_counter += 1
                lesson = Lesson(
                    id=f"L{self.lesson_counter:05d}",
                    subject_id=subj.id,
                    teacher_id=teacher.id,
                    room_id=room.id,
                    student_ids=tuple(stu.id for stu in enrolled),
                )
                placement = LessonPlacement(day=day, period=period, lesson=lesson)
                # Commit
                self.teacher_timetables[teacher.id].add(placement)
                self.teacher_busy[teacher.id].add(slot)
                self.room_busy[room.id].add(slot)
                for stu in enrolled:
                    self.student_timetables[stu.id].add(placement)
                remaining -= 1
                self.placed_lessons += 1
                placed_this_loop = True
                break
            day_pointer += 1
            # Stop if we've looped through full grid without placement
            if (
                not placed_this_loop
                and day_pointer >= len(self.days) * self.periods_per_day
            ):
                self.unscheduled[subj.id] += remaining
                break

    def _pick_teacher(
        self, candidates: List[Teacher], day: Day, period: int
    ) -> Optional[Teacher]:
        for t in candidates:
            if (day, period) in self.teacher_busy[t.id]:
                continue
            avail = t.availability.get(day.name, [])
            if avail and period not in avail:
                continue
            return t
        return None

    def _pick_room(self, day: Day, period: int) -> Optional[Room]:
        for r in self.rooms:
            if (day, period) not in self.room_busy[r.id]:
                return r
        return None

    def _write_tt(self, path: Path, tt: Timetable) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(self._serialize_tt(tt), f, indent=2)

    def _serialize_tt(self, tt: Timetable) -> Dict:
        data: Dict = {
            "owner_id": tt.owner_id,
            "periods_per_day": tt.periods_per_day,
            "days": [d.name for d in tt.days],
            "lessons": [],
        }
        for day in tt.days:
            for period in range(1, tt.periods_per_day + 1):
                for lp in tt.lessons_on(day, period):
                    data["lessons"].append(
                        {
                            "day": day.name,
                            "period": period,
                            "lesson": {
                                "id": lp.lesson.id,
                                "subject_id": lp.lesson.subject_id,
                                "teacher_id": lp.lesson.teacher_id,
                                "room_id": lp.lesson.room_id,
                                "student_ids": list(lp.lesson.student_ids),
                            },
                        }
                    )
        return data

    def _write_state(self, path: Path) -> None:
        state = {
            "periods_per_day": self.periods_per_day,
            "days": [d.name for d in self.days],
            "lesson_counter": self.lesson_counter,
            "placed_lessons": self.placed_lessons,
            "total_required": self.total_required,
            "unscheduled": dict(self.unscheduled),
            "summary": self.summary(),
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
