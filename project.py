"""
CNS1001 Project 2 — Hotel Reservation Management System (HRS)
Data Layer & Business Logic (Darien Henry)
"""
import json
import os
import sys
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


VALID_ROOM_TYPES = {"Single", "Double", "Suite"}
VALID_STATUSES = {"Available", "Occupied", "Under Maintenance"}
VALID_ROLES = {"Receptionist", "Housekeeping", "Manager"}


# ---- File path resolution -----------------------------------------
def get_data_path(filename: str = "hotel_data.json") -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


# ---- Persistence ---------------------------------------------------
def load_data() -> None:
    global rooms, guests, staff, bookings
    path = get_data_path()
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        rooms = payload.get("rooms", [])
        guests = payload.get("guests", [])
        staff = payload.get("staff", [])
        bookings = payload.get("bookings", [])
    except (json.JSONDecodeError, OSError, ValueError) as e:
        print(f"[load_data] could not read data file: {e}")
        rooms, guests, staff, bookings = [], [], [], []


def save_data() -> bool:
    payload = {"rooms": rooms, "guests": guests, "staff": staff, "bookings": bookings}
    try:
        with open(get_data_path(), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except OSError as e:
        print(f"[save_data] could not write data file: {e}")
        return False


# ---- Auto-ID generation -------------------------------------------
def next_id(prefix: str, items: list, key: str) -> str:
    highest = 0
    for item in items:
        ident = item.get(key, "")
        if ident.startswith(prefix):
            try:
                number = int(ident[len(prefix):])
                if number > highest:
                    highest = number
            except ValueError:
                continue
    return f"{prefix}{highest + 1:03d}"


# ---- Lookup helpers -----------------------------------------------
def find_room(room_id: str):
    for r in rooms:
        if r["room_id"] == room_id:
            return r
    return None


def find_guest(guest_id: str):
    for g in guests:
        if g["guest_id"] == guest_id:
            return g
    return None


def find_booking(booking_id: str):
    for b in bookings:
        if b["booking_id"] == booking_id:
            return b
    return None


def find_active_booking_for_room(room_id: str):
    for b in bookings:
        if b["room_id"] == room_id:
            room = find_room(room_id)
            if room and room["status"] == "Occupied":
                return b
    return None


# ---- Booking logic -------------------------------------------------
def calculate_booking_cost(room_id: str, check_in: str, check_out: str):
    room = find_room(room_id)
    if room is None:
        raise ValueError("Room not found.")
    try:
        d_in = datetime.strptime(check_in, "%Y-%m-%d")
        d_out = datetime.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Dates must be in YYYY-MM-DD format.")
    if d_out <= d_in:
        raise ValueError("Check-out must be after check-in.")
    nights = (d_out - d_in).days
    total = round(nights * float(room["rate"]), 2)
    return nights, total


def create_booking(guest_id: str, room_id: str, check_in: str, check_out: str):
    if find_guest(guest_id) is None:
        raise ValueError("Guest not found.")
    room = find_room(room_id)
    if room is None:
        raise ValueError("Room not found.")
    if room["status"] != "Available":
        raise ValueError(f"Room {room_id} is not available (status: {room['status']}).")
    nights, total = calculate_booking_cost(room_id, check_in, check_out)
    booking = {
        "booking_id": next_id("B", bookings, "booking_id"),
        "guest_id": guest_id,
        "room_id": room_id,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "total": total,
    }
    bookings.append(booking)
    room["status"] = "Occupied"
    save_data()
    return booking


def check_out(room_id: str):
    room = find_room(room_id)
    if room is None:
        raise ValueError("Room not found.")
    if room["status"] != "Occupied":
        raise ValueError(f"Room {room_id} is not currently occupied.")
    active = find_active_booking_for_room(room_id)
    if active is None:
        raise ValueError("No active booking found for this room.")
    room["status"] = "Available"
    save_data()
    return active


def update_room_status(room_id: str, new_status: str):
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
    room = find_room(room_id)
    if room is None:
        raise ValueError("Room not found.")
    if room["status"] == new_status:
        raise ValueError(f"Room {room_id} is already marked as '{new_status}'.")
       
    # --- MOVED THIS CHECK UP ---
    if new_status == "Available" and find_active_booking_for_room(room_id):
        raise ValueError("Cannot mark as Available. Room has an active booking.")
       
    # --- ADDED THIS CHECK (Maintenance can't be set if occupied) ---
    if new_status == "Under Maintenance" and room["status"] == "Occupied":
        raise ValueError(f"Cannot set to Maintenance. Room {room_id} is currently Occupied.")
    # ----------------------------


    room["status"] = new_status
    save_data()
    return True


# =====================================================================
# SECTION 2: GUI & VALIDATION (Domanick McFarlane)
# =====================================================================
# Domanick: Build your Tkinter windows, dashboard, and forms down here.
# Call the functions from Section 1. Use try/except to catch ValueErrors
# and show them in a messagebox.showerror().

attempt_count = 1


# ---- Validation & Input Helpers -------------------------------------
def validate_login(info, controller):
    global attempt_count
    try:
        name = validate_not_empty(info[0], "Username")
        key = validate_not_empty(info[1], "Password")
    except ValueError as e:
        messagebox.showerror(title="INPUT ERROR", message=str(e))
        return

    # Check against the global `staff` list from Section 1
    authenticated = False
    for member in staff:
        staff_user = str(
            member.get("username") or member.get("name") or member.get("staff_id", "")
        ).strip()
        staff_pass = str(
            member.get("password") or member.get("pin") or member.get("staff_id", "")
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

'''# ---- 1. New Booking Popup (Uses existing create_booking & calculate_booking_cost) ----
 class NewBookingPopup(tk.Toplevel):
     def __init__(self, parent, refresh_callback):
         super().__init__(parent)
         self.title("New Reservation")
         self.geometry("400x360")
         self.config(background="#81C1EB", padx=20, pady=20)
         self.resizable(False, False)
         self.grab_set()
         self.refresh_callback = refresh_callback

         tk.Label(self, text="Create New Booking", font=("Arial", 16, "bold"), bg="#81C1EB").pack(pady=(0, 15))

         form = tk.Frame(self, bg="#81C1EB")
         form.pack(fill="x")
         form.columnconfigure(1, weight=1)

         tk.Label(form, text="Guest ID:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
         guest_choices = [f"{g['guest_id']} - {g['name']}" for g in guests]
         self.guest_cb = ttk.Combobox(form, values=guest_choices, state="readonly")
         self.guest_cb.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

         tk.Label(form, text="Available Room:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
         room_choices = [f"{r['room_id']} ({r['type']} - ${r['rate']})" for r in rooms if r["status"] == "Available"]
         self.room_cb = ttk.Combobox(form, values=room_choices, state="readonly")
         self.room_cb.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

         tk.Label(form, text="Check-In (YYYY-MM-DD):", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
         self.checkin_entry = tk.Entry(form)
         self.checkin_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

         tk.Label(form, text="Check-Out (YYYY-MM-DD):", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
         self.checkout_entry = tk.Entry(form)
         self.checkout_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

         self.cost_label = tk.Label(self, text="Estimated Total: $0.00", font=("Arial", 11, "bold"), bg="#81C1EB", fg="#005b96")
         self.cost_label.pack(pady=10)

         btn_row = tk.Frame(self, bg="#81C1EB")
         btn_row.pack(pady=5)
         ttk.Button(btn_row, text="Calculate Cost", command=self.preview_cost, style="btn_style.TButton").pack(side="left", padx=5)
         ttk.Button(btn_row, text="Confirm Booking", command=self.save_booking, style="btn_style.TButton").pack(side="left", padx=5)

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
             nights, total = calculate_booking_cost(room_id, self.checkin_entry.get().strip(), self.checkout_entry.get().strip())
             self.cost_label.config(text=f"Estimated Total: ${total:.2f} ({nights} night{'s' if nights != 1 else ''})")
         except ValueError as e:
             messagebox.showerror("Calculation Error", str(e), parent=self)

     def save_booking(self):
         try:
             guest_id, room_id = self._get_selected_ids()
             validate_guest_exists(guest_id)
             validate_availability(room_id)
             validate_date_range(self.checkin_entry.get(), self.checkout_entry.get())
             booking = create_booking(guest_id, room_id, self.checkin_entry.get().strip(), self.checkout_entry.get().strip())
             messagebox.showinfo("Booking Confirmed", f"Booking {booking['booking_id']} created! Total: ${booking['total']:.2f}", parent=self)
             self.refresh_callback()
             self.destroy()
         except ValueError as e:
             messagebox.showerror("Booking Error", str(e), parent=self)


 #---- 2. Maintenance / Update Room Status Popup (Uses existing update_room_status) ----
 class MaintenancePopup(tk.Toplevel):
     def __init__(self, parent, refresh_callback, preselect_room=""):
         super().__init__(parent)
         self.title("Update Room Status / Maintenance")
         self.geometry("380x240")
         self.config(background="#81C1EB", padx=20, pady=20)
         self.resizable(False, False)
         self.grab_set()
         self.refresh_callback = refresh_callback

         tk.Label(self, text="Room Status & Maintenance", font=("Arial", 15, "bold"), bg="#81C1EB").pack(pady=(0, 15))

         form = tk.Frame(self, bg="#81C1EB")
         form.pack(fill="x")
         form.columnconfigure(1, weight=1)

         tk.Label(form, text="Select Room:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
         room_ids = [r["room_id"] for r in rooms]
         self.room_cb = ttk.Combobox(form, values=room_ids, state="readonly")
         if preselect_room in room_ids:
             self.room_cb.set(preselect_room)
         self.room_cb.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))

         tk.Label(form, text="New Status:", bg="#81C1EB", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
         self.status_cb = ttk.Combobox(form, values=sorted(list(VALID_STATUSES)), state="readonly")
         self.status_cb.set("Under Maintenance")
         self.status_cb.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))

         ttk.Button(self, text="Update Status", command=self.apply_status, style="btn_style.TButton").pack(pady=15)

     def apply_status(self):
         try:
             room_id = validate_not_empty(self.room_cb.get(), "Room ID")
             new_status = validate_not_empty(self.status_cb.get(), "Status")
             update_room_status(room_id, new_status)
             messagebox.showinfo("Updated", f"Room {room_id} status changed to '{new_status}'.", parent=self)
             self.refresh_callback()
             self.destroy()
         except ValueError as e:
             messagebox.showerror("Status Error", str(e), parent=self)


 #---- 3. Add Room Popup (Requires add_room() in Section 1) ----
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
             messagebox.showerror("Room Error", str(e), parent=self)


 #---- 4. Add Guest Popup (Requires add_guest() in Section 1) ----
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
             messagebox.showerror("Guest Error", str(e), parent=self)


 #---- 5. Add Staff Popup (Requires add_staff() in Section 1) ----
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
             messagebox.showerror("Staff Error", str(e), parent=self)'''


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

        button_outline = tk.Frame(self, background="black")
        button_outline.grid(row=1, column=0, padx=3, pady=(0, 5))

        button_start = ttk.Button(
            button_outline,
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

        input_box = tk.Frame(self, background="#81C1EB")
        input_box.grid(row=1, column=0, sticky="ns")

        tk.Label(
            input_box, text="Username", bg="#81C1EB", font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=3, pady=3)
        _inputUser = tk.Entry(input_box, font=("Arial", 11))
        _inputUser.grid(row=1, column=0, padx=3, pady=3)

        tk.Label(
            input_box, text="Password", bg="#81C1EB", font=("Arial", 11, "bold")
        ).grid(row=2, column=0, padx=3, pady=3)
        _inputKey = tk.Entry(input_box, show="*", font=("Arial", 11))
        _inputKey.grid(row=3, column=0, padx=3, pady=3)

        button_outline = tk.Frame(self, background="black")
        button_outline.grid(row=2, column=0, padx=3, pady=(0, 5))

        button_submit = ttk.Button(
            button_outline,
            text="SUBMIT",
            command=lambda: submit_login(_inputUser, _inputKey, controller),
            style="btn_style.TButton",
        )
        button_submit.pack(padx=2, pady=2)

        button_exit = ttk.Button(
            button_outline,
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
            ''' ("+ New Booking", self.open_booking_popup),
             ("Maintenance / Status", self.open_maintenance_popup),
             ("+ Add Room", self.open_add_room_popup),
             ("+ Add Guest", self.open_add_guest_popup),
             ("+ Add Staff", self.open_add_staff_popup),'''
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

    ''' ---- Uncomment when Staff Directory view is enabled ----
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
         self._populate_table(rows)

     ---- Popup Launchers (Uncomment along with the popup classes above) ----
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
         AddStaffPopup(self, self.show_staff)'''

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

#--------- Occupancy Report -------------------------------------------
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
    "rate": round(rate, 2)
}


#--------- Revenue Report ---------------------------------------------
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


#--------- Full bookings report----------------------------------------
def generate_bookings_report():
    print("FULL BOOKINGS REPORT")
    print()
    if len(bookings) ==0:
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


#---------- Export Bookings to csv ---------------------------------------
def export_bookings_to_csv(filename="bookings_report.csv"):
    try:
    f = open (filename, "w", newline="", encoding="utf-8")
    writer = csv.writer(f)
    writer.writerow([ 
        "booking_id",
        "guest_id",
        "guest_name",
        "room_id",
        "room_type",
        "check_in",
        "check_out",
        "nights",
        "total"
    ])
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
        writer.writerow([
            b["booking_id"],
            name,
            b["guest_id"],
            guest_name,
            b["room_id"],
            room_type,
            b["check_in"],
            b["check_out"],
            b["nights"],
            b["total"]
        ])
    f.close()
    print("Bookings saved to", filename) 
    return filename 
except OSError as e:
    print("File could not be saved:", e) 
    return None 


#----------- Export Occupancy to csv ------------------------------------
def export_occupancy_to_csv(filename="occupancy_report.csv"):
    try:
        f = open(filename, "w", newline   ="", encoding="utf-8")
        writer = csv.writer(f)
        writer.writerow([
            "total_rooms",
            "occupied",
            "available",
            "maintenance",
            "occupancy_rate"
        ])
        writer.writerow([
            report["total"],
            report["occupied"],
            report["available"],
            report["maintenance"],
            report["rate"
        ])
        f.close()
        print("Occupancy report saved to", filename)
        return filename
except OSError as e:
    print("File could not be saved:", e)
    return None



# =====================================================================
# MAIN EXECUTION
# =====================================================================
if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()


