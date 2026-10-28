"""
gui.py
------
The Tkinter graphical user interface for the Smart Campus Resource
Booking System.

There is one main window (the root). Each screen is a class that builds
its widgets inside the root window:
    LoginScreen -> RegisterScreen -> CampusScreen -> MainScreen
The MainScreen shows a menu on the left. Which buttons appear depends on
the role of the logged-in user (role-based access control).
"""

import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta

import database
import campus
import booking_manager
import reports

# Fonts and colours used by every screen
FONT_TITLE = ("Helvetica", 16, "bold")
FONT_HEADING = ("Helvetica", 13, "bold")
FONT_NORMAL = ("Helvetica", 11)
FONT_LIST = ("Courier", 10)
COLOUR_HEADER = "#1f4e79"
COLOUR_POLICY = "#ddebf7"


# ---------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------
def safe_call(function, *args):
    """Call a function and show a friendly message if the database fails."""
    try:
        return function(*args)
    except sqlite3.Error as error:
        return (False, "A database error occurred: " + str(error))


def make_listbox(parent, height=15):
    """A Listbox with vertical and horizontal scroll bars.
    Returns (frame, listbox). The caller must pack the frame."""
    frame = tk.Frame(parent)
    listbox = tk.Listbox(frame, height=height, width=100, font=FONT_LIST,
                         exportselection=False)
    y_scroll = tk.Scrollbar(frame, orient="vertical", command=listbox.yview)
    x_scroll = tk.Scrollbar(frame, orient="horizontal", command=listbox.xview)
    listbox.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
    y_scroll.pack(side="right", fill="y")
    x_scroll.pack(side="bottom", fill="x")
    listbox.pack(side="left", fill="both", expand=True)
    return frame, listbox


def fill_listbox(listbox, lines):
    """Replace everything in a Listbox with a new list of text lines."""
    listbox.delete(0, "end")
    for line in lines:
        listbox.insert("end", line)


def get_selected_index(listbox):
    """Index of the selected row, or None if nothing is selected."""
    selection = listbox.curselection()
    if len(selection) == 0:
        return None
    return selection[0]


# ---------------------------------------------------------------
# The application: owns the window and moves between screens
# ---------------------------------------------------------------
class App:
    def __init__(self):
        try:
            database.setup_database()
        except sqlite3.Error as error:
            messagebox.showerror("Database error",
                                 "The database could not be opened:\n" + str(error))
            raise SystemExit

        self.root = tk.Tk()
        self.root.title("Smart Campus Resource Booking System")
        self.root.geometry("1050x680")

        self.user = None       # the logged-in User object
        self.campus = None     # name of the currently active campus
        self.show_login()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login(self):
        self.user = None
        self.campus = None
        self.clear_screen()
        LoginScreen(self)

    def show_register(self):
        self.clear_screen()
        RegisterScreen(self)

    def show_campus_screen(self):
        self.clear_screen()
        CampusScreen(self)

    def show_main_screen(self):
        self.clear_screen()
        MainScreen(self)

    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------------
# Login screen
# ---------------------------------------------------------------
class LoginScreen:
    def __init__(self, app):
        self.app = app
        self.frame = tk.Frame(app.root, padx=30, pady=30)
        self.frame.pack(expand=True)

        tk.Label(self.frame, text="Smart Campus Resource Booking System",
                 font=FONT_TITLE).pack(pady=(0, 5))
        tk.Label(self.frame, text="Richfield Graduate Institution",
                 font=FONT_NORMAL).pack(pady=(0, 20))

        tk.Label(self.frame, text="Username", font=FONT_NORMAL).pack(anchor="w")
        self.username_entry = tk.Entry(self.frame, width=32, font=FONT_NORMAL)
        self.username_entry.pack(pady=(0, 10))

        tk.Label(self.frame, text="Password", font=FONT_NORMAL).pack(anchor="w")
        self.password_entry = tk.Entry(self.frame, width=32, show="*", font=FONT_NORMAL)
        self.password_entry.pack(pady=(0, 15))
        self.password_entry.bind("<Return>", lambda event: self.login())

        tk.Button(self.frame, text="Login", width=20, command=self.login).pack(pady=3)
        tk.Button(self.frame, text="Register as a Lecturer", width=20,
                  command=self.app.show_register).pack(pady=3)

        tk.Label(self.frame, text="Sample accounts: lecturer1 / lecturer123, "
                 "admin_jhb / admin123, operator / operator123",
                 font=("Helvetica", 9), fg="gray").pack(pady=(20, 0))
        self.username_entry.focus_set()

    def login(self):
        try:
            user, message = booking_manager.login(self.username_entry.get(),
                                                  self.password_entry.get())
        except sqlite3.Error as error:
            user, message = None, "A database error occurred: " + str(error)

        if not user:
            messagebox.showerror("Login failed", message)
            self.password_entry.delete(0, "end")
            return
        self.app.user = user
        self.app.show_campus_screen()


