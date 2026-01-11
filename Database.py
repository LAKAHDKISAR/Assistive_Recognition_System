import sqlite3
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


class MedicineDatabase:
    def __init__(self, db_name="medicine_db.sqlite"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self): #initializing the sqlite database with tables
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Creating the medicines table
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
        
        # Createing the intake schedule table  
        #putting python string literals
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
        
        # Creating the intake history table
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

    # updating details of a medicine
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


    # taking the medicine with their id
    def get_medicine_by_id(self, medicine_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM medicines WHERE id = ?', (medicine_id,))
        medicine = cursor.fetchone()
        
        conn.close()
        return medicine
    
    # taking all the medicine from the database
    def get_all_medicines(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM medicines ORDER BY medicine_name')
        medicines = cursor.fetchall()
        
        conn.close()
        return medicines
    

    # ---- 
    
    # schedule for medicine intake
    def add_schedule(self, medicine_id, time_of_day, with_food="No preference", special_instructions=""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO intake_schedule (medicine_id, time_of_day, with_food, special_instructions)
            VALUES (?, ?, ?, ?)
        ''', (medicine_id, time_of_day, with_food, special_instructions))
        
        conn.commit()
        conn.close()


    # removing the schedule for a medicine
    def delete_schedule(self, schedule_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM intake_schedule WHERE id = ?', (schedule_id,))
        
        conn.commit()
        conn.close()

    # getting schedule for a medicine
    def get_schedules_for_medicine(self, medicine_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM intake_schedule WHERE medicine_id = ?', (medicine_id,))
        schedules = cursor.fetchall()
        
        conn.close()
        return schedules
    
    #getting current schedule of medicines based on time
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
    
    #function log to keep log about medicine intake
    def log_intake(self, medicine_id, scheduled_time, status="Taken"):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO intake_history (medicine_id, scheduled_time, status)
            VALUES (?, ?, ?)
        ''', (medicine_id, scheduled_time, status))
        
        conn.commit()
        conn.close()
    

    # --------

    #searching medicine by name or other ingredients 
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
    

    # gui --------


class MedicineDatabaseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Medicine Database Manager")
        self.root.geometry("1000x700")

        self.db = MedicineDatabase()
        self.current_medicine_id = None
        
        self.setup_ui()
        
        self.setup_list_tab()

        self.setup_edit_tab()

        self.setup_schedule_tab()
        self.refresh_medicine_list()

    def setup_ui(self):

        # Main container
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Medicine List tab
        self.list_tab = tk.Frame(self.notebook)
        self.notebook.add(self.list_tab, text="Medicine List")
        
        # Adding or Editing the Medicine tab
        self.edit_tab = tk.Frame(self.notebook)
        self.notebook.add(self.edit_tab, text="Add or Edit Medicine")
        
        # Intake schedule managing tab
        self.schedule_tab = tk.Frame(self.notebook)
        self.notebook.add(self.schedule_tab, text="Intake Schedule")
        
        # The status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_list_tab(self):
        # Search frame
        search_frame = tk.Frame(self.list_tab)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.search_medicines())
        
        tk.Button(search_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Refresh", command=self.refresh_medicine_list).pack(side=tk.LEFT, padx=5)
        
        # Medicine list frame
        list_frame = tk.Frame(self.list_tab)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tree view for medicine list
        columns = ("ID", "Name", "Dosage", "Form", "Frequency")
        self.medicine_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.medicine_tree.heading(col, text=col)
            if col == "ID":
                self.medicine_tree.column(col, width=50)
            elif col == "Name":
                self.medicine_tree.column(col, width=200)
            else:
                self.medicine_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.medicine_tree.yview)
        self.medicine_tree.configure(yscroll=scrollbar.set)
        
        self.medicine_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.medicine_tree.bind('<Double-1>', self.on_medicine_double_click)
        
        # All the action buttons
        button_frame = tk.Frame(self.list_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(button_frame, text="View Details", command=self.view_medicine_details, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit", command=self.edit_selected_medicine,bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=self.delete_selected_medicine,bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Displaying the medicine details
        details_frame = tk.LabelFrame(self.list_tab, text="Medicine Details", padx=10, pady=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        from tkinter import scrolledtext
        self.details_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)


    def setup_edit_tab(self):
        # Form frame
        form_frame = tk.Frame(self.edit_tab, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Medicine Name
        tk.Label(form_frame, text="Medicine Name:*", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = tk.Entry(form_frame, width=50)
        self.name_entry.grid(row=0, column=1, pady=5, sticky=tk.W)
        
        # Dosage
        tk.Label(form_frame, text="Dosage:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dosage_entry = tk.Entry(form_frame, width=50)
        self.dosage_entry.grid(row=1, column=1, pady=5, sticky=tk.W)
        tk.Label(form_frame, text="e.g., 500mg, 10ml", fg="gray").grid(row=1, column=2, sticky=tk.W, padx=5)
        
        # Form for tablet, capsule, all that stuff
        tk.Label(form_frame, text="Form:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.form_var = tk.StringVar()
        form_combo = ttk.Combobox(form_frame, textvariable=self.form_var, width=47,values=["Tablet", "Capsule", "Syrup", "Injection", "Drops", "Cream", "Inhaler", "Other"])
        form_combo.grid(row=2, column=1, pady=5, sticky=tk.W)
        
        # Frequency
        tk.Label(form_frame, text="Frequency:", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.frequency_entry = tk.Entry(form_frame, width=50)
        self.frequency_entry.grid(row=3, column=1, pady=5, sticky=tk.W)
        tk.Label(form_frame, text="e.g., Once daily, Twice daily, As needed", fg="gray").grid(row=3, column=2, sticky=tk.W, padx=5)
        
        # Active Ingredients
        tk.Label(form_frame, text="Active Ingredients:", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, pady=5)
        self.ingredients_entry = tk.Entry(form_frame, width=50)
        self.ingredients_entry.grid(row=4, column=1, pady=5, sticky=tk.W)
        tk.Label(form_frame, text="For matching OCR text", fg="gray").grid(row=4, column=2, sticky=tk.W, padx=5)
        
        # Notes
        tk.Label(form_frame, text="Notes:", font=("Arial", 10)).grid(row=5, column=0, sticky=tk.W, pady=5)
        self.notes_text = scrolledtext.ScrolledText(form_frame, width=38, height=5)
        self.notes_text.grid(row=5, column=1, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        tk.Button(button_frame, text="Save Medicine", command=self.save_medicine,bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Clear Form", command=self.clear_form,bg="#FF9800", fg="white", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_edit,bg="#9E9E9E", fg="white", font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
    

    def setup_schedule_tab(self):
        # Medicine selection
        top_frame = tk.Frame(self.schedule_tab, padx=10, pady=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="Select Medicine:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.schedule_medicine_var = tk.StringVar()
        self.schedule_medicine_combo = ttk.Combobox(top_frame, textvariable=self.schedule_medicine_var, width=40, state='readonly')
        self.schedule_medicine_combo.pack(side=tk.LEFT, padx=5)
        self.schedule_medicine_combo.bind('<<ComboboxSelected>>', self.load_medicine_schedules)
        
        tk.Button(top_frame, text="Refresh List", command=self.refresh_schedule_medicines).pack(side=tk.LEFT, padx=5)
        
        # Schedule form frame
        form_frame = tk.LabelFrame(self.schedule_tab, text="Add Intake Schedule", padx=10, pady=10)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Time of day
        tk.Label(form_frame, text="Time of Day:*").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.time_entry = tk.Entry(form_frame, width=20)
        self.time_entry.grid(row=0, column=1, pady=5, sticky=tk.W, padx=5)
        tk.Label(form_frame, text="Format: HH:MM (24-hour)", fg="gray").grid(row=0, column=2, sticky=tk.W)
        
        # Quick time buttons
        time_button_frame = tk.Frame(form_frame)
        time_button_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        tk.Button(time_button_frame, text="Morning (08:00)", command=lambda: self.time_entry.delete(0, tk.END) or self.time_entry.insert(0, "08:00")).pack(side=tk.LEFT, padx=2)
        tk.Button(time_button_frame, text="Afternoon (14:00)", command=lambda: self.time_entry.delete(0, tk.END) or self.time_entry.insert(0, "14:00")).pack(side=tk.LEFT, padx=2)
        tk.Button(time_button_frame, text="Evening (20:00)", command=lambda: self.time_entry.delete(0, tk.END) or self.time_entry.insert(0, "20:00")).pack(side=tk.LEFT, padx=2)
        
        # With food
        tk.Label(form_frame, text="With Food:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.with_food_var = tk.StringVar(value="No preference")
        with_food_combo = ttk.Combobox(form_frame, textvariable=self.with_food_var, width=18,values=["Before food", "After food", "With food", "No preference"])
        with_food_combo.grid(row=2, column=1, pady=5, sticky=tk.W, padx=5)
        
        # Special instructions
        tk.Label(form_frame, text="Special Instructions:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.special_instructions_entry = tk.Entry(form_frame, width=50)
        self.special_instructions_entry.grid(row=3, column=1, columnspan=2, pady=5, sticky=tk.W, padx=5)
        
        tk.Button(form_frame, text="Add Schedule", command=self.add_intake_schedule,bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(row=4, column=1, pady=10, sticky=tk.W, padx=5)
        
        # Schedule list frame
        list_frame = tk.LabelFrame(self.schedule_tab, text="Current Schedules", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for schedules
        columns = ("ID", "Medicine", "Time", "With Food", "Instructions")
        self.schedule_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.schedule_tree.heading("ID", text="ID")
        self.schedule_tree.heading("Medicine", text="Medicine")
        self.schedule_tree.heading("Time", text="Time")
        self.schedule_tree.heading("With Food", text="With Food")
        self.schedule_tree.heading("Instructions", text="Special Instructions")
        
        self.schedule_tree.column("ID", width=50)
        self.schedule_tree.column("Medicine", width=200)
        self.schedule_tree.column("Time", width=100)
        self.schedule_tree.column("With Food", width=120)
        self.schedule_tree.column("Instructions", width=300)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscroll=scrollbar.set)
        
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Delete schedule button
        tk.Button(list_frame, text="Delete Selected Schedule", command=self.delete_selected_schedule,bg="#f44336", fg="white").pack(pady=5)
    
    #Buttons functionalities

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.refresh_medicine_list()

    def on_medicine_double_click(self, event):
        self.view_medicine_details()

    #searching medicine
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
        
        self.status_bar.config(text=f"Found {len(medicines)} matching medicines")

    # Deleting 
    def delete_selected_medicine(self):
        selection = self.medicine_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a medicine to delete")
            return
        
        item = self.medicine_tree.item(selection[0])
        medicine_id = item['values'][0]
        medicine_name = item['values'][1]
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{medicine_name}'?\n\nThis will also delete all associated schedules.")
        
        if confirm:
            self.db.delete_medicine(medicine_id)
            self.refresh_medicine_list()
            self.status_bar.config(text=f"Deleted: {medicine_name}")

    #viewing details logic
    def view_medicine_details(self):
        selection = self.medicine_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a medicine to view details")
            return
        
        item = self.medicine_tree.item(selection[0])
        medicine_id = item['values'][0]
        
        medicine = self.db.get_medicine_by_id(medicine_id)
        schedules = self.db.get_schedules_for_medicine(medicine_id)
        
        details = f"Medicine Details\n{'='*60}\n\n"
        details += f"Name: {medicine[1]}\n"
        details += f"Dosage: {medicine[2]}\n"
        details += f"Form: {medicine[3]}\n"
        details += f"Frequency: {medicine[4]}\n"
        details += f"Active Ingredients: {medicine[6]}\n"
        details += f"Notes: {medicine[5]}\n\n"
        
        details += f"Intake Schedule\n{'-'*60}\n"
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
        
        self.status_bar.config(text=f"Loaded {len(medicines)} medicines")

    # -- saving medicine
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
            # Update existing medicine
            self.db.update_medicine(self.current_medicine_id, name, dosage, form, frequency, notes, ingredients)
            messagebox.showinfo("Success", f"Medicine '{name}' updated successfully!")
            self.status_bar.config(text=f"Updated: {name}")
        else:
            # Add new medicine
            medicine_id = self.db.add_medicine(name, dosage, form, frequency, notes, ingredients)
            messagebox.showinfo("Success", f"Medicine '{name}' added successfully!\nID: {medicine_id}")
            self.status_bar.config(text=f"Added: {name}")
        
        self.clear_form()
        self.refresh_medicine_list()
        self.notebook.select(self.list_tab)


    #editing selected medicine
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
        
        self.notebook.select(self.edit_tab)
        self.status_bar.config(text=f"Editing: {medicine[1]}")

    def clear_form(self):
        self.current_medicine_id = None
        self.name_entry.delete(0, tk.END)
        self.dosage_entry.delete(0, tk.END)
        self.form_var.set('')
        self.frequency_entry.delete(0, tk.END)
        self.ingredients_entry.delete(0, tk.END)
        self.notes_text.delete('1.0', tk.END)
        self.status_bar.config(text="Form cleared")

    def cancel_edit(self):
        self.clear_form()
        self.notebook.select(self.list_tab)


    #---schedule tab

    def refresh_schedule_medicines(self):
        medicines = self.db.get_all_medicines()
        medicine_list = [f"{med[0]} - {med[1]}" for med in medicines]
        self.schedule_medicine_combo['values'] = medicine_list
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
                    schedule[0],  # ID
                    med[1],  # Medicine name
                    schedule[2], # Time of medicine
                    schedule[3],  # With food
                    schedule[4]   # Instructions 
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
        
        # Validate time format
        try:
            datetime.strptime(time_of_day, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Please use HH:MM format (24-hour)")
            return
        
        with_food = self.with_food_var.get()
        instructions = self.special_instructions_entry.get().strip()
        
        self.db.add_schedule(medicine_id, time_of_day, with_food, instructions)
        messagebox.showinfo("Success", f"Schedule added for {time_of_day}")
        
        # Clear form
        self.time_entry.delete(0, tk.END)
        self.special_instructions_entry.delete(0, tk.END)
        
        self.load_all_schedules()
        self.status_bar.config(text="Schedule added successfully")

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
            self.status_bar.config(text="Schedule deleted")

if __name__ == "__main__":
    root = tk.Tk()
    app = MedicineDatabaseGUI(root)
    root.mainloop()