from dataclasses import dataclass

from .types import RoomId, StudentId, SubjectId, TeacherId


@dataclass
class Teacher:
    id: TeacherId
    name: str
    office: RoomId  # for later implementation of reduced travel time
    subjects: list[SubjectId]  # List of subject IDs the teacher can teach
    availability: dict[
        str, list[int]
    ]  # Dictionary mapping day to list of available time slots


@dataclass
class Student:
    id: StudentId
    name: str
    subjects: list[SubjectId]
