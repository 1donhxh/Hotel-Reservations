"""CNS1001 Project 2 — Universal Hotel Reservation Management System (HRS).

Integrated and optimized version of the supplied team project, aligned with
hotel_reservations_calendar_picker.py.

Section 1: Data Layer & Business Logic — Darien Henry
Section 2: GUI & Validation — Domanick McFarlane
Section 3: Reports & CSV Export — Tean Thomas

First run creates 30 rooms (25 available, 5 under maintenance) and asks you
to create Manager and Receptionist accounts. Existing hotel_data.json records
are retained. Calendar selection uses built-in Tkinter; no external modules.
"""
<<<<<<< HEAD
import calendar
import csv
import hashlib
import hmac
=======
CNS1001 Project 2 — Hotel Reservation Management System (HRS)
Data Layer & Business Logic (Darien Henry)
"""

>>>>>>> 7f19f9dc89ff0412ed4ce9625664109fbbc4ce39
import json
import math
import os
import secrets
import sys
<<<<<<< HEAD
import tempfile
from datetime import datetime, date, timedelta
from tkinter import messagebox, ttk
import tkinter as tk
=======
from datetime import datetime

# -- GUI Imports (for Domanick) --
import tkinter as tk
from tkinter import ttk, messagebox

# =====================================================================
# SECTION 1: DATA LAYER & LOGIC (Darien Henry)
# =====================================================================
# ---- Data structures (all lists of dicts) --------------------------
rooms: list = []
guests: list = []
staff: list = []
bookings: list = []
>>>>>>> 7f19f9dc89ff0412ed4ce9625664109fbbc4ce39

# SECTION 1 — DATA LAYER & BUSINESS LOGIC (Darien Henry)
rooms = []
guests = []
staff = []
bookings = []

VALID_ROOM_TYPES = {"Single", "Double", "Suite"}
VALID_STATUSES = {"Available", "Occupied", "Under Maintenance"}
VALID_ROLES = {"Receptionist", "Housekeeping", "Manager"}
DEFAULT_ROOM_COUNT = 30
DEFAULT_AVAILABLE_ROOMS = 25


def initialize_default_rooms():
    """Seed a brand-new/empty inventory without modifying existing rooms."""
    # Do not recreate default rooms after a user intentionally removes every room.
    if rooms or os.path.exists(get_data_path()):
        return False
    generated = []
    for number in range(101, 131):
        offset = number - 101
        room_type = ("Single", "Double", "Suite")[offset // 10]
        rate = {"Single": 100.0, "Double": 150.0, "Suite": 250.0}[room_type]
        generated.append({
            "room_id": f"R{number}", "type": room_type, "rate": rate,
            "status": "Available" if offset < DEFAULT_AVAILABLE_ROOMS else "Under Maintenance"
        })
    rooms.extend(generated)
    persist_or_rollback(lambda: rooms.clear())
    return True

BG = "#81C1EB"
DARK = "#005B96"


def get_data_path(filename="hotel_data.json"):
    base = os.path.dirname(sys.executable if getattr(sys, "frozen", False)
                           else os.path.abspath(__file__))
    return os.path.join(base, filename)


def load_data():
    global rooms, guests, staff, bookings
    path = get_data_path()
    if not os.path.exists(path):
        rooms, guests, staff, bookings = [], [], [], []
        return
    try:
        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            raise ValueError("Data file must contain a JSON object")
        new_values = []
        for key in ("rooms", "guests", "staff", "bookings"):
            value = payload.get(key, [])
            if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
                raise ValueError(f"Invalid '{key}' data")
            new_values.append(value)
        rooms, guests, staff, bookings = new_values
        # Preserve compatibility with bookings created by the original code.
        # Historical bookings must be explicitly closed after checkout.
        occupied_assigned = set()
        for booking in reversed(bookings):
            room = next((r for r in rooms if r.get("room_id") == booking.get("room_id")), None)
            guest = next((g for g in guests if g.get("guest_id") == booking.get("guest_id")), None)
            if "status" not in booking:
                room_id = booking.get("room_id")
                can_be_active = bool(room and room.get("status") == "Occupied"
                                     and room_id not in occupied_assigned)
                booking["status"] = "Active" if can_be_active else "Completed"
                if can_be_active:
                    occupied_assigned.add(room_id)
            if "guest_name" not in booking and guest:
                booking["guest_name"] = guest.get("name", "")
            if "room_type" not in booking and room:
                booking["room_type"] = room.get("type", "Unknown")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not load hotel data: {exc}") from exc


def save_data():
    """Write the JSON atomically, returning True on success."""
    payload = {"rooms": rooms, "guests": guests, "staff": staff, "bookings": bookings}
    path = get_data_path()
    temp_path = None
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=os.path.dirname(path),
                                         prefix="hotel_", suffix=".tmp", delete=False) as file:
            temp_path = file.name
            json.dump(payload, file, indent=2)
        os.replace(temp_path, path)
        return True
    except (OSError, TypeError, ValueError) as exc:
        print(f"[save_data] Could not save: {exc}")
        return False
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def persist_or_rollback(undo):
    if not save_data():
        undo()
        raise OSError("Could not save changes. Please check file permissions and disk space.")


def next_id(prefix, items, key):
    highest = 0
    for item in items:
<<<<<<< HEAD
        ident = str(item.get(key, ""))
        suffix = ident[len(prefix):] if ident.startswith(prefix) else ""
        if suffix.isdigit():
            highest = max(highest, int(suffix))
=======
        ident = item.get(key, "")
        if ident.startswith(prefix):
            try:
                number = int(ident[len(prefix) :])
                if number > highest:
                    highest = number
            except ValueError:
                continue
>>>>>>> 7f19f9dc89ff0412ed4ce9625664109fbbc4ce39
    return f"{prefix}{highest + 1:03d}"


def find_room(room_id):
    return next((r for r in rooms if r.get("room_id") == room_id), None)


def find_guest(guest_id):
    return next((g for g in guests if g.get("guest_id") == guest_id), None)


def find_booking(booking_id):
    return next((b for b in bookings if b.get("booking_id") == booking_id), None)


def visible_rooms():
    """Rooms still in service; retired rooms remain in history."""
    return [r for r in rooms if not r.get("archived", False)]


def visible_guests():
    """Guests in the active directory; archived guests retain booking history."""
    return [g for g in guests if not g.get("archived", False)]


def find_active_booking_for_room(room_id):
    return next((b for b in bookings if b.get("room_id") == room_id
                 and b.get("status") == "Active"), None)


def validate_not_empty(value, field_name):
    cleaned = str(value).strip() if value is not None else ""
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty.")
    return cleaned


def validate_numeric(value, field_name, allow_decimal=True, positive_only=True):
    cleaned = validate_not_empty(value, field_name)
    try:
        if not allow_decimal and (not cleaned.isdigit()):
            raise ValueError
        number = float(cleaned) if allow_decimal else int(cleaned)
    except (ValueError, OverflowError):
        raise ValueError(f"{field_name} must be a valid {'number' if allow_decimal else 'whole number'}.")
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite.")
    if positive_only and number <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return number


def validate_date(date_str, field_name="Date"):
    cleaned = validate_not_empty(date_str, field_name)
    try:
        date = datetime.strptime(cleaned, "%Y-%m-%d")
        if date.strftime("%Y-%m-%d") != cleaned:
            raise ValueError
        return date
    except ValueError:
        raise ValueError(f"{field_name} must be a valid date in YYYY-MM-DD format.")


def validate_date_range(check_in, check_out):
    start = validate_date(check_in, "Check-in date")
    end = validate_date(check_out, "Check-out date")
    if end <= start:
        raise ValueError("Check-out must be after check-in.")
    return start, end


def validate_availability(room_id):
    room = find_room(validate_not_empty(room_id, "Room ID"))
    if room is None:
        raise ValueError("Room not found.")
    if room.get("archived") or room.get("status") != "Available" or find_active_booking_for_room(room_id):
        raise ValueError(f"Room {room_id} is not available.")
    return room


def validate_guest_exists(guest_id):
    guest = find_guest(validate_not_empty(guest_id, "Guest ID"))
    if guest is None or guest.get("archived"):
        raise ValueError("Guest not found or has been removed from the directory.")
    return guest


def calculate_booking_cost(room_id, check_in, check_out):
    room = find_room(room_id)
    if room is None:
        raise ValueError("Room not found.")
    start, end = validate_date_range(check_in, check_out)
    rate = validate_numeric(str(room.get("rate", "")), "Nightly rate")
    nights = (end - start).days
    return nights, round(nights * rate, 2)


def add_room(room_id, room_type, rate, status="Available"):
    room_id = validate_not_empty(room_id, "Room ID")
    if find_room(room_id):
        raise ValueError("Room ID already exists.")
    if room_type not in VALID_ROOM_TYPES:
        raise ValueError("Invalid room type.")
    rate = round(validate_numeric(str(rate), "Nightly rate"), 2)
    if status not in {"Available", "Under Maintenance"}:
        raise ValueError("New rooms must be Available or Under Maintenance.")
    room = {"room_id": room_id, "type": room_type, "rate": rate, "status": status}
    rooms.append(room)
    persist_or_rollback(lambda: rooms.remove(room))
    return room


def add_guest(name, phone, email=""):
    name = validate_not_empty(name, "Guest name")
    phone = validate_not_empty(phone, "Phone")
    email = str(email).strip()
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        raise ValueError("Enter a valid email address or leave it blank.")
    guest = {"guest_id": next_id("G", guests, "guest_id"), "name": name,
             "phone": phone, "email": email}
    guests.append(guest)
    persist_or_rollback(lambda: guests.remove(guest))
    return guest


def _hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def _verify_password(password, saved):
    if saved.startswith("pbkdf2_sha256$"):
        try:
            _, salt, _ = saved.split("$", 2)
            return hmac.compare_digest(_hash_password(password, salt), saved)
        except ValueError:
            return False
    # Original team project stored plaintext passwords. Permit migration on
    # first successful login; all new accounts store salted password hashes.
    return hmac.compare_digest(password, saved)


def add_staff(name, role, username, password):
    name = validate_not_empty(name, "Full name")
    username = validate_not_empty(username, "Username")
    password = validate_not_empty(password, "Password")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if role not in VALID_ROLES:
        raise ValueError("Invalid staff role.")
    if any(s.get("username", "").lower() == username.lower() for s in staff):
        raise ValueError("Username already exists.")
    member = {"staff_id": next_id("S", staff, "staff_id"), "name": name,
              "role": role, "username": username, "password": _hash_password(password)}
    staff.append(member)
    persist_or_rollback(lambda: staff.remove(member))
    return member


def remove_staff(staff_id, current_staff_id=None):
    """Delete a staff account, while retaining at least one manager account."""
    staff_id = validate_not_empty(staff_id, "Staff ID")
    member = next((s for s in staff if s.get("staff_id") == staff_id), None)
    if member is None:
        raise ValueError("Staff account was not found.")
    if current_staff_id is not None and staff_id == current_staff_id:
        raise ValueError("You cannot remove the account you are currently using.")
    if member.get("role") == "Manager" and sum(
        s.get("role") == "Manager" for s in staff
    ) <= 1:
        raise ValueError("You cannot remove the last manager account.")
    old_index = staff.index(member)
    staff.pop(old_index)
    persist_or_rollback(lambda: staff.insert(old_index, member))
    return member


def authenticate(username, password):
    for member in staff:
        if username == str(member.get("username") or member.get("name") or member.get("staff_id", "")):
            stored = str(member.get("password") or member.get("pin") or "")
            if stored and _verify_password(password, stored):
                # Replace legacy plaintext credentials after successful login.
                if not stored.startswith("pbkdf2_sha256$"):
                    member["password"] = _hash_password(password)
                    member.pop("pin", None)
                    save_data()
                return member
    return None


def create_booking(guest_id, room_id, check_in, check_out):
    validate_guest_exists(guest_id)
    room = validate_availability(room_id)
    nights, total = calculate_booking_cost(room_id, check_in, check_out)
    guest = find_guest(guest_id)
    booking = {"booking_id": next_id("B", bookings, "booking_id"),
               "guest_id": guest_id, "room_id": room_id,
               "guest_name": guest.get("name", "") if guest else "",
               "room_type": room.get("type", "Unknown"),
               "check_in": check_in.strip(), "check_out": check_out.strip(),
               "nights": nights, "total": total, "status": "Active"}
    previous = room["status"]
    bookings.append(booking)
    room["status"] = "Occupied"
    def undo():
        bookings.remove(booking)
        room["status"] = previous
    persist_or_rollback(undo)
    return booking


def check_out(room_id):
    room = find_room(room_id)
    if room is None:
        raise ValueError("Room not found.")
    active = find_active_booking_for_room(room_id)
    if room.get("status") != "Occupied" or active is None:
        raise ValueError("Room does not have an active booking to check out.")
    room["status"] = "Available"
    active["status"] = "Completed"
    def undo():
        room["status"] = "Occupied"
        active["status"] = "Active"
    persist_or_rollback(undo)
    return active


def cancel_booking(booking_id):
    """Cancel only an active booking; keep its history and release the room."""
    booking = find_booking(validate_not_empty(booking_id, "Booking ID"))
    if not booking:
        raise ValueError("Booking not found.")
    if booking.get("status") != "Active":
        raise ValueError("Only active bookings may be cancelled.")
    room = find_room(booking.get("room_id"))
    if not room or room.get("status") != "Occupied":
        raise ValueError("Booking and room status do not match; no changes made.")
    booking["status"] = "Cancelled"
    room["status"] = "Available"
    def undo():
        booking["status"] = "Active"
        room["status"] = "Occupied"
    persist_or_rollback(undo)
    return booking


def remove_room(room_id):
    """Retire a room with booking history; delete an unused room entirely."""
    room = find_room(validate_not_empty(room_id, "Room ID"))
    if room is None or room.get("archived"):
        raise ValueError("Room not found in the active inventory.")
    if room.get("status") == "Occupied" or find_active_booking_for_room(room_id):
        raise ValueError("Cannot remove an occupied room. Check out or cancel its active booking first.")
    related = any(b.get("room_id") == room_id for b in bookings)
    if related:
        room["archived"] = True
        persist_or_rollback(lambda: room.pop("archived", None))
    else:
        index = rooms.index(room)
        rooms.pop(index)
        persist_or_rollback(lambda: rooms.insert(index, room))
    return room


def remove_guest(guest_id):
    """Archive guests with past bookings, but never remove an active guest."""
    guest = find_guest(validate_not_empty(guest_id, "Guest ID"))
    if guest is None or guest.get("archived"):
        raise ValueError("Guest not found in the active directory.")
    related = [b for b in bookings if b.get("guest_id") == guest_id]
    if any(b.get("status") == "Active" for b in related):
        raise ValueError("Guest has an active booking. Cancel or check out the booking first.")
    if related:
        guest["archived"] = True
        persist_or_rollback(lambda: guest.pop("archived", None))
    else:
        index = guests.index(guest)
        guests.pop(index)
        persist_or_rollback(lambda: guests.insert(index, guest))
    return guest


def update_room_status(room_id, new_status):
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")
    room = find_room(room_id)
    if room is None:
        raise ValueError("Room not found.")
<<<<<<< HEAD
    previous = room["status"]
    if room.get("archived"):
        raise ValueError("Cannot update a removed room.")
    if previous == new_status:
        raise ValueError(f"Room is already marked {new_status}.")
    if find_active_booking_for_room(room_id):
        raise ValueError("Check out the active booking before changing the room status.")
    if new_status == "Occupied":
        raise ValueError("Use New Booking to mark a room Occupied.")
=======
    if room["status"] == new_status:
        raise ValueError(f"Room {room_id} is already marked as '{new_status}'.")

    # --- MOVED THIS CHECK UP ---
    if new_status == "Available" and find_active_booking_for_room(room_id):
        raise ValueError("Cannot mark as Available. Room has an active booking.")

    # --- ADDED THIS CHECK (Maintenance can't be set if occupied) ---
    if new_status == "Under Maintenance" and room["status"] == "Occupied":
        raise ValueError(
            f"Cannot set to Maintenance. Room {room_id} is currently Occupied."
        )
    # ----------------------------

>>>>>>> 7f19f9dc89ff0412ed4ce9625664109fbbc4ce39
    room["status"] = new_status
    persist_or_rollback(lambda: room.__setitem__("status", previous))
    return True

# SECTION 2 — GUI & INPUT VALIDATION (Domanick McFarlane)

def configure_styles():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("btn_style.TButton", background=BG, foreground="#101820",
                    font=("Arial", 12, "bold"), padding=(10, 8))
    style.map("btn_style.TButton", background=[("pressed", DARK), ("active", "#6497b1")])
    # Larger, bold labels for the nine dashboard actions and sidebar navigation.
    style.configure("Action.TButton", font=("Arial", 14, "bold"),
                    foreground="#101820", background=BG, padding=(12, 12))
    style.map("Action.TButton", background=[("pressed", DARK), ("active", "#6497b1")],
              foreground=[("disabled", "#666666"), ("!disabled", "#101820")])
    style.configure("Nav.TButton", font=("Arial", 14, "bold"),
                    foreground="#101820", background=BG, padding=(12, 12))
    style.map("Nav.TButton", background=[("pressed", DARK), ("active", "#6497b1")],
              foreground=[("disabled", "#666666"), ("!disabled", "#101820")])
    # Destructive actions have a distinct, accessible red style.
    style.configure("Danger.TButton", font=("Arial", 14, "bold"),
                    foreground="white", background="#B42318",
                    padding=(12, 10), relief="flat", borderwidth=1)
    style.map("Danger.TButton",
              background=[("disabled", "#A8A8A8"),
                          ("pressed", "#7A1712"), ("active", "#921D16")],
              foreground=[("disabled", "#E9E9E9"), ("!disabled", "white")])
    # High-contrast, larger bold text for table records and column titles.
    style.configure("Hotel.Treeview", background="white", foreground="#101820",
                    rowheight=40, fieldbackground="white", font=("Arial", 13, "bold"))
    style.configure("Hotel.Treeview.Heading", background=DARK, foreground="white",
                    font=("Arial", 14, "bold"), padding=(10, 12), relief="flat")
    style.map("Hotel.Treeview", background=[("selected", "#3478A7")],
              foreground=[("selected", "white")])

attempt_count = 1

class CalendarPicker(tk.Toplevel):
    """Small clickable month-view calendar built with standard Tkinter."""
    def __init__(self, parent, initial_date, on_select, minimum_date=None):
        super().__init__(parent)
        self.title("Select Date")
        self.configure(bg=BG, padx=12, pady=12)
        self.resizable(False, False)
        self.transient(parent)
        self.on_select = on_select
        self.minimum_date = minimum_date
        self.visible_year = initial_date.year
        self.visible_month = initial_date.month
        self.selected_date = initial_date

        nav = tk.Frame(self, bg=BG)
        nav.pack(fill="x", pady=(0, 10))
        tk.Button(nav, text="◀", width=3, font=("Arial", 11, "bold"),
                  command=lambda: self.change_month(-1)).pack(side="left")
        self.month_label = tk.Label(nav, bg=BG, font=("Arial", 13, "bold"))
        self.month_label.pack(side="left", expand=True, fill="x")
        tk.Button(nav, text="▶", width=3, font=("Arial", 11, "bold"),
                  command=lambda: self.change_month(1)).pack(side="right")

        self.days = tk.Frame(self, bg=BG)
        self.days.pack()
        tk.Button(self, text="Today", font=("Arial", 10, "bold"),
                  command=self.select_today).pack(fill="x", pady=(10, 0))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.draw_month()
        self.update_idletasks()
        # Display the calendar near the center of the booking form.
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_reqwidth()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_reqheight()) // 2)
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.focus_set()

    def change_month(self, delta):
        index = self.visible_year * 12 + self.visible_month - 1 + delta
        next_year, month_index = divmod(index, 12)
        if not 1 <= next_year <= 9999:
            return
        self.visible_year, self.visible_month = next_year, month_index + 1
        self.draw_month()

    def draw_month(self):
        self.month_label.configure(text=f"{calendar.month_name[self.visible_month]} {self.visible_year}")
        for child in self.days.winfo_children():
            child.destroy()
        for col, name in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            tk.Label(self.days, text=name, bg=BG, font=("Arial", 9, "bold"),
                     width=5).grid(row=0, column=col, pady=(0, 4))
        for row, week in enumerate(calendar.monthcalendar(self.visible_year, self.visible_month), 1):
            for col, day in enumerate(week):
                if day == 0:
                    tk.Label(self.days, text="", width=5, bg=BG).grid(row=row, column=col)
                    continue
                current = date(self.visible_year, self.visible_month, day)
                blocked = self.minimum_date is not None and current < self.minimum_date
                highlighted = current == self.selected_date
                tk.Button(
                    self.days, text=str(day), width=4, height=1,
                    font=("Arial", 10, "bold" if highlighted else "normal"),
                    bg=DARK if highlighted else "white",
                    fg="white" if highlighted else "black",
                    disabledforeground="#999999",
                    state="disabled" if blocked else "normal",
                    command=lambda chosen=current: self.choose(chosen)
                ).grid(row=row, column=col, padx=1, pady=1)

    def select_today(self):
        today = date.today()
        if self.minimum_date is not None and today < self.minimum_date:
            today = self.minimum_date
        self.choose(today)

    def choose(self, chosen):
        if self.minimum_date is None or chosen >= self.minimum_date:
            self.on_select(chosen.isoformat())
            self.close()

    def close(self):
        self.grab_release()
        self.destroy()
        if self.master.winfo_exists():
            self.master.grab_set()

# ---- Validation & Input Helpers -------------------------------------
def validate_login(info, controller):
    global attempt_count
    try:
        name = validate_not_empty(info[0], "Username")
        key = validate_not_empty(info[1], "Password")
    except ValueError as e:
        messagebox.showerror(title="INPUT ERROR", message=str(e))
        return

<<<<<<< HEAD
class FormPopup(tk.Toplevel):
    def __init__(self, parent, title, fields, submit_label, on_submit):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG, padx=18, pady=18)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.entries = {}
        self.on_submit = on_submit
        tk.Label(self, text=title, bg=BG, font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 15))
        for i, (key, label, options) in enumerate(fields, 1):
            tk.Label(self, text=label, bg=BG, font=("Arial", 11, "bold")).grid(
                row=i, column=0, sticky="w", pady=5)
            if key in ("check_in", "check_out"):
                # Dates are selected using a calendar, not typed manually.
                date_box = tk.Frame(self, bg=BG)
                date_box.grid(row=i, column=1, sticky="ew", padx=(12, 0), pady=5)
                date_value = tk.StringVar(value="")
                entry = tk.Entry(date_box, width=22, textvariable=date_value,
                                 font=("Arial", 11, "bold"), state="readonly",
                                 readonlybackground="white")
                entry.pack(side="left", fill="x", expand=True)
                ttk.Button(date_box, text="📅 Select", style="btn_style.TButton",
                           command=lambda k=key, v=date_value: self.open_calendar(k, v)
                           ).pack(side="left", padx=(6, 0))
            elif options:
                entry = ttk.Combobox(self, values=options, state="readonly", width=30)
                entry.current(0)
                entry.grid(row=i, column=1, sticky="ew", padx=(12, 0), pady=5)
            else:
                entry = tk.Entry(self, width=33, show="*" if "password" in key else "")
                entry.grid(row=i, column=1, sticky="ew", padx=(12, 0), pady=5)
            self.entries[key] = entry
        ttk.Button(self, text=submit_label, command=self.submit,
                   style="btn_style.TButton").grid(row=len(fields)+1, column=0,
                                                    columnspan=2, pady=16)
        # Enter submits ordinary form fields; the calendar retains day selection.
        for entry in self.entries.values():
            if isinstance(entry, (tk.Entry, ttk.Combobox)):
                entry.bind("<Return>", lambda event: self.submit())

    def open_calendar(self, key, value):
        existing = value.get()
        start_date = date.fromisoformat(existing) if existing else date.today()
        minimum_date = None
        if key == "check_out":
            check_in = self.entries.get("check_in")
            if check_in and check_in.get():
                minimum_date = date.fromisoformat(check_in.get()) + timedelta(days=1)
                if start_date < minimum_date:
                    start_date = minimum_date
        def set_date(chosen):
            value.set(chosen)
            if key == "check_in" and "check_out" in self.entries:
                check_out = self.entries["check_out"]
                if check_out.get() and check_out.get() <= chosen:
                    check_out.configure(state="normal")
                    check_out.delete(0, "end")
                    check_out.configure(state="readonly")
        CalendarPicker(self, start_date, set_date, minimum_date)

    def submit(self):
        values = {key: entry.get().strip() for key, entry in self.entries.items()}
        try:
            result = self.on_submit(values)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Input Error", str(exc), parent=self)
            return
        messagebox.showinfo("Success", str(result), parent=self)
        self.destroy()


class WelcomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        tk.Label(self, text="Universal Hotel\nReservation Management System",
                 font=("Arial", 27, "bold"), bg=BG).pack(expand=True)
        ttk.Button(self, text="OPEN", style="btn_style.TButton",
                   command=lambda: controller.show_frame("HomeFrame")).pack(pady=30)


class HomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        self.controller = controller
        self.attempts = 0

        # Center the complete login form horizontally and vertically.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        login_panel = tk.Frame(self, bg=BG, padx=28, pady=24)
        login_panel.grid(row=0, column=0)
        login_panel.columnconfigure(0, weight=1)

        tk.Label(login_panel, text="Staff Login", font=("Arial", 26, "bold"),
                 bg=BG).grid(row=0, column=0, pady=(0, 24))
        tk.Label(login_panel, text="Username", bg=BG,
                 font=("Arial", 11, "bold")).grid(row=1, column=0, pady=(0, 4))
        self.username = tk.Entry(login_panel, width=35, font=("Arial", 12))
        self.username.grid(row=2, column=0, pady=(0, 16), ipady=5)
        tk.Label(login_panel, text="Password", bg=BG,
                 font=("Arial", 11, "bold")).grid(row=3, column=0, pady=(0, 4))
        self.password = tk.Entry(login_panel, width=35, show="*", font=("Arial", 12))
        self.password.grid(row=4, column=0, pady=(0, 18), ipady=5)

        ttk.Button(login_panel, text="LOGIN", command=self.login,
                   style="btn_style.TButton").grid(row=5, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(login_panel, text="BACK", style="btn_style.TButton",
                   command=lambda: controller.show_frame("WelcomeFrame")).grid(
                       row=6, column=0, sticky="ew")

        # Pressing Enter while either login input is focused submits the form.
        self.username.bind("<Return>", self._submit_with_enter)
        self.password.bind("<Return>", self._submit_with_enter)

    def _submit_with_enter(self, event=None):
        self.login()
        return "break"

    def login(self):
        username, password = self.username.get().strip(), self.password.get()
        self.password.delete(0, "end")
        try:
            validate_not_empty(username, "Username")
            validate_not_empty(password, "Password")
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc), parent=self)
            return
        member = authenticate(username, password)
        if member:
            self.attempts = 0
            self.controller.current_staff = member
            self.controller.show_frame("MainFrame")
        else:
            self.attempts += 1
            if self.attempts >= 3:
                messagebox.showerror("Login", "Maximum attempts reached. Return to welcome screen.")
                self.attempts = 0
                self.controller.show_frame("WelcomeFrame")
            else:
                messagebox.showwarning("Login", f"Invalid credentials. Attempts left: {3-self.attempts}")
            self.password.focus_set()


class MainFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        self.controller = controller
        self.current_view = "reservations"
        self.columnconfigure(0, minsize=270)  # ~48 px wider than the previous sidebar
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        sidebar = tk.Frame(self, bg=DARK, width=270, padx=16, pady=20)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="UNIVERSAL\nHOTEL", bg=DARK, fg="white",
                 font=("Arial", 18, "bold")).pack(pady=(0, 12))
        self.user_label = tk.Label(sidebar, text="", bg=DARK, fg="white",
                                   font=("Arial", 11, "bold"), wraplength=230)
        self.user_label.pack(pady=(0, 18))
        self.nav_buttons = {}
        for label, method in (("Reservations", self.show_reservations),
                              ("Rooms", self.show_rooms), ("Guests", self.show_guests),
                              ("Staff", self.show_staff)):
            btn = ttk.Button(sidebar, text=label, command=method,
                             style="Nav.TButton")
            btn.pack(fill="x", pady=6)
            self.nav_buttons[label] = btn
        ttk.Button(sidebar, text="LOGOUT", command=self.logout,
                   style="Nav.TButton").pack(side="bottom", fill="x")
        area = tk.Frame(self, bg=BG, padx=15, pady=15)
        area.grid(row=0, column=1, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(2, weight=1)
        self.title_label = tk.Label(area, text="Reservations", bg=BG,
                                    font=("Arial", 26, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w")
        # Context actions are displayed only for the appropriate table and role.
        self.table_actions = tk.Frame(area, bg=BG)
        self.table_actions.grid(row=0, column=0, sticky="e", padx=(12, 0))
        self.remove_staff_button = ttk.Button(
            self.table_actions, text="Remove Staff", command=self.handle_remove_staff,
            style="Danger.TButton")
        self.remove_room_button = ttk.Button(
            self.table_actions, text="Remove Room", command=self.handle_remove_room,
            style="Danger.TButton")
        self.remove_guest_button = ttk.Button(
            self.table_actions, text="Remove Guest", command=self.handle_remove_guest,
            style="Danger.TButton")
        self.cancel_booking_button = ttk.Button(
            self.table_actions, text="Cancel Booking", command=self.handle_cancel_booking,
            style="Danger.TButton")
        for button in (self.remove_staff_button, self.remove_room_button,
                       self.remove_guest_button, self.cancel_booking_button):
            button.pack(side="right", padx=3)
            button.pack_forget()
        # A full-width 3 x 3 grid spreads actions evenly across the dashboard.
        actions = tk.Frame(area, bg=BG)
        actions.grid(row=1, column=0, sticky="ew", pady=(14, 18))
        for col in range(3):
            actions.columnconfigure(col, weight=1, uniform="action_cols")
        buttons = (("Add Booking", self.open_booking_popup),
                   ("Check Out", self.handle_checkout),
                   ("Add Room", self.open_add_room_popup),
                   ("Add Guest", self.open_add_guest_popup),
                   ("Add Staff", self.open_add_staff_popup),
                   ("Room Status", self.open_maintenance_popup),
                   ("Export CSV", self.handle_export_bookings),
                   ("Occupancy", self.handle_occupancy_report),
                   ("Revenue", self.handle_revenue_report))
        self.action_buttons = {}
        for i, (label, command) in enumerate(buttons):
            btn = ttk.Button(actions, text=label, command=command,
                             style="Action.TButton")
            btn.grid(row=i//3, column=i%3, padx=6, pady=6, sticky="ew", ipady=9)
            self.action_buttons[label] = btn
        table_frame = tk.Frame(area)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, show="headings", style="Hotel.Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.show_reservations()

    def logout(self):
        self.controller.current_staff = None
        self.controller.frames["HomeFrame"].username.delete(0, "end")
        self.controller.frames["HomeFrame"].password.delete(0, "end")
        self.controller.show_frame("WelcomeFrame")

    def refresh_permissions(self):
        """Show each user their role and prevent unauthorized GUI actions."""
        member = self.controller.current_staff
        role = member.get("role", "") if member else ""
        name = member.get("name", "") if member else ""
        self.user_label.config(text=f"{name}\n({role})" if member else "")
        permitted = {
            "Manager": {"Add Booking", "Check Out", "Add Room", "Add Guest", "Add Staff",
                        "Room Status", "Export CSV", "Occupancy", "Revenue"},
            "Receptionist": {"Add Booking", "Check Out", "Add Guest", "Export CSV",
                             "Occupancy"},
            "Housekeeping": {"Room Status", "Occupancy"},
        }.get(role, set())
        for label, btn in self.action_buttons.items():
            btn.configure(state="normal" if label in permitted else "disabled")
        for label, btn in self.nav_buttons.items():
            allowed = (role == "Manager" or
                       (role == "Receptionist" and label != "Staff") or
                       (role == "Housekeeping" and label == "Rooms"))
            btn.configure(state="normal" if allowed else "disabled")

    def require_role(self, *roles):
        current = self.controller.current_staff
        if not current or current.get("role") not in roles:
            messagebox.showerror("Access Denied", "Your account does not have permission for this action.")
            return False
        return True

    def _table(self, title, cols, rows, view):
        self.current_view = view
        self.title_label.configure(text=title)
        for button in (self.remove_staff_button, self.remove_room_button,
                       self.remove_guest_button, self.cancel_booking_button):
            button.pack_forget()
        member = self.controller.current_staff
        role = member.get("role", "") if member else ""
        if role == "Manager":
            selected_button = {"staff": self.remove_staff_button,
                               "rooms": self.remove_room_button,
                               "guests": self.remove_guest_button,
                               "reservations": self.cancel_booking_button}.get(view)
            if selected_button:
                selected_button.pack(side="right", padx=3)
        elif view == "reservations" and role == "Receptionist":
            self.cancel_booking_button.pack(side="right", padx=3)
        self.tree["columns"] = [col[0] for col in cols]
        for name, heading, width in cols:
            self.tree.heading(name, text=heading)
            self.tree.column(name, width=width, anchor="center", minwidth=60)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for values in rows:
            self.tree.insert("", "end", values=values)

    def show_reservations(self):
        rows = []
        for b in bookings:
            g = find_guest(b.get("guest_id"))
            rows.append((b.get("booking_id", ""), b.get("guest_name") or (g.get("name") if g else b.get("guest_id", "")),
                         b.get("room_id", ""), b.get("check_in", ""), b.get("check_out", ""),
                         b.get("nights", ""), f"${float(b.get('total', 0)):.2f}",
                         b.get("status", "")))
        self._table("Reservations Overview", [("id", "Booking ID", 90), ("guest", "Guest", 140),
                    ("room", "Room", 80), ("in", "Check-In", 100), ("out", "Check-Out", 100),
                    ("nights", "Nights", 70), ("total", "Total", 100),
                    ("status", "Status", 100)], rows, "reservations")

    def show_rooms(self):
        rows = [(r.get("room_id", ""), r.get("type", ""),
                 f"${float(r.get('rate', 0)):.2f}", r.get("status", "")) for r in visible_rooms()]
        self._table("Room Inventory & Status", [("id", "Room ID", 100),
                    ("type", "Type", 140), ("rate", "Nightly Rate", 120),
                    ("status", "Status", 170)], rows, "rooms")

    def show_guests(self):
        rows = [(g.get("guest_id", ""), g.get("name", ""), g.get("phone", ""),
                 g.get("email", "")) for g in visible_guests()]
        self._table("Registered Guests", [("id", "Guest ID", 100), ("name", "Name", 180),
                    ("phone", "Phone", 140), ("email", "Email", 200)], rows, "guests")

    def show_staff(self):
        if not self.require_role("Manager"):
            return
        rows = [(s.get("staff_id", ""), s.get("name", ""),
                 s.get("role", ""), s.get("username", "")) for s in staff]
        self._table("Staff Directory", [("id", "Staff ID", 100), ("name", "Name", 180),
                    ("role", "Role", 130), ("username", "Username", 150)], rows, "staff")

    def handle_remove_staff(self):
        """Managers can remove a selected staff account from the Staff Directory."""
        if not self.require_role("Manager"):
            return
        if self.current_view != "staff":
            messagebox.showwarning("Staff Directory", "Open the Staff Directory first.")
            return
        selected = self.tree.selection()
        if len(selected) != 1:
            messagebox.showwarning(
                "Select Staff", "Select one staff member in the table to remove."
            )
            return
        values = self.tree.item(selected[0], "values")
        if not values:
            return
        staff_id = values[0]
        member = next((s for s in staff if s.get("staff_id") == staff_id), None)
        if member is None:
            messagebox.showerror("Staff Error", "This staff account no longer exists.")
            self.show_staff()
            return
        current = self.controller.current_staff
        if current and member.get("staff_id") == current.get("staff_id"):
            messagebox.showerror("Staff Error", "You cannot remove your own account.")
            return
        if not messagebox.askyesno(
            "Confirm Staff Removal",
            f"Permanently remove {member.get('name', 'this staff member')} "
            f"({staff_id}, {member.get('role', 'Unknown')})?\n\n"
            "This will revoke their ability to log in.",
            parent=self,
        ):
            return
        try:
            removed = remove_staff(staff_id, current.get("staff_id") if current else None)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Staff Removal Failed", str(exc), parent=self)
            return
        self.show_staff()
        messagebox.showinfo(
            "Staff Removed",
            f"{removed.get('name', staff_id)} was removed successfully.",
            parent=self,
        )

    def _selected_id(self, expected_view, description):
        if self.current_view != expected_view:
            messagebox.showwarning("Open Directory", f"Open {description} first.", parent=self)
            return None
        selected = self.tree.selection()
        if len(selected) != 1:
            messagebox.showwarning("Select Record", f"Select one {description.lower()} row first.", parent=self)
            return None
        values = self.tree.item(selected[0], "values")
        return values[0] if values else None

    def handle_remove_room(self):
        if not self.require_role("Manager"):
            return
        room_id = self._selected_id("rooms", "Rooms")
        if not room_id:
            return
        room = find_room(room_id)
        if not room:
            messagebox.showerror("Room Error", "Room no longer exists.", parent=self)
            return
        related = any(b.get("room_id") == room_id for b in bookings)
        explanation = ("It will be retired from inventory, but retained in booking history."
                       if related else "It has no booking history and will be deleted.")
        if not messagebox.askyesno("Confirm Room Removal",
                f"Remove room {room_id}?\n\n{explanation}", parent=self):
            return
        try:
            remove_room(room_id)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Room Removal Failed", str(exc), parent=self)
            return
        self.show_rooms()
        messagebox.showinfo("Room Removed", f"Room {room_id} removed from inventory.", parent=self)

    def handle_remove_guest(self):
        if not self.require_role("Manager"):
            return
        guest_id = self._selected_id("guests", "Guests")
        if not guest_id:
            return
        guest = find_guest(guest_id)
        if not guest:
            messagebox.showerror("Guest Error", "Guest no longer exists.", parent=self)
            return
        related = any(b.get("guest_id") == guest_id for b in bookings)
        explanation = ("Their profile will be archived to preserve booking history."
                       if related else "Their unused profile will be deleted.")
        if not messagebox.askyesno("Confirm Guest Removal",
                f"Remove {guest.get('name', guest_id)} ({guest_id})?\n\n{explanation}", parent=self):
            return
        try:
            remove_guest(guest_id)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Guest Removal Failed", str(exc), parent=self)
            return
        self.show_guests()
        messagebox.showinfo("Guest Removed", f"Guest {guest_id} removed from directory.", parent=self)

    def handle_cancel_booking(self):
        if not self.require_role("Manager", "Receptionist"):
            return
        booking_id = self._selected_id("reservations", "Reservations")
        if not booking_id:
            return
        booking = find_booking(booking_id)
        if not booking:
            messagebox.showerror("Booking Error", "Booking no longer exists.", parent=self)
            return
        if booking.get("status") != "Active":
            messagebox.showerror("Booking Error", "Only active bookings can be cancelled.", parent=self)
            return
        if not messagebox.askyesno("Confirm Cancellation",
                f"Cancel booking {booking_id} for room {booking.get('room_id')}?\n\n"
                "The room will become available. The cancelled booking remains in history.",
                parent=self):
            return
        try:
            cancel_booking(booking_id)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Cancellation Failed", str(exc), parent=self)
            return
        self.show_reservations()
        messagebox.showinfo("Booking Cancelled", f"Booking {booking_id} cancelled.", parent=self)

    def open_booking_popup(self):
        if not self.require_role("Manager", "Receptionist"):
            return
        available_rooms = [r["room_id"] for r in visible_rooms() if r.get("status") == "Available"
                           and not find_active_booking_for_room(r["room_id"])]
        if not visible_guests() or not available_rooms:
            messagebox.showwarning("Cannot Book", "Add a guest and an available room first.")
            return
        fields = [("guest_id", "Guest ID", [g["guest_id"] for g in visible_guests()]),
                  ("room_id", "Available Room", available_rooms),
                  ("check_in", "Check-In Date", None),
                  ("check_out", "Check-Out Date", None)]
        def submit(v):
            booking = create_booking(**v)
            self.show_reservations()
            return f"Booking {booking['booking_id']} created. Total: ${booking['total']:.2f}"
        FormPopup(self, "New Booking", fields, "Confirm Booking", submit)

    def open_maintenance_popup(self):
        if not self.require_role("Manager", "Housekeeping"):
            return
        if not visible_rooms():
            messagebox.showwarning("No Rooms", "Add a room first.")
            return
        fields = [("room_id", "Room", [r["room_id"] for r in visible_rooms()]),
                  ("new_status", "New Status", ["Available", "Under Maintenance"])]
        def submit(v):
            update_room_status(**v)
            self.show_rooms()
            return "Room status updated."
        FormPopup(self, "Update Room Status", fields, "Save Status", submit)

    def open_add_room_popup(self):
        if not self.require_role("Manager"):
            return
        fields = [("room_id", "Room ID", None),
                  ("room_type", "Room Type", sorted(VALID_ROOM_TYPES)),
                  ("rate", "Nightly Rate", None),
                  ("status", "Initial Status", ["Available", "Under Maintenance"])]
        def submit(v):
            new = add_room(**v)
            self.show_rooms()
            return f"Room {new['room_id']} added."
        FormPopup(self, "Add Room", fields, "Save Room", submit)

    def open_add_guest_popup(self):
        if not self.require_role("Manager", "Receptionist"):
            return
        fields = [("name", "Full Name", None), ("phone", "Phone", None),
                  ("email", "Email (optional)", None)]
        def submit(v):
            new = add_guest(**v)
            self.show_guests()
            return f"Guest {new['guest_id']} registered."
        FormPopup(self, "Register Guest", fields, "Save Guest", submit)

    def open_add_staff_popup(self):
        if not self.require_role("Manager"):
            return
        current = self.controller.current_staff
        if current is not None and current.get("role") != "Manager":
            messagebox.showerror("Access Denied", "Only managers can add staff.")
            return
        fields = [("name", "Full Name", None), ("role", "Role", sorted(VALID_ROLES)),
                  ("username", "Username", None), ("password", "Password", None)]
        def submit(v):
            new = add_staff(**v)
            self.show_staff()
            return f"Staff {new['staff_id']} added."
        FormPopup(self, "Add Staff", fields, "Save Staff", submit)

    def handle_checkout(self):
        if not self.require_role("Manager", "Receptionist"):
            return
        if self.current_view not in ("reservations", "rooms"):
            messagebox.showwarning("Select Room", "Open Reservations or Rooms first.")
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Select a room or booking first.")
            return
        values = self.tree.item(selected[0], "values")
        room_id = values[2] if self.current_view == "reservations" else values[0]
        if self.current_view == "reservations":
            booking = find_booking(values[0])
            if not booking or booking.get("status") != "Active":
                messagebox.showerror("Check-Out Error", "Select an active booking.")
                return
        try:
            checked_out = check_out(room_id)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Check-Out Error", str(exc))
            return
        messagebox.showinfo("Success", f"Booking {checked_out['booking_id']} checked out.")
        if self.current_view == "reservations":
            self.show_reservations()
        else:
            self.show_rooms()

    def handle_export_bookings(self):
        if not self.require_role("Manager", "Receptionist"):
            return
        path = export_bookings_to_csv()
        if path:
            messagebox.showinfo("Export Complete", f"Bookings exported to:\n{path}")
        else:
            messagebox.showerror("Export Failed", "Could not write bookings CSV.")

    def handle_occupancy_report(self):
        if not self.require_role("Manager", "Receptionist", "Housekeeping"):
            return
        r = generate_occupancy_report()
        messagebox.showinfo("Occupancy Report", f"Total Rooms: {r['total']}\n"
                            f"Occupied: {r['occupied']}\nAvailable: {r['available']}\n"
                            f"Under Maintenance: {r['maintenance']}\n"
                            f"Occupancy Rate: {r['rate']}%")

    def handle_revenue_report(self):
        if not self.require_role("Manager"):
            return
        r = generate_revenue_report()
        messagebox.showinfo("Revenue Report", f"Total Bookings: {r['total_bookings']}\n"
                            f"Cancelled: {r['cancelled_bookings']}\n"
                            f"Booked Revenue (excluding cancelled): ${r['total_revenue']:.2f}\n" +
                            "\n".join(f"{t}: ${amount:.2f}" for t, amount in r['by_type'].items()))


class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hotel Reservation Management System")
        self.geometry("1100x600")
        self.configure(bg=BG)
        self.current_staff = None
        try:
            load_data()
        except RuntimeError as exc:
            messagebox.showerror("Data Error", str(exc), parent=self)
            self.destroy()
            raise
        try:
            initialize_default_rooms()
        except OSError as exc:
            messagebox.showerror("Setup Error", str(exc), parent=self)
            self.destroy()
            raise
        configure_styles()
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.frames = {}
        for screen in (WelcomeFrame, HomeFrame, MainFrame):
            frame = screen(self, self)
            self.frames[screen.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("WelcomeFrame")
        if not staff:
            self.after(100, self.setup_first_manager)

    def setup_first_manager(self):
        messagebox.showinfo(
            "First Run",
            "30 rooms are ready: 25 Available, 5 Under Maintenance.\n"
            "Create a manager account, followed by a receptionist account.\n"
            "Use different usernames and passwords (8+ characters).",
            parent=self)
        fields = [("name", "Full Name", None), ("role", "Role", ["Manager"]),
                  ("username", "Username", None), ("password", "Password", None)]
        def submit(v):
            member = add_staff(**v)
            self.after(100, self.setup_first_receptionist)
            return f"Manager login '{member['username']}' created. Next: receptionist login."
        FormPopup(self, "Set Up Manager Login", fields, "Create Manager", submit)

    def setup_first_receptionist(self):
        fields = [("name", "Full Name", None), ("role", "Role", ["Receptionist"]),
                  ("username", "Username", None), ("password", "Password", None)]
        def submit(v):
            member = add_staff(**v)
            return f"Receptionist login '{member['username']}' created. Both accounts can now log in."
        FormPopup(self, "Set Up Staff Login", fields, "Create Receptionist", submit)

    def show_frame(self, screen_name):
        frame = self.frames[screen_name]
        if screen_name == "MainFrame":
            if self.current_staff is None:
                raise ValueError("Please log in first.")
            frame.refresh_permissions()
            frame.show_reservations() if self.current_staff.get("role") != "Housekeeping" else frame.show_rooms()
        frame.tkraise()
        if screen_name == "HomeFrame":
            frame.username.focus_set()

# SECTION 3 — REPORTS & CSV EXPORT (Tean Thomas)

def generate_occupancy_report():
    inventory = visible_rooms()
    total = len(inventory)
    occupied = sum(r.get("status") == "Occupied" for r in inventory)
    maintenance = sum(r.get("status") == "Under Maintenance" for r in inventory)
    available = sum(r.get("status") == "Available" for r in inventory)
    return {"total": total, "occupied": occupied, "available": available,
            "maintenance": maintenance, "rate": round(100 * occupied / total, 2) if total else 0.0}


def generate_revenue_report():
    by_type = {}
    total = 0.0
    chargeable = [b for b in bookings if b.get("status") != "Cancelled"]
    for booking in chargeable:
        amount = float(booking.get("total", 0))
        total += amount
        room = find_room(booking.get("room_id"))
        room_type = booking.get("room_type") or (room.get("type", "Unknown") if room else "Unknown")
        by_type[room_type] = by_type.get(room_type, 0.0) + amount
    return {"total_bookings": len(bookings), "cancelled_bookings": len(bookings) - len(chargeable),
            "total_revenue": round(total, 2),
            "by_type": {key: round(value, 2) for key, value in by_type.items()}}


def generate_bookings_report():
    return [dict(booking) for booking in bookings]


def export_bookings_to_csv(filename="bookings_report.csv"):
    path = filename if os.path.isabs(filename) else get_data_path(filename)
    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["booking_id", "guest_id", "guest_name", "room_id", "room_type",
                             "check_in", "check_out", "nights", "total", "status"])
            for booking in bookings:
                guest = find_guest(booking.get("guest_id"))
                room = find_room(booking.get("room_id"))
                writer.writerow([booking.get("booking_id", ""), booking.get("guest_id", ""),
                                 booking.get("guest_name") or (guest.get("name", "") if guest else "Unknown"),
                                 booking.get("room_id", ""), booking.get("room_type") or (room.get("type", "Unknown") if room else "Unknown"),
                                 booking.get("check_in", ""), booking.get("check_out", ""),
                                 booking.get("nights", ""), booking.get("total", 0),
                                 booking.get("status", "")])
        return path
    except OSError as exc:
        print(f"CSV export failed: {exc}")
        return None


def export_occupancy_to_csv(filename="occupancy_report.csv"):
    path = filename if os.path.isabs(filename) else get_data_path(filename)
    report = generate_occupancy_report()
    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["total_rooms", "occupied", "available", "maintenance", "occupancy_rate"])
            writer.writerow([report["total"], report["occupied"], report["available"],
                             report["maintenance"], report["rate"]])
        return path
    except OSError as exc:
        print(f"Occupancy CSV export failed: {exc}")
=======
    # Check against the global `staff` list from Section 1
    authenticated = False

    if not staff and name == "admin" and key == "1234":
        authenticated = True
    else:

        for member in staff:
            staff_user = str(
                member.get("username")
                or member.get("name")
                or member.get("staff_id", "")
            ).strip()
            staff_pass = str(
                member.get("password")
                or member.get("pin")
                or member.get("staff_id", "")
            ).strip()
            if name == staff_user and key == staff_pass:
                authenticated = True
                break

    if authenticated:
        attempt_count = 1
        controller.show_frame("MainFrame")
    elif attempt_count < 3:
        messagebox.showwarning(
            title="WARNING", message=f"Attempts Left: {3 - attempt_count}"
        )
        attempt_count += 1
    else:
        attempt_count = 1
        messagebox.showerror(title="LOCKED", message="Maximum attempts reached.")
        controller.show_frame("WelcomeFrame")


def validate_not_empty(value: str, field_name: str) -> str:
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty.")
    return cleaned


def validate_numeric(
    value: str, field_name: str, allow_decimal: bool = True, positive_only: bool = True
):
    cleaned = validate_not_empty(value, field_name)
    try:
        num = float(cleaned) if allow_decimal else int(cleaned)
    except ValueError:
        num_type = "number" if allow_decimal else "whole number"
        raise ValueError(f"{field_name} must be a valid {num_type}.")

    if positive_only and num <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return num


def validate_date(date_str: str, field_name: str = "Date") -> datetime:
    cleaned = validate_not_empty(date_str, field_name)
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"{field_name} must be in YYYY-MM-DD format (e.g., 2026-11-25)."
        )


def validate_date_range(check_in: str, check_out: str) -> tuple:
    d_in = validate_date(check_in, "Check-in date")
    d_out = validate_date(check_out, "Check-out date")
    if d_out <= d_in:
        raise ValueError("Check-out date must be after the check-in date.")
    return d_in, d_out


def validate_availability(room_id: str) -> dict:
    cleaned_id = validate_not_empty(room_id, "Room ID")
    room = find_room(cleaned_id)
    if room is None:
        raise ValueError(f"Room '{cleaned_id}' was not found.")
    if room.get("status") != "Available":
        raise ValueError(
            f"Room '{cleaned_id}' is not available (Status: {room.get('status')})."
        )
    return room


def validate_guest_exists(guest_id: str) -> dict:
    cleaned_id = validate_not_empty(guest_id, "Guest ID")
    guest = find_guest(cleaned_id)
    if guest is None:
        raise ValueError(f"Guest '{cleaned_id}' was not found.")
    return guest


# ---- Button Styles & Navigation Helpers -----------------------------
def configure_styles():
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "btn_style.TButton",
        bordercolor="black",
        lightcolor="#81c1eb",
        darkcolor="#81c1eb",
        background="#81c1eb",
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "btn_style.TButton", background=[("pressed", "#005b96"), ("active", "#6497b1")]
    )

    style.configure(
        "Hotel.Treeview",
        background="white",
        foreground="black",
        rowheight=28,
        fieldbackground="white",
        font=("Arial", 11),
    )
    style.configure(
        "Hotel.Treeview.Heading",
        background="#005b96",
        foreground="white",
        font=("Arial", 11, "bold"),
        relief="flat",
    )
    style.map("Hotel.Treeview", background=[("selected", "#6497b1")])


def open_home(controller):
    controller.show_frame("HomeFrame")


def submit_login(name_entry, key_entry, controller):
    user_val = name_entry.get()
    pass_val = key_entry.get()
    validate_login([user_val, pass_val], controller)
    name_entry.delete(0, "end")
    key_entry.delete(0, "end")


def exit_to_welcome(controller):
    controller.show_frame("WelcomeFrame")


# =====================================================================
# POPUP FORMS (UNCOMMENT WHEN SECTION 1 FUNCTIONS ARE READY)
# =====================================================================


# ---- 1. New Booking Popup (Uses existing create_booking & calculate_booking_cost) ----
class NewBookingPopup(tk.Toplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.title("New Reservation")
        self.geometry("400x360")
        self.config(background="#81C1EB", padx=20, pady=20)
        self.resizable(False, False)
        self.grab_set()
        self.refresh_callback = refresh_callback

        tk.Label(
            self, text="Create New Booking", font=("Arial", 16, "bold"), bg="#81C1EB"
        ).pack(pady=(0, 15))

        form = tk.Frame(self, bg="#81C1EB")
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Guest ID:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=5
        )
        guest_choices = [f"{g['guest_id']} - {g['name']}" for g in guests]
        self.guest_cb = ttk.Combobox(form, values=guest_choices, state="readonly")
        self.guest_cb.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(
            form, text="Available Room:", bg="#81C1EB", font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", pady=5)
        room_choices = [
            f"{r['room_id']} ({r['type']} - ${r['rate']})"
            for r in rooms
            if r["status"] == "Available"
        ]
        self.room_cb = ttk.Combobox(form, values=room_choices, state="readonly")
        self.room_cb.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(
            form,
            text="Check-In (YYYY-MM-DD):",
            bg="#81C1EB",
            font=("Arial", 10, "bold"),
        ).grid(row=2, column=0, sticky="w", pady=5)
        self.checkin_entry = tk.Entry(form)
        self.checkin_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(
            form,
            text="Check-Out (YYYY-MM-DD):",
            bg="#81C1EB",
            font=("Arial", 10, "bold"),
        ).grid(row=3, column=0, sticky="w", pady=5)
        self.checkout_entry = tk.Entry(form)
        self.checkout_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        self.cost_label = tk.Label(
            self,
            text="Estimated Total: $0.00",
            font=("Arial", 11, "bold"),
            bg="#81C1EB",
            fg="#005b96",
        )
        self.cost_label.pack(pady=10)

        btn_row = tk.Frame(self, bg="#81C1EB")
        btn_row.pack(pady=5)
        ttk.Button(
            btn_row,
            text="Calculate Cost",
            command=self.preview_cost,
            style="btn_style.TButton",
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_row,
            text="Confirm Booking",
            command=self.save_booking,
            style="btn_style.TButton",
        ).pack(side="left", padx=5)

    def _get_selected_ids(self):
        g_raw = validate_not_empty(self.guest_cb.get(), "Guest")
        r_raw = validate_not_empty(self.room_cb.get(), "Room")
        guest_id = g_raw.split(" - ")[0].strip()
        room_id = r_raw.split(" ")[0].strip()
        return guest_id, room_id

    def preview_cost(self):
        try:
            _, room_id = self._get_selected_ids()
            validate_date_range(self.checkin_entry.get(), self.checkout_entry.get())
            nights, total = calculate_booking_cost(
                room_id,
                self.checkin_entry.get().strip(),
                self.checkout_entry.get().strip(),
            )
            self.cost_label.config(
                text=f"Estimated Total: ${total:.2f} ({nights} night{'s' if nights != 1 else ''})"
            )
        except ValueError as e:
            messagebox.showerror("Calculation Error", str(e), parent=self)

    def save_booking(self):
        try:
            guest_id, room_id = self._get_selected_ids()
            validate_guest_exists(guest_id)
            validate_availability(room_id)
            validate_date_range(self.checkin_entry.get(), self.checkout_entry.get())
            booking = create_booking(
                guest_id,
                room_id,
                self.checkin_entry.get().strip(),
                self.checkout_entry.get().strip(),
            )
            messagebox.showinfo(
                "Booking Confirmed",
                f"Booking {booking['booking_id']} created! Total: ${booking['total']:.2f}",
                parent=self,
            )
            self.refresh_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Booking Error", str(e), parent=self)


# ---- 2. Maintenance / Update Room Status Popup (Uses existing update_room_status) ----
class MaintenancePopup(tk.Toplevel):
    def __init__(self, parent, refresh_callback, preselect_room=""):
        super().__init__(parent)
        self.title("Update Room Status / Maintenance")
        self.geometry("380x240")
        self.config(background="#81C1EB", padx=20, pady=20)
        self.resizable(False, False)
        self.grab_set()
        self.refresh_callback = refresh_callback

        tk.Label(
            self,
            text="Room Status & Maintenance",
            font=("Arial", 15, "bold"),
            bg="#81C1EB",
        ).pack(pady=(0, 15))

        form = tk.Frame(self, bg="#81C1EB")
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        tk.Label(
            form, text="Select Room:", bg="#81C1EB", font=("Arial", 10, "bold")
        ).grid(row=0, column=0, sticky="w", pady=6)
        room_ids = [r["room_id"] for r in rooms]
        self.room_cb = ttk.Combobox(form, values=room_ids, state="readonly")
        if preselect_room in room_ids:
            self.room_cb.set(preselect_room)
        self.room_cb.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))

        tk.Label(
            form, text="New Status:", bg="#81C1EB", font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", pady=6)
        self.status_cb = ttk.Combobox(
            form, values=sorted(list(VALID_STATUSES)), state="readonly"
        )
        self.status_cb.set("Under Maintenance")
        self.status_cb.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))

        ttk.Button(
            self,
            text="Update Status",
            command=self.apply_status,
            style="btn_style.TButton",
        ).pack(pady=15)

    def apply_status(self):
        try:
            room_id = validate_not_empty(self.room_cb.get(), "Room ID")
            new_status = validate_not_empty(self.status_cb.get(), "Status")
            update_room_status(room_id, new_status)
            messagebox.showinfo(
                "Updated",
                f"Room {room_id} status changed to '{new_status}'.",
                parent=self,
            )
            self.refresh_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Status Error", str(e), parent=self)


"""#---- 3. Add Room Popup (Requires add_room() in Section 1) ----
class AddRoomPopup(tk.Toplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.title("Add New Room")
        self.geometry("380x280")
        self.config(background="#81C1EB", padx=20, pady=20)
        self.resizable(False, False)
        self.grab_set()
        self.refresh_callback = refresh_callback

        tk.Label(self, text="Add Hotel Room", font=("Arial", 16, "bold"), bg="#81C1EB").pack(pady=(0, 15))

        form = tk.Frame(self, bg="#81C1EB")
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Room ID (e.g. R101):", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.id_entry = tk.Entry(form)
        self.id_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(form, text="Room Type:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.type_cb = ttk.Combobox(form, values=sorted(list(VALID_ROOM_TYPES)), state="readonly")
        self.type_cb.set("Single")
        self.type_cb.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(form, text="Nightly Rate ($):", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.rate_entry = tk.Entry(form)
        self.rate_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(form, text="Initial Status:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        self.status_cb = ttk.Combobox(form, values=["Available", "Under Maintenance"], state="readonly")
        self.status_cb.set("Available")
        self.status_cb.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        ttk.Button(self, text="Save Room", command=self.save_room, style="btn_style.TButton").pack(pady=15)

    def save_room(self):
        try:
            room_id = validate_not_empty(self.id_entry.get(), "Room ID")
            room_type = validate_not_empty(self.type_cb.get(), "Room Type")
            rate = validate_numeric(self.rate_entry.get(), "Nightly Rate", allow_decimal=True, positive_only=True)
            status = self.status_cb.get()
            add_room(room_id, room_type, rate, status)
            messagebox.showinfo("Success", f"Room {room_id} added!", parent=self)
            self.refresh_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Room Error", str(e), parent=self)"""

"""#---- 4. Add Guest Popup (Requires add_guest() in Section 1) ----
class AddGuestPopup(tk.Toplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.title("Register New Guest")
        self.geometry("380x260")
        self.config(background="#81C1EB", padx=20, pady=20)
        self.resizable(False, False)
        self.grab_set()
        self.refresh_callback = refresh_callback

        tk.Label(self, text="Register Guest", font=("Arial", 16, "bold"), bg="#81C1EB").pack(pady=(0, 15))

        form = tk.Frame(self, bg="#81C1EB")
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Full Name:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(form)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(form, text="Phone:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.phone_entry = tk.Entry(form)
        self.phone_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(form, text="Email:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.email_entry = tk.Entry(form)
        self.email_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        ttk.Button(self, text="Register Guest", command=self.save_guest, style="btn_style.TButton").pack(pady=15)

    def save_guest(self):
        try:
            name = validate_not_empty(self.name_entry.get(), "Guest Name")
            phone = validate_not_empty(self.phone_entry.get(), "Phone")
            email = self.email_entry.get().strip()
            guest = add_guest(name, phone, email)
            messagebox.showinfo("Success", f"Guest {guest['name']} ({guest['guest_id']}) registered!", parent=self)
            self.refresh_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Guest Error", str(e), parent=self)"""

"""#---- 5. Add Staff Popup (Requires add_staff() in Section 1) ----
class AddStaffPopup(tk.Toplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.title("Add Staff Member")
        self.geometry("380x290")
        self.config(background="#81C1EB", padx=20, pady=20)
        self.resizable(False, False)
        self.grab_set()
        self.refresh_callback = refresh_callback

        tk.Label(self, text="Add Staff Account", font=("Arial", 16, "bold"), bg="#81C1EB").pack(pady=(0, 15))

        form = tk.Frame(self, bg="#81C1EB")
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Full Name:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(form)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(form, text="Role:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.role_cb = ttk.Combobox(form, values=sorted(list(VALID_ROLES)), state="readonly")
        self.role_cb.set("Receptionist")
        self.role_cb.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(form, text="Username:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.user_entry = tk.Entry(form)
        self.user_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(form, text="Password:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        self.pass_entry = tk.Entry(form, show="*")
        self.pass_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        ttk.Button(self, text="Save Staff", command=self.save_staff, style="btn_style.TButton").pack(pady=15)

    def save_staff(self):
        try:
            name = validate_not_empty(self.name_entry.get(), "Full Name")
            role = validate_not_empty(self.role_cb.get(), "Role")
            username = validate_not_empty(self.user_entry.get(), "Username")
            password = validate_not_empty(self.pass_entry.get(), "Password")
            member = add_staff(name, role, username, password)
            messagebox.showinfo("Success", f"Staff {member['name']} ({member['staff_id']}) added!", parent=self)
            self.refresh_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Staff Error", str(e), parent=self)"""


# ---- Welcome Screen -------------------------------------------------
class WelcomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, background="#81C1EB")
        self.columnconfigure(0, weight=1)
        for a in range(3):
            if a != 1:
                self.rowconfigure(a, weight=1, uniform="equal_cols")

        label = tk.Label(
            self,
            text="Welcome To The Universal Hotel\nReservation Management System",
            font=("Arial", 40, "bold"),
            fg="black",
            bg="#81c1eb",
            padx=50,
            pady=30,
        )
        label.grid(row=0, column=0, sticky="n")

        button_container = tk.Frame(self, background="black")
        button_container.grid(row=1, column=0, padx=3, pady=(0, 5))

        button_start = ttk.Button(
            button_container,
            text="OPEN",
            command=lambda: open_home(controller),
            style="btn_style.TButton",
        )
        button_start.pack(padx=2, pady=2)


# ---- Home / Login Screen --------------------------------------------
class HomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, background="#81C1EB")
        self.columnconfigure(0, weight=1)
        for a in range(3):
            if a != 1:
                self.rowconfigure(a, weight=1, uniform="equal_cols")

        label = tk.Label(
            self,
            text="Welcome To The Universal Hotel\nReservation Management System",
            font=("Arial", 40, "bold"),
            fg="black",
            bg="#81c1eb",
            padx=50,
            pady=30,
        )
        label.grid(row=0, column=0, sticky="n")

        input_box = tk.Frame(self, background="#3678A5")
        input_box.grid(row=1, column=0, sticky="ns")

        tk.Label(
            input_box, text="Username", bg="#3678A5", font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=3, pady=3)
        _inputUser = tk.Entry(input_box, font=("Arial", 11))
        _inputUser.grid(row=1, column=0, padx=3, pady=3)

        tk.Label(
            input_box, text="Password", bg="#3678A5", font=("Arial", 11, "bold")
        ).grid(row=2, column=0, padx=3, pady=3)
        _inputKey = tk.Entry(input_box, show="*", font=("Arial", 11))
        _inputKey.grid(row=3, column=0, padx=3, pady=3)

        button_container = tk.Frame(self, background="#81c1eb")
        button_container.grid(row=2, column=0, padx=3, pady=(0, 5))

        submit_outline = tk.Frame(button_container, background="black")
        submit_outline.pack(pady=(0, 10))
        button_submit = ttk.Button(
            submit_outline,
            text="SUBMIT",
            command=lambda: submit_login(_inputUser, _inputKey, controller),
            style="btn_style.TButton",
        )
        button_submit.pack(padx=2, pady=2)

        exit_outline = tk.Frame(button_container, background="black")
        exit_outline.pack()
        button_exit = ttk.Button(
            exit_outline,
            text="EXIT",
            command=lambda: exit_to_welcome(controller),
            style="btn_style.TButton",
        )
        button_exit.pack(padx=2, pady=2)


# ---- Main Dashboard Screen ------------------------------------------
class MainFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, background="#81C1EB")
        self.controller = controller
        self.current_view = "reservations"

        self.columnconfigure(0, weight=0, minsize=220)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        sidebar = tk.Frame(self, background="#005b96", padx=15, pady=20)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.columnconfigure(0, weight=1)

        tk.Label(
            sidebar,
            text="UNIVERSAL\nHOTEL",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#005b96",
            justify="center",
        ).grid(row=0, column=0, pady=(0, 30))

        nav_items = [
            ("Reservations", self.show_reservations),
            ("Room Status", self.show_rooms),
            ("Guest Directory", self.show_guests),
            # ("Staff Directory", self.show_staff),  # Uncomment when staff view is needed
        ]

        for idx, (text, command) in enumerate(nav_items, start=1):
            btn_frame = tk.Frame(sidebar, background="black")
            btn_frame.grid(row=idx, column=0, sticky="ew", pady=6)
            btn_frame.columnconfigure(0, weight=1)

            nav_btn = ttk.Button(
                btn_frame, text=text, command=command, style="btn_style.TButton"
            )
            nav_btn.grid(row=0, column=0, sticky="ew", padx=1, pady=1)

        sidebar.rowconfigure(10, weight=1)

        logout_outline = tk.Frame(sidebar, background="black")
        logout_outline.grid(row=11, column=0, sticky="ew", pady=(20, 0))
        logout_outline.columnconfigure(0, weight=1)

        logout_btn = ttk.Button(
            logout_outline,
            text="LOGOUT",
            command=lambda: exit_to_welcome(self.controller),
            style="btn_style.TButton",
        )
        logout_btn.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

    def _build_main_area(self):
        self.content_area = tk.Frame(self, background="#81C1EB", padx=25, pady=20)
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.columnconfigure(0, weight=1)
        self.content_area.rowconfigure(2, weight=1)

        self.section_title = tk.Label(
            self.content_area,
            text="Reservations Overview",
            font=("Arial", 26, "bold"),
            fg="black",
            bg="#81C1EB",
            anchor="w",
        )
        self.section_title.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        # Action Bar
        action_bar = tk.Frame(self.content_area, background="#81C1EB")
        action_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        actions = [
            ("Check Out Room", self.handle_checkout),
            ("Export Bookings CSV", self.handle_export_bookings),
            ("Occupancy Report", self.handle_occupancy_report),
            # ---- Uncomment below to enable popup form buttons ----
            # ("+ New Booking", self.open_booking_popup),
            # ("Maintenance / Status", self.open_maintenance_popup),
            # ("+ Add Room", self.open_add_room_popup),
            # ("+ Add Guest", self.open_add_guest_popup),
            # ("+ Add Staff", self.open_add_staff_popup),,
        ]

        for idx, (label, cmd) in enumerate(actions):
            outline = tk.Frame(action_bar, background="black")
            outline.grid(row=0, column=idx, padx=(0, 8), pady=2)
            ttk.Button(
                outline, text=label, command=cmd, style="btn_style.TButton"
            ).pack(padx=1, pady=1)

        # Treeview Table
        table_frame = tk.Frame(self.content_area, background="black", bd=1)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, show="headings", style="Hotel.Treeview")
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.show_reservations()

    def _configure_columns(self, col_defs):
        self.tree["columns"] = list(col_defs.keys())
        for col, (title, width) in col_defs.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="center")

    def _populate_table(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert("", "end", values=row)

    def show_reservations(self):
        self.current_view = "reservations"
        self.section_title.config(text="Reservations Overview")
        self._configure_columns(
            {
                "id": ("Booking ID", 90),
                "guest": ("Guest Name", 160),
                "room": ("Room ID", 80),
                "checkin": ("Check-In", 100),
                "checkout": ("Check-Out", 100),
                "nights": ("Nights", 60),
                "total": ("Total ($)", 90),
            }
        )
        rows = []
        for b in bookings:
            guest = find_guest(b["guest_id"])
            g_name = guest["name"] if guest else b["guest_id"]
            rows.append(
                (
                    b["booking_id"],
                    g_name,
                    b["room_id"],
                    b["check_in"],
                    b["check_out"],
                    b["nights"],
                    f"${b['total']:.2f}",
                )
            )
        self._populate_table(rows)

    def show_rooms(self):
        self.current_view = "rooms"
        self.section_title.config(text="Room Inventory & Status")
        self._configure_columns(
            {
                "room_id": ("Room ID", 100),
                "type": ("Room Type", 140),
                "rate": ("Nightly Rate", 120),
                "status": ("Status", 160),
            }
        )
        rows = [
            (r["room_id"], r["type"], f"${r['rate']:.2f}", r["status"]) for r in rooms
        ]
        self._populate_table(rows)

    def show_guests(self):
        self.current_view = "guests"
        self.section_title.config(text="Registered Guests")
        self._configure_columns(
            {
                "guest_id": ("Guest ID", 100),
                "name": ("Full Name", 180),
                "phone": ("Phone", 130),
                "email": ("Email", 180),
            }
        )
        rows = [
            (g["guest_id"], g["name"], g.get("phone", "—"), g.get("email", "—"))
            for g in guests
        ]
        self._populate_table(rows)

    """# ---- Uncomment when Staff Directory view is enabled ----
     def show_staff(self):
         self.current_view = "staff"
         self.section_title.config(text="Staff Directory")
         self._configure_columns(
             {
                 "staff_id": ("Staff ID", 100),
                 "name": ("Full Name", 180),
                 "role": ("Role", 140),
                 "username": ("Username", 140),
             }
         )
         rows = [
             (s.get("staff_id", "—"), s.get("name", "—"), s.get("role", "—"), s.get("username", "—"))
             for s in staff
         ]
         self._populate_table(rows)"""

    """# ---- Popup Launchers (Uncomment along with the popup classes above) ----
     def open_booking_popup(self):
         NewBookingPopup(self, self.show_reservations)
    
     def open_maintenance_popup(self):
         selected = self.tree.selection()
         preselect = ""
         if selected:
             vals = self.tree.item(selected[0], "values")
             preselect = vals[2] if self.current_view == "reservations" else (vals[0] if self.current_view == "rooms" else "")
         MaintenancePopup(self, self.show_rooms, preselect_room=preselect)
    
     def open_add_room_popup(self):
         AddRoomPopup(self, self.show_rooms)
    
     def open_add_guest_popup(self):
         AddGuestPopup(self, self.show_guests)
    
     def open_add_staff_popup(self):
         AddStaffPopup(self, self.show_staff)"""

    def handle_checkout(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a row first.")
            return

        values = self.tree.item(selected[0], "values")
        room_id = values[2] if self.current_view == "reservations" else values[0]

        try:
            check_out(room_id)
            messagebox.showinfo(
                "Success", f"Room {room_id} checked out and marked Available."
            )
            (
                self.show_reservations()
                if self.current_view == "reservations"
                else self.show_rooms()
            )
        except ValueError as e:
            messagebox.showerror("Check-Out Error", str(e))

    def handle_export_bookings(self):
        result = export_bookings_to_csv()
        if result:
            messagebox.showinfo("Export Complete", f"Bookings exported to {result}")
        else:
            messagebox.showerror("Export Failed", "Could not save CSV file.")

    def handle_occupancy_report(self):
        rep = generate_occupancy_report()
        msg = (
            f"Total Rooms: {rep['total']}\n"
            f"Occupied: {rep['occupied']}\n"
            f"Available: {rep['available']}\n"
            f"Under Maintenance: {rep['maintenance']}\n"
            f"Occupancy Rate: {rep['rate']}%"
        )
        messagebox.showinfo("Occupancy Report", msg)


# ---- Main Application Controller ------------------------------------
class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hotel Reservation Management System")
        self.geometry("1050x550")
        self.config(background="#81C1EB")

        load_data()
        configure_styles()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.frames = {}
        for ScreenClass in (WelcomeFrame, HomeFrame, MainFrame):
            frame = ScreenClass(parent=self, controller=self)
            self.frames[ScreenClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("WelcomeFrame")

    def show_frame(self, screen_name):
        frame = self.frames[screen_name]
        if screen_name == "MainFrame":
            frame.show_reservations()
        frame.tkraise()


# =====================================================================
# SECTION 3: REPORTS & CSV EXPORT (Tean Thomas)
# =====================================================================

import csv


# --------- Occupancy Report -------------------------------------------
def generate_occupancy_report():
    total_rooms = len(rooms)
    occupied = 0
    maintenance = 0
    for r in rooms:
        if r["status"] == "Occupied":
            occupied = occupied + 1
        elif r["status"] == "Under Maintenance":
            maintenance = maintenance + 1

    available = total_rooms - occupied - maintenance
    if total_rooms > 0:
        rate = occupied / total_rooms * 100
    else:
        rate = 0

    print("Total rooms:", total_rooms)
    print("Occupied rooms:", occupied)
    print("Available rooms:", available)
    print("Rooms under maintenance:", maintenance)
    print("Occupancy rate:", round(rate, 2), "%")
    return {
        "total": total_rooms,
        "occupied": occupied,
        "available": available,
        "maintenance": maintenance,
        "rate": round(rate, 2),
    }


# --------- Revenue Report ---------------------------------------------
def generate_revenue_report():
    total = 0
    for b in bookings:
        total = total + b["total"]
        print("Total Bookings:", len(bookings))
        print("Total Revenue: $" + str(total))

    by_type = {}
    for b in bookings:
        room = find_rooms(b["rooms_id"])
        if room:
            t = room["type"]
        else:
            t = "Unknown"
            if t in by_type:
                by_type[t] = by_type[t] + b["total"]
            else:
                by_type[t] = b["total"]
        for t in by_type:
            print(t, ": $", by_type[t])
        return by_type


# --------- Full bookings report----------------------------------------
def generate_bookings_report():
    print("FULL BOOKINGS REPORT")
    print()
    if len(bookings) == 0:
        print("No bookings found.")
        return []
    for b in bookings:
        print("--------------------------------")
        print("Booking ID:", b["booking_id"])
        print("Guest ID:", b["guest_id"])
        print("Room ID:", b["room_id"])
        print("Check In:", b["check_in"])
        print("Check Out:", b["check_out"])
        print("Nights:", b["nights"])
        print("Total: $", b["total"])
        print("--------------------------------")
        print("Total Bookings:", len(bookings))
        return bookings


# ---------- Export Bookings to csv ---------------------------------------
def export_bookings_to_csv(filename="bookings_report.csv"):
    try:
        f = open(filename, "w", newline="", encoding="utf-8")
        writer = csv.writer(f)
        writer.writerow(
            [
                "Booking ID",
                "Guest ID",
                "Guest Name",
                "Room ID",
                "Room Type",
                "Check In",
                "Check Out",
                "Nights",
                "Total",
            ]
        )
        for b in bookings:
            guest = find_guest(b["guest_id"])
            if guest:
                guest_name = guest["name"]
            else:
                guest_name = "Unknown"
            room = find_room(b["room_id"])
            if room:
                room_type = room["type"]
            else:
                room_type = "Unknown"
            writer.writerow(
                [
                    b["booking_id"],
                    b["guest_id"],
                    b["guest_name"],
                    b["room_id"],
                    b["room_type"],
                    b["check_in"],
                    b["check_out"],
                    b["nights"],
                    b["total"],
                ]
            )
        f.close()
        print("Bookings report saved to", filename)
        return filename
    except OSError as e:
        print("File could not be saved:", e)
        return None


# ----------- Export Occupancy to csv ------------------------------------
def export_occupancy_to_csv(filename="occupancy_report.csv"):
    try:
        f = open(filename, "w", newline="", encoding="utf-8")
        writer = csv.writer(f)
        writer.writerow(
            ["total_rooms", "occupied", "available", "maintenance", "occupancy_rate"]
        )
        writer.writerow(
            [
                report["total"],
                report["occupied"],
                report["available"],
                report["maintenance"],
                report["rate"],
            ]
        )
        f.close()
        print("Occupancy report saved to", filename)
        return filename
    except OSError as e:
        print("File could not be saved:", e)
>>>>>>> 7f19f9dc89ff0412ed4ce9625664109fbbc4ce39
        return None


if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()
