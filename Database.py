import sqlite3
from datetime import datetime

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk


class MedicineDatabase:
    def __init__(self, db_name="medicine_db.sqlite"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_name TEXT NOT NULL,
                dosage TEXT,
                form TEXT,
                frequency TEXT,
                notes TEXT,
                active_ingredients TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS intake_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                time_of_day TEXT NOT NULL,
                with_food TEXT,
                special_instructions TEXT,
                FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intake_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_time TEXT,
                status TEXT,
                FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()


    def add_medicine(self, name, dosage="", form="", frequency="", notes="", active_ingredients=""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO medicines (medicine_name, dosage, form, frequency, notes, active_ingredients)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, dosage, form, frequency, notes, active_ingredients))
        
        medicine_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return medicine_id


    def delete_medicine(self, medicine_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM medicines WHERE id = ?', (medicine_id,))
        conn.commit()
        conn.close()


    def update_medicine(self, medicine_id, name, dosage, form, frequency, notes, active_ingredients):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE medicines 
            SET medicine_name = ?, dosage = ?, form = ?, frequency = ?, 
                notes = ?, active_ingredients = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, dosage, form, frequency, notes, active_ingredients, medicine_id))
        
        conn.commit()
        conn.close()

    def get_medicine_by_id(self, medicine_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM medicines WHERE id = ?', (medicine_id,))
        medicine = cursor.fetchone()
        
        conn.close()
        return medicine
    
    def get_all_medicines(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM medicines ORDER BY medicine_name')
        medicines = cursor.fetchall()
        
        conn.close()
        return medicines

    def add_schedule(self, medicine_id, time_of_day, with_food="No preference", special_instructions=""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO intake_schedule (medicine_id, time_of_day, with_food, special_instructions)
            VALUES (?, ?, ?, ?)
        ''', (medicine_id, time_of_day, with_food, special_instructions))
        
        conn.commit()
        conn.close()

    def delete_schedule(self, schedule_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM intake_schedule WHERE id = ?', (schedule_id,))
        
        conn.commit()
        conn.close()

    def get_schedules_for_medicine(self, medicine_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM intake_schedule WHERE medicine_id = ?', (medicine_id,))
        schedules = cursor.fetchall()
        
        conn.close()
        return schedules
    
    def get_current_schedule(self):
        current_time = datetime.now().strftime("%H:%M")
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.*, s.time_of_day, s.with_food, s.special_instructions
            FROM medicines m
            JOIN intake_schedule s ON m.id = s.medicine_id
            ORDER BY s.time_of_day
        ''')
        
        schedules = cursor.fetchall()
        conn.close()
        return schedules
    
    def log_intake(self, medicine_id, scheduled_time, status="Taken"):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO intake_history (medicine_id, scheduled_time, status)
            VALUES (?, ?, ?)
        ''', (medicine_id, scheduled_time, status))
        
        conn.commit()
        conn.close()

    def search_medicine_by_name(self, search_term):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        search_pattern = f"%{search_term}%"
        cursor.execute('''
            SELECT * FROM medicines 
            WHERE medicine_name LIKE ? OR active_ingredients LIKE ?
            ORDER BY medicine_name
        ''', (search_pattern, search_pattern))
        
        medicines = cursor.fetchall()
        conn.close()
        return medicines


# Set CustomTkinter theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MedicineDatabaseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Medicine Database Manager")
        self.root.geometry("1200x800")

        self.db = MedicineDatabase()
        self.current_medicine_id = None
        
        self.setup_ui()
        self.setup_list_tab()
        self.setup_edit_tab()
        self.setup_schedule_tab()
        self.refresh_medicine_list()

    def setup_ui(self):
        # Main container
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title header
        header_frame = ctk.CTkFrame(main_container, corner_radius=15, height=80)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        ctk.CTkLabel(header_frame, text="Medicine Database Manager",font=ctk.CTkFont(size=28, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(header_frame, text="Organize and manage your medications with ease", font=ctk.CTkFont(size=13), text_color=("gray60", "gray50")).pack()
        
        # Tabview
        self.tabview = ctk.CTkTabview(main_container, corner_radius=15)
        self.tabview.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.list_tab = self.tabview.add("Medicine List")
        self.edit_tab = self.tabview.add("Add/Edit Medicine")
        self.schedule_tab = self.tabview.add("Intake Schedule")
        
        # Status bar
        self.status_bar = ctk.CTkFrame(self.root, height=35, corner_radius=0)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready",font=ctk.CTkFont(size=12), anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=15, pady=5)

    def setup_list_tab(self):
        # Search section
        search_frame = ctk.CTkFrame(self.list_tab, corner_radius=10)
        search_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill=tk.X, padx=15, pady=15)
        
        ctk.CTkLabel(search_inner, text="Search:", font=ctk.CTkFont(size=14, weight="bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_entry = ctk.CTkEntry(search_inner, width=350, height=35, placeholder_text="Search by name or ingredients...")
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.search_medicines())
        
        ctk.CTkButton(search_inner, text="Clear", width=100, height=35, command=self.clear_search, fg_color=("gray60", "gray40"), hover_color=("gray55", "gray35")).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(search_inner, text="Refresh", width=100, height=35, command=self.refresh_medicine_list).pack(side=tk.LEFT, padx=5)
        
        # Medicine list section
        list_frame = ctk.CTkFrame(self.list_tab, corner_radius=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        ctk.CTkLabel(list_frame, text="All Medicines", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10), padx=15, anchor="w")
        
        # Treeview container
        tree_container = ctk.CTkFrame(list_frame, fg_color=("gray85", "gray20"))
        tree_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Scrollbar and Treeview
        from tkinter import ttk
        
        tree_scroll_frame = tk.Frame(tree_container, bg=("#F0F0F0" if ctk.get_appearance_mode() == "Light" else "#2B2B2B"))
        tree_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        columns = ("ID", "Name", "Dosage", "Form", "Frequency")
        self.medicine_tree = ttk.Treeview(tree_scroll_frame, columns=columns, show='headings', height=12)
        
        # Configure treeview style
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview", background=("#F0F0F0" if ctk.get_appearance_mode() == "Light" else "#2B2B2B"),foreground=("#000000" if ctk.get_appearance_mode() == "Light" else "#FFFFFF"),fieldbackground=("#F0F0F0" if ctk.get_appearance_mode() == "Light" else "#2B2B2B"),  borderwidth=0, font=("Arial", 11))
        style.configure("Treeview.Heading",  background=("#1F6AA5"), foreground="white", borderwidth=0, font=("Arial", 11, "bold"))
        style.map('Treeview', background=[('selected', '#1F6AA5')])
        
        for col in columns:
            self.medicine_tree.heading(col, text=col)
            if col == "ID":
                self.medicine_tree.column(col, width=50)
            elif col == "Name":
                self.medicine_tree.column(col, width=250)
            else:
                self.medicine_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(tree_scroll_frame, orient=tk.VERTICAL, command=self.medicine_tree.yview)
        self.medicine_tree.configure(yscroll=scrollbar.set)
        
        self.medicine_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.medicine_tree.bind('<Double-1>', self.on_medicine_double_click)
        
        # Action buttons
        button_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        ctk.CTkButton(button_frame, text="View Details", command=self.view_medicine_details, height=35, fg_color=("#2196F3", "#2196F3"), hover_color=("#1E88E5", "#1E88E5")).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(button_frame, text="Edit",command=self.edit_selected_medicine, height=35, fg_color=("#2196F3", "#1976D2"), hover_color=("#1E88E5", "#1565C0")).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(button_frame, text="Delete", command=self.delete_selected_medicine, height=35, fg_color=("#E63946", "#D62828"), hover_color=("#C92A35", "#B91F26")).pack(side=tk.LEFT, padx=5)
        
        # Details section
        details_frame = ctk.CTkFrame(self.list_tab, corner_radius=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        ctk.CTkLabel(details_frame, text="Medicine Details", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10), padx=15, anchor="w")
        
        details_container = ctk.CTkFrame(details_frame, fg_color=("gray85", "gray20"))
        details_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.details_text = tk.Text(details_container, height=8, wrap=tk.WORD, bg=("#F0F0F0" if ctk.get_appearance_mode() == "Light" else "#2B2B2B"), fg=("#000000" if ctk.get_appearance_mode() == "Light" else "#FFFFFF"), relief=tk.FLAT, font=("Arial", 11),borderwidth=0, highlightthickness=0)
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def setup_edit_tab(self):
        # Scrollable frame for form
        scrollable_frame = ctk.CTkScrollableFrame(self.edit_tab, fg_color="transparent")
        scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Form container
        form_frame = ctk.CTkFrame(scrollable_frame, corner_radius=10)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ctk.CTkLabel(form_frame, text="Medicine Information",font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 15), padx=20, anchor="w")
        
        # Inner form
        inner_form = ctk.CTkFrame(form_frame, fg_color="transparent")
        inner_form.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Medicine Name
        ctk.CTkLabel(inner_form, text="Medicine Name:*",font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, sticky=tk.W, pady=(10, 5), padx=10)
        self.name_entry = ctk.CTkEntry(inner_form, width=450, height=35,placeholder_text="Enter medicine name")
        self.name_entry.grid(row=1, column=0, pady=(0, 15), padx=10, sticky=tk.W)
        
        # Dosage
        ctk.CTkLabel(inner_form, text="Dosage:",font=ctk.CTkFont(size=13, weight="bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5), padx=10)
        self.dosage_entry = ctk.CTkEntry(inner_form, width=450, height=35, placeholder_text="e.g., 500mg, 10ml")
        self.dosage_entry.grid(row=3, column=0, pady=(0, 15), padx=10, sticky=tk.W)
        
        # Form
        ctk.CTkLabel(inner_form, text="Form:",
                    font=ctk.CTkFont(size=13, weight="bold")).grid(row=4, column=0, sticky=tk.W, pady=(10, 5), padx=10)
        self.form_var = tk.StringVar()
        self.form_combo = ctk.CTkComboBox(inner_form, width=450, height=35, variable=self.form_var, values=["Tablet", "Capsule", "Syrup", "Injection", "Drops", "Cream", "Inhaler", "Other"])
        self.form_combo.grid(row=5, column=0, pady=(0, 15), padx=10, sticky=tk.W)
        
        # Frequency
        ctk.CTkLabel(inner_form, text="Frequency:", font=ctk.CTkFont(size=13, weight="bold")).grid(row=6, column=0, sticky=tk.W, pady=(10, 5), padx=10)
        self.frequency_entry = ctk.CTkEntry(inner_form, width=450, height=35, placeholder_text="e.g., Once daily, Twice daily, As needed")
        self.frequency_entry.grid(row=7, column=0, pady=(0, 15), padx=10, sticky=tk.W)
        
        # Active Ingredients
        ctk.CTkLabel(inner_form, text="Active Ingredients:", font=ctk.CTkFont(size=13, weight="bold")).grid(row=8, column=0, sticky=tk.W, pady=(10, 5), padx=10)
        self.ingredients_entry = ctk.CTkEntry(inner_form, width=450, height=35, placeholder_text="For matching OCR text")
        self.ingredients_entry.grid(row=9, column=0, pady=(0, 15), padx=10, sticky=tk.W)
        
        # Notes
        ctk.CTkLabel(inner_form, text="Notes:",font=ctk.CTkFont(size=13, weight="bold")).grid(row=10, column=0, sticky=tk.W, pady=(10, 5), padx=10)
        
        notes_container = ctk.CTkFrame(inner_form, fg_color=("gray85", "gray20"))
        notes_container.grid(row=11, column=0, pady=(0, 20), padx=10, sticky=tk.W)
        
        self.notes_text = tk.Text(notes_container, width=55, height=5, bg=("#F0F0F0" if ctk.get_appearance_mode() == "Light" else "#2B2B2B"), fg=("#000000" if ctk.get_appearance_mode() == "Light" else "#FFFFFF"), relief=tk.FLAT, font=("Arial", 11), borderwidth=0, highlightthickness=0)
        self.notes_text.pack(padx=2, pady=2)
        
        # Buttons
        button_frame = ctk.CTkFrame(inner_form, fg_color="transparent")
        button_frame.grid(row=12, column=0, pady=20, padx=10)
        
        ctk.CTkButton(button_frame, text="Save Medicine", command=self.save_medicine, width=150, height=40, fg_color=("#2CC985", "#2FA572"), hover_color=("#28B075", "#268F63"), font=ctk.CTkFont(size=14, weight="bold")).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(button_frame, text="Clear Form", command=self.clear_form, width=150, height=40, fg_color=("#FF9800", "#F57C00"), hover_color=("#FB8C00", "#E65100")).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel_edit, width=150, height=40, fg_color=("gray60", "gray40"), hover_color=("gray55", "gray35")).pack(side=tk.LEFT, padx=5)

    def setup_schedule_tab(self):
        # Medicine selection section
        top_frame = ctk.CTkFrame(self.schedule_tab, corner_radius=10)
        top_frame.pack(fill=tk.X, padx=15, pady=15)
        
        top_inner = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_inner.pack(fill=tk.X, padx=20, pady=20)
        
        ctk.CTkLabel(top_inner, text="Select Medicine:", font=ctk.CTkFont(size=14, weight="bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.schedule_medicine_var = tk.StringVar()
        self.schedule_medicine_combo = ctk.CTkComboBox(top_inner, width=400, height=35,variable=self.schedule_medicine_var,state='readonly', command=self.load_medicine_schedules)
        self.schedule_medicine_combo.pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(top_inner, text="Refresh List", command=self.refresh_schedule_medicines,height=35).pack(side=tk.LEFT, padx=10)
        
        # Schedule form section
        form_frame = ctk.CTkFrame(self.schedule_tab, corner_radius=10)
        form_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Add Intake Schedule",font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 15), padx=20, anchor="w")
        
        form_inner = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_inner.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Time of day
        time_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        time_frame.pack(fill=tk.X, pady=5)
        
        ctk.CTkLabel(time_frame, text="Time of Day:*",font=ctk.CTkFont(size=13, weight="bold"),width=150).pack(side=tk.LEFT, padx=5)
        
        self.time_entry = ctk.CTkEntry(time_frame, width=150, height=35, placeholder_text="HH:MM")
        self.time_entry.pack(side=tk.LEFT, padx=5)
        
        ctk.CTkLabel(time_frame, text="(24-hour format)",text_color=("gray60", "gray50")).pack(side=tk.LEFT, padx=5)
        
        # Quick time buttons
        time_btn_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        time_btn_frame.pack(fill=tk.X, pady=10, padx=(160, 0))
        
        ctk.CTkButton(time_btn_frame, text="Morning (08:00)",command=lambda: self.set_time("08:00"), width=140, height=30, fg_color=("gray70", "gray30"), hover_color=("gray65", "gray25")).pack(side=tk.LEFT, padx=3)
        
        ctk.CTkButton(time_btn_frame, text="Afternoon (14:00)", command=lambda: self.set_time("14:00"), width=150, height=30, fg_color=("gray70", "gray30"), hover_color=("gray65", "gray25")).pack(side=tk.LEFT, padx=3)
        
        ctk.CTkButton(time_btn_frame, text="Evening (20:00)",command=lambda: self.set_time("20:00"), width=140, height=30, fg_color=("gray70", "gray30"), hover_color=("gray65", "gray25")).pack(side=tk.LEFT, padx=3)
        
        # With food
        food_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        food_frame.pack(fill=tk.X, pady=10)
        
        ctk.CTkLabel(food_frame, text="With Food:", font=ctk.CTkFont(size=13, weight="bold"), width=150).pack(side=tk.LEFT, padx=5)
        
        self.with_food_var = tk.StringVar(value="No preference")
        with_food_combo = ctk.CTkComboBox(food_frame, width=250, height=35, variable=self.with_food_var,values=["Before food", "After food", "With food", "No preference"])
        with_food_combo.pack(side=tk.LEFT, padx=5)
        
        # Special instructions
        inst_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        inst_frame.pack(fill=tk.X, pady=10)
        
        ctk.CTkLabel(inst_frame, text="Instructions:",font=ctk.CTkFont(size=13, weight="bold"),width=150).pack(side=tk.LEFT, padx=5)
        
        self.special_instructions_entry = ctk.CTkEntry(inst_frame, width=450, height=35, placeholder_text="Any special instructions")
        self.special_instructions_entry.pack(side=tk.LEFT, padx=5)
        
        # Add button
        ctk.CTkButton(form_inner, text="Add Schedule", command=self.add_intake_schedule, width=200, height=40,fg_color=("#2CC985", "#2FA572"), hover_color=("#28B075", "#268F63"), font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)
        
        # Schedule list section
        list_frame = ctk.CTkFrame(self.schedule_tab, corner_radius=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        ctk.CTkLabel(list_frame, text="Current Schedules", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10), padx=20, anchor="w")
        
        # Treeview container
        tree_container = ctk.CTkFrame(list_frame, fg_color=("gray85", "gray20"))
        tree_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        from tkinter import ttk
        
        tree_scroll_frame = tk.Frame(tree_container, bg=("#F0F0F0" if ctk.get_appearance_mode() == "Light" else "#2B2B2B"))
        tree_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        columns = ("ID", "Medicine", "Time", "With Food", "Instructions")
        self.schedule_tree = ttk.Treeview(tree_scroll_frame, columns=columns, show='headings', height=10)
        
        self.schedule_tree.heading("ID", text="ID")
        self.schedule_tree.heading("Medicine", text="Medicine")
        self.schedule_tree.heading("Time", text="Time")
        self.schedule_tree.heading("With Food", text="With Food")
        self.schedule_tree.heading("Instructions", text="Special Instructions")
        
        self.schedule_tree.column("ID", width=50)
        self.schedule_tree.column("Medicine", width=200)
        self.schedule_tree.column("Time", width=100)
        self.schedule_tree.column("With Food", width=120)
        self.schedule_tree.column("Instructions", width=350)
        
        scrollbar = ttk.Scrollbar(tree_scroll_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscroll=scrollbar.set)
        
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Deleting button
        ctk.CTkButton(list_frame, text="Delete Selected Schedule",
                     command=self.delete_selected_schedule,
                     height=35,
                     fg_color=("#E63946", "#D62828"),
                     hover_color=("#C92A35", "#B91F26")).pack(pady=(0, 20))
    
    # button functions
    
    def set_time(self, time_str):
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, time_str)
    
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.refresh_medicine_list()

    def on_medicine_double_click(self, event):
        self.view_medicine_details()

    def search_medicines(self):
        search_term = self.search_entry.get()
        
        for item in self.medicine_tree.get_children():
            self.medicine_tree.delete(item)
        
        if not search_term:
            self.refresh_medicine_list()
            return
        
        medicines = self.db.search_medicine_by_name(search_term)
        for med in medicines:
            self.medicine_tree.insert('', tk.END, values=(med[0], med[1], med[2], med[3], med[4]))
        
        self.status_label.configure(text=f"🔍 Found {len(medicines)} matching medicines")

    def delete_selected_medicine(self):
        selection = self.medicine_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a medicine to delete")
            return
        
        item = self.medicine_tree.item(selection[0])
        medicine_id = item['values'][0]
        medicine_name = item['values'][1]
        
        confirm = messagebox.askyesno("Confirm Delete",  f"Are you sure you want to delete '{medicine_name}'?\n\nThis will also delete all associated schedules.")
        
        if confirm:
            self.db.delete_medicine(medicine_id)
            self.refresh_medicine_list()
            self.status_label.configure(text=f"🗑️ Deleted: {medicine_name}")

    def view_medicine_details(self):
        selection = self.medicine_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a medicine to view details")
            return
        
        item = self.medicine_tree.item(selection[0])
        medicine_id = item['values'][0]
        
        medicine = self.db.get_medicine_by_id(medicine_id)
        schedules = self.db.get_schedules_for_medicine(medicine_id)
        
        details = f"MEDICINE DETAILS\n{'='*70}\n\n"
        details += f"Name: {medicine[1]}\n"
        details += f"Dosage: {medicine[2]}\n"
        details += f"Form: {medicine[3]}\n"
        details += f"Frequency: {medicine[4]}\n"
        details += f"Active Ingredients: {medicine[6]}\n"
        details += f"Notes: {medicine[5]}\n\n"
        
        details += f"INTAKE SCHEDULE\n{'-'*70}\n"
        if schedules:
            for schedule in schedules:
                details += f"• {schedule[2]} - {schedule[3]} - {schedule[4]}\n"
        else:
            details += "No schedules set\n"
        
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', details)
    
    def refresh_medicine_list(self):
        for item in self.medicine_tree.get_children():
            self.medicine_tree.delete(item)
        
        medicines = self.db.get_all_medicines()
        for med in medicines:
            self.medicine_tree.insert('', tk.END, values=(med[0], med[1], med[2], med[3], med[4]))
        
        self.status_label.configure(text=f"✓ Loaded {len(medicines)} medicines")

    def save_medicine(self):
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showerror("Validation Error", "Medicine name is required!")
            return
        
        dosage = self.dosage_entry.get().strip()
        form = self.form_var.get()
        frequency = self.frequency_entry.get().strip()
        ingredients = self.ingredients_entry.get().strip()
        notes = self.notes_text.get('1.0', tk.END).strip()
        
        if self.current_medicine_id:
            self.db.update_medicine(self.current_medicine_id, name, dosage, form, frequency, notes, ingredients)
            messagebox.showinfo("Success", f"Medicine '{name}' updated successfully!")
            self.status_label.configure(text=f"✓ Updated: {name}")
        else:
            medicine_id = self.db.add_medicine(name, dosage, form, frequency, notes, ingredients)
            messagebox.showinfo("Success", f"Medicine '{name}' added successfully!\nID: {medicine_id}")
            self.status_label.configure(text=f"✓ Added: {name}")
        
        self.clear_form()
        self.refresh_medicine_list()
        self.tabview.set("Medicine List")

    def edit_selected_medicine(self):
        selection = self.medicine_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a medicine to edit")
            return
        
        item = self.medicine_tree.item(selection[0])
        medicine_id = item['values'][0]
        
        medicine = self.db.get_medicine_by_id(medicine_id)
        
        self.current_medicine_id = medicine_id
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, medicine[1])
        
        self.dosage_entry.delete(0, tk.END)
        self.dosage_entry.insert(0, medicine[2])
        
        self.form_var.set(medicine[3])
        
        self.frequency_entry.delete(0, tk.END)
        self.frequency_entry.insert(0, medicine[4])
        
        self.ingredients_entry.delete(0, tk.END)
        self.ingredients_entry.insert(0, medicine[6])
        
        self.notes_text.delete('1.0', tk.END)
        self.notes_text.insert('1.0', medicine[5])
        
        self.tabview.set("Add/Edit Medicine")
        self.status_label.configure(text=f"Editing: {medicine[1]}")

    def clear_form(self):
        self.current_medicine_id = None
        self.name_entry.delete(0, tk.END)
        self.dosage_entry.delete(0, tk.END)
        self.form_var.set('')
        self.frequency_entry.delete(0, tk.END)
        self.ingredients_entry.delete(0, tk.END)
        self.notes_text.delete('1.0', tk.END)
        self.status_label.configure(text="🔄 Form cleared")

    def cancel_edit(self):
        self.clear_form()
        self.tabview.set("Medicine List")

    # schedule tab function

    def refresh_schedule_medicines(self):
        medicines = self.db.get_all_medicines()
        medicine_list = [f"{med[0]} - {med[1]}" for med in medicines]
        self.schedule_medicine_combo.configure(values=medicine_list)
        if medicine_list:
            self.schedule_medicine_combo.set(medicine_list[0])
        self.load_all_schedules()

    def load_medicine_schedules(self, event=None):
        self.load_all_schedules()

    def load_all_schedules(self):
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        medicines = self.db.get_all_medicines()
        for med in medicines:
            schedules = self.db.get_schedules_for_medicine(med[0])
            for schedule in schedules:
                self.schedule_tree.insert('', tk.END, values=(
                    schedule[0],
                    med[1],
                    schedule[2],
                    schedule[3],
                    schedule[4]
                ))
    
    def add_intake_schedule(self):
        selected = self.schedule_medicine_var.get()
        if not selected:
            messagebox.showwarning("No Medicine", "Please select a medicine first")
            return
        
        medicine_id = int(selected.split(' - ')[0])
        time_of_day = self.time_entry.get().strip()
        
        if not time_of_day:
            messagebox.showerror("Validation Error", "Time is required!")
            return
        
        try:
            datetime.strptime(time_of_day, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Please use HH:MM format (24-hour)")
            return
        
        with_food = self.with_food_var.get()
        instructions = self.special_instructions_entry.get().strip()
        
        self.db.add_schedule(medicine_id, time_of_day, with_food, instructions)
        messagebox.showinfo("Success", f"Schedule added for {time_of_day}")
        
        self.time_entry.delete(0, tk.END)
        self.special_instructions_entry.delete(0, tk.END)
        
        self.load_all_schedules()
        self.status_label.configure(text="✓ Schedule added successfully")

    def delete_selected_schedule(self):
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a schedule to delete")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_id = item['values'][0]
        
        confirm = messagebox.askyesno("Confirm Delete", "Delete this schedule?")
        if confirm:
            self.db.delete_schedule(schedule_id)
            self.load_all_schedules()
            self.status_label.configure(text="Schedule deleted")


if __name__ == "__main__":
    root = ctk.CTk()
    app = MedicineDatabaseGUI(root)
    root.mainloop()