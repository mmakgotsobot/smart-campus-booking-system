"""
test_system.py
--------------
Automatic tests for the program logic (database, rules, bookings, reports).
Run with:   python test_system.py
The tests use a temporary database, so your real data is never touched.
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta

import database
import campus
import booking_manager as bm
import reports


def future_date(days):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


class SystemTests(unittest.TestCase):

    def setUp(self):
        # A fresh temporary database for every test
        database.DB_NAME = os.path.join(tempfile.mkdtemp(), "test.db")
        database.setup_database()
        self.lecturer1 = bm.login("lecturer1", "lecturer123")[0]
        self.lecturer2 = bm.login("lecturer2", "lecturer123")[0]
        self.admin_jhb = bm.login("admin_jhb", "admin123")[0]
        self.admin_pta = bm.login("admin_pta", "admin123")[0]
        self.operator = bm.login("operator", "operator123")[0]

    # ---------- registration and login ----------
    def test_register_and_login(self):
        ok, message = bm.register_lecturer("new_lect", "New Lecturer", "secret1", "secret1")
        self.assertTrue(ok, message)
        user, message = bm.login("new_lect", "secret1")
        self.assertEqual(user.get_role(), "Lecturer")

    def test_register_validation(self):
        self.assertFalse(bm.register_lecturer("", "A", "secret1", "secret1")[0])
        self.assertFalse(bm.register_lecturer("ab", "A", "secret1", "secret1")[0])
        self.assertFalse(bm.register_lecturer("abc", "A", "123", "123")[0])
        self.assertFalse(bm.register_lecturer("abc", "A", "secret1", "different")[0])
        self.assertFalse(bm.register_lecturer("lecturer1", "A", "secret1", "secret1")[0])

    def test_login_failures(self):
        self.assertIsNone(bm.login("lecturer1", "wrong")[0])
        self.assertIsNone(bm.login("nobody", "x")[0])
        self.assertIsNone(bm.login("", "")[0])

    def test_password_is_not_stored_as_plain_text(self):
        row = database.get_user("lecturer1")
        self.assertNotEqual(row["password_hash"], "lecturer123")

    def test_roles_and_permissions(self):
        self.assertTrue(self.lecturer1.has_permission("book_resource"))
        self.assertFalse(self.lecturer1.has_permission("manage_resources"))
        self.assertTrue(self.admin_jhb.has_permission("manage_resources"))
        self.assertFalse(self.admin_jhb.has_permission("book_resource"))
        self.assertTrue(self.operator.has_permission("compare_campuses"))
        self.assertEqual(self.admin_jhb.get_campus_choices(campus.get_campus_names()),
                         ["Johannesburg"])
        self.assertEqual(len(self.lecturer1.get_campus_choices(campus.get_campus_names())), 3)

    # ---------- booking rules per campus ----------
    def test_johannesburg_rules(self):
        d = future_date(5)
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-01", d, "09:00", "121")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-01", d, "07:00", "60")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-01", d, "17:30", "60")[0])
        self.assertTrue(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-01", d, "09:00", "120")[0])

    def test_pretoria_projector_rule(self):
        d = future_date(5)
        self.assertFalse(bm.make_booking(self.lecturer1, "Pretoria", "PTA-PRJ-01", d, "09:00", "90")[0])
        self.assertTrue(bm.make_booking(self.lecturer1, "Pretoria", "PTA-PRJ-01", d, "09:00", "60")[0])
        self.assertTrue(bm.make_booking(self.lecturer1, "Pretoria", "PTA-LAB-01", d, "10:00", "180")[0])

    def test_durban_rules(self):
        d = future_date(5)
        self.assertFalse(bm.make_booking(self.lecturer1, "Durban", "DBN-LAB-01", d, "09:00", "91")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Durban", "DBN-LAB-01", d, "08:00", "60")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Durban", "DBN-LAB-01", future_date(15), "09:00", "60")[0])
        # max 2 bookings per lecturer per day
        self.assertTrue(bm.make_booking(self.lecturer1, "Durban", "DBN-LAB-01", d, "09:00", "60")[0])
        self.assertTrue(bm.make_booking(self.lecturer1, "Durban", "DBN-PRJ-01", d, "10:00", "60")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Durban", "DBN-SEM-01", d, "11:00", "60")[0])

    def test_durban_seminar_room_needs_one_day_notice(self):
        rule = campus.get_campus("Durban").get_rule()
        now = datetime(2030, 3, 4, 8, 0)
        same_day = datetime(2030, 3, 4, 10, 0)
        next_day = datetime(2030, 3, 5, 10, 0)
        self.assertFalse(rule.check_booking("Seminar Room", same_day, 60, 0, now)[0])
        self.assertTrue(rule.check_booking("Seminar Room", next_day, 60, 0, now)[0])
        self.assertTrue(rule.check_booking("Computer Lab", same_day, 60, 0, now)[0])

    def test_policy_text_available_for_every_campus(self):
        for name in campus.get_campus_names():
            self.assertIn("min per booking", campus.get_campus(name).get_rule().describe())

    # ---------- bookings ----------
    def test_overlapping_bookings_are_prevented(self):
        d = future_date(6)
        self.assertTrue(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")[0])
        self.assertFalse(bm.make_booking(self.lecturer2, "Johannesburg", "JHB-LAB-02", d, "10:30", "30")[0])
        self.assertFalse(bm.make_booking(self.lecturer2, "Johannesburg", "JHB-LAB-02", d, "09:30", "60")[0])
        self.assertTrue(bm.make_booking(self.lecturer2, "Johannesburg", "JHB-LAB-02", d, "11:00", "60")[0])

    def test_booking_in_the_past_is_rejected(self):
        yesterday = future_date(-1)
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", yesterday, "10:00", "60")[0])

    def test_bad_input_is_rejected(self):
        d = future_date(5)
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", "05/11/2030", "10:00", "60")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "25:00", "60")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "10:00", "abc")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "10:00", "0")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "", d, "10:00", "60")[0])
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "NOPE-99", d, "10:00", "60")[0])

    def test_resource_must_belong_to_selected_campus(self):
        d = future_date(5)
        self.assertFalse(bm.make_booking(self.lecturer1, "Johannesburg", "PTA-LAB-01", d, "10:00", "60")[0])

    def test_unavailable_resource_cannot_be_booked(self):
        d = future_date(5)
        bm.update_resource(self.admin_jhb, "Johannesburg", "JHB-LAB-02", "Computer Lab B",
                           "Computer Lab", "Unavailable")
        ok, message = bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")
        self.assertFalse(ok)
        states = dict((r["resource_id"], s) for r, s in bm.get_availability("Johannesburg"))
        self.assertEqual(states["JHB-LAB-02"], "Unavailable")

    def test_availability_shows_booked_slot(self):
        d = future_date(6)
        bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")
        states = dict((r["resource_id"], s) for r, s in
                      bm.get_availability("Johannesburg", d, "10:15", "30"))
        self.assertEqual(states["JHB-LAB-02"], "Booked")
        self.assertEqual(states["JHB-LAB-01"], "Available")

    def test_only_lecturers_can_book(self):
        d = future_date(5)
        self.assertFalse(bm.make_booking(self.admin_jhb, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")[0])
        self.assertFalse(bm.make_booking(self.operator, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")[0])

    def test_booking_is_linked_to_lecturer_and_campus(self):
        d = future_date(6)
        bm.make_booking(self.lecturer1, "Pretoria", "PTA-LAB-01", d, "08:00", "60")
        mine = [b for b in bm.get_my_bookings(self.lecturer1, "All") if b["booking_date"] == d]
        self.assertEqual(len(mine), 1)
        self.assertEqual(mine[0]["username"], "lecturer1")
        self.assertEqual(mine[0]["campus"], "Pretoria")
        self.assertEqual(mine[0]["duration_minutes"], 60)
        self.assertEqual(mine[0]["start_time"], "08:00")

    # ---------- viewing and cancelling ----------
    def test_active_and_history_views(self):
        active = bm.get_my_bookings(self.lecturer1, "Active")
        history = bm.get_my_bookings(self.lecturer1, "History")
        everything = bm.get_my_bookings(self.lecturer1, "All")
        self.assertEqual(len(active) + len(history), len(everything))
        self.assertTrue(len(active) > 0 and len(history) > 0)
        for b in active:
            self.assertIn(bm.booking_state(b), ("Upcoming", "In progress"))

    def test_cancel_future_booking(self):
        d = future_date(7)
        bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")
        booking = [b for b in bm.get_my_bookings(self.lecturer1, "Active") if b["booking_date"] == d][0]
        ok, message = bm.cancel_booking(self.lecturer1, booking["booking_id"])
        self.assertTrue(ok, message)
        self.assertEqual(database.get_booking(booking["booking_id"])["status"], "Cancelled")
        # the slot is free again
        self.assertTrue(bm.make_booking(self.lecturer2, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")[0])
        # cancelling twice fails
        self.assertFalse(bm.cancel_booking(self.lecturer1, booking["booking_id"])[0])

    def test_cannot_cancel_past_or_other_users_booking(self):
        past = [b for b in bm.get_my_bookings(self.lecturer1, "History")
                if b["status"] == "Active"][0]
        self.assertFalse(bm.cancel_booking(self.lecturer1, past["booking_id"])[0])
        future = bm.get_my_bookings(self.lecturer1, "Active")[0]
        self.assertFalse(bm.cancel_booking(self.lecturer2, future["booking_id"])[0])
        self.assertFalse(bm.cancel_booking(self.lecturer1, 99999)[0])

    # ---------- resources ----------
    def test_add_resource_and_duplicates(self):
        ok, message = bm.add_resource(self.admin_jhb, "Johannesburg", "jhb-lab-09", "Lab Z", "Computer Lab")
        self.assertTrue(ok, message)
        self.assertIsNotNone(database.get_resource("JHB-LAB-09"))
        # same ID again (even in lower case) is rejected
        self.assertFalse(bm.add_resource(self.admin_jhb, "Johannesburg", "JHB-LAB-09", "Other", "Computer Lab")[0])
        # an ID used on another campus is rejected too (IDs are unique system-wide)
        self.assertFalse(bm.add_resource(self.operator, "Durban", "JHB-LAB-01", "Other", "Computer Lab")[0])

    def test_add_resource_validation(self):
        self.assertFalse(bm.add_resource(self.admin_jhb, "Johannesburg", "", "Name", "Computer Lab")[0])
        self.assertFalse(bm.add_resource(self.admin_jhb, "Johannesburg", "A B!", "Name", "Computer Lab")[0])
        self.assertFalse(bm.add_resource(self.admin_jhb, "Johannesburg", "X-1", "", "Computer Lab")[0])
        self.assertFalse(bm.add_resource(self.admin_jhb, "Johannesburg", "X-1", "Name", "Spaceship")[0])

    def test_resource_access_control(self):
        self.assertFalse(bm.add_resource(self.lecturer1, "Johannesburg", "X-1", "Name", "Computer Lab")[0])
        self.assertFalse(bm.add_resource(self.admin_pta, "Johannesburg", "X-1", "Name", "Computer Lab")[0])
        self.assertTrue(bm.add_resource(self.operator, "Johannesburg", "X-1", "Name", "Computer Lab")[0])
        self.assertFalse(bm.remove_resource(self.admin_pta, "Johannesburg", "X-1")[0])

    def test_update_resource(self):
        ok, message = bm.update_resource(self.admin_jhb, "Johannesburg", "JHB-PRJ-01",
                                         "Projector Deluxe", "Multimedia Projector", "Available")
        self.assertTrue(ok, message)
        self.assertEqual(database.get_resource("JHB-PRJ-01")["name"], "Projector Deluxe")
        self.assertFalse(bm.update_resource(self.admin_jhb, "Johannesburg", "NOPE", "x",
                                            "Computer Lab", "Available")[0])

    def test_remove_resource_cancels_future_bookings(self):
        d = future_date(8)
        bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")
        self.assertTrue(bm.count_future_bookings("JHB-LAB-02") >= 1)
        ok, message = bm.remove_resource(self.admin_jhb, "Johannesburg", "JHB-LAB-02")
        self.assertTrue(ok, message)
        self.assertIsNone(database.get_resource("JHB-LAB-02"))
        left = [b for b in database.get_active_resource_bookings("JHB-LAB-02")
                if bm.booking_end(b) > datetime.now()]
        self.assertEqual(left, [])

    # ---------- reports ----------
    def test_campus_report_numbers(self):
        stats = reports.campus_stats("Johannesburg")
        # 6 example bookings are added for Johannesburg (5 past + 1 future)
        self.assertEqual(stats["total"], 6)
        self.assertEqual(stats["cancelled"], 0)
        self.assertAlmostEqual(stats["average"], (90 + 60 + 120 + 60 + 60 + 90) / 6)
        self.assertEqual(stats["ranking"][0][0], "Computer Lab A (JHB-LAB-01)")
        lines = "\n".join(reports.campus_report("Johannesburg"))
        self.assertIn("Total number of bookings", lines)
        self.assertIn("Most frequently used resources", lines)
        self.assertIn("Average booking duration", lines)

    def test_cancelled_bookings_not_counted(self):
        d = future_date(6)
        bm.make_booking(self.lecturer1, "Johannesburg", "JHB-LAB-02", d, "10:00", "60")
        before = reports.campus_stats("Johannesburg")["total"]
        booking = [b for b in bm.get_my_bookings(self.lecturer1, "Active") if b["booking_date"] == d][0]
        bm.cancel_booking(self.lecturer1, booking["booking_id"])
        after = reports.campus_stats("Johannesburg")
        self.assertEqual(after["total"], before - 1)
        self.assertEqual(after["cancelled"], 1)

    def test_comparison_report_contains_all_campuses(self):
        text = "\n".join(reports.comparison_report())
        for name in campus.get_campus_names():
            self.assertIn(name, text)
        self.assertIn("Differences caused by campus-specific rules", text)

    def test_list_pages_have_data(self):
        self.assertTrue(len(reports.all_booking_lines()) >= 15)
        self.assertEqual(len(reports.all_resource_lines()), 11)
        self.assertTrue(len(reports.campus_booking_lines("Durban")) >= 4)

    # ---------- persistence and extensibility ----------
    def test_data_persists_between_runs(self):
        bm.register_lecturer("persist_me", "Persist Me", "secret1", "secret1")
        # Simulate closing and re-opening the program with the same database file
        database.setup_database()
        self.assertIsNotNone(database.get_user("persist_me"))
        self.assertEqual(len(database.get_all_bookings()), 15)   # not duplicated

    def test_new_campus_with_minimal_changes(self):
        campus.campuses["Cape Town"] = campus.Campus(
            "Cape Town", "Western Cape",
            campus.BookingRule("Cape Town Policy", 45, 8 * 60, 16 * 60, 7, 1))
        try:
            database.setup_database()          # adds the campus to the database
            self.assertTrue(bm.add_resource(self.operator, "Cape Town", "CPT-LAB-01",
                                            "Lab", "Computer Lab")[0])
            d = future_date(3)
            self.assertFalse(bm.make_booking(self.lecturer1, "Cape Town", "CPT-LAB-01", d, "09:00", "60")[0])
            self.assertTrue(bm.make_booking(self.lecturer1, "Cape Town", "CPT-LAB-01", d, "09:00", "45")[0])
        finally:
            del campus.campuses["Cape Town"]


if __name__ == "__main__":
    unittest.main(verbosity=2)
