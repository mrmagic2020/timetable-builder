from models.timetable import Day, Lesson, LessonPlacement, Timetable


def generate_timetable_example():
    tt = Timetable(periods_per_day=6)
    lesson = Lesson(id="L001", subject_id="SUB001", teacher_id=1, room_id="R001")
    tt.add(LessonPlacement(day=Day.MON, period=1, lesson=lesson))
    return tt


if __name__ == "__main__":
    # Example timetable (not persisted)
    _tt = generate_timetable_example()
    print(
        "Example timetable built with",
        len(_tt.lessons_on(Day.MON, 1)),
        "lesson(s) at Mon P1",
    )
