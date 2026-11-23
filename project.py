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
        f = open(filename, "w", newline="", encoding="utf-8")
        writer = csv.writer(f)
        writer.writerow([
            "Booking ID",
            "Guest ID",
            "Guest Name",
            "Room ID",
            "Room Type",
            "Check In", 
            "Check Out",
            "Nights",
            "Total"
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
                b["guest_id"],
                b["guest_name"],
                b["room_id"],
                b["room_type"],
                b["check_in"],
                b["check_out"],
                b["nights"],
                b["total"]
            ])
        f.close()
        print("Bookings report saved to", filename)
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
        writer.writerow ([
            report["total"],
            report["occupied"],
            report["available"],
            report["maintenance"],
            report["rate"]
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
    # This will eventually start Domanick's GUI
    pass


