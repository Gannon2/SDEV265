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

        # Auto refresh functionality
        self.auto_refresh_interval = 1000  # 1 second
        self.auto_refresh_id = None  # Store the after id
        self.schedule_auto_refresh()

        # Clean up statements
        self.root = root
        self.running = True  # Add a flag to track application state
        
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
        # Cancel any existing refresh
        if self.auto_refresh_id:
            self.root.after_cancel(self.auto_refresh_id)
        
        # Schedule new refresh and store the ID
        self.auto_refresh_id = self.root.after(
            self.auto_refresh_interval, 
            self.refresh_all_queues
        )
    
    def refresh_all_queues(self):
        """Refresh all queue displays in the application"""
        try:
            # Refresh CustomerView
            customer_view = self.frames.get(CustomerView)
            if customer_view is not None:
                if hasattr(customer_view, 'queue_tree') and customer_view.queue_tree is not None:
                    if customer_view.queue_tree.winfo_exists():
                        customer_view.refresh_queue_view()
            
            # Refresh EmployeeView
            employee_view = self.frames.get(EmployeeView)
            if (employee_view is not None 
                and hasattr(employee_view, 'queue_tree')
                and employee_view.queue_tree is not None
                and employee_view.queue_tree.winfo_exists()):
                employee_view.refresh_queue()
            
            # Refresh AdminView
            admin_view = self.frames.get(AdminView)
            if admin_view is not None:
                # Refresh main queue tree in admin tab
                if (hasattr(admin_view, 'queue_tree')
                    and admin_view.queue_tree is not None
                    and admin_view.queue_tree.winfo_exists()):
                    admin_view.refresh_queue()
                
                # Refresh monitors window
                if (hasattr(admin_view, 'monitors_window')
                    and admin_view.monitors_window is not None
                    and hasattr(admin_view, 'monitors_tree')
                    and admin_view.monitors_tree is not None
                    and admin_view.monitors_tree.winfo_exists()):
                    admin_view.refresh_monitors_view(admin_view.monitors_tree)
                    
        except Exception as e:
            print(f"Refresh skipped: {str(e)}")
        finally:
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

        self.schedule_auto_refresh() # Ensure refresh continues after view switch
    
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

    # ===== NEW SHARED METHODS =====
    def get_queue_data(self):
        """Get current queue data from file"""
        try:
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_queue_data(self, queue):
        """Save queue data to file"""
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f)
    
    def get_customer_data(self):
        """Get all customer data from database"""
        try:
            with open(self.database_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_customer_data(self, customers):
        """Save customer data to database"""
        with open(self.database_file, 'w') as f:
            json.dump(customers, f)
    
    def create_queue_treeview(self, parent, detailed=False):
        """Create a queue treeview widget with option for detailed view"""
        if detailed:
            # Detailed view for admin/employee with time column
            tree = ttk.Treeview(parent, columns=('Position', 'Name', 'Status', 'Time'), show='headings')
            tree.heading('Position', text='Position')
            tree.heading('Name', text='Name')
            tree.heading('Status', text='Status')
            tree.heading('Time', text='Waiting Time')
            tree.column('Position', width=80, anchor='center')
            tree.column('Name', width=150)
            tree.column('Status', width=100, anchor='center')
            tree.column('Time', width=150, anchor='center')
        else:
            # Simple view for customers
            tree = ttk.Treeview(parent, columns=('Position', 'Name', 'Status'), show='headings')
            tree.heading('Position', text='Position')
            tree.heading('Name', text='Name')
            tree.heading('Status', text='Status')
            tree.column('Position', width=80, anchor='center')
            tree.column('Name', width=150)
            tree.column('Status', width=100, anchor='center')
        return tree
    
    def populate_queue_tree(self, tree, detailed=False):
        """Populate a treeview with current queue data, preserving selection if detailed view"""
        # Store current selection
        selected_item = tree.selection()[0] if tree.selection() else None
        selected_name = None
        if selected_item:
            selected_name = tree.item(selected_item)['values'][1]  # Name is at index 1

        # Clear and repopulate
        for item in tree.get_children():
            tree.delete(item)

        queue = self.get_queue_data()
        for idx, item in enumerate(queue):
            name = item["name"]
            status = item["status"]

            if detailed:
                try:
                    timestamp = float(item["timestamp"])
                    wait_time = datetime.now() - datetime.fromtimestamp(timestamp)
                    wait_time_str = str(wait_time).split('.')[0]  # Remove microseconds
                except:
                    wait_time_str = "N/A"
                values = (idx + 1, name, status, wait_time_str)
            else:
                values = (idx + 1, name, status)

            tree.insert('', tk.END, values=values)

            # Restore selection if this was the selected item
            if selected_name and name == selected_name:
                tree.selection_set(tree.get_children()[-1])
    
    def add_customer_to_queue(self, name):
        """
        Add customer to queue with duplicate checking
        Returns: (success, existing_status) tuple
        """
        queue = self.get_queue_data()
        
        # Check if already in queue
        for item in queue:
            if item["name"] == name:
                return False, item["status"]
        
        # Add to queue if not exists
        queue.append({
            "name": name,
            "status": "In Queue",
            "timestamp": datetime.now().timestamp()
        })
        self.save_queue_data(queue)
        return True, None
    
    def remove_from_queue(self, name):
        """Remove customer from queue by name"""
        queue = self.get_queue_data()
        updated_queue = [item for item in queue if item["name"] != name]
        if len(queue) != len(updated_queue):
            self.save_queue_data(updated_queue)
            return True
        return False
    
    def update_queue_status(self, name, new_status):
        """Update a customer's status in the queue"""
        queue = self.get_queue_data()
        updated = False
        
        for item in queue:
            if item["name"] == name:
                item["status"] = new_status
                updated = True
                break
        
        if updated:
            self.save_queue_data(queue)
        return updated
    
    def complete_customer(self, name, status="Completed"):
        """
        Complete a customer transaction
        Moves from queue to history and updates stats
        """
        # Remove from queue
        self.remove_from_queue(name)
        
        # Add to history
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        
        history.append({
            "name": name,
            "timestamp": datetime.now().timestamp(),
            "status": status
        })
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f)
    
    def lookup_customer(self, phone_number):
        """Lookup customer name by phone number"""
        customers = self.get_customer_data()
        for customer in customers:
            if customer["phone"] == phone_number:
                return customer["name"]
        return None
    
    def register_customer(self, phone_number, name):
        """
        Register new customer in database
        Returns: True if registered, False if already exists
        """
        customers = self.get_customer_data()
        
        # Check if phone already exists
        for customer in customers:
            if customer["phone"] == phone_number:
                return False
        
        # Add new customer
        customers.append({
            "phone": phone_number,
            "name": name,
            "registration_timestamp": datetime.now().timestamp()
        })
        self.save_customer_data(customers)
        return True

    def cleanup(self):
        """Clean up scheduled events before closing"""
        self.running = False
        if self.auto_refresh_id:
            self.root.after_cancel(self.auto_refresh_id)
            self.auto_refresh_id = None

