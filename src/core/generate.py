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
        """Perform student-centric scheduling with backtracking to ensure all requirements are met."""
        # Build requirements list: [(student_id, subject_id, lessons_needed)]
        requirements = self._build_requirements()
        self.total_required = sum(req[2] for req in requirements)
        
        # Try to schedule using backtracking
        if not self._backtrack_schedule(requirements, 0):
            print(f"Warning: Could not schedule all requirements. Placed {self.placed_lessons}/{self.total_required} lessons.")
        
        self._update_unscheduled_tracking(requirements)

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

    def _build_requirements(self) -> List[Tuple[StudentId, SubjectId, int]]:
        """Build a list of (student_id, subject_id, lessons_needed) requirements."""
        requirements = []
        for student in self.students:
            for subject_id in student.subjects:
                if subject_id in self.subject_index:
                    subject = self.subject_index[subject_id]
                    lessons_needed = subject.required_per_cycle
                    if lessons_needed > 0:
                        requirements.append((student.id, subject_id, lessons_needed))
        
        # Sort by total workload for better backtracking performance
        requirements.sort(key=lambda x: (-x[2], x[0], x[1]))
        return requirements

    def _backtrack_schedule(self, requirements: List[Tuple[StudentId, SubjectId, int]], req_index: int) -> bool:
        """Recursive backtracking to schedule all requirements."""
        if req_index >= len(requirements):
            return True  # All requirements scheduled
        
        student_id, subject_id, lessons_needed = requirements[req_index]
        
        # Try to schedule all lessons for this (student, subject) pair
        placements = []
        for lesson_num in range(lessons_needed):
            placement = self._find_slot_for_student_subject(student_id, subject_id, placements)
            if placement is None:
                # Backtrack: remove previously placed lessons for this requirement
                self._remove_placements(placements)
                return False
            
            placements.append(placement)
            self._commit_placement(placement)
        
        # Try to schedule remaining requirements
        if self._backtrack_schedule(requirements, req_index + 1):
            return True
        
        # Backtrack: remove all placements for this requirement
        self._remove_placements(placements)
        return False

    def _find_slot_for_student_subject(
        self, 
        student_id: StudentId, 
        subject_id: SubjectId, 
        existing_placements: List[LessonPlacement]
    ) -> Optional[LessonPlacement]:
        """Find a free slot for a student-subject lesson."""
        qualified_teachers = self.subject_teachers.get(subject_id, [])
        if not qualified_teachers:
            return None
        
        # Try all possible slots
        for day in self.days:
            for period in range(1, self.periods_per_day + 1):
                # Check if student is free
                if self.student_timetables[student_id].lessons_on(day, period):
                    continue
                
                # Check if this conflicts with existing placements we're trying to place
                if any(p.day == day and p.period == period for p in existing_placements):
                    continue
                
                # Find an available teacher
                teacher = self._pick_teacher(qualified_teachers, day, period)
                if teacher is None:
                    continue
                
                # Find an available room
                room = self._pick_room(day, period)
                if room is None:
                    continue
                
                # Create the lesson placement
                self.lesson_counter += 1
                lesson = Lesson(
                    id=f"L{self.lesson_counter:05d}",
                    subject_id=subject_id,
                    teacher_id=teacher.id,
                    room_id=room.id,
                    student_ids=(student_id,),
                )
                return LessonPlacement(day=day, period=period, lesson=lesson)
        
        return None

    def _commit_placement(self, placement: LessonPlacement) -> None:
        """Add a placement to all relevant timetables and update occupancy."""
        slot = (placement.day, placement.period)
        
        # Add to teacher timetable
        self.teacher_timetables[placement.lesson.teacher_id].add(placement)
        self.teacher_busy[placement.lesson.teacher_id].add(slot)
        
        # Add to room occupancy
        self.room_busy[placement.lesson.room_id].add(slot)
        
        # Add to student timetables
        for student_id in placement.lesson.student_ids:
            self.student_timetables[student_id].add(placement)
        
        self.placed_lessons += 1

    def _remove_placements(self, placements: List[LessonPlacement]) -> None:
        """Remove placements from timetables and update occupancy (backtrack)."""
        for placement in placements:
            slot = (placement.day, placement.period)
            
            # Remove from teacher timetable
            self.teacher_timetables[placement.lesson.teacher_id].remove(placement)
            self.teacher_busy[placement.lesson.teacher_id].discard(slot)
            
            # Remove from room occupancy
            self.room_busy[placement.lesson.room_id].discard(slot)
            
            # Remove from student timetables
            for student_id in placement.lesson.student_ids:
                self.student_timetables[student_id].remove(placement)
            
            self.placed_lessons -= 1

    def _update_unscheduled_tracking(self, requirements: List[Tuple[StudentId, SubjectId, int]]) -> None:
        """Update unscheduled counts based on what wasn't placed."""
        scheduled_by_subject = defaultdict(int)
        for req in requirements:
            student_id, subject_id, lessons_needed = req
            # Count actual scheduled lessons for this student-subject
            student_tt = self.student_timetables[student_id]
            scheduled_count = 0
            for day in self.days:
                for period in range(1, self.periods_per_day + 1):
                    for lp in student_tt.lessons_on(day, period):
                        if lp.lesson.subject_id == subject_id:
                            scheduled_count += 1
            
            unscheduled = max(0, lessons_needed - scheduled_count)
            if unscheduled > 0:
                self.unscheduled[subject_id] += unscheduled

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
            "unscheduled": {str(k): v for k, v in self.unscheduled.items()},
            "summary": self.summary(),
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
