"""
users.py
--------
User classes for the three roles (Lecturer, Campus Administrator and
System Operator).

Concepts used from the study guide: classes, inheritance,
encapsulation (private attributes), polymorphism and sets.
"""


class User:
    """Base class for every user of the system."""

    def __init__(self, username, full_name, role, campus=None):
        # Private attributes (encapsulation)
        self.__username = username
        self.__full_name = full_name
        self.__role = role
        self.__campus = campus      # only used by campus administrators

    def get_username(self):
        return self.__username

    def get_full_name(self):
        return self.__full_name

    def get_role(self):
        return self.__role

    def get_campus(self):
        return self.__campus

    def get_permissions(self):
        """A set of permission names. Each child class overrides this."""
        return set()

    def has_permission(self, permission):
        return permission in self.get_permissions()

    def get_campus_choices(self, all_campus_names):
        """Campuses this user may select after logging in."""
        return list(all_campus_names)

    def __str__(self):
        return self.__full_name + " (" + self.__role + ")"


class Lecturer(User):
    """Books resources for teaching or presentations."""

    def __init__(self, username, full_name):
        super().__init__(username, full_name, "Lecturer")

    def get_permissions(self):
        return {"book_resource", "view_own_bookings", "cancel_booking"}


class CampusAdministrator(User):
    """Manages the resources at one specific campus."""

    def __init__(self, username, full_name, campus):
        super().__init__(username, full_name, "Campus Administrator", campus)

    def get_permissions(self):
        return {"manage_resources", "view_campus_bookings",
                "view_availability", "view_campus_report"}

    def get_campus_choices(self, all_campus_names):
        # An administrator can only work with their own campus.
        return [self.get_campus()]


class SystemOperator(User):
    """Institutional management with system-wide access."""

    def __init__(self, username, full_name):
        super().__init__(username, full_name, "System Operator")

    def get_permissions(self):
        return {"manage_resources", "view_campus_bookings",
                "view_availability", "view_campus_report",
                "view_all_bookings", "view_all_resources",
                "compare_campuses"}


def create_user_object(row):
    """Turn a database row (a dictionary) into the correct User object."""
    role = row["role"]
    if role == "Lecturer":
        return Lecturer(row["username"], row["full_name"])
    elif role == "Campus Administrator":
        return CampusAdministrator(row["username"], row["full_name"], row["campus"])
    elif role == "System Operator":
        return SystemOperator(row["username"], row["full_name"])
    return None
