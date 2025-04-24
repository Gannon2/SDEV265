import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import json

class AttendSmartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AttendSmart")
        self.root.geometry("1000x700")
        
        # Initialize files
        self.database_file = "database.json"
        self.queue_file = "queue.json"
        self.admins_file = "admins.json"
        self.history_file = "history.json"
        self.employees_file = "employees.json"
        
        # Create files if they don't exist
        self.initialize_files()
        
        # Custom fonts
        self.title_font = Font(family="Helvetica", size=16, weight="bold")
        self.label_font = Font(family="Helvetica", size=12)
        self.button_font = Font(family="Helvetica", size=10)
        
        # Create container frame
        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Initialize frames
        self.frames = {}
        for F in (CustomerView, AdminLogin, EmployeeView, AdminView):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        # Show customer view by default
        self.show_frame(CustomerView)
        
        # Auto-refresh setup
        self.auto_refresh_interval = 1000  # 1 second
        self.schedule_auto_refresh()
    
    def schedule_auto_refresh(self):
        """Schedule automatic refresh of all queue displays"""
        self.root.after(self.auto_refresh_interval, self.refresh_all_queues)
    
    def refresh_all_queues(self):
        """Refresh all queue displays in the application"""
        # Refresh CustomerView queue popup if it exists
        if hasattr(self.frames[CustomerView], 'queue_window') and self.frames[CustomerView].queue_window.winfo_exists():
            self.frames[CustomerView].refresh_queue_view()
        
        # Refresh EmployeeView queue tab
        if hasattr(self.frames[EmployeeView], 'queue_tree'):
            self.frames[EmployeeView].refresh_queue()
        
        # Refresh AdminView queue tab and monitors view
        if hasattr(self.frames[AdminView], 'queue_tree'):
            self.frames[AdminView].refresh_queue()
            if hasattr(self.frames[AdminView], 'monitors_window') and self.frames[AdminView].monitors_window.winfo_exists():
                self.frames[AdminView].refresh_monitors_view(self.frames[AdminView].monitors_tree)
        
        # Schedule the next refresh
        self.schedule_auto_refresh()
    
    def initialize_files(self):
        # Initialize all JSON files with default structure
        files = {
            self.database_file: [],
            self.queue_file: [],
            self.history_file: [],
            self.admins_file: [{
                "username": "admin",
                "password_hash": hashlib.sha256("admin".encode()).hexdigest()
            }],
            self.employees_file: [{
                "username": "employee",
                "password_hash": hashlib.sha256("employee".encode()).hexdigest()
            }]
        }
        
        for file, default_data in files.items():
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump(default_data, f)
            else:
                try:
                    with open(file, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    with open(file, 'w') as f:
                        json.dump(default_data, f)
    
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        if cont == AdminView:
            frame.build_admin_view()
        elif cont == EmployeeView:
            frame.build_employee_view()
    
    def verify_admin(self, username, password):
        return self._verify_credentials(username, password, self.admins_file)
    
    def verify_employee(self, username, password):
        return self._verify_credentials(username, password, self.employees_file)
    
    def _verify_credentials(self, username, password, file):
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return False
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            with open(file, 'r') as f:
                users = json.load(f)
                for user in users:
                    if user.get("username") == username and user.get("password_hash") == hashed_password:
                        return True
            
            messagebox.showerror("Error", "Invalid username or password")
            return False
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")
            return False

class CustomerView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        # Top frame for header elements
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # AttendSmart label in top-left
        self.title_label = tk.Label(top_frame, text="AttendSmart", 
                                  font=controller.title_font)
        self.title_label.pack(side=tk.LEFT)
        
        # Admin/Employee login button in top-right
        self.login_button = tk.Button(top_frame, text="Admin/Employee Login", 
                                    font=controller.button_font, 
                                    command=lambda: controller.show_frame(AdminLogin))
        self.login_button.pack(side=tk.RIGHT)
        
        # Welcome label
        self.welcome_label = tk.Label(self, text="Welcome", 
                                    font=controller.title_font)
        self.welcome_label.pack(pady=20)
        
        # Phone number entry
        self.phone_label = tk.Label(self, text="Please enter your phone number", 
                                  font=controller.label_font)
        self.phone_label.pack()
        
        self.phone_entry = tk.Entry(self, font=controller.label_font, justify='center')
        self.phone_entry.pack(pady=5, ipady=5)
        
        # Submit button for phone number
        self.submit_button = tk.Button(self, text="Submit", 
                                     font=controller.button_font, 
                                     command=self.check_phone_number)
        self.submit_button.pack(pady=10)
        
        # Response area
        self.response_frame = tk.Frame(self)
        self.response_frame.pack(pady=10)
        
        # Queue button (initially hidden)
        self.view_queue_button = tk.Button(self, text="View Queue", 
                                         font=controller.button_font, 
                                         command=self.show_queue_view, 
                                         state=tk.DISABLED)
        self.view_queue_button.pack(pady=10)

        # Back button (hidden initially)
        self.back_button = tk.Button(self, text="Back to Main", 
                                   font=controller.button_font,
                                   command=self.show_main_screen)
        self.back_button.pack(pady=10)
        self.back_button.pack_forget()
    
    def show_main_screen(self):
        """Reset the view to its initial state"""
        self.phone_entry.delete(0, tk.END)
        for widget in self.response_frame.winfo_children():
            widget.destroy()
        self.view_queue_button.config(state=tk.DISABLED)
        self.back_button.pack_forget()
        self.title_label.pack(side=tk.LEFT)  # Restore title if hidden
        self.welcome_label.pack(pady=20)  # Restore welcome label

    def check_phone_number(self):
        phone_number = self.phone_entry.get().strip()
        if not phone_number:
            messagebox.showerror("Error", "Please enter a phone number")
            return
        
        # Check database for registration
        name = self.lookup_in_database(phone_number)
        
        # Check if already in queue
        in_queue, queue_data = self.check_if_in_queue(phone_number)
        
        # Clear previous response
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        if in_queue:
            # Customer is already in queue - show their status
            self.show_queue_status(phone_number, name, queue_data)
        else:
            # Not in queue - proceed with registration/queue addition
            if name:
                # If found in database
                tk.Label(self.response_frame, text=f"Are you {name}?", 
                        font=self.controller.label_font).pack()
                tk.Button(self.response_frame, text="Yes", 
                        font=self.controller.button_font,
                        command=lambda: self.add_to_queue(name)).pack(side=tk.LEFT, padx=5)
                tk.Button(self.response_frame, text="No", 
                        font=self.controller.button_font,
                        command=self.ask_for_name).pack(side=tk.LEFT, padx=5)
            else:
                # If not found
                self.ask_for_name()

    def check_if_in_queue(self, phone_number):
        """Check if phone number is already in queue and return position"""
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
                
            # Get customer name from database
            name = self.lookup_in_database(phone_number)
            if not name:
                return False, None
                
            for idx, item in enumerate(queue):
                if item["name"] == name:
                    return True, {
                        "position": idx + 1,
                        "timestamp": item["timestamp"],
                        "status": item["status"]
                    }
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return False, None

    def show_queue_status(self, phone_number, name, queue_data):
        """Show the customer their current queue status"""
        # Hide the main title and welcome label to make more room
        self.title_label.pack_forget()
        self.welcome_label.pack_forget()
        
        # Calculate wait time
        try:
            timestamp = float(queue_data["timestamp"])
            wait_time = datetime.now() - datetime.fromtimestamp(timestamp)
            wait_time_str = str(wait_time).split('.')[0]  # Remove microseconds
        except:
            wait_time_str = "Unknown"
        
        # Show queue information
        tk.Label(self.response_frame, 
                text=f"You're already in the queue, {name}!",
                font=self.controller.label_font).pack(pady=5)
        
        tk.Label(self.response_frame, 
                text=f"Position: {queue_data['position']}",
                font=self.controller.label_font).pack()
        
        tk.Label(self.response_frame, 
                text=f"Status: {queue_data['status']}",
                font=self.controller.label_font).pack()
        
        tk.Label(self.response_frame, 
                text=f"Waiting time: {wait_time_str}",
                font=self.controller.label_font).pack(pady=10)
        
        # Add action buttons
        button_frame = tk.Frame(self.response_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Remove Me From Queue",
                font=self.controller.button_font,
                command=lambda: self.remove_from_queue(name)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Refresh Status",
                font=self.controller.button_font,
                command=lambda: self.check_phone_number()).pack(side=tk.LEFT, padx=5)
        
        # Show the back button and view queue button
        self.back_button.pack(pady=10)
        self.view_queue_button.config(state=tk.NORMAL)

    def remove_from_queue(self, name):
        """Remove customer from queue"""
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
            
            # Filter out the item to remove
            updated_queue = [item for item in queue if item["name"] != name]
            
            with open(self.controller.queue_file, 'w') as f:
                json.dump(updated_queue, f)
            
            messagebox.showinfo("Success", "You have been removed from the queue")
            self.show_main_screen()
        except (FileNotFoundError, json.JSONDecodeError):
            messagebox.showerror("Error", "Could not update queue")

    def ask_for_name(self):
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.response_frame, 
                text="What is your name? (first and last separated by spaces)", 
                font=self.controller.label_font).pack()
        
        self.name_entry = tk.Entry(self.response_frame, 
                                font=self.controller.label_font)
        self.name_entry.pack(pady=5)
        
        tk.Button(self.response_frame, text="Submit", 
                font=self.controller.button_font,
                command=self.register_name).pack()
    
    def register_name(self):
        full_name = self.name_entry.get().strip()
        if not full_name or len(full_name.split()) < 2:
            messagebox.showerror("Error", "Please enter both first and last name")
            return
        
        # Add to database
        phone_number = self.phone_entry.get().strip()
        timestamp = datetime.now().timestamp()
        
        with open(self.controller.database_file, 'r') as f:
            customers = json.load(f)
        
        customers.append({
            "phone": phone_number,
            "name": full_name,
            "registration_timestamp": timestamp
        })
        
        with open(self.controller.database_file, 'w') as f:
            json.dump(customers, f)
        
        # Add to queue
        self.add_to_queue(full_name)
    
    def add_to_queue(self, name):
        # Add to queue file
        timestamp = datetime.now().timestamp()
        
        with open(self.controller.queue_file, 'r') as f:
            queue = json.load(f)
        
        queue.append({
            "name": name,
            "status": "In Queue",
            "timestamp": timestamp
        })
        
        with open(self.controller.queue_file, 'w') as f:
            json.dump(queue, f)
        
        # Update response
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.response_frame, text=f"{name} has been added to the queue.", 
                font=self.controller.label_font).pack()
        
        # Enable view queue button and show back button
        self.view_queue_button.config(state=tk.NORMAL)
        self.back_button.pack(pady=10)
    
    def lookup_in_database(self, phone_number):
        try:
            with open(self.controller.database_file, 'r') as f:
                customers = json.load(f)
                for customer in customers:
                    if customer["phone"] == phone_number:
                        return customer["name"]
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        return None
    
    def show_queue_view(self):
        self.queue_window = tk.Toplevel(self)
        self.queue_window.title("Current Queue")
        self.queue_window.geometry("600x400")
        
        # Create treeview
        self.queue_tree = ttk.Treeview(self.queue_window, columns=('Name', 'Status', 'Time'), show='headings')
        self.queue_tree.heading('Name', text='Name')
        self.queue_tree.heading('Status', text='Status')
        self.queue_tree.heading('Time', text='Waiting Time')
        self.queue_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial load
        self.refresh_queue_view()
        
        # Add window close handler
        self.queue_window.protocol("WM_DELETE_WINDOW", self.on_queue_window_close)
    
    def on_queue_window_close(self):
        """Handle window closing"""
        self.queue_window.destroy()
        delattr(self, 'queue_window')
    
    def refresh_queue_view(self, tree=None):
        """Refresh the queue view window"""
        if not hasattr(self, 'queue_window') or not self.queue_window.winfo_exists():
            return
        
        tree = self.queue_tree  # Use the instance treeview
        
        # Clear existing data
        for item in tree.get_children():
            tree.delete(item)
        
        # Load queue data
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
                for item in queue:
                    name = item["name"]
                    status = item["status"]
                    try:
                        timestamp = float(item["timestamp"])
                        wait_time = datetime.now() - datetime.fromtimestamp(timestamp)
                        wait_time_str = str(wait_time).split('.')[0]  # Remove microseconds
                    except:
                        wait_time_str = "N/A"
                    
                    tree.insert('', tk.END, values=(name, status, wait_time_str))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