class CustomerView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.queue_tree = None  # Initialize queue_tree attribute
        self.setup_ui()

    def setup_ui(self):
        """Initialize all UI components"""
         # Top frame with title and login button
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.title_label = tk.Label(top_frame, text="AttendSmart", 
                                  font=self.controller.title_font)
        self.title_label.pack(side=tk.LEFT)
        
        self.login_button = tk.Button(top_frame, text="Admin/Employee Login", 
                                    font=self.controller.button_font, 
                                    command=lambda: self.controller.show_frame(AdminLogin))
        self.login_button.pack(side=tk.RIGHT)
        
        # Main interface
        self.welcome_label = tk.Label(self, text="Welcome", 
                                    font=self.controller.title_font)
        self.welcome_label.pack(pady=20)
        
        # Phone number entry
        self.phone_label = tk.Label(self, text="Please enter your phone number", 
                                  font=self.controller.label_font)
        self.phone_label.pack()
        
        self.phone_entry = tk.Entry(self, font=self.controller.label_font, justify='center')
        self.phone_entry.pack(pady=5, ipady=5)
        
        self.submit_button = tk.Button(self, text="Submit", 
                                     font=self.controller.button_font, 
                                     command=self.check_phone_number)
        self.submit_button.pack(pady=10)
        
        # Response area (dynamic content)
        self.response_frame = tk.Frame(self)
        self.response_frame.pack(pady=10)

        # Queue display on main screen (simple view)
        self.queue_frame = tk.LabelFrame(self, text="Current Queue", font=self.controller.label_font)
        self.queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create simple queue treeview (without time)
        self.queue_tree = self.controller.create_queue_treeview(self.queue_frame, detailed=False)
        self.queue_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.queue_frame, orient="vertical", command=self.queue_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_tree.configure(yscrollcommand=scrollbar.set)

        # Initial population of queue (simple view)
        self.controller.populate_queue_tree(self.queue_tree, detailed=False)

    def show_main_screen(self):
        """Reset the view to initial state"""
        self.phone_entry.delete(0, tk.END)
        for widget in self.response_frame.winfo_children():
            widget.destroy()
        self.back_button.pack_forget()
        self.title_label.pack(side=tk.LEFT)
        self.welcome_label.pack(pady=20)

    def check_phone_number(self):
        """Handle phone number submission"""
        phone_number = self.phone_entry.get().strip()
        if not phone_number:
            messagebox.showerror("Error", "Please enter a phone number")
            return
        
        # Use controller method to lookup customer
        name = self.controller.lookup_customer(phone_number)
        
        # Check if already in queue
        in_queue, queue_data = self.check_if_in_queue(phone_number, name)
        
        # Clear previous response
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        if in_queue:
            self.show_queue_status(phone_number, name, queue_data)
        else:
            self.handle_new_queue_entry(phone_number, name)

    def check_if_in_queue(self, phone_number, name):
        """Check if customer is already in queue"""
        if not name:
            return False, None
            
        queue = self.controller.get_queue_data()
        for idx, item in enumerate(queue):
            if item["name"] == name:
                return True, {
                    "position": idx + 1,
                    "timestamp": item["timestamp"],
                    "status": item["status"]
                }
        return False, None

    def handle_new_queue_entry(self, phone_number, name):
        """Handle flow for customer not currently in queue"""
        if name:
            # Existing customer found
            tk.Label(self.response_frame, text=f"Are you {name}?", 
                    font=self.controller.label_font).pack()
            
            button_frame = tk.Frame(self.response_frame)
            button_frame.pack(pady=5)
            
            tk.Button(button_frame, text="Yes", 
                    font=self.controller.button_font,
                    command=lambda: self.add_to_queue(name)).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="No", 
                    font=self.controller.button_font,
                    command=self.ask_for_name).pack(side=tk.LEFT, padx=5)
        else:
            # New customer
            self.ask_for_name()

    def show_queue_status(self, phone_number, name, queue_data):
        """Display current queue status for customer"""
        self.title_label.pack_forget()
        self.welcome_label.pack_forget()
        
        # Calculate wait time
        try:
            wait_time = datetime.now() - datetime.fromtimestamp(float(queue_data["timestamp"]))
            wait_time_str = str(wait_time).split('.')[0]
        except:
            wait_time_str = "Unknown"
        
        # Display queue information
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
        
        # Action buttons
        button_frame = tk.Frame(self.response_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Remove Me From Queue",
                font=self.controller.button_font,
                command=lambda: self.remove_from_queue(name)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Refresh Status",
                font=self.controller.button_font,
                command=lambda: self.check_phone_number()).pack(side=tk.LEFT, padx=5)
        
        # Show navigation buttons
        self.back_button.pack(pady=10)

    def remove_from_queue(self, name):
        """Remove customer from queue using controller method"""
        if self.controller.remove_from_queue(name):
            messagebox.showinfo("Success", "You have been removed from the queue")
            self.show_main_screen()
        else:
            messagebox.showerror("Error", "Could not update queue")

    def ask_for_name(self):
        """Prompt for customer name"""
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.response_frame, 
                text="What is your name? (first and last)", 
                font=self.controller.label_font).pack()
        
        self.name_entry = tk.Entry(self.response_frame, 
                                font=self.controller.label_font)
        self.name_entry.pack(pady=5)
        
        tk.Button(self.response_frame, text="Submit", 
                font=self.controller.button_font,
                command=self.register_name).pack()

    def register_name(self):
        """Register new customer and add to queue"""
        full_name = self.name_entry.get().strip()
        if not full_name or len(full_name.split()) < 2:
            messagebox.showerror("Error", "Please enter both first and last name")
            return
        
        phone_number = self.phone_entry.get().strip()
        
        # Use controller method to register customer
        if self.controller.register_customer(phone_number, full_name):
            self.add_to_queue(full_name)
        else:
            messagebox.showerror("Error", "This phone number is already registered")

    def add_to_queue(self, name):
        """Add customer to queue using controller method"""
        added, status = self.controller.add_customer_to_queue(name)
        
        # Clear response area
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        if added:
            # Successfully added to queue
            tk.Label(self.response_frame, 
                    text=f"{name} has been added to the queue.",
                    font=self.controller.label_font).pack()
            
            # Show back button
            self.back_button.pack(pady=10)
            
            # Refresh queue display
            self.refresh_queue_view()
        else:
            # Already in queue
            tk.Label(self.response_frame, 
                    text=f"{name} is already in the queue (Status: {status})",
                    font=self.controller.label_font).pack()
            
            button_frame = tk.Frame(self.response_frame)
            button_frame.pack(pady=10)
            
            tk.Button(button_frame, text="Refresh Status",
                    font=self.controller.button_font,
                    command=lambda: self.check_phone_number()).pack(side=tk.LEFT, padx=5)

    def refresh_queue_view(self):
        """Refresh the queue display on main screen"""
        if hasattr(self, 'queue_tree') and self.queue_tree is not None:
            self.controller.populate_queue_tree(self.queue_tree)

