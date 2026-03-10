from tkinter import *
from tkinter import messagebox
from datetime import datetime
from tkcalendar import DateEntry
import mysql.connector
import os

# ---------------- WINDOW ----------------
root = Tk()
root.title("Travel Agency Reservation System")
root.geometry("900x720")

# ---------------- DATABASE ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="travel_agency"
)
cursor = db.cursor(buffered=True)

# ---------------- VARIABLES ----------------
bus_var = StringVar(value="1")
seat_var = IntVar(value=0)
name_var = StringVar()
sex_var = StringVar(value="M")
age_var = IntVar()

seat_buttons = {}

# ---------------- DATE FUNCTIONS ----------------
def get_ui_date():
    return date_entry.get()

def get_db_date():
    ui_date = datetime.strptime(get_ui_date(), "%d-%m-%Y")
    return ui_date.strftime("%Y-%m-%d")

# ---------------- VALIDATION ----------------
def validate():
    if not name_var.get().strip():
        messagebox.showerror("Error", "Enter passenger name")
        return False

    if sex_var.get() not in ("M", "F"):
        messagebox.showerror("Error", "Select gender")
        return False

    if age_var.get() <= 0 or age_var.get() > 100:
        messagebox.showerror("Error", "Invalid age")
        return False

    return True

# ---------------- LOAD SEATS ----------------
def load_seats():
    for btn in seat_buttons.values():
        btn.config(bg="lightgreen", state=NORMAL, relief=RAISED)

    cursor.execute(
        "SELECT seat_no FROM reservations WHERE bus_no=%s AND travel_date=%s",
        (bus_var.get(), get_db_date())
    )

    for (seat,) in cursor.fetchall():
        if seat in seat_buttons:
            seat_buttons[seat].config(bg="red", state=DISABLED)

    seat_var.set(0)

# ---------------- SELECT SEAT ----------------
def select_seat(no):
    seat_var.set(no)
    for btn in seat_buttons.values():
        if btn["state"] == NORMAL:
            btn.config(relief=RAISED)
    seat_buttons[no].config(relief=SUNKEN)

# ---------------- RESERVE ----------------
def reserve_seat():
    if not validate():
        return

    if seat_var.get() == 0:
        messagebox.showerror("Error", "Select a seat")
        return

    cursor.execute(
        "SELECT 1 FROM reservations WHERE bus_no=%s AND travel_date=%s AND seat_no=%s",
        (bus_var.get(), get_db_date(), seat_var.get())
    )
    if cursor.fetchone():
        messagebox.showerror("Error", "Seat already booked")
        return

    cursor.execute(
        "SELECT destination, depart_time, arrive_time, fare FROM buses WHERE bus_no=%s",
        (bus_var.get(),)
    )
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Error", "Bus not found")
        return

    dest, dep, arr, fare = row

    cursor.execute(
        """INSERT INTO reservations
        (bus_no, travel_date, seat_no, name, sex, age, fare)
        VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (
            bus_var.get(),
            get_db_date(),
            seat_var.get(),
            name_var.get().upper(),
            sex_var.get(),
            age_var.get(),
            fare
        )
    )
    db.commit()

    load_seats()
    display_ticket(dest, dep, arr, fare)
    clear_form()

# ---------------- DISPLAY TICKET ----------------
def display_ticket(dest, dep, arr, fare):
    text.config(state=NORMAL)
    text.delete("1.0", END)

    text.insert(END, f"""
=========================================
            RESERVATION TICKET
=========================================

Bus No      : {bus_var.get()}
Route       : DELHI → {dest}
Travel Date : {get_ui_date()}

Departure   : {dep}
Arrival     : {arr}

Seat No     : {seat_var.get()}
Passenger   : {name_var.get().upper()}
Gender      : {sex_var.get()}
Age         : {age_var.get()}

Fare        : Rs.{fare}

=========================================
      BOOKING CONFIRMED SUCCESSFULLY
=========================================
""")

    text.config(state=DISABLED)

# ---------------- PRINT ----------------
def print_ticket():
    ticket_content = text.get("1.0", END).strip()

    if not ticket_content:
        messagebox.showerror("Error", "No ticket to print")
        return

    try:
        with open("ticket.txt", "w", encoding="utf-8") as file:
            file.write(ticket_content)

        os.startfile("ticket.txt", "print")
    except Exception as e:
        messagebox.showerror("Error", f"Printing failed:\n{e}")

# ---------------- CLEAR ----------------
def clear_form():
    name_var.set("")
    sex_var.set("M")
    age_var.set(0)
    seat_var.set(0)

    for btn in seat_buttons.values():
        if btn["state"] == NORMAL:
            btn.config(relief=RAISED)

# ---------------- UI ----------------

Label(root, text="Travel Agency Reservation System",
      bg="black", fg="white", font=("Arial", 18, "bold")).pack(pady=10)

# Bus + Date
top = Frame(root)
top.pack(pady=5)

Label(top, text="Bus No").grid(row=0, column=0, padx=5)
OptionMenu(top, bus_var, "1", "2", "3").grid(row=0, column=1)

Label(top, text="Date").grid(row=0, column=2, padx=5)
date_entry = DateEntry(top, width=12,
                       background='darkblue',
                       foreground='white',
                       borderwidth=2,
                       date_pattern='dd-mm-yyyy')
date_entry.grid(row=0, column=3)

# Passenger Details
form = Frame(root)
form.pack(pady=10)

Label(form, text="Name").grid(row=0, column=0)
Entry(form, textvariable=name_var, width=20).grid(row=0, column=1)

Label(form, text="Gender").grid(row=1, column=0)
Radiobutton(form, text="Male", variable=sex_var, value="M").grid(row=1, column=1)
Radiobutton(form, text="Female", variable=sex_var, value="F").grid(row=1, column=2)

Label(form, text="Age").grid(row=0, column=3)
Spinbox(form, from_=1, to=100, textvariable=age_var, width=5).grid(row=0, column=4)

# Load Seats
Button(root, text="Load Seats", bg="blue", fg="white",
       command=load_seats).pack(pady=5)

# Seat Layout
seat_frame = Frame(root)
seat_frame.pack()

Label(seat_frame, text="Seat Layout (Green=Free, Red=Booked)",
      font=("Arial", 12)).grid(row=0, column=0, columnspan=8)

n = 1
for r in range(1, 6):
    for c in range(8):
        btn = Button(seat_frame, text=n, width=4, bg="lightgreen",
                     command=lambda x=n: select_seat(x))
        btn.grid(row=r, column=c, padx=3, pady=3)
        seat_buttons[n] = btn
        n += 1

# Actions
actions = Frame(root)
actions.pack(pady=10)

Button(actions, text="Reserve Seat", bg="green", fg="white",
       command=reserve_seat).grid(row=0, column=0, padx=10)

Button(actions, text="Print Ticket", bg="purple", fg="white",
       command=print_ticket).grid(row=0, column=1, padx=10)

# Ticket Display
ticket_frame = Frame(root)
ticket_frame.pack(pady=10)

scrollbar = Scrollbar(ticket_frame)
scrollbar.pack(side=RIGHT, fill=Y)

text = Text(ticket_frame, height=12, width=85,
            yscrollcommand=scrollbar.set)
text.pack(side=LEFT)

scrollbar.config(command=text.yview)

# Close Handler
def on_close():
    cursor.close()
    db.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
