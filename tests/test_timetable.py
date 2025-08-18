import pytest

from src.models.timetable import Day, Lesson, LessonPlacement, Timetable


def test_add_and_query_lessons():
    tt = Timetable()
    l1 = Lesson(id="L1", subject_id="S1", teacher_id=1, room_id="R1")
    p1 = LessonPlacement(day=Day.MON, period=1, lesson=l1)
    tt.add(p1)

    assert tt.lessons_on(Day.MON, 1) == [p1]
    assert tt.count_subject_on_day("S1", Day.MON) == 1


def test_room_collision():
    tt = Timetable()
    p = 1
    tt.add(
        LessonPlacement(day=Day.MON, period=p, lesson=Lesson("L1", "S1", 1, "R1"))
    )
    with pytest.raises(ValueError):
        tt.add(
            LessonPlacement(
                day=Day.MON, period=p, lesson=Lesson("L2", "S2", 2, "R1")
            )
        )


def test_teacher_collision():
    tt = Timetable()
    p = 1
    tt.add(
        LessonPlacement(day=Day.MON, period=p, lesson=Lesson("L1", "S1", 1, "R1"))
    )
    with pytest.raises(ValueError):
        tt.add(
            LessonPlacement(
                day=Day.MON, period=p, lesson=Lesson("L2", "S2", 1, "R2")
            )
        )
