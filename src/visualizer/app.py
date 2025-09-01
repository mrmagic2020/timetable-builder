"""
Main Application Class for Timetable Visualizer

Provides the main entry point and application orchestration.
"""

import os
import sys
from pathlib import Path

from .data_manager import TimetableDataManager
from .gui import TimetableVisualizerGUI


class TimetableVisualizerApp:
    """Main application class for the timetable visualizer."""
    
    def __init__(self, project_root: str | None = None):
        """
        Initialize the application.
        
        Args:
            project_root: Root directory of the timetable-builder project.
                         If None, will try to auto-detect.
        """
        if project_root is None:
            project_root = self._find_project_root()
            
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.output_dir = self.project_root / "output"
        
        # Validate directories exist
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        if not self.output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {self.output_dir}")
            
        # Initialize components
        self.data_manager = TimetableDataManager(str(self.data_dir), str(self.output_dir))
        self.gui = None
        
    def _find_project_root(self) -> str:
        """
        Auto-detect the project root directory.
        
        Returns:
            Path to the project root
        """
        # Start from current file's directory and go up
        current_path = Path(__file__).parent
        
        while current_path != current_path.parent:
            # Look for characteristic files/directories
            if (current_path / "data").exists() and (current_path / "output").exists():
                return str(current_path)
            current_path = current_path.parent
            
        # If not found, try current working directory
        cwd = Path.cwd()
        if (cwd / "data").exists() and (cwd / "output").exists():
            return str(cwd)
            
        # Default fallback
        raise FileNotFoundError(
            "Could not find project root. Please specify project_root parameter."
        )
        
    def run(self):
        """Run the application."""
        try:
            from .gui import TimetableVisualizerGUI, TKINTER_AVAILABLE
            
            if not TKINTER_AVAILABLE:
                print("GUI mode requires tkinter, which is not available.")
                print("Running in CLI mode instead...")
                self.run_cli()
                return
                
            self.gui = TimetableVisualizerGUI(self.data_manager)
            self.gui.run()
        except ImportError as e:
            print(f"GUI not available: {e}")
            print("Running in CLI mode instead...")
            self.run_cli()
        except Exception as e:
            print(f"Error running application: {e}")
            sys.exit(1)
            
    def run_cli(self):
        """Run a simple command-line interface version."""
        print("Timetable Visualizer CLI")
        print("========================")
        
        try:
            # Load available timetables
            available = self.data_manager.get_available_timetables()
            
            if not available:
                print("No timetables found in output directory.")
                return
                
            print(f"\nFound {len(available)} timetables:")
            for i, person in enumerate(available, 1):
                print(f"{i:3d}. {person['name']} ({person['type'].title()} - ID: {person['id']})")
                
            # Get user selection
            while True:
                try:
                    choice = input(f"\nSelect a person (1-{len(available)}) or 'q' to quit: ").strip()
                    if choice.lower() == 'q':
                        break
                        
                    index = int(choice) - 1
                    if 0 <= index < len(available):
                        person = available[index]
                        self._display_cli_timetable(person)
                    else:
                        print("Invalid selection. Please try again.")
                        
                except ValueError:
                    print("Invalid input. Please enter a number or 'q'.")
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                    
        except Exception as e:
            print(f"Error: {e}")
            
    def _display_cli_timetable(self, person: dict):
        """Display a timetable in CLI format."""
        print(f"\nTimetable for {person['name']} ({person['type'].title()} - ID: {person['id']})")
        print("=" * 80)
        
        # Load timetable
        timetable = self.data_manager.load_timetable(person['id'], person['type'])
        if not timetable:
            print("Timetable not found.")
            return
            
        lessons = timetable.get('lessons', [])
        if not lessons:
            print("No lessons found.")
            return
            
        # Sort lessons by day and period
        sorted_lessons = sorted(lessons, key=lambda x: (x['day'], x['period']))
        
        current_day = None
        for lesson_entry in sorted_lessons:
            day = lesson_entry['day']
            period = lesson_entry['period']
            lesson = lesson_entry['lesson']
            
            if day != current_day:
                current_day = day
                day_name = day.replace('A', 'Week A ').replace('B', 'Week B ')
                print(f"\n{day_name}:")
                print("-" * 40)
                
            subject_name = self.data_manager.get_subject_name(lesson['subject_id'])
            teacher_name = self.data_manager.get_teacher_name(lesson['teacher_id'])
            room = lesson['room_id']
            
            print(f"  Period {period}: {subject_name}")
            print(f"    Teacher: {teacher_name}")
            print(f"    Room: {room}")
            print()


def main():
    """Main entry point for the application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Timetable Visualizer")
    parser.add_argument(
        "--project-root", 
        help="Root directory of the timetable-builder project"
    )
    parser.add_argument(
        "--cli", 
        action="store_true", 
        help="Run in command-line mode instead of GUI"
    )
    parser.add_argument(
        "--gui", 
        action="store_true", 
        help="Run in GUI mode (default behavior)"
    )
    
    args = parser.parse_args()
    
    try:
        app = TimetableVisualizerApp(args.project_root)
        
        if args.cli:
            app.run_cli()
        else:
            app.run()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
