import datetime
from dataclasses import dataclass


@dataclass
class Subject:
    id: str
    name: str
    intensity: int  # Intensity of the subject (1-5 scale)
    required_per_cycle: int  # Number of times the subject must be taught in a cycle
    constraints: list[str]  # List of constraint IDs that apply to this subject


@dataclass
class TimeSlot:
    start: datetime.time
    end: datetime.time


@dataclass
class SchoolClass:
    """Represents a class grouping (e.g., 10A) with a primary subject focus.

    This can evolve as the data model matures; kept minimal for now.
    """

    name: str
    subject_id: str
