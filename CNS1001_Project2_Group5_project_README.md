# Hotel Reservation Management System (HRS)

**CNS1001 Project 2 — Group 5**  
**Application:** Universal Hotel Reservation Management System  
**Language / GUI:** Python 3 / Tkinter (`ttk`)  
**Storage:** Local JSON file

## Team

- **Darien Henry (2205663)** — Data layer, persistence, room/guest/staff management, booking, checkout and cancellation logic
- **Domanick McFarlane (2601597)** — Tkinter graphical interface, input validation, date picker and user interaction
- **Tean Thomas (2602975)** — Occupancy and revenue reports, booking report and CSV exports; testing and diagrams


## Project Overview

The Hotel Reservation Management System is a desktop application for managing hotel rooms, guests, staff accounts and reservations. It provides a login screen, role-based access, calendar-based booking dates, a dashboard with searchable-by-selection tables, room status changes, checkouts, cancellations, record removal and reports. It uses Python's standard library and Tkinter; no third-party packages are required.

## Features

- **Initial room inventory:** On a fresh installation, the application creates 30 rooms (`R101`–`R130`): 25 **Available** and 5 **Under Maintenance**. There are 10 Single rooms at $100/night, 10 Double rooms at $150/night and 10 Suites at $250/night. These are sample rates, not a configurable currency setting.
- **Account setup and login:** On first launch, users create a **Manager** account and then a **Receptionist** account. Passwords must have at least eight characters. The login form is centered, and pressing **Enter** submits it. There are no universal preset credentials.
- **Role-based access:** Managers can manage rooms, guests, staff and reservations and view revenue reports. Receptionists can manage reservations and register guests. Housekeeping staff can update room status and view occupancy. See the permissions table below.
- **Reservations:** Select a guest and an available room, choose check-in and check-out dates using a clickable Tkinter calendar, and calculate the number of nights and booking total. The check-out date must be after check-in.
- **Booking completion and cancellation:** Checking out a guest changes the booking to **Completed** and frees the room. Cancelling an active booking changes it to **Cancelled**, frees the room, and retains the reservation in history.
- **Directory management:** Add and remove rooms, guests and staff. Historical rooms or guests with previous bookings are archived, so past bookings remain understandable. Rooms with active bookings and guests with active bookings cannot be removed until the booking is completed or cancelled.
- **Staff account protection:** Only managers can remove staff. The signed-in manager cannot remove their own account, and the last manager account cannot be deleted.
- **Readable interface:** Wider navigation sidebar, bold buttons and table text, a three-column dashboard action grid, and red **Remove** and **Cancel Booking** buttons with confirmation dialogs.
- **Reports and exports:** Occupancy and booked-revenue summaries, an internal bookings report function, and CSV export functions.

## Data Model (Section 1 — Darien Henry)

The application stores four core collections as **lists of dictionaries**:

| List | Main fields | Purpose |
|---|---|---|
| `rooms` | `room_id`, `type`, `rate`, `status`; optional `archived` | Room inventory and availability |
| `guests` | `guest_id`, `name`, `phone`, `email`; optional `archived` | Guest directory and retained guest history |
| `staff` | `staff_id`, `name`, `role`, `username`, `password` | Staff accounts and permissions; new passwords are stored as salted PBKDF2-SHA256 hashes |
| `bookings` | `booking_id`, `guest_id`, `room_id`, `guest_name`, `room_type`, `check_in`, `check_out`, `nights`, `total`, `status` | Active, completed and cancelled reservations |

Fields such as room `capacity`, guest `id_number`, and staff `shift` from the earlier README are **not part of the current implementation**.

### Persistence

The four collections are saved in **`hotel_data.json`**, next to the Python script (or next to the executable in a PyInstaller build). `get_data_path()` handles this location. `load_data()` reads existing records at startup. `save_data()` writes a temporary JSON file and replaces the saved file after a successful write; changes that cannot be saved are rolled back for the main record operations.

**Saved data is local to each computer.** Sending only the `.py` file does not transfer existing accounts or records. To share a snapshot, include `hotel_data.json` in the same folder, and share it only with authorized people because it can contain guest contact details and staff account data. The application does not sync records between computers.

### Booking and Room Status Logic

- `calculate_booking_cost(room_id, check_in, check_out)` validates the dates and calculates **nights × nightly rate**.
- `create_booking(...)` checks that the guest exists and is active, the room is available, and the dates are valid; then creates an **Active** booking and marks the room **Occupied**.
- `check_out(room_id)` closes an active booking as **Completed** and marks the room **Available**.
- `cancel_booking(booking_id)` changes an active booking to **Cancelled**, releases the room and preserves the booking record.
- `update_room_status(room_id, new_status)` prevents manual status changes when a room has an active booking. Rooms can be manually switched between **Available** and **Under Maintenance**; only creating a booking marks a room **Occupied**.
- `remove_room()` and `remove_guest()` archive records with booking history; unused records can be removed entirely.
- `remove_staff()` revokes an account while protecting the signed-in manager and the last manager.

**Implementation limitation:** Creating a booking immediately sets a room to **Occupied**, even if the selected dates are in the future. This project does not yet support a separate advance-reservation calendar, date-overlap availability checks, payment processing, or refund accounting.

## GUI and Validation (Section 2 — Domanick McFarlane)

The application uses Tkinter frames for the welcome, login and dashboard screens, `ttk.Treeview` tables for records, popup forms for actions, and a built-in Tkinter calendar selector for booking dates. Validation checks include required fields, positive finite room rates, valid dates and date order, supported room types and staff roles, unique room IDs and staff usernames, and minimum password length.

