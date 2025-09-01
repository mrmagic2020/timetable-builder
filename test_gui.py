#!/usr/bin/env python3
"""
Simple test to verify the GUI loads correctly.
"""

import sys
import tkinter as tk
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from visualizer.data_manager import TimetableDataManager
    from visualizer.gui import TimetableVisualizerGUI
    
    print("Testing GUI components...")
    
    # Initialize data manager
    project_root = Path(__file__).parent
    data_dir = project_root / "data"
    output_dir = project_root / "output" / "timetables"
    data_manager = TimetableDataManager(str(data_dir), str(output_dir))
    
    print(f"Found {len(data_manager.get_all_people())} people in timetable data")
    
    # Test basic GUI creation
    root = tk.Tk()
    root.withdraw()  # Hide the root window for testing
    
    print("Creating GUI...")
    gui = TimetableVisualizerGUI(data_manager)
    
    print("GUI created successfully!")
    print("You can now run: python -m src.visualizer")
    
    root.destroy()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
