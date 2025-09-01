#!/usr/bin/env python3
"""
Demo script for the Timetable Visualizer

This script demonstrates the usage of the visualizer package.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.visualizer.app import TimetableVisualizerApp


def demo_data_manager():
    """Demonstrate the data manager functionality."""
    print("=== Data Manager Demo ===\n")
    
    app = TimetableVisualizerApp(str(project_root))
    dm = app.data_manager
    
    # Show available timetables
    available = dm.get_available_timetables()
    print(f"Total available timetables: {len(available)}")
    
    # Show first 5 students and teachers
    students = [p for p in available if p['type'] == 'student'][:5]
    teachers = [p for p in available if p['type'] == 'teacher'][:5]
    
    print(f"\nFirst 5 students:")
    for student in students:
        print(f"  - {student['name']} (ID: {student['id']})")
    
    print(f"\nFirst 5 teachers:")
    for teacher in teachers:
        print(f"  - {teacher['name']} (ID: {teacher['id']})")
    
    # Demonstrate search
    print(f"\nSearch results for 'Alice':")
    alice_results = dm.search_people('Alice')
    for person in alice_results:
        print(f"  - {person['name']} ({person['type']} - ID: {person['id']})")
    
    # Load and display a sample timetable
    if students:
        sample_student = students[0]
        print(f"\nSample timetable for {sample_student['name']}:")
        timetable = dm.load_timetable(sample_student['id'], sample_student['type'])
        
        if timetable:
            lessons = timetable.get('lessons', [])
            print(f"  Total lessons: {len(lessons)}")
            
            # Show first 3 lessons
            for i, lesson_entry in enumerate(lessons[:3]):
                lesson = lesson_entry['lesson']
                day = lesson_entry['day']
                period = lesson_entry['period']
                
                subject_name = dm.get_subject_name(lesson['subject_id'])
                teacher_name = dm.get_teacher_name(lesson['teacher_id'])
                room = lesson['room_id']
                
                print(f"    {i+1}. {day} Period {period}: {subject_name}")
                print(f"       Teacher: {teacher_name}, Room: {room}")
    
    print()


def demo_search_functionality():
    """Demonstrate the search functionality."""
    print("=== Search Functionality Demo ===\n")
    
    app = TimetableVisualizerApp(str(project_root))
    dm = app.data_manager
    
    # Test various search queries
    test_queries = ['1540000', 'Ruby', 'Teacher', 'Mr', 'Wilson']
    
    for query in test_queries:
        results = dm.search_people(query)
        print(f"Search for '{query}': {len(results)} results")
        for person in results[:3]:  # Show first 3 results
            print(f"  - {person['name']} ({person['type']} - ID: {person['id']})")
        print()


def demo_cli_interface():
    """Demonstrate the CLI interface programmatically."""
    print("=== CLI Interface Demo ===\n")
    
    print("To run the interactive CLI, use:")
    print("  python visualizer.py --cli")
    print()
    
    print("To run the GUI (if tkinter is available), use:")
    print("  python visualizer.py")
    print()
    
    print("The CLI allows you to:")
    print("  1. See all available timetables")
    print("  2. Select a person by number")
    print("  3. View their complete timetable")
    print("  4. Navigate back to select another person")
    print()


def main():
    """Run all demos."""
    print("Timetable Visualizer Demo")
    print("=" * 50)
    print()
    
    try:
        demo_data_manager()
        demo_search_functionality()
        demo_cli_interface()
        
        print("Demo completed successfully!")
        print("\nTry running: python visualizer.py --cli")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
