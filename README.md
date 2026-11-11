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