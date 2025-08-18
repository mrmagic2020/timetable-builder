from __future__ import annotations

import json
from pathlib import Path
from typing import List

from src.models.facilities import Room, RoomType
from src.models.people import Student, Teacher
from src.models.curriculum import Subject


def _read_json(path: str | Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_rooms(json_path: str | Path) -> List[Room]:
    data = _read_json(json_path)
    rooms: List[Room] = []
    for r in data:
        rooms.append(
            Room(
                id=r["id"],
                capacity=int(r["capacity"]),
                type=RoomType(r["type"]),
            )
        )
    return rooms


def load_teachers(json_path: str | Path) -> List[Teacher]:
    data = _read_json(json_path)
    teachers: List[Teacher] = []
    for t in data:
        teachers.append(
            Teacher(
                id=int(t["id"]),
                name=t["name"],
                office=t["office"],
                subjects=list(t.get("subjects", [])),
                availability={k: list(map(int, v)) for k, v in t.get("availability", {}).items()},
            )
        )
    return teachers


def load_students(json_path: str | Path) -> List[Student]:
    data = _read_json(json_path)
    students: List[Student] = []
    for s in data:
        students.append(
            Student(
                id=int(s["id"]),
                name=s["name"],
                subjects=list(s.get("subjects", [])),
            )
        )
    return students


def load_subjects(json_path: str | Path) -> List[Subject]:
    data = _read_json(json_path)
    subjects: List[Subject] = []
    for s in data:
        subjects.append(
            Subject(
                id=s["id"],
                name=s["name"],
                intensity=int(s["intensity"]),
                required_per_cycle=int(s["required_per_cycle"]),
                constraints=list(s.get("constraints", [])),
            )
        )
    return subjects
