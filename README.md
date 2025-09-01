# timetable-builder

A heuristic-based timetable builder with visualization capabilities.

## Features

- **Timetable Generation**: Heuristic-based scheduling algorithm
- **Data Visualization**: Interactive GUI and CLI for viewing generated timetables
- **Search Functionality**: Find people by name or ID quickly
- **Multiple Formats**: Support for both students and teachers

## Visualizing Timetables

After generating timetables, you can visualize them using the built-in visualizer:

### GUI Mode (Recommended)

```bash
# Make sure you have tkinter support (see installation below)
python -m src.visualizer
```

### CLI Mode

```bash
python -m src.visualizer --cli
```

### Installation Requirements for GUI

On macOS with Homebrew:

```bash
brew install python-tk
# Create a new virtual environment with the tkinter-enabled Python
/opt/homebrew/bin/python3.13 -m venv .venv_tkinter
source .venv_tkinter/bin/activate
pip install -r requirements.txt
```

## Data layout

JSON files under `data/` provide input entities:

- `subjects.json`

  - id: string (e.g., "SUB001")
  - name: string
  - intensity: int (1-5)
  - required_per_cycle: int (lessons needed per cycle)
  - constraints: string[] (IDs of applicable constraints)

- `teachers.json`

  - id: int
  - name: string
  - office: string
  - subjects: string[] (subject IDs)
  - availability: { DayAbbrev: int[] } (e.g., {"Mon":[1,2,3]})

- `students.json`

  - id: int
  - name: string
  - subjects: string[]

- `rooms.json`

  - id: string
  - capacity: int
  - type: string (matches `RoomType` enum display values)
  - location: string

- `constraints.json`
  - Array of constraint objects with a `type` and initialization kwargs. Types defined in `models/constraints.py`.

## Loading data

Use the loaders:

- `load_subjects(data/subjects.json)` -> `List[Subject]`
- `load_teachers(data/teachers.json)` -> `List[Teacher]`
- `load_students(data/students.json)` -> `List[Student]`
- `load_rooms(data/rooms.json)` -> `List[Room]`
- `load_constraints(data/constraints.json)` -> `List[BaseConstraint]`

IDs are standardized as follows:

- SubjectId, RoomId: string
- TeacherId, StudentId: int
