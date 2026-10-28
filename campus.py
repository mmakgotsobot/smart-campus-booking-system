"""
campus.py
---------
Campus classes and the campus-specific booking rules.

Each campus has its own BookingRule object. The rules are kept here,
separate from the rest of the system, so a new campus or a new rule can
be added with very small changes (Section 5.2 of the case study).

Concepts used from the study guide: classes, encapsulation (private
attributes), inheritance, polymorphism, dictionaries, tuples and lists.
"""

from datetime import timedelta

# The kinds of resources that can be registered at a campus.
RESOURCE_TYPES = ["Computer Lab", "Multimedia Projector",
                  "Seminar Room", "Presentation Equipment"]

# A resource can only be booked when its status is "Available".
RESOURCE_STATUSES = ["Available", "Unavailable"]


class BookingRule:
    """Base class: the booking rules that every campus shares.

    A campus can inherit from this class and override check_booking()
    to add its own extra rules (polymorphism).
    """

    def __init__(self, policy_name, max_minutes, open_minutes,
                 close_minutes, max_days_ahead, max_per_day):
        # Attributes start with two underscores, so they are hidden
        # (encapsulation). Other code uses the get methods below.
        self.__policy_name = policy_name
        self.__max_minutes = max_minutes        # longest single booking
        self.__open_minutes = open_minutes      # earliest start (minutes after midnight)
        self.__close_minutes = close_minutes    # latest finish (minutes after midnight)
        self.__max_days_ahead = max_days_ahead  # how far ahead a booking may be made
        self.__max_per_day = max_per_day        # bookings per lecturer per day

    # ---- get methods ----
    def get_policy_name(self):
        return self.__policy_name

    def get_max_minutes(self):
        return self.__max_minutes

    def get_open_minutes(self):
        return self.__open_minutes

    def get_close_minutes(self):
        return self.__close_minutes

    def get_max_days_ahead(self):
        return self.__max_days_ahead

    def get_max_per_day(self):
        return self.__max_per_day

    def extra_rule_text(self):
        """Text for any extra rule. Child classes override this."""
        return ""

    def describe(self):
        """One line that tells the user which policy is in effect."""
        open_h, open_m = divmod(self.__open_minutes, 60)
        close_h, close_m = divmod(self.__close_minutes, 60)
        text = (self.__policy_name + ": max " + str(self.__max_minutes) +
                " min per booking, hours " +
                f"{open_h:02d}:{open_m:02d}-{close_h:02d}:{close_m:02d}" +
                ", max " + str(self.__max_per_day) + " booking(s) per day" +
                ", up to " + str(self.__max_days_ahead) + " days ahead")
        extra = self.extra_rule_text()
        if extra != "":
            text = text + ". " + extra
        return text

    def check_booking(self, resource_type, start_dt, duration, bookings_that_day, now):
        """Check a booking against the rules.

        start_dt         - datetime when the booking starts
        duration         - length in minutes
        bookings_that_day - how many active bookings this lecturer already
                           has on this campus on that day
        now              - the current datetime
        Returns a tuple (ok, message).
        """
        start_minutes = start_dt.hour * 60 + start_dt.minute
        end_minutes = start_minutes + duration

        if duration > self.__max_minutes:
            return (False, "This campus allows a maximum of " +
                    str(self.__max_minutes) + " minutes per booking.")

        if start_minutes < self.__open_minutes or end_minutes > self.__close_minutes:
            return (False, "Bookings must be within the campus booking hours (" +
                    self.__hours_text() + ").")

        if start_dt.date() > (now + timedelta(days=self.__max_days_ahead)).date():
            return (False, "Bookings can only be made up to " +
                    str(self.__max_days_ahead) + " days in advance.")

        if bookings_that_day >= self.__max_per_day:
            return (False, "You already have the maximum of " +
                    str(self.__max_per_day) + " booking(s) for that day on this campus.")

        return (True, "")

    def __hours_text(self):
        open_h, open_m = divmod(self.__open_minutes, 60)
        close_h, close_m = divmod(self.__close_minutes, 60)
        return f"{open_h:02d}:{open_m:02d}-{close_h:02d}:{close_m:02d}"


class JohannesburgRule(BookingRule):
    """Johannesburg: standard working hours, no extra rule."""

    def __init__(self):
        super().__init__("Johannesburg Policy", 120, 8 * 60, 18 * 60, 30, 3)


class PretoriaRule(BookingRule):
    """Pretoria: long opening hours, but projectors are shared equipment."""

    def __init__(self):
        super().__init__("Pretoria Policy", 180, 7 * 60, 20 * 60, 60, 4)

    def extra_rule_text(self):
        return "Multimedia projectors may be booked for 60 minutes at most."

    def check_booking(self, resource_type, start_dt, duration, bookings_that_day, now):
        # First run the shared rules, then the Pretoria extra rule.
        ok, message = super().check_booking(resource_type, start_dt, duration,
                                            bookings_that_day, now)
        if not ok:
            return (ok, message)
        if resource_type == "Multimedia Projector" and duration > 60:
            return (False, "Pretoria allows projectors to be booked for 60 minutes at most.")
        return (True, "")


class DurbanRule(BookingRule):
    """Durban: shorter days and priority access to seminar rooms."""

    def __init__(self):
        super().__init__("Durban Policy", 90, 9 * 60, 17 * 60, 14, 2)

    def extra_rule_text(self):
        return "Seminar rooms (priority access) must be booked at least 1 day ahead."

    def check_booking(self, resource_type, start_dt, duration, bookings_that_day, now):
        ok, message = super().check_booking(resource_type, start_dt, duration,
                                            bookings_that_day, now)
        if not ok:
            return (ok, message)
        if resource_type == "Seminar Room" and start_dt.date() <= now.date():
            return (False, "Durban seminar rooms must be booked at least 1 day in advance.")
        return (True, "")


class Campus:
    """A campus has a name, a location and its own booking rule object."""

    def __init__(self, name, location, rule):
        self.__name = name
        self.__location = location
        self.__rule = rule

    def get_name(self):
        return self.__name

    def get_location(self):
        return self.__location

    def get_rule(self):
        return self.__rule


# All campuses are kept in a dictionary: campus name -> Campus object.
# TO ADD A NEW CAMPUS: write a rule class above (or reuse BookingRule)
# and add one line here. Nothing else needs to change.
campuses = {
    "Johannesburg": Campus("Johannesburg", "Gauteng", JohannesburgRule()),
    "Pretoria": Campus("Pretoria", "Gauteng", PretoriaRule()),
    "Durban": Campus("Durban", "KwaZulu-Natal", DurbanRule()),
}


def get_campus(name):
    """Return the Campus object for a name, or None if it does not exist."""
    return campuses.get(name)


def get_campus_names():
    """Return the campus names as a sorted list."""
    return sorted(campuses.keys())
