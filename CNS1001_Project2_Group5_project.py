"""CNS1001 Project 2 — Universal Hotel Reservation Management System (HRS).

Group 5 hotel reservation application.

Section 1: Data Layer & Business Logic — Darien Henry
Section 2: GUI & Validation — Domanick McFarlane
Section 3: Reports & CSV Export — Tean Thomas

First run creates 30 rooms (25 available, 5 under maintenance) and asks you
to create Manager and Receptionist accounts. Existing hotel_data.json records
are retained. Calendar selection uses built-in Tkinter; no external modules.
"""
import calendar
import csv
import hashlib
import hmac
import json
import math
import os
import secrets
import sys
import tempfile
from datetime import datetime, date, timedelta
from tkinter import messagebox, ttk
import tkinter as tk

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
        ident = str(item.get(key, ""))
        suffix = ident[len(prefix):] if ident.startswith(prefix) else ""
        if suffix.isdigit():
            highest = max(highest, int(suffix))
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
    previous = room["status"]
    if room.get("archived"):
        raise ValueError("Cannot update a removed room.")
    if previous == new_status:
        raise ValueError(f"Room is already marked {new_status}.")
    if find_active_booking_for_room(room_id):
        raise ValueError("Check out the active booking before changing the room status.")
    if new_status == "Occupied":
        raise ValueError("Use New Booking to mark a room Occupied.")
    room["status"] = new_status
    persist_or_rollback(lambda: room.__setitem__("status", previous))
    return True

# SECTION 2 — GUI & INPUT VALIDATION (Domanick McFarlane)

def configure_styles():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("btn_style.TButton", background="#52a4db", foreground="#101820",
                    font=("Arial", 12, "bold"), padding=(10, 8))
    style.map("btn_style.TButton", background=[("pressed", DARK), ("active", "#6497b1")])
    # Larger, bold labels for the nine dashboard actions and sidebar navigation.
    style.configure("Action.TButton", font=("Arial", 14, "bold"),
                    foreground="#101820", background="#52a4db", padding=(12, 12))
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
        return None


def main():
    """Launch the hotel reservation application and its Tkinter event loop."""
    app = HotelApp()
    app.mainloop()


if __name__ == "__main__":
    main()