# ---------------------------------------------------------------
# Register screen (lecturers only)
# ---------------------------------------------------------------
class RegisterScreen:
    def __init__(self, app):
        self.app = app
        self.frame = tk.Frame(app.root, padx=30, pady=30)
        self.frame.pack(expand=True)

        tk.Label(self.frame, text="Register a Lecturer Account",
                 font=FONT_TITLE).pack(pady=(0, 15))

        tk.Label(self.frame, text="Full name", font=FONT_NORMAL).pack(anchor="w")
        self.name_entry = tk.Entry(self.frame, width=32, font=FONT_NORMAL)
        self.name_entry.pack(pady=(0, 8))

        tk.Label(self.frame, text="Username", font=FONT_NORMAL).pack(anchor="w")
        self.username_entry = tk.Entry(self.frame, width=32, font=FONT_NORMAL)
        self.username_entry.pack(pady=(0, 8))

        tk.Label(self.frame, text="Password (at least 6 characters)",
                 font=FONT_NORMAL).pack(anchor="w")
        self.password_entry = tk.Entry(self.frame, width=32, show="*", font=FONT_NORMAL)
        self.password_entry.pack(pady=(0, 8))

        tk.Label(self.frame, text="Confirm password", font=FONT_NORMAL).pack(anchor="w")
        self.confirm_entry = tk.Entry(self.frame, width=32, show="*", font=FONT_NORMAL)
        self.confirm_entry.pack(pady=(0, 15))

        tk.Button(self.frame, text="Create Account", width=20,
                  command=self.register).pack(pady=3)
        tk.Button(self.frame, text="Back to Login", width=20,
                  command=self.app.show_login).pack(pady=3)

    def register(self):
        ok, message = safe_call(booking_manager.register_lecturer,
                                self.username_entry.get(), self.name_entry.get(),
                                self.password_entry.get(), self.confirm_entry.get())
        if ok:
            messagebox.showinfo("Registration successful", message)
            self.app.show_login()
        else:
            messagebox.showerror("Registration failed", message)


# ---------------------------------------------------------------
# Campus selection screen
# ---------------------------------------------------------------
class CampusScreen:
    def __init__(self, app):
        self.app = app
        self.frame = tk.Frame(app.root, padx=30, pady=30)
        self.frame.pack(expand=True)

        tk.Label(self.frame, text="Welcome, " + app.user.get_full_name(),
                 font=FONT_TITLE).pack()
        tk.Label(self.frame, text="Role: " + app.user.get_role(),
                 font=FONT_NORMAL).pack(pady=(0, 15))
        tk.Label(self.frame, text="Select a campus to work with:",
                 font=FONT_HEADING).pack()

        # Only the campuses this user is allowed to use are shown.
        self.choices = app.user.get_campus_choices(campus.get_campus_names())
        self.listbox = tk.Listbox(self.frame, height=len(self.choices) + 1, width=30,
                                  font=FONT_NORMAL, exportselection=False)
        for name in self.choices:
            self.listbox.insert("end", name)
        self.listbox.pack(pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.show_policy)

        self.policy_label = tk.Label(self.frame, text="", wraplength=500,
                                     justify="left", bg=COLOUR_POLICY, padx=8, pady=6)
        self.policy_label.pack(pady=10)

        tk.Button(self.frame, text="Continue", width=20,
                  command=self.continue_clicked).pack(pady=3)
        tk.Button(self.frame, text="Logout", width=20,
                  command=self.app.show_login).pack(pady=3)

        # An administrator has only one campus, so select it automatically.
        if len(self.choices) == 1:
            self.listbox.selection_set(0)
            self.show_policy(None)

    def selected_campus(self):
        index = get_selected_index(self.listbox)
        if index is None:
            return None
        return self.choices[index]

    def show_policy(self, event):
        name = self.selected_campus()
        if name is not None:
            rule = campus.get_campus(name).get_rule()
            self.policy_label.configure(text="Booking policy: " + rule.describe())

    def continue_clicked(self):
        name = self.selected_campus()
        if name is None:
            messagebox.showwarning("Select a campus", "Please select a campus first.")
            return
        self.app.campus = name
        self.app.show_main_screen()


