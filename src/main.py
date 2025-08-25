from pathlib import Path

from src.core.generate import TimetableScheduler
from src.loaders.DataLoaders import (
    load_rooms,
    load_students,
    load_subjects,
    load_teachers,
)
from src.models.timetable import Day, Lesson, LessonPlacement, Timetable


def generate_timetable_example():
    tt = Timetable(periods_per_day=6, owner_id=0)
    lesson = Lesson(id="L001", subject_id="SUB001", teacher_id=1, room_id="R001")
    tt.add(LessonPlacement(day=Day.AMON, period=1, lesson=lesson))
    return tt


def generate_all():
    subjects = load_subjects("data/subjects.json")
    teachers = load_teachers("data/teachers.json")
    students = load_students("data/students.json")
    rooms = load_rooms("data/rooms.json")
    scheduler = TimetableScheduler(
        subjects=subjects,
        teachers=teachers,
        students=students,
        rooms=rooms,
        periods_per_day=6,
    )
    scheduler.schedule_all()
    scheduler.save()
    print("Generated timetables written to output/timetables")


if __name__ == "__main__":
    generate_all()
