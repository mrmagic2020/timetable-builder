"""
Launcher script for the Timetable Visualizer

This script provides an easy way to launch the visualizer from the project root.
"""

#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from src.visualizer.app import TimetableVisualizerApp
    
    def main():
        """Main entry point."""
        import argparse
        
        parser = argparse.ArgumentParser(description="Timetable Visualizer")
        parser.add_argument(
            "--cli", 
            action="store_true", 
            help="Run in command-line mode instead of GUI"
        )
        
        args = parser.parse_args()
        
        try:
            app = TimetableVisualizerApp(str(project_root))
            
            if args.cli:
                app.run_cli()
            else:
                app.run()
                
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Failed to import visualizer: {e}")
    print("Please ensure you're running this from the correct directory.")
    sys.exit(1)
