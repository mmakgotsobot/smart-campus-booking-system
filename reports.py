"""
reports.py
----------
Builds the campus reports and the cross-campus comparison. Every function
returns a list of text lines that the GUI shows in a Listbox.
"""

from datetime import datetime

import database
import campus
import booking_manager

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]


# ---------------------------------------------------------------
# Formatting single rows (used by several GUI pages)
# ---------------------------------------------------------------
def booking_line(booking, show_campus=False, show_user=False):
    start = booking_manager.booking_start(booking)
    end = booking_manager.booking_end(booking)
    line = ("#" + str(booking["booking_id"])).ljust(6)
    line += booking["booking_date"] + "  "
    line += start.strftime("%H:%M") + "-" + end.strftime("%H:%M") + "  "
    line += booking["resource_name"][:20].ljust(21)
    if show_campus:
        line += booking["campus"].ljust(14)
    if show_user:
        line += booking["username"].ljust(11)
    line += booking_manager.booking_state(booking)
    return line


def resource_line(resource, state=None, show_campus=False):
    if state is None:
        state = resource["status"]
    line = ""
    if show_campus:
        line += resource["campus"].ljust(14)
    line += resource["resource_id"].ljust(12)
    line += resource["name"][:22].ljust(23)
    line += resource["resource_type"].ljust(24)
    line += state
    return line


# ---------------------------------------------------------------
# Statistics for one campus
# ---------------------------------------------------------------
def campus_stats(campus_name):
    """Collect the numbers used by the reports (returns a dictionary)."""
    all_bookings = database.get_campus_bookings(campus_name)
    counted = []         # bookings that were not cancelled
    cancelled = 0
    for b in all_bookings:
        if b["status"] == "Cancelled":
            cancelled += 1
        else:
            counted.append(b)

    total_minutes = 0
    uses = {}            # resource name -> number of bookings
    minutes_per_resource = {}
    per_weekday = {}
    for day in WEEKDAYS:
        per_weekday[day] = 0

    for b in counted:
        total_minutes += b["duration_minutes"]
        label = b["resource_name"] + " (" + b["resource_id"] + ")"
        uses[label] = uses.get(label, 0) + 1
        minutes_per_resource[label] = minutes_per_resource.get(label, 0) + b["duration_minutes"]
        day_name = WEEKDAYS[booking_manager.booking_start(b).weekday()]
        per_weekday[day_name] += 1

    if len(counted) > 0:
        average = total_minutes / len(counted)
    else:
        average = 0

    # Sort the resources from most used to least used
    ranking = sorted(uses.items(), key=lambda item: item[1], reverse=True)

    return {"total": len(counted), "cancelled": cancelled,
            "average": average, "total_minutes": total_minutes,
            "ranking": ranking, "minutes_per_resource": minutes_per_resource,
            "per_weekday": per_weekday,
            "resource_count": len(database.get_resources(campus_name))}