# ---------------------------------------------------------------
# Main screen: header, role-based menu and the content area
# ---------------------------------------------------------------
class MainScreen:
    def __init__(self, app):
        self.app = app
        self.frame = tk.Frame(app.root)
        self.frame.pack(fill="both", expand=True)

        # Header shows the active campus and the user
        header = tk.Frame(self.frame, bg=COLOUR_HEADER, padx=10, pady=8)
        header.pack(fill="x")
        tk.Label(header, text="Active campus: " + app.campus, bg=COLOUR_HEADER,
                 fg="white", font=FONT_TITLE).pack(side="left")
        tk.Button(header, text="Logout", command=app.show_login).pack(side="right")
        tk.Button(header, text="Change Campus",
                  command=app.show_campus_screen).pack(side="right", padx=8)
        tk.Label(header, text=str(app.user), bg=COLOUR_HEADER, fg="white",
                 font=FONT_NORMAL).pack(side="right", padx=15)

        # The booking policy in effect is always visible
        rule = campus.get_campus(app.campus).get_rule()
        tk.Label(self.frame, text="Booking policy in effect - " + rule.describe(),
                 wraplength=1000, justify="left", anchor="w", bg=COLOUR_POLICY,
                 padx=10, pady=4).pack(fill="x")

        body = tk.Frame(self.frame)
        body.pack(fill="both", expand=True)
        menu = tk.Frame(body, padx=8, pady=8)
        menu.pack(side="left", fill="y")
        self.content = tk.Frame(body)
        self.content.pack(side="right", fill="both", expand=True)

        # Each menu item: (button text, permission needed, function that builds the page)
        campus_name = app.campus
        items = [
            ("Book a Resource", "book_resource",
             lambda parent: ResourceSlotPage(parent, app, True)),
            ("My Bookings", "view_own_bookings",
             lambda parent: MyBookingsPage(parent, app)),
            ("Resource Availability", "view_availability",
             lambda parent: ResourceSlotPage(parent, app, False)),
            ("Manage Resources", "manage_resources",
             lambda parent: ManageResourcesPage(parent, app)),
            ("Campus Bookings", "view_campus_bookings",
             lambda parent: TextListPage(parent, "Bookings at " + campus_name,
                                         lambda: reports.campus_booking_lines(campus_name),
                                         reports.booking_header(show_user=True))),
            ("Campus Report", "view_campus_report",
             lambda parent: TextListPage(parent, "Report for " + campus_name,
                                         lambda: reports.campus_report(campus_name))),
            ("All Bookings", "view_all_bookings",
             lambda parent: TextListPage(parent, "Bookings at all campuses",
                                         reports.all_booking_lines,
                                         reports.booking_header(True, True))),
            ("All Resources", "view_all_resources",
             lambda parent: TextListPage(parent, "Resources at all campuses",
                                         reports.all_resource_lines,
                                         reports.resource_header(True))),
            ("Compare Campuses", "compare_campuses",
             lambda parent: TextListPage(parent, "Cross-campus comparison",
                                         reports.comparison_report)),
        ]

        first_page = None
        for text, permission, builder in items:
            if app.user.has_permission(permission):
                tk.Button(menu, text=text, width=22,
                          command=lambda b=builder: self.open_page(b)).pack(pady=3)
                if first_page is None:
                    first_page = builder
        if first_page is not None:
            self.open_page(first_page)

    def open_page(self, builder):
        for widget in self.content.winfo_children():
            widget.destroy()
        builder(self.content)


