"""
database.py
-----------
All SQLite code lives in this file. The rest of the program calls these
functions and never writes SQL itself.

Tables:  campuses, users, resources, bookings
Every value is passed to SQL with ? placeholders (see section 5.6 of the
study guide) so user input can never break the SQL statement.
"""

import os
import sqlite3
import hashlib
from datetime import datetime, timedelta

import campus

# The database file is saved next to this program so data survives restarts.
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campus_booking.db")


def get_connection():
    """Open a connection to the database. Rows come back as dictionaries."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password):
    """Passwords are never stored as plain text."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def run_query(sql, values=()):
    """Run a SELECT and return a list of dictionaries."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
        rows = [dict(row) for row in cur.fetchall()]
        return rows
    finally:
        conn.close()


def run_change(sql, values=()):
    """Run an INSERT, UPDATE or DELETE. Returns the new row id."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


# ---------------------------------------------------------------
# Creating the tables and the starting data
# ---------------------------------------------------------------
def create_tables():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS campuses (
                           name TEXT PRIMARY KEY NOT NULL,
                           location TEXT NOT NULL)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
                           username TEXT PRIMARY KEY NOT NULL,
                           full_name TEXT NOT NULL,
                           password_hash TEXT NOT NULL,
                           role TEXT NOT NULL,
                           campus TEXT,
                           FOREIGN KEY (campus) REFERENCES campuses (name))''')
        # resource_id is the unique identifier that prevents duplicates.
        cur.execute('''CREATE TABLE IF NOT EXISTS resources (
                           resource_id TEXT PRIMARY KEY NOT NULL,
                           name TEXT NOT NULL,
                           resource_type TEXT NOT NULL,
                           campus TEXT NOT NULL,
                           status TEXT NOT NULL DEFAULT 'Available',
                           FOREIGN KEY (campus) REFERENCES campuses (name))''')
        # The resource name is copied into each booking so the booking
        # history is still readable if a resource is removed later.
        cur.execute('''CREATE TABLE IF NOT EXISTS bookings (
                           booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                           resource_id TEXT NOT NULL,
                           resource_name TEXT NOT NULL,
                           resource_type TEXT NOT NULL,
                           username TEXT NOT NULL,
                           campus TEXT NOT NULL,
                           booking_date TEXT NOT NULL,
                           start_time TEXT NOT NULL,
                           duration_minutes INTEGER NOT NULL,
                           status TEXT NOT NULL DEFAULT 'Active',
                           created_at TEXT NOT NULL,
                           FOREIGN KEY (username) REFERENCES users (username),
                           FOREIGN KEY (campus) REFERENCES campuses (name))''')
        conn.commit()
    finally:
        conn.close()


def setup_database():
    """Create the tables, then add the starting data the first time only."""
    create_tables()
    sync_campuses()
    if len(run_query("SELECT username FROM users")) == 0:
        add_starting_data()


def sync_campuses():
    """Make sure every campus in the dictionary in campus.py is in the database.
    This is what lets a new campus be added with one line of code."""
    for name in campus.get_campus_names():
        run_change("INSERT OR IGNORE INTO campuses (name, location) VALUES (?, ?)",
                   (name, campus.get_campus(name).get_location()))


def add_starting_data():
    """Resources, user accounts and a few example bookings."""
    # Starting resources: (id, name, type, campus)
    resources = [
        ("JHB-LAB-01", "Computer Lab A", "Computer Lab", "Johannesburg"),
        ("JHB-LAB-02", "Computer Lab B", "Computer Lab", "Johannesburg"),
        ("JHB-PRJ-01", "Projector 1", "Multimedia Projector", "Johannesburg"),
        ("JHB-SEM-01", "Seminar Room 1", "Seminar Room", "Johannesburg"),
        ("PTA-LAB-01", "Computer Lab A", "Computer Lab", "Pretoria"),
        ("PTA-PRJ-01", "Projector 1", "Multimedia Projector", "Pretoria"),
        ("PTA-SEM-01", "Seminar Room 1", "Seminar Room", "Pretoria"),
        ("PTA-PRS-01", "Presentation Kit 1", "Presentation Equipment", "Pretoria"),
        ("DBN-LAB-01", "Computer Lab A", "Computer Lab", "Durban"),
        ("DBN-PRJ-01", "Projector 1", "Multimedia Projector", "Durban"),
        ("DBN-SEM-01", "Seminar Room 1", "Seminar Room", "Durban"),
    ]
    for r in resources:
        run_change('''INSERT INTO resources (resource_id, name, resource_type, campus)
                      VALUES (?, ?, ?, ?)''', r)

    # Starting user accounts: (username, full name, password, role, campus)
    users = [
        ("operator", "Olivia Operator", "operator123", "System Operator", None),
        ("admin_jhb", "Jabu Admin", "admin123", "Campus Administrator", "Johannesburg"),
        ("admin_pta", "Pieter Admin", "admin123", "Campus Administrator", "Pretoria"),
        ("admin_dbn", "Dumisani Admin", "admin123", "Campus Administrator", "Durban"),
        ("lecturer1", "Lerato Lecturer", "lecturer123", "Lecturer", None),
        ("lecturer2", "Liam Lecturer", "lecturer123", "Lecturer", None),
    ]
    for u in users:
        run_change('''INSERT INTO users (username, full_name, password_hash, role, campus)
                      VALUES (?, ?, ?, ?, ?)''',
                   (u[0], u[1], hash_password(u[2]), u[3], u[4]))

    add_example_bookings()


def add_example_bookings():
    """A few example bookings so the reports have something to show.

    Each tuple is: (days from today, resource id, lecturer, start, minutes).
    All of them follow the rules of their campus.
    """
    examples = [
        (-9, "JHB-LAB-01", "lecturer1", "09:00", 90),
        (-7, "JHB-PRJ-01", "lecturer2", "10:00", 60),
        (-5, "JHB-LAB-01", "lecturer2", "13:00", 120),
        (-3, "JHB-SEM-01", "lecturer1", "14:00", 60),
        (-2, "JHB-LAB-01", "lecturer1", "08:00", 60),
        (2, "JHB-LAB-02", "lecturer1", "11:00", 90),
        (-8, "PTA-LAB-01", "lecturer1", "07:00", 180),
        (-6, "PTA-PRJ-01", "lecturer2", "09:00", 60),
        (-4, "PTA-LAB-01", "lecturer2", "12:00", 120),
        (-1, "PTA-SEM-01", "lecturer1", "15:00", 90),
        (3, "PTA-PRS-01", "lecturer2", "10:00", 60),
        (-10, "DBN-LAB-01", "lecturer2", "09:00", 60),
        (-6, "DBN-PRJ-01", "lecturer1", "11:00", 60),
        (-3, "DBN-LAB-01", "lecturer1", "13:00", 90),
        (4, "DBN-SEM-01", "lecturer2", "14:00", 60),
    ]
    today = datetime.now().date()
    for days, resource_id, username, start, minutes in examples:
        resource = get_resource(resource_id)
        date_text = (today + timedelta(days=days)).strftime("%Y-%m-%d")
        insert_booking(resource, username, date_text, start, minutes)


# ---------------------------------------------------------------
# Users
# ---------------------------------------------------------------
def get_user(username):
    rows = run_query("SELECT * FROM users WHERE username = ?", (username,))
    if len(rows) == 0:
        return None
    return rows[0]


def insert_user(username, full_name, password, role, campus_name=None):
    """Raises sqlite3.IntegrityError if the username already exists."""
    run_change('''INSERT INTO users (username, full_name, password_hash, role, campus)
                  VALUES (?, ?, ?, ?, ?)''',
               (username, full_name, hash_password(password), role, campus_name))


# ---------------------------------------------------------------
# Resources
# ---------------------------------------------------------------
def get_resources(campus_name=None):
    """Resources of one campus, or of every campus when no name is given."""
    if campus_name is None:
        return run_query("SELECT * FROM resources ORDER BY campus, resource_id")
    return run_query("SELECT * FROM resources WHERE campus = ? ORDER BY resource_id",
                     (campus_name,))


def get_resource(resource_id):
    rows = run_query("SELECT * FROM resources WHERE resource_id = ?", (resource_id,))
    if len(rows) == 0:
        return None
    return rows[0]


def insert_resource(resource_id, name, resource_type, campus_name):
    """Raises sqlite3.IntegrityError if the resource id already exists."""
    run_change('''INSERT INTO resources (resource_id, name, resource_type, campus)
                  VALUES (?, ?, ?, ?)''',
               (resource_id, name, resource_type, campus_name))


def update_resource(resource_id, name, resource_type, status):
    run_change('''UPDATE resources SET name = ?, resource_type = ?, status = ?
                  WHERE resource_id = ?''',
               (name, resource_type, status, resource_id))


def delete_resource(resource_id):
    run_change("DELETE FROM resources WHERE resource_id = ?", (resource_id,))


# ---------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------
def insert_booking(resource, username, date_text, start_text, minutes):
    """Save a booking. 'resource' is a resource dictionary."""
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return run_change('''INSERT INTO bookings
                         (resource_id, resource_name, resource_type, username, campus,
                          booking_date, start_time, duration_minutes, status, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?)''',
                      (resource["resource_id"], resource["name"], resource["resource_type"],
                       username, resource["campus"], date_text, start_text, minutes, created))


def get_booking(booking_id):
    rows = run_query("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
    if len(rows) == 0:
        return None
    return rows[0]


def get_bookings_for_resource_on_date(resource_id, date_text):
    """Active bookings only (cancelled ones do not block a time slot)."""
    return run_query('''SELECT * FROM bookings WHERE resource_id = ?
                        AND booking_date = ? AND status = 'Active' ''',
                     (resource_id, date_text))


def get_active_resource_bookings(resource_id):
    return run_query('''SELECT * FROM bookings WHERE resource_id = ?
                        AND status = 'Active' ''', (resource_id,))


def count_user_bookings_on_date(username, campus_name, date_text):
    rows = run_query('''SELECT COUNT(*) AS total FROM bookings
                        WHERE username = ? AND campus = ? AND booking_date = ?
                        AND status = 'Active' ''',
                     (username, campus_name, date_text))
    return rows[0]["total"]


def get_user_bookings(username):
    return run_query('''SELECT * FROM bookings WHERE username = ?
                        ORDER BY booking_date DESC, start_time DESC''', (username,))


def get_campus_bookings(campus_name):
    return run_query('''SELECT bookings.*, users.full_name FROM bookings
                        JOIN users ON users.username = bookings.username
                        WHERE bookings.campus = ?
                        ORDER BY booking_date DESC, start_time DESC''', (campus_name,))


def get_all_bookings():
    return run_query('''SELECT bookings.*, users.full_name FROM bookings
                        JOIN users ON users.username = bookings.username
                        ORDER BY bookings.campus, booking_date DESC, start_time DESC''')


def cancel_booking(booking_id):
    run_change("UPDATE bookings SET status = 'Cancelled' WHERE booking_id = ?",
               (booking_id,))
