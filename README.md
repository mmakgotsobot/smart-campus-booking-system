# Smart Campus Resource Booking System

**Module:** Programming 512 - Richfield Graduate Institution
**Case study:** Smart Campus Resource Booking System (100 marks)
**Language:** Python 3 (Tkinter for the GUI, SQLite for the database)

**GitHub repository:** https://github.com/YOUR-USERNAME/smart-campus-booking-system
*(replace YOUR-USERNAME with your own GitHub username after you push - see "Putting the project on GitHub" below)*

---

## 1. What the application does

Richfield Graduate Institution has several campuses that share resources such as
computer labs, multimedia projectors, seminar rooms and presentation equipment.
Bookings used to be done by email, spreadsheets and paper, which caused double
bookings and no central reporting.

This desktop application replaces that with one system that:

* supports **three campuses**, each with its **own booking rules**;
* has **three user roles** (Lecturer, Campus Administrator, System Operator);
* uses a **Tkinter GUI** for every action;
* stores everything in an **SQLite database**, so data is kept between runs;
* **prevents double bookings**, past bookings and bookings of unavailable resources;
* produces **campus reports** and a **cross-campus comparison**.

## 2. How to run it

**Requirements:** Python 3.8 or newer. No extra packages are needed (`tkinter`
and `sqlite3` come with Python on Windows and macOS).
On Linux, if tkinter is missing: `sudo apt install python3-tk`.

**Option A - PyCharm (recommended)**
1. Unzip the folder and open it in PyCharm (File > Open).
2. Open `main.py`, right-click it and choose **Run 'main'**.

**Option B - command line**
```
cd Smart_Campus_Booking_System
python main.py
```

The database file `campus_booking.db` is created automatically the first time the
program runs, together with the campuses, resources, sample accounts and a few
example bookings. Delete that file if you ever want to reset the data.

**To run the automatic tests:** `python test_system.py`

## 3. Sample accounts

| Role | Username | Password | Campus |
|---|---|---|---|
| Lecturer | `lecturer1` | `lecturer123` | any |
| Lecturer | `lecturer2` | `lecturer123` | any |
| Campus Administrator | `admin_jhb` | `admin123` | Johannesburg |
| Campus Administrator | `admin_pta` | `admin123` | Pretoria |
| Campus Administrator | `admin_dbn` | `admin123` | Durban |
| System Operator | `operator` | `operator123` | all |

New lecturers can create their own account with **Register as a Lecturer** on the login screen.
Administrator and operator accounts are created by management (they are in the starting data).

## 4. How to use it

1. **Login** (or register as a lecturer).
2. **Select a campus.** The active campus is shown at the top of every screen, and the
   booking policy that is in effect is shown directly underneath it.
3. Use the menu on the left. The buttons you see depend on your role.

### Lecturer
* **Book a Resource** - pick a date (`YYYY-MM-DD`), start time (`HH:MM`) and duration (minutes).
  The resource list updates as you type and every 10 seconds: green = available, red = booked
  for that time, grey = unavailable. Select a resource and click **Book Selected Resource**.
* **My Bookings** - view active bookings, past history (completed and cancelled) or everything.
  Select a future booking and click **Cancel Selected Booking**.

### Campus Administrator (own campus only)
* **Manage Resources** - add, update (name, type, available/unavailable) and remove resources.
* **Campus Bookings** - all bookings at the campus.
* **Resource Availability** - check what is free for any date/time.
* **Campus Report** - total bookings, most used resources, average duration, hours per
  resource and a bookings-per-weekday trend.

### System Operator (system-wide)
* Everything an administrator can do, for any campus, plus
* **All Bookings** and **All Resources** across every campus, and
* **Compare Campuses** - resource usage, booking trends and the differences caused by each campus's rules.

## 5. Campus booking policies (Section 5 of the case study)

| Rule | Johannesburg | Pretoria | Durban |
|---|---|---|---|
| Maximum duration per booking | 120 min | 180 min | 90 min |
| Booking hours | 08:00-18:00 | 07:00-20:00 | 09:00-17:00 |
| Max bookings per lecturer per day | 3 | 4 | 2 |
| Book up to ... days ahead | 30 | 60 | 14 |
| Extra rule | none | Projectors max 60 min | Seminar rooms (priority access) need 1 day notice |

The rules are applied automatically for the selected campus and the policy text is always visible.

**Adding a new campus or rule:** the rules live in `campus.py`, separate from the rest of the system.
To add a campus, add one line to the `campuses` dictionary (reuse `BookingRule` or write a small
child class that overrides `check_booking`). On the next start the campus is added to the database
automatically. No other file needs to change.

## 6. Requirements checklist