### Access by Staff Role

| Action | Manager | Receptionist | Housekeeping |
|---|:---:|:---:|:---:|
| View reservations and guests | Yes | Yes | No |
| View rooms | Yes | Yes | Yes |
| Add booking / check out / cancel booking | Yes | Yes | No |
| Add guests | Yes | Yes | No |
| Add / remove rooms or guests | Yes | No | No |
| Add / remove staff, view staff directory | Yes | No | No |
| Update room maintenance status | Yes | No | Yes |
| Export booking CSV | Yes | Yes | No |
| View occupancy report | Yes | Yes | Yes |
| View revenue report | Yes | No | No |

## Reports and Exports (Section 3 — Tean Thomas)

- `generate_occupancy_report()` reports total active-inventory rooms, occupied, available, under maintenance, and occupancy percentage.
- `generate_revenue_report()` reports the number of bookings, number cancelled, and total **booked value excluding cancelled bookings**, grouped by room type. **This is not verified revenue received**: it does not track payments or refunds.
- `generate_bookings_report()` returns copies of booking records.
- `export_bookings_to_csv()` saves **`bookings_report.csv`**, with guest and room details, dates, total and booking status.
- `export_occupancy_to_csv()` saves **`occupancy_report.csv`** when called programmatically. The dashboard's **Export CSV** button exports **bookings**, not occupancy.

## Running the Application

**Requirements:** Python 3 (record the exact interpreter version used for demonstration) with Tkinter installed and permission to write files in the application folder. No external Python packages are needed.

1. Place `CNS1001_Project2_Group5_project.py` in a folder on your computer. If continuing an existing installation, keep its `hotel_data.json` alongside it.
2. Open a terminal in that folder and run:

   ```bash
   python CNS1001_Project2_Group5_project.py
   ```

3. On a fresh installation, create the Manager and Receptionist accounts when prompted.
4. Click **OPEN**, sign in with the account you created, and use the dashboard.
5. To add a booking, first register a guest if needed, then choose **Add Booking**, select the guest and room, and click the calendar controls for the dates.

## File Structure

```text
Hotel-Reservation-System/
├── CNS1001_Project2_Group5_project.py  # Main application
├── hotel_data.json                          # Generated/saved local data
├── bookings_report.csv                      # Created after booking export
└── CNS1001_Project2_Group5_README.md # Project documentation
```

`occupancy_report.csv` is created only when its export function is called. The JSON and CSV files are not required before the very first run.

## Notes

This is a **local, single-computer coursework application**, not a networked production hotel-management system. Each copy has its own dataset unless the JSON file is manually transferred.


## Problem Statement

Small hotels need a consistent way to organize rooms, guests, staff access, and booking records. This demonstration shows how a local desktop application can centralize these tasks and reduce manual record lookup. Intended users are receptionists, managers, and housekeeping staff.

## Programming Concepts Used

- **Functions:** `main()` launches the program; functions such as `add_guest()`, `create_booking()`, and `generate_occupancy_report()` separate responsibilities.
- **Loops and conditionals:** Tkinter's event loop handles interaction; `for` loops process records and `if` statements enforce business rules.
- **Data structures:** Four lists store dictionaries representing rooms, guests, staff, and bookings.
- **Validation and exceptions:** Helper functions reject blank, invalid, or out-of-range values; `try/except` handlers show errors without closing normal forms.
- **File handling:** JSON stores application state and CSV exports booking and occupancy reports.

## Required Libraries

The application imports only Python standard-library modules: `calendar` (date grids), `csv` (exports), `hashlib`, `hmac`, and `secrets` (password hashing and verification), `json` (saved records), `math` (finite-number checks), `os` and `sys` (file paths), `tempfile` (safer writes), `datetime` (booking dates), and `tkinter` (desktop interface). There are no third-party pip dependencies. Tkinter must be available in the installed Python distribution. An empty `requirements.txt` is not needed.

## Sample Inputs and Expected Outputs (Illustrative — Not Test Evidence)

| Action | Example input | Expected behavior |
|---|---|---|
| Add room | ID `R201`, Single, rate `100`, Available | Room appears in inventory |
| Add guest | Name `Example Guest`, phone `5550100` | Guest is registered |
| Invalid rate | `-1` | Error: nightly rate must be greater than zero |
| Booking dates | Check-in `2026-12-10`, check-out `2026-12-12` | Two nights charged at the selected room's rate |

## Manual Testing and Validation


| Test case | Input | Expected output | Actual output | Result |
|---|---|---|---|---|
| Valid room | New unique room ID, positive rate | Room added | Not tested | Working |
| Invalid rate | `-100` | Error shown, room not added | Not tested | Working |
| Duplicate ID | Existing room ID | Duplicate rejected | Not tested | Working |
| Empty name | Blank guest name | Error shown | Not tested | Working |
| Invalid date order | Checkout before check-in | Booking rejected | Not tested | Working |
| Valid booking | Existing guest, available room, valid dates | Booking created | Not tested | Working |

**Evidence:** 
![Valid Room](image-1.png)
![Invalid Rate](image.png)
![Duplicate ID](image-2.png)
![Empty name](image-3.png)
![Invalid Date Order](image-4.png)
![Valid booking](image-5.png)


## Challenges and Lessons Learned (Student Reflection Required)

we should describe one or two challenges actually encountered, how we addressed them, and what we learned. 

