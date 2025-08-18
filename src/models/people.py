from dataclasses import dataclass


@dataclass
class Teacher:
    id: str
    name: str
    office: str  # for later implementation of reduced travel time
    subjects: list[str]  # List of subject IDs the teacher can teach
    availability: dict[
        str, list[int]
    ]  # Dictionary mapping day to list of available time slots


@dataclass
class Student:
    id: int
    name: str
    year: int  # year that they graduate (so we can delete expired students)
    status: str  # suspended etc, expelled whatever
    subjects: list[str]
    availability: dict[str, list[int]]