| Case study requirement | Where it is done |
|---|---|
| Multiple campuses using lists, dictionaries, sets | `campus.py` (`campuses` dictionary, lists of types/statuses); `users.py` (permission **sets**) |
| Authentication + role-based access, using OOP | `users.py` (`User`, `Lecturer`, `CampusAdministrator`, `SystemOperator`), `booking_manager.login` |
| Tkinter GUI | `gui.py` |
| Track availability, bookings, duration | `booking_manager.get_availability`, `make_booking`; `bookings` table |
| SQLite persistence | `database.py` |
| 3.1 Lecturer: register, login, select campus, view resources, book, history | `RegisterScreen`, `LoginScreen`, `CampusScreen`, `ResourceSlotPage`, `MyBookingsPage` |
| 3.2 Administrator: add/update/remove resources, view campus bookings, monitor usage | `ManageResourcesPage`, "Campus Bookings", "Campus Report" |
| 3.3 Operator: system-wide view, comparative reports | "All Bookings", "All Resources", "Compare Campuses" |
| 4.1 Campus selection, active campus shown | `CampusScreen`, header of `MainScreen` |
| 4.2 Resources tied to a campus, unique ID, duplicates rejected | `resources` table (PRIMARY KEY), `booking_manager.add_resource` |
| 4.3 Booking date/time/duration, linked to lecturer and campus, no overlaps | `bookings` table, `booking_manager.overlaps` |
| 5.1 At least three campuses with different rules, applied automatically, policy shown | `campus.py` rule classes; policy label in `MainScreen` |
| 5.2 Rules separated from core logic, easy to extend | `campus.py` |
| 6.1 View active, cancel future (saved to DB), view history | `MyBookingsPage`, `booking_manager.cancel_booking` |
| 6.2 Real-time availability, block unavailable resources | `ResourceSlotPage` (auto refresh), `make_booking` |
| 7.1 Campus report: total, most used, average duration | `reports.campus_report` |
| 7.2 Cross-campus comparison | `reports.comparison_report` |
| 8. Users, campuses/resources, bookings stored in SQLite | `database.py` (4 tables) |
| 10. Readable, commented code, user-friendly GUI, validation, error handling | all files; `messagebox` dialogs, `try/except` around database calls |

## 7. Project files

| File | Purpose |
|---|---|
| `main.py` | Starts the program |
| `gui.py` | All Tkinter screens (login, register, campus selection, main menu and pages) |
| `booking_manager.py` | Program logic: login, registration, resources, bookings, validation |
| `campus.py` | `Campus` class and the booking-rule classes for each campus |
| `users.py` | `User` base class and the three role classes |
| `database.py` | All SQLite code, table creation and starting data |
| `reports.py` | Campus report, comparison report and list formatting |
| `test_system.py` | 32 automatic tests of the program logic |
| `Smart_Campus_Booking_System_Documentation.pdf` | Short written documentation |
| `README.md` | This file |

## 8. Concepts from the study guide that are used

* **Chapter 1 - Lists and tuples:** lists of resources and bookings; tuples such as `(ok, message)` return values.
* **Chapter 2 - Dictionaries and sets:** `campuses` dictionary, database rows as dictionaries, usage counters, permission sets.
* **Chapter 3 - OOP:** classes, encapsulation (private `__attributes` with get methods), inheritance
  (`Lecturer(User)`, `PretoriaRule(BookingRule)`), polymorphism (`get_permissions`, `check_booking`, `get_campus_choices`).
* **Chapter 4 - Tkinter:** `Tk`, `Frame`, `Label`, `Entry`, `Button`, `Listbox`, `Radiobutton`, `OptionMenu`,
  message boxes and event handling (button commands and `bind`).
* **Chapter 5 - Databases:** `sqlite3`, `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`,
  `?` placeholders, primary keys and foreign keys, exception handling for database errors.

## 9. Database design

* `campuses (name PK, location)`
* `users (username PK, full_name, password_hash, role, campus FK)` - passwords are stored hashed (SHA-256), never as plain text.
* `resources (resource_id PK, name, resource_type, campus FK, status)`
* `bookings (booking_id PK, resource_id, resource_name, resource_type, username FK, campus FK, booking_date, start_time, duration_minutes, status, created_at)`

Cancelled bookings are kept (status `Cancelled`) so the history stays complete; they do not block a time slot and are not counted in the "total bookings" report figure.

## 10. Input validation and error handling

* Date must be `YYYY-MM-DD`, time `HH:MM`, duration a whole number between 15 and 600 minutes.
* No bookings in the past; no bookings of unavailable or non-existent resources.
* Usernames: at least 3 letters/numbers; passwords: at least 6 characters and must match the confirmation.
* Resource IDs: letters, numbers and dashes only; duplicates are rejected.
* Administrators cannot manage another campus; only lecturers can book.
* Database errors are caught and shown in a message box instead of crashing the program.

## 11. Putting the project on GitHub

1. Create an empty repository on https://github.com (for example `smart-campus-booking-system`).
2. In the project folder (PyCharm terminal or Git Bash) run:
```
git init
git add .
git commit -m "Smart Campus Resource Booking System - Programming 512"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/smart-campus-booking-system.git
git push -u origin main
```
3. Replace the link at the top of this README with your real repository link, then run
   `git add README.md`, `git commit -m "Add GitHub link"` and `git push`.

The included `.gitignore` keeps the generated database file out of the repository.

## 12. Notes and limitations

* This is a single-computer desktop application: it does not have a network login or server.
* Times are treated as local time with no time-zone handling.
* The sample accounts and passwords are for demonstration only.