# ---------------------------------------------------------------
# A simple page that shows a list of text lines with a Refresh button
# ---------------------------------------------------------------
class TextListPage:
    def __init__(self, parent, title, get_lines, header=""):
        self.get_lines = get_lines
        self.frame = tk.Frame(parent, padx=10, pady=10)
        self.frame.pack(fill="both", expand=True)

        top = tk.Frame(self.frame)
        top.pack(fill="x")
        tk.Label(top, text=title, font=FONT_HEADING).pack(side="left")
        tk.Button(top, text="Refresh", command=self.refresh).pack(side="right")

        if header != "":
            tk.Label(self.frame, text=header, font=FONT_LIST, anchor="w").pack(fill="x")
        box, self.listbox = make_listbox(self.frame, 22)
        box.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        try:
            lines = self.get_lines()
        except sqlite3.Error as error:
            lines = ["A database error occurred: " + str(error)]
        if len(lines) == 0:
            lines = ["(nothing to show yet)"]
        fill_listbox(self.listbox, lines)


# ---------------------------------------------------------------
# Resource availability + booking page
# ---------------------------------------------------------------
class ResourceSlotPage:
    """Shows each resource and whether it is free for the chosen date, time
    and duration. When allow_booking is True a lecturer can book it."""

    def __init__(self, parent, app, allow_booking):
        self.app = app
        self.allow_booking = allow_booking
        self.rows = []     # resource dictionaries, in the same order as the Listbox

        self.frame = tk.Frame(parent, padx=10, pady=10)
        self.frame.pack(fill="both", expand=True)

        if allow_booking:
            title = "Book a Resource"
        else:
            title = "Resource Availability"
        tk.Label(self.frame, text=title + " - " + app.campus,
                 font=FONT_HEADING).pack(anchor="w")
        tk.Label(self.frame, text="Choose a date, start time and duration. The list "
                 "updates automatically.", font=FONT_NORMAL).pack(anchor="w", pady=(0, 5))

        # Input fields (laid out with grid inside their own frame)
        form = tk.Frame(self.frame)
        form.pack(fill="x", pady=5)
        tk.Label(form, text="Date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w", padx=5)
        tk.Label(form, text="Start time (HH:MM)").grid(row=0, column=1, sticky="w", padx=5)
        tk.Label(form, text="Duration (minutes)").grid(row=0, column=2, sticky="w", padx=5)

        self.date_entry = tk.Entry(form, width=16)
        self.time_entry = tk.Entry(form, width=16)
        self.duration_entry = tk.Entry(form, width=16)
        self.date_entry.grid(row=1, column=0, padx=5)
        self.time_entry.grid(row=1, column=1, padx=5)
        self.duration_entry.grid(row=1, column=2, padx=5)

        tomorrow = datetime.now() + timedelta(days=1)
        self.date_entry.insert(0, tomorrow.strftime("%Y-%m-%d"))
        self.time_entry.insert(0, "09:00")
        self.duration_entry.insert(0, "60")

        # Update the list whenever the user types in one of the fields
        for entry in (self.date_entry, self.time_entry, self.duration_entry):
            entry.bind("<KeyRelease>", lambda event: self.refresh())
        tk.Button(form, text="Check Availability",
                  command=self.refresh).grid(row=1, column=3, padx=10)

        tk.Label(self.frame, text=reports.resource_header(), font=FONT_LIST,
                 anchor="w").pack(fill="x", pady=(10, 0))
        box, self.listbox = make_listbox(self.frame, 12)
        box.pack(fill="both", expand=True)

        if allow_booking:
            tk.Button(self.frame, text="Book Selected Resource", width=26,
                      command=self.book).pack(pady=8)

        self.refresh()
        self.keep_refreshing()

    def selected_resource_id(self):
        index = get_selected_index(self.listbox)
        if index is None or index >= len(self.rows):
            return ""
        return self.rows[index]["resource_id"]

    def refresh(self):
        """Reload the resource list with the current availability."""
        previous_id = self.selected_resource_id()
        try:
            results = booking_manager.get_availability(
                self.app.campus, self.date_entry.get(),
                self.time_entry.get(), self.duration_entry.get())
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error))
            return

        self.rows = []
        self.listbox.delete(0, "end")
        for resource, state in results:
            self.rows.append(resource)
            self.listbox.insert("end", reports.resource_line(resource, state))
            index = len(self.rows) - 1
            if state == "Available":
                self.listbox.itemconfig(index, fg="dark green")
            elif state == "Booked":
                self.listbox.itemconfig(index, fg="red")
            else:
                self.listbox.itemconfig(index, fg="gray")
            if resource["resource_id"] == previous_id:
                self.listbox.selection_set(index)

    def keep_refreshing(self):
        """Refresh every 10 seconds so the availability stays up to date."""
        if self.frame.winfo_exists():
            self.refresh()
            self.app.root.after(10000, self.keep_refreshing)

    def book(self):
        ok, message = safe_call(booking_manager.make_booking, self.app.user,
                                self.app.campus, self.selected_resource_id(),
                                self.date_entry.get(), self.time_entry.get(),
                                self.duration_entry.get())
        if ok:
            messagebox.showinfo("Booking confirmed", message)
        else:
            messagebox.showerror("Booking failed", message)
        self.refresh()