class AdminLogin(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        login_frame = tk.Frame(self)
        login_frame.pack(expand=True)
        
        tk.Label(login_frame, text="Staff Login", 
                font=controller.title_font).pack(pady=20)
        
        # NEW: Role selection
        self.role_var = tk.StringVar(value="employee")
        ttk.Radiobutton(login_frame, text="Employee", variable=self.role_var,
                       value="employee").pack()
        ttk.Radiobutton(login_frame, text="Admin/Owner", variable=self.role_var,
                       value="admin").pack()
        
        tk.Label(login_frame, text="Username:", 
                font=controller.label_font).pack(pady=5)
        self.username_entry = tk.Entry(login_frame, 
                                     font=controller.label_font)
        self.username_entry.pack(pady=5)
        
        tk.Label(login_frame, text="Password:", 
                font=controller.label_font).pack(pady=5)
        self.password_entry = tk.Entry(login_frame, 
                                     font=controller.label_font, 
                                     show="*")
        self.password_entry.pack(pady=5)
        
        tk.Button(login_frame, text="Login", 
                 font=controller.button_font, 
                 command=self.attempt_login).pack(pady=10)
        
        tk.Button(login_frame, text="Back to Customer View", 
                 font=controller.button_font, 
                 command=lambda: controller.show_frame(CustomerView)).pack(pady=10)
    
    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()
        
        if role == "admin":
            if self.controller.verify_admin(username, password):
                self.controller.show_frame(AdminView)
        else:
            if self.controller.verify_employee(username, password):
                self.controller.show_frame(EmployeeView)

class EmployeeView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.notebook = None
    
    def build_employee_view(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.queue_tab = ttk.Frame(self.notebook)
        self.add_customer_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.queue_tab, text="Manage Queue")
        self.notebook.add(self.add_customer_tab, text="Add Customer")

        # Build each tab
        self.build_queue_tab()
        self.build_add_customer_tab()
        
        # Add logout button
        logout_button = tk.Button(self, text="Logout", 
                                font=self.controller.button_font, 
                                command=lambda: self.controller.show_frame(CustomerView))
        logout_button.pack(pady=10)
    
    def build_queue_tab(self):
        """Build the queue management tab"""
        # Queue treeview
        self.queue_tree = ttk.Treeview(self.queue_tab, 
                                     columns=('Name', 'Status', 'Time'), 
                                     show='headings')
        self.queue_tree.heading('Name', text='Name')
        self.queue_tree.heading('Status', text='Status')
        self.queue_tree.heading('Time', text='Waiting Time')
        self.queue_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load queue data
        self.refresh_queue()
        
        # Action buttons
        button_frame = tk.Frame(self.queue_tab)
        button_frame.pack(pady=10)
        
        actions = [
            ("Mark as In Process", "In Process"),
            ("Mark as Ready", "Ready"),
            ("Mark as Completed", "Completed"),
            ("Remove", "remove")
        ]
        
        for text, action in actions:
            tk.Button(button_frame, text=text,
                     command=lambda a=action: self.queue_action(a)).pack(side=tk.LEFT, padx=5)
    
    def build_add_customer_tab(self):
        """Tab for adding customers to queue"""
        # Phone number entry
        tk.Label(self.add_customer_tab, text="Customer Phone Number", 
                font=self.controller.label_font).pack(pady=10)
        
        self.phone_entry = tk.Entry(self.add_customer_tab, 
                                  font=self.controller.label_font, 
                                  justify='center')
        self.phone_entry.pack(pady=5, ipady=5)
        
        # Submit button
        tk.Button(self.add_customer_tab, text="Check Phone", 
                 font=self.controller.button_font,
                 command=self.check_phone_number).pack(pady=10)
        
        # Response area
        self.response_frame = tk.Frame(self.add_customer_tab)
        self.response_frame.pack(pady=10)
    
    def check_phone_number(self):
        """Check if phone exists in database"""
        phone_number = self.phone_entry.get().strip()
        if not phone_number:
            messagebox.showerror("Error", "Please enter a phone number")
            return
        
        # Check database for registration
        name = self.lookup_in_database(phone_number)
        
        # Clear previous response
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        if name:
            # If found in database
            tk.Label(self.response_frame, text=f"Customer: {name}", 
                    font=self.controller.label_font).pack()
            tk.Button(self.response_frame, text="Add to Queue", 
                    font=self.controller.button_font,
                    command=lambda: self.add_to_queue(name)).pack(pady=10)
        else:
            # If not found
            self.ask_for_name()
    
    def ask_for_name(self):
        """Ask for new customer name"""
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.response_frame, 
                text="Customer Name (first and last)", 
                font=self.controller.label_font).pack()
        
        self.name_entry = tk.Entry(self.response_frame, 
                                font=self.controller.label_font)
        self.name_entry.pack(pady=5)
        
        tk.Button(self.response_frame, text="Register & Add to Queue", 
                font=self.controller.button_font,
                command=self.register_name).pack()
    
    def register_name(self):
        """Register new customer and add to queue"""
        full_name = self.name_entry.get().strip()
        if not full_name:
            messagebox.showerror("Error", "Please enter a name")
            return
        
        # Add to database
        phone_number = self.phone_entry.get().strip()
        timestamp = datetime.now().timestamp()
        
        with open(self.controller.database_file, 'r') as f:
            customers = json.load(f)
        
        customers.append({
            "phone": phone_number,
            "name": full_name,
            "registration_timestamp": timestamp
        })
        
        with open(self.controller.database_file, 'w') as f:
            json.dump(customers, f)
        
        # Add to queue
        self.add_to_queue(full_name)
    
    def add_to_queue(self, name):
        """Add customer to queue with duplicate checking"""
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
                
            # Check if customer already exists with any status
            for item in queue:
                if item["name"] == name:
                    # Clear previous response
                    for widget in self.response_frame.winfo_children():
                        widget.destroy()
                    
                    # Show message that customer is already in queue
                    tk.Label(self.response_frame, 
                            text=f"{name} is already in the queue (Status: {item['status']})",
                            font=self.controller.label_font).pack()
                    
                    # Add action buttons
                    button_frame = tk.Frame(self.response_frame)
                    button_frame.pack(pady=10)
                    
                    tk.Button(button_frame, text="Refresh Status",
                            font=self.controller.button_font,
                            command=lambda: self.check_phone_number()).pack(side=tk.LEFT, padx=5)
                    
                    tk.Button(button_frame, text="View Queue",
                            font=self.controller.button_font,
                            command=self.show_queue_view).pack(side=tk.LEFT, padx=5)
                    return
                    
        except (FileNotFoundError, json.JSONDecodeError):
            # If queue file doesn't exist or is empty, continue to add
            queue = []
        
        # If not in queue, proceed with adding
        timestamp = datetime.now().timestamp()
        
        queue.append({
            "name": name,
            "status": "In Queue",
            "timestamp": timestamp
        })
        
        with open(self.controller.queue_file, 'w') as f:
            json.dump(queue, f)
        
        # Update response
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.response_frame, 
                text=f"{name} has been added to the queue.",
                font=self.controller.label_font).pack()
        
        # Show view queue button
        tk.Button(self.response_frame, text="View Queue",
                 font=self.controller.button_font,
                 command=self.show_queue_view).pack(pady=10)
        
        # Refresh the queue tab
        self.refresh_queue()
    
    def lookup_in_database(self, phone_number):
        """Lookup customer in database"""
        try:
            with open(self.controller.database_file, 'r') as f:
                customers = json.load(f)
                for customer in customers:
                    if customer["phone"] == phone_number:
                        return customer["name"]
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        return None
    
    def refresh_queue(self, event=None):
        """Refresh the queue display"""
        if hasattr(self, 'queue_tree'):
            # Clear existing data
            for item in self.queue_tree.get_children():
                self.queue_tree.delete(item)
            
            # Load queue data
            try:
                with open(self.controller.queue_file, 'r') as f:
                    queue = json.load(f)
                    for item in queue:
                        name = item["name"]
                        status = item["status"]
                        try:
                            timestamp = float(item["timestamp"])
                            wait_time = datetime.now() - datetime.fromtimestamp(timestamp)
                            wait_time_str = str(wait_time).split('.')[0]  # Remove microseconds
                        except:
                            wait_time_str = "N/A"
                        
                        self.queue_tree.insert('', tk.END, values=(name, status, wait_time_str))
            except (FileNotFoundError, json.JSONDecodeError):
                pass
    
    def queue_action(self, action):
        selected_item = self.queue_tree.selection()
        if selected_item:
            name = self.queue_tree.item(selected_item)['values'][0]
            if action == "remove":
                self.remove_from_queue(name)
            else:
                self.update_status(name, action)
            self.refresh_queue()
    
    def update_status(self, name, new_status):
        if new_status in ["Completed", "Cancelled"]:
            self.complete_customer(name, new_status)
        else:
            self.update_queue_file(name, new_status)
        self.refresh_queue()
    
    def remove_from_queue(self, name):
        self.remove_from_queue_file(name)
        self.refresh_queue()
    
    def complete_customer(self, name, status="Completed"):
        # Remove from queue
        self.remove_from_queue_file(name)
        
        # Add to history
        with open(self.controller.history_file, 'r') as f:
            history = json.load(f)
        
        history.append({
            "name": name,
            "timestamp": datetime.now().timestamp(),
            "status": status
        })
        
        with open(self.controller.history_file, 'w') as f:
            json.dump(history, f)
        
        self.refresh_queue()
    
    def update_queue_file(self, name, new_status):
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
            
            for item in queue:
                if item["name"] == name:
                    item["status"] = new_status
                    break
            
            with open(self.controller.queue_file, 'w') as f:
                json.dump(queue, f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def remove_from_queue_file(self, name):
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
            
            # Filter out the item to remove
            updated_queue = [item for item in queue if item["name"] != name]
            
            with open(self.controller.queue_file, 'w') as f:
                json.dump(updated_queue, f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def show_queue_view(self):
        """Show the queue in a popup window"""
        self.queue_window = tk.Toplevel(self)
        self.queue_window.title("Current Queue")
        self.queue_window.geometry("600x400")
        
        # Create treeview
        self.queue_tree_popup = ttk.Treeview(self.queue_window, columns=('Name', 'Status', 'Time'), show='headings')
        self.queue_tree_popup.heading('Name', text='Name')
        self.queue_tree_popup.heading('Status', text='Status')
        self.queue_tree_popup.heading('Time', text='Waiting Time')
        self.queue_tree_popup.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial load
        self.refresh_queue_view_popup()
        
        # Add window close handler
        self.queue_window.protocol("WM_DELETE_WINDOW", self.on_queue_window_close)
    
    def on_queue_window_close(self):
        """Handle window closing"""
        self.queue_window.destroy()
        delattr(self, 'queue_window')
        delattr(self, 'queue_tree_popup')
    
    def refresh_queue_view_popup(self):
        """Refresh the queue view window"""
        if not hasattr(self, 'queue_window') or not self.queue_window.winfo_exists():
            return
        
        # Clear existing data
        for item in self.queue_tree_popup.get_children():
            self.queue_tree_popup.delete(item)
        
        # Load queue data
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
                for item in queue:
                    name = item["name"]
                    status = item["status"]
                    try:
                        timestamp = float(item["timestamp"])
                        wait_time = datetime.now() - datetime.fromtimestamp(timestamp)
                        wait_time_str = str(wait_time).split('.')[0]  # Remove microseconds
                    except:
                        wait_time_str = "N/A"
                    
                    self.queue_tree_popup.insert('', tk.END, values=(name, status, wait_time_str))
        except (FileNotFoundError, json.JSONDecodeError):
            pass


class AdminView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.notebook = None
    
    def build_admin_view(self):
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.home_tab = ttk.Frame(self.notebook)
        self.reports_tab = ttk.Frame(self.notebook)
        self.queue_tab = ttk.Frame(self.notebook)
        self.customers_tab = ttk.Frame(self.notebook)
        self.add_customer_tab = ttk.Frame(self.notebook)  # New tab
        
        self.notebook.add(self.home_tab, text="Home")
        self.notebook.add(self.reports_tab, text="Reports")
        self.notebook.add(self.queue_tab, text="Manage Queue")
        self.notebook.add(self.customers_tab, text="Customers")
        self.notebook.add(self.add_customer_tab, text="Add Customer")  # Add new tab
        
        # Build each tab
        self.build_home_tab()
        self.build_reports_tab()
        self.build_queue_tab()
        self.build_customers_tab()
        self.build_add_customer_tab()  # Build new tab
        
        # Add logout button
        logout_button = tk.Button(self, text="Logout", 
                                font=self.controller.button_font, 
                                command=lambda: self.controller.show_frame(CustomerView))
        logout_button.pack(pady=10)
    
    def build_add_customer_tab(self):
        """Tab for adding customers to queue (similar to main screen)"""
        # Phone number entry
        tk.Label(self.add_customer_tab, text="Customer Phone Number", 
                font=self.controller.label_font).pack(pady=10)
        
        self.phone_entry = tk.Entry(self.add_customer_tab, 
                                  font=self.controller.label_font, 
                                  justify='center')
        self.phone_entry.pack(pady=5, ipady=5)
        
        # Submit button
        tk.Button(self.add_customer_tab, text="Check Phone", 
                 font=self.controller.button_font,
                 command=self.check_phone_number).pack(pady=10)
        
        # Response area
        self.response_frame = tk.Frame(self.add_customer_tab)
        self.response_frame.pack(pady=10)
    
    def check_phone_number(self):
        """Same functionality as CustomerView but for admin"""
        phone_number = self.phone_entry.get().strip()
        if not phone_number:
            messagebox.showerror("Error", "Please enter a phone number")
            return
        
        # Check database for registration
        name = self.lookup_in_database(phone_number)
        
        # Clear previous response
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        if name:
            # If found in database
            tk.Label(self.response_frame, text=f"Customer: {name}", 
                    font=self.controller.label_font).pack()
            tk.Button(self.response_frame, text="Add to Queue", 
                    font=self.controller.button_font,
                    command=lambda: self.add_to_queue(name)).pack(pady=10)
        else:
            # If not found
            self.ask_for_name()
    
    def ask_for_name(self):
        """Ask for new customer name"""
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.response_frame, 
                text="Customer Name (first and last)", 
                font=self.controller.label_font).pack()
        
        self.name_entry = tk.Entry(self.response_frame, 
                                font=self.controller.label_font)
        self.name_entry.pack(pady=5)
        
        tk.Button(self.response_frame, text="Register & Add to Queue", 
                font=self.controller.button_font,
                command=self.register_name).pack()
    
    def register_name(self):
        """Register new customer and add to queue"""
        full_name = self.name_entry.get().strip()
        if not full_name:
            messagebox.showerror("Error", "Please enter a name")
            return
        
        # Add to database
        phone_number = self.phone_entry.get().strip()
        timestamp = datetime.now().timestamp()
        
        with open(self.controller.database_file, 'r') as f:
            customers = json.load(f)
        
        customers.append({
            "phone": phone_number,
            "name": full_name,
            "registration_timestamp": timestamp
        })
        
        with open(self.controller.database_file, 'w') as f:
            json.dump(customers, f)
        
        # Add to queue
        self.add_to_queue(full_name)
    
    def add_to_queue(self, name):
        """Add customer to queue with duplicate checking"""
        # First check if customer is already in queue
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
                
            # Check if customer already exists with any status
            for item in queue:
                if item["name"] == name:
                    # Clear previous response
                    for widget in self.response_frame.winfo_children():
                        widget.destroy()
                    
                    # Show message that customer is already in queue
                    tk.Label(self.response_frame, 
                            text=f"{name} is already in the queue (Status: {item['status']})",
                            font=self.controller.label_font).pack()
                    
                    # Add refresh button
                    tk.Button(self.response_frame, text="Refresh Status",
                            font=self.controller.button_font,
                            command=lambda: self.check_phone_number()).pack(pady=5)
                    return
                    
        except (FileNotFoundError, json.JSONDecodeError):
            # If queue file doesn't exist or is empty, continue to add
            queue = []
        
        # If not in queue, proceed with adding
        timestamp = datetime.now().timestamp()
        
        queue.append({
            "name": name,
            "status": "In Queue",
            "timestamp": timestamp
        })
        
        with open(self.controller.queue_file, 'w') as f:
            json.dump(queue, f)
        
        # Update response
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.response_frame, 
                text=f"{name} has been added to the queue.",
                font=self.controller.label_font).pack()
        
        # Refresh the queue tab
        self.refresh_queue()
    
    def lookup_in_database(self, phone_number):
        """Lookup customer in database"""
        try:
            with open(self.controller.database_file, 'r') as f:
                customers = json.load(f)
                for customer in customers:
                    if customer["phone"] == phone_number:
                        return customer["name"]
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        return None
    
    def build_home_tab(self):
        # Get queue stats
        in_queue = 0
        in_process = 0
        ready = 0
        
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
                for item in queue:
                    status = item["status"]
                    if status == "In Queue":
                        in_queue += 1
                    elif status == "In Process":
                        in_process += 1
                    elif status == "Ready":
                        ready += 1
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Display stats
        stats_frame = tk.Frame(self.home_tab)
        stats_frame.pack(pady=20)
        
        tk.Label(stats_frame, text="Queue Status:", 
                font=self.controller.title_font).pack()
        
        stats_text = f"In Queue: {in_queue} | In Process: {in_process} | Ready: {ready}"
        tk.Label(stats_frame, text=stats_text, 
                font=self.controller.label_font).pack(pady=10)
        
        # Navigation buttons
        button_frame = tk.Frame(self.home_tab)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Go to Customers' View", 
                 font=self.controller.button_font,
                 command=lambda: self.controller.show_frame(CustomerView)).pack(pady=10, fill=tk.X)
        
        tk.Button(button_frame, text="Go to Monitors View", 
                 font=self.controller.button_font,
                 command=self.show_monitors_view).pack(pady=10, fill=tk.X)
    
    def build_reports_tab(self):
        # Create frame for charts
        self.reports_frame = ttk.Frame(self.reports_tab)
        self.reports_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create frame for outcome chart
        outcome_frame = ttk.Frame(self.reports_frame)
        outcome_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create frame for growth chart
        growth_frame = ttk.Frame(self.reports_frame)
        growth_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generate and display charts
        self.generate_outcome_chart(outcome_frame)
        self.generate_growth_chart(growth_frame)
        
        # Refresh button
        refresh_button = tk.Button(self.reports_tab, text="Refresh Reports", 
                                 font=self.controller.button_font, 
                                 command=self.refresh_reports)
        refresh_button.pack(pady=10)
    
    def generate_outcome_chart(self, parent_frame):
        # Get data from history file
        completed = 0
        cancelled = 0
        
        try:
            with open(self.controller.history_file, 'r') as f:
                history = json.load(f)
                for item in history:
                    status = item["status"]
                    if status == "Completed":
                        completed += 1
                    elif status == "Cancelled":
                        cancelled += 1
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 4))
        
        if completed + cancelled > 0:
            # Calculate percentages
            total = completed + cancelled
            complete_pct = (completed / total) * 100 if total > 0 else 0
            cancelled_pct = (cancelled / total) * 100 if total > 0 else 0
            
            # Create bar chart
            categories = ['Completed', 'Cancelled']
            percentages = [complete_pct, cancelled_pct]
            colors = ['#4CAF50', '#F44336']
            
            bars = ax.bar(categories, percentages, color=colors, width=0.6)
            ax.set_ylim(0, 100)
            ax.set_ylabel('Percentage (%)')
            ax.set_title('Customer Outcomes')
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%',
                        ha='center', va='bottom')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            ax.set_title('Customer Outcomes (No Data)')
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def generate_growth_chart(self, parent_frame):
        # Focus on March-June
        months_order = ['Mar', 'Apr', 'May', 'Jun']
        
        # Initialize data
        month_data = {month: {'total': 0, 'new': 0} for month in months_order}
        current_year = datetime.now().year
        
        try:
            # Count total customers per month (first registration)
            with open(self.controller.database_file, 'r') as f:
                customers = json.load(f)
                for customer in customers:
                    try:
                        timestamp = float(customer["registration_timestamp"])
                        date = datetime.fromtimestamp(timestamp)
                        if date.year == current_year:
                            month = date.strftime('%b')
                            if month in month_data:
                                month_data[month]['total'] += 1
                    except:
                        pass
            
            # Count new customers per month (from history)
            with open(self.controller.history_file, 'r') as f:
                history = json.load(f)
                for item in history:
                    if item["status"] == "Completed":
                        try:
                            timestamp = float(item["timestamp"])
                            date = datetime.fromtimestamp(timestamp)
                            if date.year == current_year:
                                month = date.strftime('%b')
                                if month in month_data:
                                    month_data[month]['new'] += 1
                        except:
                            pass
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Prepare data
        total_customers = [month_data[month]['total'] for month in months_order]
        new_customers = [month_data[month]['new'] for month in months_order]
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 4))
        bar_width = 0.35
        x = range(len(months_order))
        
        ax.bar(x, total_customers, bar_width, label='Total Customers', color='#2196F3')
        ax.bar([i + bar_width for i in x], new_customers, bar_width, label='New Customers', color='#FFC107')
        
        ax.set_xlabel('Month')
        ax.set_ylabel('Number of Customers')
        ax.set_title(f'Customer Growth ({current_year})')
        ax.set_xticks([i + bar_width/2 for i in x])
        ax.set_xticklabels(months_order)
        ax.legend()
        
        # Set y-axis limit dynamically
        max_value = max(total_customers + new_customers + [1])  # Ensure at least 1
        ax.set_ylim(0, max_value + 5)
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def refresh_reports(self):
        # Destroy existing widgets in reports tab
        for widget in self.reports_tab.winfo_children():
            widget.destroy()
        
        # Rebuild reports tab
        self.build_reports_tab()
    
    def build_queue_tab(self):
        # Create treeview for queue
        self.queue_tree = ttk.Treeview(self.queue_tab, 
                                     columns=('Name', 'Status', 'Time'), 
                                     show='headings')
        self.queue_tree.heading('Name', text='Name')
        self.queue_tree.heading('Status', text='Status')
        self.queue_tree.heading('Time', text='Waiting Time')
        self.queue_tree.column('Name', width=200)
        self.queue_tree.column('Status', width=100)
        self.queue_tree.column('Time', width=150)
        self.queue_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load queue data
        self.refresh_queue()
        
        # Add buttons for queue management
        button_frame = tk.Frame(self.queue_tab)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Mark as Ready", 
                 command=lambda: self.update_status("Ready")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Mark in Process", 
                 command=lambda: self.update_status("In Process")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Mark as Completed", 
                 command=lambda: self.update_status("Completed")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Mark as Cancelled", 
                 command=lambda: self.update_status("Cancelled")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove from Queue", 
                 command=self.remove_from_queue).pack(side=tk.LEFT, padx=5)
    
    def refresh_queue(self):
        # Clear existing data
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        
        # Load queue data
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
                for item in queue:
                    name = item["name"]
                    status = item["status"]
                    try:
                        timestamp = float(item["timestamp"])
                        wait_time = datetime.now() - datetime.fromtimestamp(timestamp)
                        wait_time_str = str(wait_time).split('.')[0]  # Remove microseconds
                    except:
                        wait_time_str = "N/A"
                    
                    self.queue_tree.insert('', tk.END, values=(name, status, wait_time_str))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def update_status(self, new_status):
        selected_item = self.queue_tree.selection()
        if selected_item:
            name = self.queue_tree.item(selected_item)['values'][0]
            if new_status in ["Completed", "Cancelled"]:
                self.complete_customer(name, new_status)
            else:
                self.update_queue_file(name, new_status)
            self.refresh_queue()
            self.refresh_reports()
    
    def remove_from_queue(self):
        selected_item = self.queue_tree.selection()
        if selected_item:
            name = self.queue_tree.item(selected_item)['values'][0]
            self.remove_from_queue_file(name)
            self.refresh_queue()
    
    def complete_customer(self, name, status="Completed"):
        # Remove from queue
        self.remove_from_queue_file(name)
        
        # Add to history
        with open(self.controller.history_file, 'r') as f:
            history = json.load(f)
        
        history.append({
            "name": name,
            "timestamp": datetime.now().timestamp(),
            "status": status
        })
        
        with open(self.controller.history_file, 'w') as f:
            json.dump(history, f)
        
        self.refresh_queue()
        self.refresh_reports()
    
    def update_queue_file(self, name, new_status):
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
            
            for item in queue:
                if item["name"] == name:
                    item["status"] = new_status
                    break
            
            with open(self.controller.queue_file, 'w') as f:
                json.dump(queue, f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def remove_from_queue_file(self, name):
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
            
            # Filter out the item to remove
            updated_queue = [item for item in queue if item["name"] != name]
            
            with open(self.controller.queue_file, 'w') as f:
                json.dump(updated_queue, f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def build_customers_tab(self):
        # Create treeview for customers
        self.customers_tree = ttk.Treeview(self.customers_tab, 
                                         columns=('Phone', 'Name', 'Date'), 
                                         show='headings')
        self.customers_tree.heading('Phone', text='Phone Number')
        self.customers_tree.heading('Name', text='Name')
        self.customers_tree.heading('Date', text='Registration Date')
        self.customers_tree.column('Phone', width=150)
        self.customers_tree.column('Name', width=200)
        self.customers_tree.column('Date', width=150)
        self.customers_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load customers data
        self.refresh_customers()
        
        # Add search functionality
        search_frame = tk.Frame(self.customers_tab)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search:", 
                font=self.controller.label_font).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, 
                                    font=self.controller.label_font)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.search_customers)
    
    def search_customers(self, event=None):
        query = self.search_entry.get().lower()
        
        # Clear existing data
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Load and filter customers data
        try:
            with open(self.controller.database_file, 'r') as f:
                customers = json.load(f)
                for customer in customers:
                    phone = customer["phone"]
                    name = customer["name"]
                    timestamp = customer["registration_timestamp"]
                    
                    if query in phone.lower() or query in name.lower():
                        try:
                            date = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M')
                        except:
                            date = "N/A"
                        
                        self.customers_tree.insert('', tk.END, values=(phone, name, date))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def refresh_customers(self):
        # Clear existing data
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Load customers data
        try:
            with open(self.controller.database_file, 'r') as f:
                customers = json.load(f)
                for customer in customers:
                    phone = customer["phone"]
                    name = customer["name"]
                    timestamp = customer["registration_timestamp"]
                    try:
                        date = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M')
                    except:
                        date = "N/A"
                    
                    self.customers_tree.insert('', tk.END, values=(phone, name, date))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def show_monitors_view(self):
        self.monitors_window = tk.Toplevel(self)
        self.monitors_window.title("Monitors View")
        self.monitors_window.geometry("800x400")
        
        # Create treeview for queue
        self.monitors_tree = ttk.Treeview(self.monitors_window, 
                           columns=('Name', 'Status', 'Time'), 
                           show='headings')
        self.monitors_tree.heading('Name', text='Name')
        self.monitors_tree.heading('Status', text='Status')
        self.monitors_tree.heading('Time', text='Waiting Time')
        self.monitors_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial load
        self.refresh_monitors_view(self.monitors_tree)
        
        # Add window close handler
        self.monitors_window.protocol("WM_DELETE_WINDOW", self.on_monitors_window_close)
    
    def on_monitors_window_close(self):
        """Handle window closing"""
        self.monitors_window.destroy()
        delattr(self, 'monitors_window')
        delattr(self, 'monitors_tree')
    
    def refresh_monitors_view(self, tree):
        """Refresh the queue view window"""
        if not hasattr(self, 'monitors_window') or not self.monitors_window.winfo_exists():
            return
        
        # Clear existing data
        for item in tree.get_children():
            tree.delete(item)
        
        # Load queue data
        try:
            with open(self.controller.queue_file, 'r') as f:
                queue = json.load(f)
                for item in queue:
                    name = item["name"]
                    status = item["status"]
                    try:
                        timestamp = float(item["timestamp"])
                        wait_time = datetime.now() - datetime.fromtimestamp(timestamp)
                        wait_time_str = str(wait_time).split('.')[0]  # Remove microseconds
                    except:
                        wait_time_str = "N/A"
                    
                    tree.insert('', tk.END, values=(name, status, wait_time_str))
        except (FileNotFoundError, json.JSONDecodeError):
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = AttendSmartApp(root)
    root.mainloop()