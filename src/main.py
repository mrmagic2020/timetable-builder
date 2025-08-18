import datetime
from pathlib import Path

from models.people import Teacher, Student
from models.facilities import Room, RoomType
from models.curriculum import Subject, TimeSlot
from models.constraints import (
    BaseConstraint,
    SubjectSpacing,
    NoSplitLessons,
    RoomProximity,
    RoomPreference,
)
from loaders.ConstraintLoader import load_constraints


def generate_data():
    print("F1")

    teachers = [
        Teacher("T001", "Mr. Cox", "A101", ["Software", "Physics"], {}),
        Teacher("T002", "Ms. Zhou", "G311", ["English", "History"], {}),
    ]
    students = [
        Student(
            1546002,
            "Daniel",
            2026,
            "Active",
            ["Software", "English", "History", "Physics"],
            {},
        ),
        Student(
            1546003,
            "Arnold",
            2026,
            "Active",
            ["Physics", "History", "English", "Software"],
            {},
        ),
    ]
    rooms = [
        Room("R001", 30, RoomType.CLASSROOM, "C410"),
        Room("R002", 25, RoomType.LAB, "S205"),
    ]
    subjects = [
        Subject("SUB001", "Software", 5, 30, []),
        Subject("SUB002", "English", 1, 2, []),
        Subject("SUB003", "History", 2, 3, []),
        Subject("SUB004", "Physics", 4, 24, []),
    ]
    classes = []
    time_slots = [
        TimeSlot(
            datetime.time(9, 0), datetime.time(10, 0)
        ),  # period slots (idk if this works correctly datetime kinda funky)
        TimeSlot(datetime.time(10, 0), datetime.time(11, 0)),
    ]
    print("F2")


def generate_timetable():
    print("F1")


generate_data()
