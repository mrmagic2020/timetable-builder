"""
Data Manager for Timetable Visualizer

Handles loading and managing timetable data from JSON files.
"""

import json
import os
from typing import Dict, List, Optional, Union
from pathlib import Path


class TimetableDataManager:
    """Manages loading and accessing timetable data."""

    def __init__(self, data_dir: str, output_dir: str):
        """
        Initialize the data manager.

        Args:
            data_dir: Path to the data directory containing students.json, teachers.json, etc.
            output_dir: Path to the output directory containing generated timetables
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir) / "timetables"

        # Cache for loaded data
        self._students: Optional[List[Dict]] = None
        self._teachers: Optional[List[Dict]] = None
        self._subjects: Optional[List[Dict]] = None
        self._timetables_cache: Dict[str, Dict] = {}

    def load_students(self) -> List[Dict]:
        """Load student data from students.json."""
        if self._students is None:
            students_file = self.data_dir / "students.json"
            with open(students_file, "r") as f:
                self._students = json.load(f)
        if not self._students:
            raise ValueError("No student data found.")
        return self._students

    def load_teachers(self) -> List[Dict]:
        """Load teacher data from teachers.json."""
        if self._teachers is None:
            teachers_file = self.data_dir / "teachers.json"
            with open(teachers_file, "r") as f:
                self._teachers = json.load(f)
        if not self._teachers:
            raise ValueError("No teacher data found.")
        return self._teachers

    def load_subjects(self) -> List[Dict]:
        """Load subject data from subjects.json."""
        if self._subjects is None:
            subjects_file = self.data_dir / "subjects.json"
            with open(subjects_file, "r") as f:
                self._subjects = json.load(f)
        if not self._subjects:
            raise ValueError("No subject data found.")
        return self._subjects

    def get_all_people(self) -> List[Dict]:
        """Get combined list of all students and teachers with type information."""
        people = []

        # Add students
        for student in self.load_students():
            people.append(
                {"id": student["id"], "name": student["name"], "type": "student"}
            )

        # Add teachers
        for teacher in self.load_teachers():
            people.append(
                {"id": teacher["id"], "name": teacher["name"], "type": "teacher"}
            )

        return people

    def search_people(self, query: str) -> List[Dict]:
        """
        Search for people by name or ID.

        Args:
            query: Search query (name or ID)

        Returns:
            List of matching people
        """
        query = query.lower()
        all_people = self.get_all_people()

        matches = []
        for person in all_people:
            # Check if query matches name or ID
            if query in person["name"].lower() or query in str(person["id"]):
                matches.append(person)

        return matches

    def load_timetable(
        self, person_id: Union[int, str], person_type: str
    ) -> Optional[Dict]:
        """
        Load timetable for a specific person.

        Args:
            person_id: ID of the person
            person_type: 'student' or 'teacher'

        Returns:
            Timetable data or None if not found
        """
        cache_key = f"{person_type}_{person_id}"

        if cache_key in self._timetables_cache:
            return self._timetables_cache[cache_key]

        # Construct filename
        filename = f"{person_type}_{person_id}.json"
        timetable_file = self.output_dir / filename

        if not timetable_file.exists():
            return None

        try:
            with open(timetable_file, "r") as f:
                timetable_data = json.load(f)
                self._timetables_cache[cache_key] = timetable_data
                return timetable_data
        except (json.JSONDecodeError, IOError):
            return None

    def get_subject_name(self, subject_id: str) -> str:
        """Get the full name of a subject from its ID."""
        subjects = self.load_subjects()
        for subject in subjects:
            if subject["id"] == subject_id:
                return subject["name"]
        return subject_id  # Return ID if name not found

    def get_teacher_name(self, teacher_id: int) -> str:
        """Get the name of a teacher from their ID."""
        teachers = self.load_teachers()
        for teacher in teachers:
            if teacher["id"] == teacher_id:
                return teacher["name"]
        return f"Teacher {teacher_id}"  # Return generic name if not found

    def get_available_timetables(self) -> List[Dict]:
        """Get list of all available timetables."""
        available = []

        if not self.output_dir.exists():
            return available

        # Find all timetable files
        for file_path in self.output_dir.glob("*.json"):
            if file_path.name == "scheduler_state.json":
                continue

            # Parse filename to extract type and ID
            filename = file_path.stem
            if filename.startswith("student_"):
                person_id = filename.replace("student_", "")
                person_type = "student"
            elif filename.startswith("teacher_"):
                person_id = filename.replace("teacher_", "")
                person_type = "teacher"
            else:
                continue

            # Get person name
            if person_type == "student":
                students = self.load_students()
                person_name = next(
                    (s["name"] for s in students if str(s["id"]) == person_id),
                    f"Student {person_id}",
                )
            else:
                teachers = self.load_teachers()
                person_name = next(
                    (t["name"] for t in teachers if str(t["id"]) == person_id),
                    f"Teacher {person_id}",
                )

            available.append(
                {
                    "id": person_id,
                    "name": person_name,
                    "type": person_type,
                    "file_path": str(file_path),
                }
            )

        return sorted(available, key=lambda x: (x["type"], x["name"]))
