"""
booking_manager.py
------------------
The main program logic: registering, logging in, managing resources and
making / cancelling bookings. It sits between the GUI and the database.

Almost every function returns a tuple (ok, message):
    ok      - True when it worked, False when it did not
    message - text the GUI can show to the user
"""

import sqlite3
from datetime import datetime, timedelta

import database
import campus
from users import create_user_object


# ---------------------------------------------------------------
# Small helper functions for dates and times
# ---------------------------------------------------------------
def parse_date(date_text):
    """Turn 'YYYY-MM-DD' into a date. Returns None when it is not valid."""
    try:
        return datetime.strptime(date_text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_time(time_text):
    """Turn 'HH:MM' into minutes after midnight. Returns None when not valid."""
    try:
        t = datetime.strptime(time_text.strip(), "%H:%M")
        return t.hour * 60 + t.minute
    except ValueError:
        return None


def minutes_to_text(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_duration(duration_text):
    """Duration in minutes as a whole number. Returns None when not valid."""
    try:
        value = int(duration_text.strip())
    except ValueError:
        return None
    if value < 15 or value > 600:
        return None
    return value


def booking_start(booking):
    """The start of a booking as a datetime."""
    return datetime.strptime(booking["booking_date"] + " " + booking["start_time"],
                             "%Y-%m-%d %H:%M")


def booking_end(booking):
    """The end of a booking as a datetime."""
    return booking_start(booking) + timedelta(minutes=booking["duration_minutes"])


def booking_state(booking, now=None):
    """Cancelled, Upcoming, In progress or Completed."""
    if now is None:
        now = datetime.now()
    if booking["status"] == "Cancelled":
        return "Cancelled"
    if now < booking_start(booking):
        return "Upcoming"
    if now < booking_end(booking):
        return "In progress"
    return "Completed"


# ---------------------------------------------------------------
# Registration and login
# ---------------------------------------------------------------
def register_lecturer(username, full_name, password, confirm):
    """Lecturers register themselves. Other roles are created by management."""
    username = username.strip()
    full_name = full_name.strip()

    if username == "" or full_name == "" or password == "" or confirm == "":
        return (False, "Please fill in all the fields.")
    if len(username) < 3 or not username.replace("_", "").isalnum():
        return (False, "Username must be at least 3 letters/numbers (underscore allowed).")
    if len(password) < 6:
        return (False, "Password must be at least 6 characters long.")
    if password != confirm:
        return (False, "The two passwords do not match.")

    try:
        database.insert_user(username, full_name, password, "Lecturer")
    except sqlite3.IntegrityError:
        return (False, "That username is already taken. Please choose another.")
    return (True, "Account created. You can now log in.")


def login(username, password):
    """Returns (user object, message). The user object is None if login fails."""
    username = username.strip()
    if username == "" or password == "":
        return (None, "Please enter your username and password.")

    row = database.get_user(username)
    if row is None or row["password_hash"] != database.hash_password(password):
        return (None, "Incorrect username or password.")
    return (create_user_object(row), "Login successful.")


# ---------------------------------------------------------------
# Managing resources (campus administrators and system operators)
# ---------------------------------------------------------------
def can_manage_campus(user, campus_name):
    """Administrators may only manage their own campus."""
    if not user.has_permission("manage_resources"):
        return False
    if user.get_role() == "Campus Administrator":
        return user.get_campus() == campus_name
    return True


def clean_resource_id(resource_id):
    return resource_id.strip().upper()


def add_resource(user, campus_name, resource_id, name, resource_type):
    if not can_manage_campus(user, campus_name):
        return (False, "You do not have permission to manage resources on this campus.")

    resource_id = clean_resource_id(resource_id)
    name = name.strip()
    if resource_id == "" or name == "":
        return (False, "Please enter both a resource ID and a name.")
    if len(resource_id) > 20 or not resource_id.replace("-", "").isalnum():
        return (False, "Resource ID may only contain letters, numbers and dashes (max 20).")
    if resource_type not in campus.RESOURCE_TYPES:
        return (False, "Please choose a valid resource type.")
    if campus.get_campus(campus_name) is None:
        return (False, "That campus does not exist.")

    # Duplicate check (the database also protects us with the primary key).
    if database.get_resource(resource_id) is not None:
        return (False, "A resource with the ID " + resource_id + " already exists.")
    try:
        database.insert_resource(resource_id, name, resource_type, campus_name)
    except sqlite3.IntegrityError:
        return (False, "A resource with the ID " + resource_id + " already exists.")
    return (True, "Resource " + resource_id + " was added to " + campus_name + ".")


def update_resource(user, campus_name, resource_id, name, resource_type, status):
    if not can_manage_campus(user, campus_name):
        return (False, "You do not have permission to manage resources on this campus.")

    resource_id = clean_resource_id(resource_id)
    name = name.strip()
    if resource_id == "":
        return (False, "Please select a resource from the list or enter its ID.")
    resource = database.get_resource(resource_id)
    if resource is None or resource["campus"] != campus_name:
        return (False, "No resource with ID " + resource_id + " exists on this campus.")
    if name == "":
        return (False, "The resource name cannot be empty.")
    if resource_type not in campus.RESOURCE_TYPES:
        return (False, "Please choose a valid resource type.")
    if status not in campus.RESOURCE_STATUSES:
        return (False, "Please choose a valid status.")

    database.update_resource(resource_id, name, resource_type, status)
    return (True, "Resource " + resource_id + " was updated.")


def remove_resource(user, campus_name, resource_id):
    """Remove a resource. Its future bookings are cancelled first."""
    if not can_manage_campus(user, campus_name):
        return (False, "You do not have permission to manage resources on this campus.")

    resource_id = clean_resource_id(resource_id)
    if resource_id == "":
        return (False, "Please select a resource from the list first.")
    resource = database.get_resource(resource_id)
    if resource is None or resource["campus"] != campus_name:
        return (False, "No resource with ID " + resource_id + " exists on this campus.")

    cancelled = 0
    now = datetime.now()
    for booking in database.get_active_resource_bookings(resource_id):
        if booking_end(booking) > now:
            database.cancel_booking(booking["booking_id"])
            cancelled += 1

    database.delete_resource(resource_id)
    return (True, "Resource " + resource_id + " was removed. " +
            str(cancelled) + " future booking(s) were cancelled.")


def count_future_bookings(resource_id):
    """Used by the GUI to warn the administrator before removing a resource."""
    total = 0
    now = datetime.now()
    for booking in database.get_active_resource_bookings(resource_id):
        if booking_end(booking) > now:
            total += 1
    return total


# ---------------------------------------------------------------
# Availability
# ---------------------------------------------------------------
def overlaps(resource_id, date_text, start_minutes, duration):
    """True when the time slot clashes with an active booking."""
    end_minutes = start_minutes + duration
    for booking in database.get_bookings_for_resource_on_date(resource_id, date_text):
        old_start = parse_time(booking["start_time"])
        old_end = old_start + booking["duration_minutes"]
        # Two time slots overlap when each one starts before the other ends.
        if start_minutes < old_end and old_start < end_minutes:
            return True
    return False


def get_availability(campus_name, date_text="", start_text="", duration_text=""):
    """List every resource on a campus with its availability.

    Returns a list of tuples (resource dictionary, state text).
    If the date/time/duration are not valid yet, only the resource status
    (Available / Unavailable) is shown.
    """
    the_date = parse_date(date_text)
    start = parse_time(start_text)
    duration = parse_duration(duration_text)
    slot_is_valid = the_date is not None and start is not None and duration is not None

    results = []
    for resource in database.get_resources(campus_name):
        if resource["status"] != "Available":
            state = "Unavailable"
        elif slot_is_valid and overlaps(resource["resource_id"],
                                        the_date.strftime("%Y-%m-%d"), start, duration):
            state = "Booked"
        else:
            state = "Available"
        results.append((resource, state))
    return results


# ---------------------------------------------------------------
# Booking and cancelling
# ---------------------------------------------------------------
def make_booking(user, campus_name, resource_id, date_text, start_text, duration_text):
    """Create a booking after checking every rule."""
    if not user.has_permission("book_resource"):
        return (False, "Only lecturers can book resources.")

    # 1. Check the input
    the_date = parse_date(date_text)
    if the_date is None:
        return (False, "Please enter the date as YYYY-MM-DD, for example 2026-11-05.")
    start = parse_time(start_text)
    if start is None:
        return (False, "Please enter the start time as HH:MM, for example 09:30.")
    duration = parse_duration(duration_text)
    if duration is None:
        return (False, "Duration must be a whole number of minutes (15 to 600).")
    if resource_id == "":
        return (False, "Please select a resource from the list first.")

    # 2. Check the resource
    resource = database.get_resource(resource_id)
    if resource is None or resource["campus"] != campus_name:
        return (False, "That resource does not exist on the selected campus.")
    if resource["status"] != "Available":
        return (False, "This resource is currently unavailable and cannot be booked.")

    # 3. The booking must be in the future
    start_dt = datetime(the_date.year, the_date.month, the_date.day,
                        start // 60, start % 60)
    now = datetime.now()
    if start_dt <= now:
        return (False, "You cannot make a booking in the past.")

    # 4. Apply the booking policy of the selected campus
    rule = campus.get_campus(campus_name).get_rule()
    date_text = the_date.strftime("%Y-%m-%d")
    already = database.count_user_bookings_on_date(user.get_username(), campus_name, date_text)
    ok, message = rule.check_booking(resource["resource_type"], start_dt,
                                     duration, already, now)
    if not ok:
        return (False, message)

    # 5. No overlapping bookings for the same resource
    if overlaps(resource_id, date_text, start, duration):
        return (False, "This resource is already booked for part of that time. "
                       "Please choose a different time.")

    # 6. Save the booking
    database.insert_booking(resource, user.get_username(), date_text,
                            minutes_to_text(start), duration)
    return (True, resource["name"] + " booked on " + date_text + " at " +
            minutes_to_text(start) + " for " + str(duration) + " minutes.")


def get_my_bookings(user, view):
    """view is 'Active', 'History' or 'All'. Returns a list of dictionaries."""
    now = datetime.now()
    result = []
    for booking in database.get_user_bookings(user.get_username()):
        state = booking_state(booking, now)
        is_active = state in ("Upcoming", "In progress")
        if view == "All":
            result.append(booking)
        elif view == "Active" and is_active:
            result.append(booking)
        elif view == "History" and not is_active:
            result.append(booking)
    return result


def cancel_booking(user, booking_id):
    """Lecturers can cancel their own bookings that have not started yet."""
    if not user.has_permission("cancel_booking"):
        return (False, "You do not have permission to cancel bookings.")

    booking = database.get_booking(booking_id)
    if booking is None:
        return (False, "That booking could not be found.")
    if booking["username"] != user.get_username():
        return (False, "You can only cancel your own bookings.")
    if booking["status"] == "Cancelled":
        return (False, "This booking is already cancelled.")
    if booking_start(booking) <= datetime.now():
        return (False, "Only future bookings can be cancelled.")

    database.cancel_booking(booking_id)
    return (True, "Booking " + str(booking_id) + " was cancelled.")