# ---------------------------------------------------------------
# A lecturer's own bookings
# ---------------------------------------------------------------
class MyBookingsPage:
    def __init__(self, parent, app):
        self.app = app
        self.rows = []

        self.frame = tk.Frame(parent, padx=10, pady=10)
        self.frame.pack(fill="both", expand=True)
        tk.Label(self.frame, text="My Bookings", font=FONT_HEADING).pack(anchor="w")

        options = tk.Frame(self.frame)
        options.pack(fill="x", pady=5)
        self.view_var = tk.StringVar(value="Active")
        tk.Radiobutton(options, text="Active bookings", variable=self.view_var,
                       value="Active", command=self.refresh).pack(side="left", padx=5)
        tk.Radiobutton(options, text="Past history (completed/cancelled)",
                       variable=self.view_var, value="History",
                       command=self.refresh).pack(side="left", padx=5)
        tk.Radiobutton(options, text="Everything", variable=self.view_var,
                       value="All", command=self.refresh).pack(side="left", padx=5)

        tk.Label(self.frame, text=reports.booking_header(show_campus=True),
                 font=FONT_LIST, anchor="w").pack(fill="x")
        box, self.listbox = make_listbox(self.frame, 15)
        box.pack(fill="both", expand=True)

        tk.Button(self.frame, text="Cancel Selected Booking", width=26,
                  command=self.cancel).pack(pady=8)
        self.refresh()

    def refresh(self):
        try:
            self.rows = booking_manager.get_my_bookings(self.app.user, self.view_var.get())
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error))
            return
        lines = []
        for booking in self.rows:
            lines.append(reports.booking_line(booking, show_campus=True))
        if len(lines) == 0:
            lines = ["(no bookings to show)"]
        fill_listbox(self.listbox, lines)

    def cancel(self):
        index = get_selected_index(self.listbox)
        if index is None or index >= len(self.rows):
            messagebox.showwarning("Select a booking", "Please select a booking first.")
            return
        booking = self.rows[index]
        if not messagebox.askyesno("Cancel booking",
                                   "Cancel booking #" + str(booking["booking_id"]) + " for " +
                                   booking["resource_name"] + "?"):
            return
        ok, message = safe_call(booking_manager.cancel_booking, self.app.user,
                                booking["booking_id"])
        if ok:
            messagebox.showinfo("Booking cancelled", message)
        else:
            messagebox.showerror("Could not cancel", message)
        self.refresh()