def campus_report(campus_name):
    """Report for one campus: totals, top resources, average duration, trends."""
    stats = campus_stats(campus_name)
    rule = campus.get_campus(campus_name).get_rule()

    lines = []
    lines.append("CAMPUS REPORT: " + campus_name.upper())
    lines.append("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    lines.append("Policy: " + rule.describe())
    lines.append("")
    lines.append("Total number of bookings (not cancelled): " + str(stats["total"]))
    lines.append("Cancelled bookings: " + str(stats["cancelled"]))
    lines.append("Average booking duration: " + format(stats["average"], ".1f") + " minutes")
    lines.append("Total hours booked: " + format(stats["total_minutes"] / 60, ".1f"))
    lines.append("")
    lines.append("Most frequently used resources:")
    if len(stats["ranking"]) == 0:
        lines.append("   (no bookings yet)")
    for label, count in stats["ranking"][:3]:
        lines.append("   " + label + " - " + str(count) + " booking(s)")
    lines.append("")
    lines.append("Usage per resource (hours booked):")
    if len(stats["minutes_per_resource"]) == 0:
        lines.append("   (no bookings yet)")
    for label in sorted(stats["minutes_per_resource"]):
        hours = stats["minutes_per_resource"][label] / 60
        lines.append("   " + label.ljust(34) + format(hours, ".1f").rjust(5) + " h")
    lines.append("")
    lines.append("Usage trend (bookings per weekday):")
    for day in WEEKDAYS:
        count = stats["per_weekday"][day]
        lines.append("   " + day.ljust(10) + ("#" * count) + " " + str(count))
    return lines


# ---------------------------------------------------------------
# Comparing the campuses (system operators)
# ---------------------------------------------------------------
def comparison_report():
    names = campus.get_campus_names()
    all_stats = {}
    for name in names:
        all_stats[name] = campus_stats(name)

    lines = []
    lines.append("CROSS-CAMPUS COMPARISON REPORT")
    lines.append("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    lines.append("")
    lines.append("1. Resource usage across campuses")
    header = ("Campus".ljust(14) + "Bookings".rjust(9) + "Cancelled".rjust(10) +
              "Avg min".rjust(9) + "Hours".rjust(7) + "Resources".rjust(10) +
              "Hrs/resource".rjust(13))
    lines.append(header)
    lines.append("-" * len(header))
    for name in names:
        s = all_stats[name]
        if s["resource_count"] > 0:
            per_resource = s["total_minutes"] / 60 / s["resource_count"]
        else:
            per_resource = 0
        lines.append(name.ljust(14) + str(s["total"]).rjust(9) +
                     str(s["cancelled"]).rjust(10) +
                     format(s["average"], ".1f").rjust(9) +
                     format(s["total_minutes"] / 60, ".1f").rjust(7) +
                     str(s["resource_count"]).rjust(10) +
                     format(per_resource, ".2f").rjust(13))
    lines.append("")
    lines.append("Most used resource per campus:")
    for name in names:
        ranking = all_stats[name]["ranking"]
        if len(ranking) > 0:
            lines.append("   " + name.ljust(14) + ranking[0][0] + " - " +
                         str(ranking[0][1]) + " booking(s)")
        else:
            lines.append("   " + name.ljust(14) + "(no bookings yet)")
    lines.append("")
    lines.append("2. Booking trends (bookings per weekday)")
    day_header = "Campus".ljust(14)
    for day in WEEKDAYS:
        day_header += day[:3].rjust(5)
    lines.append(day_header)
    for name in names:
        row = name.ljust(14)
        for day in WEEKDAYS:
            row += str(all_stats[name]["per_weekday"][day]).rjust(5)
        lines.append(row)
    lines.append("")
    lines.append("3. Differences caused by campus-specific rules")
    for name in names:
        lines.append("   " + campus.get_campus(name).get_rule().describe())
    lines.append("")
    lines.append("Observations:")
    busiest = max(names, key=lambda n: all_stats[n]["total"])
    longest = max(names, key=lambda n: all_stats[n]["average"])
    strictest = min(names, key=lambda n: campus.get_campus(n).get_rule().get_max_minutes())
    lines.append("   - Most bookings: " + busiest + " (" + str(all_stats[busiest]["total"]) + ")")
    lines.append("   - Longest average booking: " + longest + " (" +
                 format(all_stats[longest]["average"], ".1f") + " min)")
    lines.append("   - Strictest duration limit: " + strictest + " (" +
                 str(campus.get_campus(strictest).get_rule().get_max_minutes()) + " min)")
    return lines


# ---------------------------------------------------------------
# Column headings and line lists used by the GUI list pages
# ---------------------------------------------------------------
def booking_header(show_campus=False, show_user=False):
    line = "ID".ljust(6) + "Date".ljust(12) + "Time".ljust(13) + "Resource".ljust(21)
    if show_campus:
        line += "Campus".ljust(14)
    if show_user:
        line += "User".ljust(11)
    return line + "Status"


def resource_header(show_campus=False):
    line = ""
    if show_campus:
        line += "Campus".ljust(14)
    return line + "ID".ljust(12) + "Name".ljust(23) + "Type".ljust(24) + "Status"


def campus_booking_lines(campus_name):
    lines = []
    for booking in database.get_campus_bookings(campus_name):
        lines.append(booking_line(booking, show_user=True))
    return lines


def all_booking_lines():
    lines = []
    for booking in database.get_all_bookings():
        lines.append(booking_line(booking, show_campus=True, show_user=True))
    return lines


def all_resource_lines():
    lines = []
    for resource in database.get_resources():
        lines.append(resource_line(resource, show_campus=True))
    return lines
