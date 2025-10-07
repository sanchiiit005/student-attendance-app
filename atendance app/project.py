import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
from datetime import datetime

class StudentAttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Attendance Manager")
        self.root.geometry("1200x700")

        # App theme
        self.theme = tk.StringVar(value="light")
        self.style = ttk.Style(self.root)
        self.set_theme()

        # Data
        self.students = {} # {class: [student_id, name]}
        self.attendance = {}  # {class: {date: {student_id: status}}}
        self.current_class = tk.StringVar()

        self.create_widgets()
        self.load_initial_data()

    def set_theme(self):
        if self.theme.get() == "light":
            self.root.configure(bg="#f0f0f0")
            self.style.theme_use('clam')
            self.style.configure('.', background='#f0f0f0', foreground='black')
            self.style.configure('TFrame', background='#f0f0f0')
            self.style.configure('TLabel', background='#f0f0f0', foreground='black')
            self.style.configure('TButton', background='#e0e0e0', foreground='black')
            self.style.configure('Treeview', background='white', foreground='black', fieldbackground='white')
            self.style.map('TButton', background=[('active', '#d0d0d0')])
        else: # Dark theme
            self.root.configure(bg="#2e2e2e")
            self.style.theme_use('clam')
            self.style.configure('.', background='#2e2e2e', foreground='white')
            self.style.configure('TFrame', background='#2e2e2e')
            self.style.configure('TLabel', background='#2e2e2e', foreground='white')
            self.style.configure('TButton', background='#555555', foreground='white')
            self.style.configure('Treeview', background='#333333', foreground='white', fieldbackground='#333333')
            self.style.map('TButton', background=[('active', '#666666')])

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Left Control Panel
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side="left", fill="y", padx=10)

        # Right Data Display Panel
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        # --- Left Panel Widgets ---

        # Theme Toggle
        theme_frame = ttk.LabelFrame(left_panel, text="Theme", padding="10")
        theme_frame.pack(fill="x", pady=10)
        ttk.Radiobutton(theme_frame, text="Light", variable=self.theme, value="light", command=self.set_theme).pack(side="left", padx=5)
        ttk.Radiobutton(theme_frame, text="Dark", variable=self.theme, value="dark", command=self.set_theme).pack(side="left", padx=5)

        # Class Management
        class_frame = ttk.LabelFrame(left_panel, text="Class Management", padding="10")
        class_frame.pack(fill="x", pady=10)
        ttk.Label(class_frame, text="Select Class:").pack(pady=5)
        self.class_combo = ttk.Combobox(class_frame, textvariable=self.current_class, state='readonly')
        self.class_combo.pack(fill="x", pady=5)
        self.class_combo.bind("<<ComboboxSelected>>", self.on_class_change)
        ttk.Button(class_frame, text="Add New Class", command=self.add_class).pack(fill="x", pady=5)


        # Student Management
        student_frame = ttk.LabelFrame(left_panel, text="Student Management", padding="10")
        student_frame.pack(fill="x", pady=10)
        ttk.Button(student_frame, text="Add Student", command=self.add_student).pack(fill="x", pady=5)
        ttk.Button(student_frame, text="Remove Selected Student", command=self.remove_student).pack(fill="x", pady=5)

        # Data Management
        data_frame = ttk.LabelFrame(left_panel, text="Data Import/Export", padding="10")
        data_frame.pack(fill="x", pady=10)
        ttk.Button(data_frame, text="Import Students (CSV)", command=self.import_students_csv).pack(fill="x", pady=5)
        ttk.Button(data_frame, text="Export Attendance (CSV)", command=self.export_attendance_csv).pack(fill="x", pady=5)


        # --- Right Panel Widgets ---

        # Student List
        student_list_frame = ttk.Frame(right_panel)
        student_list_frame.pack(fill="both", expand=True, pady=10)

        self.student_tree = ttk.Treeview(student_list_frame, columns=("id", "name", "status"), show="headings")
        self.student_tree.heading("id", text="Student ID")
        self.student_tree.heading("name", text="Name")
        self.student_tree.heading("status", text="Attendance Status")
        self.student_tree.pack(side="left", fill="both", expand=True)
        self.student_tree.bind("<<TreeviewSelect>>", self.show_student_details)

        # Student Details Panel
        self.detail_panel = ttk.LabelFrame(right_panel, text="Student Details", padding="10")
        self.detail_panel.pack(fill="x", pady=10)

        self.detail_name = tk.StringVar()
        self.detail_id = tk.StringVar()
        ttk.Label(self.detail_panel, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(self.detail_panel, textvariable=self.detail_name).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(self.detail_panel, text="ID:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(self.detail_panel, textvariable=self.detail_id).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Attendance Buttons
        attendance_button_frame = ttk.Frame(self.detail_panel)
        attendance_button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(attendance_button_frame, text="Mark Present", command=lambda: self.mark_attendance("Present")).pack(side="left", padx=5)
        ttk.Button(attendance_button_frame, text="Mark Absent", command=lambda: self.mark_attendance("Absent")).pack(side="left", padx=5)

    def on_class_change(self, event):
        self.populate_student_list()
        self.clear_details()

    def add_class(self):
        class_name = self.simple_input_dialog("Add Class", "Enter new class name:")
        if class_name:
            if class_name not in self.students:
                self.students[class_name] = []
                self.attendance[class_name] = {}
                self.update_class_list()
                self.current_class.set(class_name)
                self.populate_student_list()
            else:
                messagebox.showerror("Error", "Class already exists.")

    def update_class_list(self):
        self.class_combo['values'] = sorted(list(self.students.keys()))

    def add_student(self):
        if not self.current_class.get():
            messagebox.showerror("Error", "Please select or add a class first.")
            return

        student_name = self.simple_input_dialog("Add Student", "Enter student name:")
        student_id = self.simple_input_dialog("Add Student", "Enter student ID:")

        if student_name and student_id:
            current_students = self.students[self.current_class.get()]
            if any(s[0] == student_id for s in current_students):
                messagebox.showerror("Error", "Student with this ID already exists in this class.")
                return
            current_students.append([student_id, student_name])
            self.populate_student_list()

    def remove_student(self):
        selected_item = self.student_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a student to remove.")
            return
        
        student_id = self.student_tree.item(selected_item, "values")[0]
        current_students = self.students[self.current_class.get()]
        self.students[self.current_class.get()] = [s for s in current_students if s[0] != student_id]
        self.populate_student_list()
        self.clear_details()

    def populate_student_list(self):
        for i in self.student_tree.get_children():
            self.student_tree.delete(i)
        
        cls = self.current_class.get()
        if not cls:
            return

        today = datetime.now().strftime("%Y-%m-%d")
        today_attendance = self.attendance.get(cls, {}).get(today, {})
        
        for student_id, name in sorted(self.students.get(cls, []), key=lambda x: x[1]):
            status = today_attendance.get(student_id, "Not Marked")
            self.student_tree.insert("", "end", values=(student_id, name, status))

    def mark_attendance(self, status):
        selected_item = self.student_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a student.")
            return

        student_id = self.student_tree.item(selected_item, "values")[0]
        cls = self.current_class.get()
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in self.attendance[cls]:
            self.attendance[cls][today] = {}
        
        self.attendance[cls][today][student_id] = status
        self.populate_student_list() # Refresh to show new status

    def show_student_details(self, event):
        selected_item = self.student_tree.selection()
        if selected_item:
            student_id, name, _ = self.student_tree.item(selected_item, "values")
            self.detail_id.set(student_id)
            self.detail_name.set(name)

    def clear_details(self):
        self.detail_id.set("")
        self.detail_name.set("")

    def import_students_csv(self):
        cls = self.current_class.get()
        if not cls:
            messagebox.showerror("Error", "Please select a class to import students into.")
            return

        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader) # Skip header
                for row in reader:
                    if len(row) == 2:
                        student_id, name = row
                        if not any(s[0] == student_id for s in self.students[cls]):
                            self.students[cls].append([student_id, name])
            self.populate_student_list()
            messagebox.showinfo("Success", "Students imported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {e}")

    def export_attendance_csv(self):
        cls = self.current_class.get()
        if not cls:
            messagebox.showerror("Error", "Please select a class to export.")
            return
            
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                # Header
                header = ["Date", "Student ID", "Student Name", "Status"]
                writer.writerow(header)
                # Data
                for date, records in sorted(self.attendance.get(cls, {}).items()):
                    for student_id, status in records.items():
                        student_name = next((s[1] for s in self.students[cls] if s[0] == student_id), "N/A")
                        writer.writerow([date, student_id, student_name, status])
            messagebox.showinfo("Success", f"Attendance for {cls} exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def simple_input_dialog(self, title, prompt):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        ttk.Label(dialog, text=prompt).pack(padx=20, pady=10)
        entry = ttk.Entry(dialog)
        entry.pack(padx=20, pady=5)
        entry.focus()
        
        result = None
        def on_ok():
            nonlocal result
            result = entry.get()
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=on_ok).pack(pady=10)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return result

    def load_initial_data(self):
        # Create some dummy data for demonstration
        self.students = {
            "Physics 101": [["1001", "Alice"], ["1002", "Bob"]],
            "History 202": [["2001", "Charlie"], ["2002", "Diana"]]
        }
        self.attendance = {
            "Physics 101": {
                "2023-10-26": {"1001": "Present", "1002": "Absent"}
            }
        }
        self.update_class_list()
        if self.students:
            self.current_class.set(list(self.students.keys())[0])
            self.on_class_change(None)

def main():
    root = tk.Tk()
    app = StudentAttendanceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