# ---------------------------------------------------------------
# Add, update and remove resources (administrators and operators)
# ---------------------------------------------------------------
class ManageResourcesPage:
    def __init__(self, parent, app):
        self.app = app
        self.rows = []

        self.frame = tk.Frame(parent, padx=10, pady=10)
        self.frame.pack(fill="both", expand=True)
        tk.Label(self.frame, text="Manage Resources - " + app.campus,
                 font=FONT_HEADING).pack(anchor="w")

        tk.Label(self.frame, text=reports.resource_header(), font=FONT_LIST,
                 anchor="w").pack(fill="x", pady=(8, 0))
        box, self.listbox = make_listbox(self.frame, 9)
        box.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.fill_form)

        form = tk.Frame(self.frame, pady=8)
        form.pack(fill="x")
        tk.Label(form, text="Resource ID").grid(row=0, column=0, sticky="w", padx=5)
        tk.Label(form, text="Name").grid(row=0, column=1, sticky="w", padx=5)
        tk.Label(form, text="Type").grid(row=0, column=2, sticky="w", padx=5)
        tk.Label(form, text="Status").grid(row=0, column=3, sticky="w", padx=5)

        self.id_entry = tk.Entry(form, width=14)
        self.name_entry = tk.Entry(form, width=22)
        self.type_var = tk.StringVar(value=campus.RESOURCE_TYPES[0])
        self.status_var = tk.StringVar(value=campus.RESOURCE_STATUSES[0])
        type_menu = tk.OptionMenu(form, self.type_var, *campus.RESOURCE_TYPES)
        type_menu.configure(width=20)
        status_menu = tk.OptionMenu(form, self.status_var, *campus.RESOURCE_STATUSES)
        status_menu.configure(width=12)

        self.id_entry.grid(row=1, column=0, padx=5)
        self.name_entry.grid(row=1, column=1, padx=5)
        type_menu.grid(row=1, column=2, padx=5)
        status_menu.grid(row=1, column=3, padx=5)

        buttons = tk.Frame(self.frame)
        buttons.pack(pady=5)
        tk.Button(buttons, text="Add Resource", width=16,
                  command=self.add).pack(side="left", padx=4)
        tk.Button(buttons, text="Update Resource", width=16,
                  command=self.update).pack(side="left", padx=4)
        tk.Button(buttons, text="Remove Selected", width=16,
                  command=self.remove).pack(side="left", padx=4)
        tk.Button(buttons, text="Clear Form", width=12,
                  command=self.clear_form).pack(side="left", padx=4)
        tk.Label(self.frame, text="Tip: click a resource in the list to edit it. "
                 "Set the status to Unavailable to stop bookings.",
                 font=("Helvetica", 9), fg="gray").pack()
        self.refresh()

    def refresh(self):
        # Remember which resource was selected so it stays selected afterwards
        previous = get_selected_index(self.listbox)
        previous_id = ""
        if previous is not None and previous < len(self.rows):
            previous_id = self.rows[previous]["resource_id"]

        try:
            self.rows = database.get_resources(self.app.campus)
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error))
            return
        lines = []
        for resource in self.rows:
            lines.append(reports.resource_line(resource))
        fill_listbox(self.listbox, lines)

        for index in range(len(self.rows)):
            if self.rows[index]["resource_id"] == previous_id:
                self.listbox.selection_set(index)

    def fill_form(self, event):
        index = get_selected_index(self.listbox)
        if index is None or index >= len(self.rows):
            return
        resource = self.rows[index]
        self.id_entry.delete(0, "end")
        self.id_entry.insert(0, resource["resource_id"])
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, resource["name"])
        self.type_var.set(resource["resource_type"])
        self.status_var.set(resource["status"])

    def clear_form(self):
        self.id_entry.delete(0, "end")
        self.name_entry.delete(0, "end")
        self.type_var.set(campus.RESOURCE_TYPES[0])
        self.status_var.set(campus.RESOURCE_STATUSES[0])

    def add(self):
        ok, message = safe_call(booking_manager.add_resource, self.app.user,
                                self.app.campus, self.id_entry.get(),
                                self.name_entry.get(), self.type_var.get())
        self.show_result(ok, message, "Resource added", "Could not add resource")
        if ok:
            self.clear_form()

    def update(self):
        ok, message = safe_call(booking_manager.update_resource, self.app.user,
                                self.app.campus, self.id_entry.get(),
                                self.name_entry.get(), self.type_var.get(),
                                self.status_var.get())
        self.show_result(ok, message, "Resource updated", "Could not update resource")

    def remove(self):
        index = get_selected_index(self.listbox)
        if index is None or index >= len(self.rows):
            messagebox.showwarning("Select a resource",
                                   "Please select a resource in the list first.")
            return
        resource = self.rows[index]
        future = booking_manager.count_future_bookings(resource["resource_id"])
        question = ("Remove " + resource["resource_id"] + " (" + resource["name"] + ")?\n" +
                    str(future) + " future booking(s) will be cancelled.")
        if not messagebox.askyesno("Remove resource", question):
            return
        ok, message = safe_call(booking_manager.remove_resource, self.app.user,
                                self.app.campus, resource["resource_id"])
        self.show_result(ok, message, "Resource removed", "Could not remove resource")
        if ok:
            self.clear_form()

    def show_result(self, ok, message, good_title, bad_title):
        if ok:
            messagebox.showinfo(good_title, message)
        else:
            messagebox.showerror(bad_title, message)
        self.refresh()
