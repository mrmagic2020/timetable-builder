from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Union


@dataclass
class BaseConstraint(ABC):
    id: str
    name: str
    is_hard: bool
    weight: float = 1.0

    def __post_init__(self):
        if not self.id:
            raise ValueError("Constraint ID cannot be empty")
        if not self.name:
            raise ValueError("Constraint name cannot be empty")
        if self.is_hard is None:
            raise ValueError("Constraint must specify if it is hard or soft")

    @abstractmethod
    def evaluate(self, timetable) -> Union[bool, int]:
        """
        Hard   → return True / False  (valid / violated)
        Soft   → return penalty (0 = perfect, >0 = worse)
        """

    def explain(self, timetable) -> str:
        """Optional human-readable reason for violation."""
        return ""


@dataclass
class SubjectSpacing(BaseConstraint):
    """
    Penalise having more than `max_per_day` lessons of a given subject.
    """

    id: str = ""
    name: str = "subject_spacing"
    is_hard: bool = False
    max_per_day: int = 2

    def evaluate(self, timetable) -> int:
        return 0  # Placeholder for actual evaluation logic


@dataclass
class NoSplitLessons(BaseConstraint):
    """
    Penalise having split lessons of the same subject within a day.
    """

    id: str = ""
    name: str = "no_split_lessons"
    is_hard: bool = False

    def evaluate(self, timetable) -> int:
        return 0


@dataclass
class RoomProximity(BaseConstraint):
    """
    Penalise having lessons of the same subject in different rooms on the same day.
    """

    id: str = ""
    name: str = "room_proximity"
    is_hard: bool = False

    def evaluate(self, timetable) -> int:
        return 0


@dataclass
class RoomPreference(BaseConstraint):
    """
    Penalise not using preferred rooms for certain subjects.
    """

    id: str = ""
    name: str = "room_preference"
    is_hard: bool = False
    preferred_rooms: list[str] = field(default_factory=list)

    def evaluate(self, timetable) -> int:
        return 0
