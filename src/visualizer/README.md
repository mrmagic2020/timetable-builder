# Timetable Visualizer

A GUI and CLI tool for visualizing generated timetable data from the timetable-builder project.

## Features

- **Search Interface**: Quickly find students and teachers by name or ID
- **Multiple Views**: 
  - Grid view: Traditional timetable grid layout
  - List view: Chronological list of lessons
  - JSON view: Raw data view for debugging
- **GUI and CLI**: Both graphical and command-line interfaces available

## Installation

The visualizer uses only Python standard library modules (tkinter for GUI), so no additional dependencies are required beyond what's already needed for the main timetable-builder project.

## Usage

### GUI Mode (Default)

From the project root directory:

```bash
python visualizer.py
```

This will open a graphical interface where you can:

1. Search for people by typing in the search box
2. Select a person from the results list
3. Click "Load Timetable" or double-click to view their timetable
4. Switch between different views using the tabs

### CLI Mode

For a simple command-line interface:

```bash
python visualizer.py --cli
```

This will show a numbered list of all available timetables and allow you to select one to view.

### Programmatic Usage

You can also use the visualizer components in your own code:

```python
from src.visualizer import TimetableVisualizerApp

# Create and run the app
app = TimetableVisualizerApp("/path/to/project/root")
app.run()  # GUI mode
# or
app.run_cli()  # CLI mode
```

## Components

### Data Manager (`data_manager.py`)

Handles loading and caching of timetable data from JSON files. Provides methods to:
- Load student, teacher, and subject data
- Search for people by name or ID
- Load individual timetables
- Get human-readable names for subjects and teachers

### GUI (`gui.py`)

Provides the main graphical interface with:
- Search functionality with auto-complete
- Three different view modes for timetables
- Responsive layout with scrollbars
- Status updates and error handling

### App (`app.py`)

Main application orchestrator that:
- Auto-detects project structure
- Provides both GUI and CLI interfaces
- Handles initialization and error management

## File Structure

```
src/visualizer/
├── __init__.py          # Package initialization
├── data_manager.py      # Data loading and management
├── gui.py              # GUI components and interface
└── app.py              # Main application class

visualizer.py           # Launcher script
```

## Data Format

The visualizer expects the following directory structure:

```
project_root/
├── data/
│   ├── students.json    # Student information
│   ├── teachers.json    # Teacher information
│   └── subjects.json    # Subject information
└── output/
    └── timetables/
        ├── student_*.json  # Individual student timetables
        └── teacher_*.json  # Individual teacher timetables
```

## Error Handling

The visualizer includes comprehensive error handling for:
- Missing data files
- Corrupted JSON data
- Missing timetables
- GUI errors

Errors are displayed in message boxes (GUI mode) or printed to console (CLI mode).

## Extending the Visualizer

To add new features:

1. **New View Modes**: Add methods to `TimetableVisualizerGUI` and create new tabs
2. **Export Features**: Extend `TimetableDataManager` with export methods
3. **Filtering**: Add filter options to the search interface
4. **Statistics**: Add analysis features to the data manager

## Tips

- Use the search box to quickly find people - it searches both names and IDs
- Double-click on search results to quickly load a timetable
- The grid view shows a traditional timetable layout
- The list view is useful for seeing all lessons chronologically
- The JSON view is helpful for debugging or understanding the data structure
