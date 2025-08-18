from dataclasses import dataclass
from enum import Enum


class RoomType(Enum):
    CLASSROOM = "Classroom"
    LAB = "Laboratory"
    WORKSHOP = "DT Workshop"
    THEATRE = "Theatre"
    DRAMA = "Drama Room"
    MUSIC = "Music Room"
    LIBRARY = "Library"
    STAFF = "Staff Room"
    SPORT = "Sport Field"


@dataclass
class Room:
    id: str
    capacity: int
    type: RoomType
    location: str
