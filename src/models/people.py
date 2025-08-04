from dataclasses import dataclass


@dataclass
class Teacher:
    id: str
    name: str
    subjects: list[str]  # List of subject IDs the teacher can teach
    availability: dict[
        str, list[int]
    ]  # Dictionary mapping day to list of available time slots
