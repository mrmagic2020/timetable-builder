"""
GUI Components for Timetable Visualizer

Provides the main GUI interface for the timetable visualizer.
"""


import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
TKINTER_AVAILABLE = True

from typing import Dict, List, Optional
import json

from .data_manager import TimetableDataManager


class TimetableVisualizerGUI:
    """Main GUI class for the timetable visualizer."""
    
    def __init__(self, data_manager: TimetableDataManager):
        """
        Initialize the GUI.
        
        Args:
            data_manager: TimetableDataManager instance
        """
        if not TKINTER_AVAILABLE:
            raise ImportError("tkinter is not available. GUI mode requires tkinter to be installed.")
            
        self.data_manager = data_manager
        self.root = tk.Tk()
        self.root.title("Timetable Visualizer")
        self.root.geometry("1200x800")
        
        # Current displayed timetable
        self.current_timetable = None
        self.current_person = None
        
        self.setup_gui()
        
    def setup_gui(self):
        """Set up the GUI components."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Status bar (must be first to initialize status_var)
        self.setup_status_bar(main_frame)
        
        # Search section
        self.setup_search_section(main_frame)
        
        # Timetable display section
        self.setup_timetable_section(main_frame)
        
    def setup_search_section(self, parent):
        """Set up the search and person selection section."""
        # Search frame
        search_frame = ttk.LabelFrame(parent, text="Search & Select Person", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        # Search label and entry
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=1, sticky="we", padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        search_button = ttk.Button(search_frame, text="Search", command=self.perform_search)
        search_button.grid(row=0, column=2, padx=(0, 10))
        
        # Results listbox
        ttk.Label(search_frame, text="Results:").grid(row=1, column=0, sticky="wn", padx=(0, 5), pady=(10, 0))
        
        # Create listbox with scrollbar
        listbox_frame = ttk.Frame(search_frame)
        listbox_frame.grid(row=1, column=1, columnspan=2, sticky="wens", pady=(10, 0))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        self.results_listbox = tk.Listbox(listbox_frame, height=6)
        self.results_listbox.grid(row=0, column=0, sticky="wens")
        self.results_listbox.bind('<Double-Button-1>', self.on_person_select)
        
        results_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        results_scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_listbox.config(yscrollcommand=results_scrollbar.set)
        
        # Load timetable button
        load_button = ttk.Button(search_frame, text="Load Timetable", command=self.load_selected_timetable)
        load_button.grid(row=2, column=1, pady=(10, 0), sticky=tk.W)
        
        # Initially populate with all available timetables
        self.populate_all_people()
        
    def setup_timetable_section(self, parent):
        """Set up the timetable display section."""
        # Timetable frame
        timetable_frame = ttk.LabelFrame(parent, text="Timetable", padding="10")
        timetable_frame.grid(row=1, column=0, columnspan=2, sticky="wens")
        timetable_frame.columnconfigure(0, weight=1)
        timetable_frame.rowconfigure(0, weight=1)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(timetable_frame)
        self.notebook.grid(row=0, column=0, sticky="wens")
        
        # Grid view tab
        self.setup_grid_view()
        
        # List view tab
        self.setup_list_view()
        
        # JSON view tab
        self.setup_json_view()
        
    def setup_grid_view(self):
        """Set up the grid view of the timetable."""
        grid_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(grid_frame, text="Grid View")
        
        # Create treeview for grid display
        columns = ['Period'] + []  # Will be populated with days
        self.grid_tree = ttk.Treeview(grid_frame, columns=columns, show='tree headings', height=15)
        self.grid_tree.grid(row=0, column=0, sticky="wens")
        
        # Configure grid weights
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.rowconfigure(0, weight=1)
        
        # Add scrollbars
        grid_v_scrollbar = ttk.Scrollbar(grid_frame, orient=tk.VERTICAL, command=self.grid_tree.yview)
        grid_v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_tree.config(yscrollcommand=grid_v_scrollbar.set)
        
        grid_h_scrollbar = ttk.Scrollbar(grid_frame, orient=tk.HORIZONTAL, command=self.grid_tree.xview)
        grid_h_scrollbar.grid(row=1, column=0, sticky="we")
        self.grid_tree.config(xscrollcommand=grid_h_scrollbar.set)
        
    def setup_list_view(self):
        """Set up the list view of the timetable."""
        list_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(list_frame, text="List View")
        
        # Create treeview for list display
        self.list_tree = ttk.Treeview(list_frame, columns=('Day', 'Period', 'Subject', 'Teacher', 'Room'), show='headings', height=20)
        self.list_tree.grid(row=0, column=0, sticky="wens")
        
        # Configure column headings
        self.list_tree.heading('Day', text='Day')
        self.list_tree.heading('Period', text='Period')
        self.list_tree.heading('Subject', text='Subject')
        self.list_tree.heading('Teacher', text='Teacher')
        self.list_tree.heading('Room', text='Room')
        
        # Configure column widths
        self.list_tree.column('Day', width=100)
        self.list_tree.column('Period', width=60)
        self.list_tree.column('Subject', width=250)
        self.list_tree.column('Teacher', width=150)
        self.list_tree.column('Room', width=100)
        
        # Configure grid weights
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Add scrollbars
        list_v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.list_tree.yview)
        list_v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.list_tree.config(yscrollcommand=list_v_scrollbar.set)
        
        list_h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.list_tree.xview)
        list_h_scrollbar.grid(row=1, column=0, sticky="we")
        self.list_tree.config(xscrollcommand=list_h_scrollbar.set)
        
    def setup_json_view(self):
        """Set up the JSON view of the timetable."""
        json_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(json_frame, text="JSON View")
        
        # Create text widget for JSON display
        self.json_text = scrolledtext.ScrolledText(json_frame, wrap=tk.WORD, width=80, height=25)
        self.json_text.grid(row=0, column=0, sticky="wens")
        
        # Configure grid weights
        json_frame.columnconfigure(0, weight=1)
        json_frame.rowconfigure(0, weight=1)
        
    def setup_status_bar(self, parent):
        """Set up the status bar."""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a person to view their timetable")
        
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky="we", pady=(10, 0))
        
    def populate_all_people(self):
        """Populate the results listbox with all available people."""
        try:
            available_timetables = self.data_manager.get_available_timetables()
            self.results_listbox.delete(0, tk.END)
            
            for person in available_timetables:
                display_text = f"{person['name']} ({person['type'].title()} - ID: {person['id']})"
                self.results_listbox.insert(tk.END, display_text)
                
            self.status_var.set(f"Loaded {len(available_timetables)} available timetables")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load people: {str(e)}")
            self.status_var.set("Error loading data")
            
    def on_search_change(self, event):
        """Handle search entry changes."""
        # Auto-search as user types (with debouncing)
        self.root.after_idle(self.perform_search)
        
    def perform_search(self):
        """Perform search based on current search term."""
        query = self.search_var.get().strip()
        
        if not query:
            self.populate_all_people()
            return
            
        try:
            matches = self.data_manager.search_people(query)
            self.results_listbox.delete(0, tk.END)
            
            for person in matches:
                display_text = f"{person['name']} ({person['type'].title()} - ID: {person['id']})"
                self.results_listbox.insert(tk.END, display_text)
                
            self.status_var.set(f"Found {len(matches)} matches for '{query}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")
            self.status_var.set("Search error")
            
    def on_person_select(self, event):
        """Handle double-click on person in results."""
        self.load_selected_timetable()
        
    def load_selected_timetable(self):
        """Load and display the selected person's timetable."""
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a person from the results list.")
            return
            
        # Parse the selected item to get person info
        selected_text = self.results_listbox.get(selection[0])
        
        try:
            # Extract person info from display text
            # Format: "Name (Type - ID: id)"
            name_part = selected_text.split(' (')[0]
            info_part = selected_text.split(' (')[1].rstrip(')')
            type_part = info_part.split(' - ID: ')[0].lower()
            id_part = info_part.split(' - ID: ')[1]
            
            # Load timetable
            timetable_data = self.data_manager.load_timetable(id_part, type_part)
            
            if timetable_data:
                self.current_timetable = timetable_data
                self.current_person = {'name': name_part, 'type': type_part, 'id': id_part}
                self.display_timetable()
                self.status_var.set(f"Loaded timetable for {name_part}")
            else:
                messagebox.showerror("Error", f"Timetable not found for {name_part}")
                self.status_var.set("Timetable not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load timetable: {str(e)}")
            self.status_var.set("Error loading timetable")
            
    def display_timetable(self):
        """Display the current timetable in all views."""
        if not self.current_timetable:
            return
            
        try:
            self.display_grid_view()
            self.display_list_view()
            self.display_json_view()
            
            # Update window title
            if self.current_person:
                person_name = self.current_person['name']
                person_type = self.current_person['type'].title()
                self.root.title(f"Timetable Visualizer - {person_name} ({person_type})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display timetable: {str(e)}")
            
    def display_grid_view(self):
        """Display timetable in grid format."""
        # Clear existing data
        for item in self.grid_tree.get_children():
            self.grid_tree.delete(item)
            
        if not self.current_timetable:
            return
            
        timetable = self.current_timetable
        days = timetable.get('days', [])
        periods_per_day = timetable.get('periods_per_day', 6)
        lessons = timetable.get('lessons', [])
        
        # Configure columns
        columns = ['Period'] + [day.replace('A', 'Week A ').replace('B', 'Week B ') for day in days]
        self.grid_tree['columns'] = columns
        self.grid_tree.heading('#0', text='', anchor=tk.W)
        self.grid_tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.grid_tree.heading(col, text=col, anchor=tk.CENTER)
            self.grid_tree.column(col, width=150, anchor=tk.CENTER)
            
        # Create lesson lookup
        lesson_lookup = {}
        for lesson_entry in lessons:
            day = lesson_entry['day']
            period = lesson_entry['period']
            lesson = lesson_entry['lesson']
            
            if day not in lesson_lookup:
                lesson_lookup[day] = {}
            lesson_lookup[day][period] = lesson
            
        # Populate grid
        for period in range(1, periods_per_day + 1):
            row_values = [f"Period {period}"]
            
            for day in days:
                if day in lesson_lookup and period in lesson_lookup[day]:
                    lesson = lesson_lookup[day][period]
                    subject_name = self.data_manager.get_subject_name(lesson['subject_id'])
                    teacher_name = self.data_manager.get_teacher_name(lesson['teacher_id'])
                    room = lesson['room_id']
                    
                    cell_text = f"{subject_name}\n{teacher_name}\n{room}"
                else:
                    cell_text = "Free"
                    
                row_values.append(cell_text)
                
            self.grid_tree.insert('', tk.END, values=row_values)
            
    def display_list_view(self):
        """Display timetable in list format."""
        # Clear existing data
        for item in self.list_tree.get_children():
            self.list_tree.delete(item)
            
        if not self.current_timetable:
            return
            
        timetable = self.current_timetable
        lessons = timetable.get('lessons', [])
        
        # Sort lessons by day and period
        sorted_lessons = sorted(lessons, key=lambda x: (x['day'], x['period']))
        
        for lesson_entry in sorted_lessons:
            day = lesson_entry['day'].replace('A', 'Week A ').replace('B', 'Week B ')
            period = lesson_entry['period']
            lesson = lesson_entry['lesson']
            
            subject_name = self.data_manager.get_subject_name(lesson['subject_id'])
            teacher_name = self.data_manager.get_teacher_name(lesson['teacher_id'])
            room = lesson['room_id']
            
            self.list_tree.insert('', tk.END, values=(day, period, subject_name, teacher_name, room))
            
    def display_json_view(self):
        """Display timetable in JSON format."""
        self.json_text.delete(1.0, tk.END)
        
        if self.current_timetable:
            formatted_json = json.dumps(self.current_timetable, indent=2)
            self.json_text.insert(1.0, formatted_json)
            
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
        
    def destroy(self):
        """Destroy the GUI."""
        self.root.destroy()
