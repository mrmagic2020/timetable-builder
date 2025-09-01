"""
Timetable Visualizer Package

This package provides a GUI interface for visualizing generated timetable data.
It allows users to search for and view timetables for students and teachers.
"""

from .data_manager import TimetableDataManager
from .gui import TimetableVisualizerGUI
from .app import TimetableVisualizerApp

__all__ = ['TimetableDataManager', 'TimetableVisualizerGUI', 'TimetableVisualizerApp']
