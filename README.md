# Hotel Reservation Management System (HRS)
**CNS1001 Project 2 — Group [#]**

## Team
- Darien Henry ([ID]) — Data layer, persistence, booking/checkout logic
- Domanick McFarlane ([ID]) — GUI & Validation
- Tean Thomas ([ID]) — Reports, Testing & Diagrams

## Data Model (Darien Henry)
The application stores four core record sets as **lists of dictionaries**:

| List | Fields | Purpose |
|---|---|---|
| `rooms` | room_id, type, rate, capacity, status | Inventory of hotel rooms |
| `guests` | guest_id, name, contact, id_number | Registered guests |
| `staff` | staff_id, name, role, shift | Hotel employees |
| `bookings` | booking_id, guest_id, room_id, check_in, check_out, nights, total | Active & past reservations |

### Persistence
All four lists are serialized to `hotel_data.json` next to the executable/script.
`get_data_path()` uses `sys.frozen` to detect a PyInstaller build and places the
file beside the `.exe`, so data survives restarts.
`load_data()` is called once at startup; `save_data()` is called after every
state-changing operation.

### Booking & Status Logic
`calculate_booking_cost()` parses the two dates, rejects non-positive stays,
and returns `(nights, nights × rate)`.
`create_booking()` validates guest existence, room availability, and dates,
then appends the booking and flips the room status to **Occupied**.
`check_out()` validates the room is Occupied and frees it.
`update_room_status()` enforces strict rules: it prevents staff from manually marking an occupied room as "Available" (forcing them to use the Check-Out flow) or "Under Maintenance".

# Universal Hotel Reservation Management System (HRS) — GUI & Validation Module
  
**Section:** Section 2 — GUI & Validation 
**Author:** Domanick McFarlane  

## Overview
This module implements the Tkinter desktop interface, navigation controller, and input validation layer for the **Universal Hotel Reservation Management System**.

## Key Features

### 1. Multi-Screen Navigation (`HotelApp`)
* **`WelcomeFrame`:** Landing screen with quick launch into the login portal.
* **`HomeFrame`:** Staff authentication screen with masked password entry, empty-field checks, and a 3-attempt lockout mechanism that returns to the Welcome screen after 3 failed tries.
* **`MainFrame`:** Two-column dashboard layout featuring:
  * **Fixed Navigation Sidebar (`#005b96`):** Switch dynamically between *Reservations*, *Room Status*, *Guest Directory*, and (optional) *Staff Directory*.
  * **Action Bar:** Quick actions for *Check Out Room*, *Export Bookings CSV*, and *Occupancy Report*, plus pre-wired hooks for popup forms.
  * **Styled `ttk.Treeview` (`Hotel.Treeview`):** Dynamically reconfigures columns and refreshes live data from `hotel_data.json`.
  
### 2. Input Validation & Error Handling
All validation helpers raise descriptive `ValueError` exceptions that are caught by GUI handlers inside `try / except ValueError as e:` blocks and displayed via `messagebox.showerror()`:
* `validate_login(info, controller)` — Verifies non-empty credentials and authenticates against the global `staff` list.
* `validate_not_empty(value, field_name)` — Ensures required fields are not blank or whitespace-only.
* `validate_numeric(value, field_name, allow_decimal, positive_only)` — Validates numeric inputs such as room rates.
* `validate_date(date_str, field_name)` & `validate_date_range(check_in, check_out)` — Enforces `YYYY-MM-DD` formatting and verifies check-out occurs after check-in.
* `validate_availability(room_id)` — Confirms the room exists and has status `"Available"`.
* `validate_guest_exists(guest_id)` — Confirms the guest ID exists in the system.

### 3. Pre-Built Popup Forms (`Toplevel`)
Five modal popup classes are included (currently commented out for modular activation):
* **`NewBookingPopup`:** Create reservations with live cost calculation (`calculate_booking_cost` & `create_booking`).
* **`MaintenancePopup`:** Change room status (`update_room_status`), auto-selecting any highlighted room row.
* **`AddRoomPopup`:** Add new rooms to the inventory (`add_room`).
* **`AddGuestPopup`:** Register new guests (`add_guest`).
* **`AddStaffPopup`:** Create new staff accounts (`add_staff`).

## Authentication Note
`validate_login()` checks credentials against the `staff` list loaded from `hotel_data.json` (matching `username`, `name`, or `staff_id` paired with `password`, `pin`, or `staff_id`). Ensure at least one staff record exists in `hotel_data.json` to log in.