class AdminLogin(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.setup_login_ui()

    def setup_login_ui(self):
        """Initialize all login UI components"""
        login_frame = tk.Frame(self)
        login_frame.pack(expand=True, pady=50)
        
        # Title
        tk.Label(login_frame, text="Staff Login", 
                font=self.controller.title_font).pack(pady=20)
        
        # Role selection
        self.role_var = tk.StringVar(value="employee")
        role_frame = tk.Frame(login_frame)
        role_frame.pack(pady=10)
        
        ttk.Radiobutton(role_frame, text="Employee", 
                       variable=self.role_var,
                       value="employee").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(role_frame, text="Admin/Owner", 
                       variable=self.role_var,
                       value="admin").pack(side=tk.LEFT, padx=10)
        
        # Username field
        tk.Label(login_frame, text="Username:", 
                font=self.controller.label_font).pack(pady=5)
        
        self.username_entry = tk.Entry(login_frame, 
                                     font=self.controller.label_font,
                                     width=25)
        self.username_entry.pack(pady=5)
        
        # Password field
        tk.Label(login_frame, text="Password:", 
                font=self.controller.label_font).pack(pady=5)
        
        self.password_entry = tk.Entry(login_frame, 
                                     font=self.controller.label_font,
                                     show="*",
                                     width=25)
        self.password_entry.pack(pady=5)
        
        # Login button
        tk.Button(login_frame, text="Login", 
                 font=self.controller.button_font,
                 width=15,
                 command=self.attempt_login).pack(pady=15)
        
        # Back button
        tk.Button(login_frame, text="Back to Customer View", 
                 font=self.controller.button_font,
                 command=lambda: self.controller.show_frame(CustomerView)).pack(pady=10)
        
        # Bind Enter key to login
        self.password_entry.bind('<Return>', lambda event: self.attempt_login())

    def attempt_login(self):
        """Handle login attempt with validation"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        if role == "admin":
            if self.controller.verify_admin(username, password):
                self.clear_fields()
                self.controller.show_frame(AdminView)
            else:
                self.handle_failed_login()
        else:
            if self.controller.verify_employee(username, password):
                self.clear_fields()
                self.controller.show_frame(EmployeeView)
            else:
                self.handle_failed_login()

    def clear_fields(self):
        """Clear sensitive input fields"""
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def handle_failed_login(self):
        """Handle failed login attempts"""
        self.password_entry.delete(0, tk.END)
        messagebox.showerror("Login Failed", 
                           "Invalid username or password\nPlease try again")
        self.password_entry.focus_set()

class EmployeeView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.notebook = None
        self.queue_tree = None
        self.phone_entry = None
        self.response_frame = None
        self.name_entry = None

    def build_employee_view(self):
        """Initialize the employee dashboard"""
        self.clear_widgets()
        self.create_notebook()
        self.add_tabs()
        self.add_logout_button()

    def clear_widgets(self):
        """Clear all existing widgets"""
        for widget in self.winfo_children():
            widget.destroy()

    def create_notebook(self):
        """Create the tabbed interface"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_tabs(self):
        """Add and configure all tabs"""
        # Queue Management Tab
        self.queue_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.queue_tab, text="Manage Queue")
        self.build_queue_tab()

        # Add Customer Tab
        self.add_customer_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.add_customer_tab, text="Add Customer")
        self.build_add_customer_tab()

    def build_queue_tab(self):
        """Build the queue management interface"""
        # Create detailed treeview with time column
        self.queue_tree = self.controller.create_queue_treeview(self.queue_tab, detailed=True)
        self.queue_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.queue_tab, orient="vertical", command=self.queue_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_tree.configure(yscrollcommand=scrollbar.set)

        # Initial data load (detailed view)
        self.refresh_queue()

        # Action buttons
        self.add_queue_action_buttons()

    def add_queue_action_buttons(self):
        """Add buttons for queue management actions"""
        button_frame = tk.Frame(self.queue_tab)
        button_frame.pack(pady=10, fill=tk.X)
        
        actions = [
            ("Mark as In Process", "In Process"),
            ("Mark as Ready", "Ready"),
            ("Mark as Completed", "Completed"),
            ("Remove from Queue", "remove")
        ]
        
        for text, action in actions:
            btn = tk.Button(button_frame, text=text,
                          font=self.controller.button_font,
                          command=lambda a=action: self.handle_queue_action(a))
            btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def handle_queue_action(self, action):
        """Handle all queue management actions"""
        selected_item = self.queue_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a customer first")
            return
            
        name = self.queue_tree.item(selected_item)['values'][1]  # Name is at index 1
        
        if action == "remove":
            if self.controller.remove_from_queue(name):
                messagebox.showinfo("Success", f"Removed {name} from queue")
        elif action == "Completed":
            self.controller.complete_customer(name)
            messagebox.showinfo("Completed", f"Marked {name} as completed")
        else:
            if self.controller.update_queue_status(name, action):
                messagebox.showinfo("Updated", f"Updated {name} status to {action}")
        
        self.refresh_queue()

    def build_add_customer_tab(self):
        """Build the customer registration interface"""
        # Phone number entry
        tk.Label(self.add_customer_tab, 
                text="Customer Phone Number", 
                font=self.controller.label_font).pack(pady=10)
        
        self.phone_entry = tk.Entry(self.add_customer_tab, 
                                  font=self.controller.label_font, 
                                  justify='center')
        self.phone_entry.pack(pady=5, ipady=5, fill=tk.X, padx=20)
        
        # Submit button
        tk.Button(self.add_customer_tab, 
                 text="Check Phone", 
                 font=self.controller.button_font,
                 command=self.check_phone_number).pack(pady=10)
        
        # Response area
        self.response_frame = tk.Frame(self.add_customer_tab)
        self.response_frame.pack(pady=10, fill=tk.BOTH, expand=True)

    def check_phone_number(self):
        """Check if phone exists in database"""
        phone_number = self.phone_entry.get().strip()
        if not phone_number:
            messagebox.showerror("Error", "Please enter a phone number")
            return
        
        # Use controller method to lookup customer
        name = self.controller.lookup_customer(phone_number)
        
        # Clear previous response
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        if name:
            # Existing customer found
            self.show_customer_found_response(name)
        else:
            # New customer
            self.show_new_customer_form()

    def show_customer_found_response(self, name):
        """Display options for existing customer"""
        tk.Label(self.response_frame, 
                text=f"Customer Found: {name}", 
                font=self.controller.label_font).pack(pady=5)
        
        tk.Button(self.response_frame, 
                text="Add to Queue", 
                font=self.controller.button_font,
                command=lambda: self.add_to_queue(name)).pack(pady=10)
        
        tk.Button(self.response_frame, 
                text="View Queue", 
                font=self.controller.button_font,
                command=self.show_queue_popup).pack(pady=5)

    def show_new_customer_form(self):
        """Display form for new customer registration"""
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.response_frame, 
                text="New Customer Registration", 
                font=self.controller.label_font).pack(pady=5)
        
        tk.Label(self.response_frame, 
                text="Full Name (First Last)", 
                font=self.controller.label_font).pack(pady=5)
        
        self.name_entry = tk.Entry(self.response_frame, 
                                 font=self.controller.label_font)
        self.name_entry.pack(pady=5, ipady=3, fill=tk.X, padx=20)
        
        tk.Button(self.response_frame, 
                text="Register & Add to Queue", 
                font=self.controller.button_font,
                command=self.register_new_customer).pack(pady=10)

    def register_new_customer(self):
        """Handle new customer registration"""
        full_name = self.name_entry.get().strip()
        phone_number = self.phone_entry.get().strip()
        
        if not full_name or len(full_name.split()) < 2:
            messagebox.showerror("Error", "Please enter both first and last name")
            return
            
        if not phone_number:
            messagebox.showerror("Error", "Phone number is required")
            return
        
        # Use controller method to register customer
        if self.controller.register_customer(phone_number, full_name):
            self.add_to_queue(full_name)
        else:
            messagebox.showerror("Error", "This phone number is already registered")

    def add_to_queue(self, name):
        """Add customer to queue using controller method"""
        added, status = self.controller.add_customer_to_queue(name)
        
        # Clear response area
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        if added:
            tk.Label(self.response_frame, 
                    text=f"{name} added to queue successfully", 
                    font=self.controller.label_font).pack(pady=10)
            
            # Show queue button
            tk.Button(self.response_frame, 
                     text="View Current Queue", 
                     font=self.controller.button_font,
                     command=self.show_queue_popup).pack(pady=5)
            
            # Refresh queue display
            self.refresh_queue()
        else:
            tk.Label(self.response_frame, 
                    text=f"{name} is already in queue (Status: {status})", 
                    font=self.controller.label_font).pack(pady=10)
            
            tk.Button(self.response_frame, 
                     text="Refresh Status", 
                     font=self.controller.button_font,
                     command=self.check_phone_number).pack(pady=5)

    def show_queue_popup(self):
        """Display queue in popup window"""
        queue_window = tk.Toplevel(self)
        queue_window.title("Current Queue")
        queue_window.geometry("700x500")
        
        # Use controller's standardized treeview
        tree = self.controller.create_queue_treeview(queue_window)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(queue_window, 
                                orient="vertical", 
                                command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Populate with data
        self.controller.populate_queue_tree(tree)
        
        # Close button
        tk.Button(queue_window, 
                 text="Close", 
                 font=self.controller.button_font,
                 command=queue_window.destroy).pack(pady=10)

    def refresh_queue(self):
        """Refresh the queue display (detailed view)"""
        if hasattr(self, 'queue_tree'):
            self.controller.populate_queue_tree(self.queue_tree, detailed=True)

    def add_logout_button(self):
        """Add logout button at bottom"""
        logout_frame = tk.Frame(self)
        logout_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        tk.Button(logout_frame, 
                 text="Logout", 
                 font=self.controller.button_font,
                 command=lambda: self.controller.show_frame(CustomerView)
                 ).pack(side=tk.RIGHT, padx=10)

class AdminView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.notebook = None
        self.queue_tree = None
        self.customers_tree = None
        self.reports_frame = None
        self.monitors_window = None

    def build_admin_view(self):
        """Initialize the admin dashboard"""
        self.clear_widgets()
        self.create_notebook()
        self.add_tabs()
        self.add_logout_button()
        self.refresh_reports()  # Initial report generation

    def clear_widgets(self):
        """Clear all existing widgets"""
        for widget in self.winfo_children():
            widget.destroy()

    def create_notebook(self):
        """Create the tabbed interface"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_tabs(self):
        """Add and configure all admin tabs"""
        tabs = [
            ("Dashboard", self.build_home_tab),
            ("Reports", self.build_reports_tab),
            ("Queue", self.build_queue_tab),
            ("Customers", self.build_customers_tab),
            ("Add Customer", self.build_add_customer_tab)
        ]

        for tab_name, builder in tabs:
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name)
            builder(tab_frame)  # Pass the tab_frame to the builder

    def build_home_tab(self, parent):
        """Build the admin dashboard tab"""
        dashboard_frame = tk.Frame(parent)
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Queue stats
        stats_frame = tk.LabelFrame(dashboard_frame, text="Queue Statistics", 
                                font=self.controller.label_font)
        stats_frame.pack(fill=tk.X, pady=10)

        # Get queue data using controller
        queue = self.controller.get_queue_data()
        in_queue = sum(1 for item in queue if item["status"] == "In Queue")
        in_process = sum(1 for item in queue if item["status"] == "In Process")
        ready = sum(1 for item in queue if item["status"] == "Ready")

        stats_text = f"In Queue: {in_queue} | In Process: {in_process} | Ready: {ready}"
        tk.Label(stats_frame, text=stats_text, 
                font=self.controller.label_font).pack(pady=10)

        # Quick actions
        actions_frame = tk.LabelFrame(dashboard_frame, text="Quick Actions",
                                    font=self.controller.label_font)
        actions_frame.pack(fill=tk.X, pady=10)

        tk.Button(actions_frame, text="View Customer Queue",
                command=lambda: self.notebook.select(2),  # Queue tab index
                font=self.controller.button_font).pack(pady=5, fill=tk.X)

        tk.Button(actions_frame, text="View Customer Database",
                command=lambda: self.notebook.select(3),  # Customers tab index
                font=self.controller.button_font).pack(pady=5, fill=tk.X)

        tk.Button(actions_frame, text="Open Queue Monitor",
                command=self.show_monitors_view,
                font=self.controller.button_font).pack(pady=5, fill=tk.X)

        # Add logout button to dashboard
        logout_frame = tk.Frame(dashboard_frame)
        logout_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        tk.Button(logout_frame, text="Logout",
                command=lambda: self.controller.show_frame(CustomerView),
                font=self.controller.button_font).pack(side=tk.RIGHT, padx=10)

    def build_reports_tab(self, parent):
        """Build the reports tab with analytics"""
        self.reports_frame = ttk.Frame(parent)
        self.reports_frame.pack(fill=tk.BOTH, expand=True)

        # Refresh button
        tk.Button(parent, text="Refresh Reports",
                 command=self.refresh_reports,
                 font=self.controller.button_font).pack(pady=5)

    def refresh_reports(self):
        """Generate and display all reports"""
        if not hasattr(self, 'reports_frame'):
            return

        # Clear existing reports
        for widget in self.reports_frame.winfo_children():
            widget.destroy()

        # Outcome report
        self.generate_outcome_report()

        # Growth report
        self.generate_growth_report()

    def generate_outcome_report(self):
        """Generate customer outcome report"""
        try:
            with open(self.controller.history_file, 'r') as f:
                history = json.load(f)
                completed = sum(1 for item in history if item["status"] == "Completed")
                cancelled = sum(1 for item in history if item["status"] == "Cancelled")
        except (FileNotFoundError, json.JSONDecodeError):
            completed, cancelled = 0, 0

        frame = ttk.LabelFrame(self.reports_frame, text="Customer Outcomes")
        frame.pack(fill=tk.X, padx=10, pady=5)

        fig, ax = plt.subplots(figsize=(8, 3))
        if completed + cancelled > 0:
            categories = ['Completed', 'Cancelled']
            counts = [completed, cancelled]
            colors = ['#4CAF50', '#F44336']
            bars = ax.bar(categories, counts, color=colors)
            ax.set_title('Customer Service Outcomes')
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height}',
                        ha='center', va='bottom')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            ax.set_title('Customer Outcomes (No Data)')

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def generate_growth_report(self):
        """Generate customer growth report"""
        try:
            with open(self.controller.database_file, 'r') as f:
                customers = json.load(f)
            
            # Group by month
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            monthly_counts = {month: 0 for month in months}
            
            for customer in customers:
                try:
                    timestamp = float(customer["registration_timestamp"])
                    month = datetime.fromtimestamp(timestamp).strftime('%b')
                    if month in monthly_counts:
                        monthly_counts[month] += 1
                except:
                    continue
        except (FileNotFoundError, json.JSONDecodeError):
            monthly_counts = {month: 0 for month in months}

        frame = ttk.LabelFrame(self.reports_frame, text="Customer Growth")
        frame.pack(fill=tk.X, padx=10, pady=5)

        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(list(monthly_counts.keys()), list(monthly_counts.values()), 
               marker='o', color='#2196F3')
        ax.set_title('Monthly Customer Registrations')
        ax.set_ylabel('Number of Customers')
        ax.grid(True, linestyle='--', alpha=0.6)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def build_queue_tab(self, parent):
        """Build the queue management tab"""
        # Create detailed treeview with time column
        self.queue_tree = self.controller.create_queue_treeview(parent, detailed=True)
        self.queue_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.queue_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_tree.configure(yscrollcommand=scrollbar.set)

        # Initial data load (detailed view)
        self.refresh_queue()

        # Action buttons
        self.add_queue_action_buttons(parent)

    def add_queue_action_buttons(self, parent):
        """Add queue management buttons"""
        button_frame = tk.Frame(parent)
        button_frame.pack(pady=10, fill=tk.X)
        
        actions = [
            ("Mark as Ready", "Ready"),
            ("Mark as In Process", "In Process"),
            ("Mark as Completed", "Completed"),
            ("Mark as Cancelled", "Cancelled"),
            ("Remove", "remove")
        ]
        
        for text, action in actions:
            btn = tk.Button(button_frame, text=text,
                          font=self.controller.button_font,
                          command=lambda a=action: self.handle_queue_action(a))
            btn.pack(side=tk.LEFT, padx=5, expand=True)

    def handle_queue_action(self, action):
        """Handle queue management actions"""
        selected_item = self.queue_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a customer first")
            return
            
        name = self.queue_tree.item(selected_item)['values'][1]  # Name is at index 1
        
        if action == "remove":
            if self.controller.remove_from_queue(name):
                messagebox.showinfo("Success", f"Removed {name} from queue")
        elif action in ["Completed", "Cancelled"]:
            self.controller.complete_customer(name, action)
            messagebox.showinfo("Success", f"Marked {name} as {action}")
        else:
            if self.controller.update_queue_status(name, action):
                messagebox.showinfo("Updated", f"Updated {name} status to {action}")
        
        self.refresh_queue()
        if hasattr(self, 'monitors_window') and self.monitors_window.winfo_exists():
            self.refresh_monitors_view(self.monitors_tree)

    def build_customers_tab(self, parent):
        """Build the customer database tab"""
        # Create treeview
        self.customers_tree = ttk.Treeview(parent, 
                                         columns=('Phone', 'Name', 'Date'), 
                                         show='headings')
        self.customers_tree.heading('Phone', text='Phone Number')
        self.customers_tree.heading('Name', text='Name')
        self.customers_tree.heading('Date', text='Registration Date')
        self.customers_tree.column('Phone', width=150)
        self.customers_tree.column('Name', width=200)
        self.customers_tree.column('Date', width=150)
        self.customers_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.customers_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.customers_tree.configure(yscrollcommand=scrollbar.set)
        
        # Search functionality
        search_frame = tk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search:", 
                font=self.controller.label_font).pack(side=tk.LEFT)
        
        self.search_entry = tk.Entry(search_frame, 
                                   font=self.controller.label_font)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.search_customers)
        
        # Initial data load
        self.refresh_customers()

    def search_customers(self, event=None):
        """Filter customers based on search query"""
        query = self.search_entry.get().lower()
        
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        customers = self.controller.get_customer_data()
        for customer in customers:
            phone = customer["phone"]
            name = customer["name"]
            if query in phone.lower() or query in name.lower():
                try:
                    date = datetime.fromtimestamp(
                        float(customer["registration_timestamp"])
                    ).strftime('%Y-%m-%d %H:%M')
                except:
                    date = "N/A"
                
                self.customers_tree.insert('', tk.END, values=(phone, name, date))

    def refresh_customers(self):
        """Reload customer data"""
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        customers = self.controller.get_customer_data()
        for customer in customers:
            phone = customer["phone"]
            name = customer["name"]
            try:
                date = datetime.fromtimestamp(
                    float(customer["registration_timestamp"])
                    ).strftime('%Y-%m-%d %H:%M')
            except:
                date = "N/A"
            
            self.customers_tree.insert('', tk.END, values=(phone, name, date))

    def build_add_customer_tab(self, parent):
        """Build the customer registration tab"""
        form_frame = tk.Frame(parent)
        form_frame.pack(pady=20)
        
        # Phone number
        tk.Label(form_frame, text="Phone Number:", 
                font=self.controller.label_font).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.add_phone_entry = tk.Entry(form_frame, 
                                      font=self.controller.label_font)
        self.add_phone_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Name
        tk.Label(form_frame, text="Full Name:", 
                font=self.controller.label_font).grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.add_name_entry = tk.Entry(form_frame, 
                                     font=self.controller.label_font)
        self.add_name_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Buttons
        button_frame = tk.Frame(parent)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Register Customer",
                 command=self.register_customer,
                 font=self.controller.button_font).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Clear Form",
                 command=self.clear_add_customer_form,
                 font=self.controller.button_font).pack(side=tk.LEFT, padx=5)

    def register_customer(self):
        """Register new customer from admin interface"""
        phone = self.add_phone_entry.get().strip()
        name = self.add_name_entry.get().strip()
        
        if not phone or not name:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        if len(name.split()) < 2:
            messagebox.showerror("Error", "Please enter full name (first and last)")
            return
        
        if self.controller.register_customer(phone, name):
            messagebox.showinfo("Success", f"Customer {name} registered successfully")
            self.clear_add_customer_form()
            self.refresh_customers()
        else:
            messagebox.showerror("Error", "This phone number is already registered")

    def clear_add_customer_form(self):
        """Clear the customer registration form"""
        self.add_phone_entry.delete(0, tk.END)
        self.add_name_entry.delete(0, tk.END)

    def show_monitors_view(self):
        """Display the queue monitor window"""
        # Check if window exists properly
        if hasattr(self, 'monitors_window'):
            try:
                if self.monitors_window and self.monitors_window.winfo_exists():
                    self.monitors_window.lift()
                    self.refresh_monitors_view(self.monitors_tree)
                    return
            except tk.TclError:
                # Window was destroyed but reference still exists
                self.monitors_window = None
        
        # Create new window if it doesn't exist or was closed
        self.monitors_window = tk.Toplevel(self)
        self.monitors_window.title("Queue Monitor")
        self.monitors_window.geometry("800x500")
        
        # Create treeview
        self.monitors_tree = self.controller.create_queue_treeview(self.monitors_window)
        self.monitors_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.monitors_window, 
                                orient="vertical", 
                                command=self.monitors_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.monitors_tree.configure(yscrollcommand=scrollbar.set)
        
        # Initial data load
        self.refresh_monitors_view(self.monitors_tree)
        
        # Close button
        tk.Button(self.monitors_window, text="Close",
                command=self.on_monitors_window_close,
                font=self.controller.button_font).pack(pady=10)
        
        self.monitors_window.protocol("WM_DELETE_WINDOW", self.on_monitors_window_close)

    def refresh_monitors_view(self, tree):
        """Refresh the monitors window"""
        if not hasattr(self, 'monitors_window') or not self.monitors_window:
            return
        try:
            if self.monitors_window.winfo_exists():
                self.controller.populate_queue_tree(tree)
        except tk.TclError:
            self.monitors_window = None

    def on_monitors_window_close(self):
        """Clean up monitors window resources"""
        if hasattr(self, 'monitors_window') and self.monitors_window:
            try:
                self.monitors_window.destroy()
            except tk.TclError:
                pass  # Window was already destroyed
            self.monitors_window = None
        
        if hasattr(self, 'monitors_tree'):
            del self.monitors_tree

    def refresh_queue(self):
        """Refresh the queue display (detailed view)"""
        if hasattr(self, 'queue_tree'):
            self.controller.populate_queue_tree(self.queue_tree, detailed=True)

    def add_logout_button(self):
        """Add logout button at bottom"""
        logout_frame = tk.Frame(self)
        logout_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        tk.Button(logout_frame, text="Logout",
                 command=lambda: self.controller.show_frame(CustomerView),
                 font=self.controller.button_font).pack(side=tk.RIGHT, padx=10)
        
    def refresh_queue_view(self):
        """Refresh the queue popup window if it exists"""
        if hasattr(self, 'queue_window') and self.queue_window.winfo_exists():
            self.controller.populate_queue_tree(self.queue_tree)
    
    def on_queue_window_close(self):
        """Clean up queue window resources"""
        if hasattr(self, 'queue_window'):
            self.queue_window.destroy()
            delattr(self, 'queue_window')
            delattr(self, 'queue_tree')
    
    def show_queue_view(self):
        """Display current queue in popup window"""
        self.queue_window = tk.Toplevel(self)
        self.queue_window.title("Current Queue")
        self.queue_window.geometry("600x400")
        
        # Use controller's standardized treeview creation
        self.queue_tree = self.controller.create_queue_treeview(self.queue_window)
        self.queue_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Populate with current queue data
        self.controller.populate_queue_tree(self.queue_tree)
        
        self.queue_window.protocol("WM_DELETE_WINDOW", self.on_queue_window_close)

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendSmartApp(root)
    
    def on_closing():
        if hasattr(app, 'running') and app.running:
            app.cleanup()
        root.destroy()
    
    # Set protocol handler immediately after creating the window
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()