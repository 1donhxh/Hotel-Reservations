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


# =====================================================================
# SECTION 2: GUI & VALIDATION (Domanick McFarlane)
# =====================================================================
# Domanick: Build your Tkinter windows, dashboard, and forms down here.
# Call the functions from Section 1. Use try/except to catch ValueErrors
# and show them in a messagebox.showerror().






# =====================================================================
# SECTION 3: REPORTS & CSV EXPORT (Tean Thomas)
# =====================================================================
# Tean: Write your report generation and CSV export functions down here.






# =====================================================================
# MAIN EXECUTION
# =====================================================================
if __name__ == "__main__":
    # This will eventually start Domanick's GUI
    pass


