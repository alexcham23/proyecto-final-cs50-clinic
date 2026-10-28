import os
import re
from datetime import datetime

from cs50 import SQL
from flask import Flask, flash, g, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, role_required

# Configure application
app = Flask(__name__)

# Custom filter
#app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///clinicMedic.db")
app.extensions["db"] = db


@app.before_request
def load_current_user():
    """Load the current user from the database for this request."""
    g.user = None

    if session.get("user_id") is not None:
        rows = db.execute(
            "SELECT id, full_name, role FROM users WHERE id = ?",
            session["user_id"],
        )
        if rows:
            g.user = rows[0]


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show the dashboard for the current user's role."""
    dashboards = {
        "admin": "admin_dashboard.html",
        "receptionist": "receptionist_dashboard.html",
        "doctor": "doctor_dashboard.html",
    }

    template = dashboards.get(g.user["role"])
    if template is None:
        return apology("invalid user role", 403)

    if g.user["role"] == "admin":
        # Fetch all users for the admin dashboard
        total_patients = db.execute("SELECT COUNT(*) AS total FROM patients")[0]["total"]
        total_doctors = db.execute("SELECT COUNT(*) AS total FROM users WHERE role = 'doctor'")[0]["total"]
        total_appointments = db.execute("SELECT COUNT(*) AS total FROM appointments")[0]["total"]
        return render_template(template, patients=total_patients, doctors=total_doctors, appointments=total_appointments)
    elif g.user["role"] == "receptionist":
        # Fetch today's appointments for the receptionist dashboard
        today_appointments = db.execute(
            """
            SELECT a.id, a.scheduled_date, a.scheduled_time, a.status,
            p.first_name || ' ' || p.last_name AS patient_name,
            d.full_name AS doctor_name, d.specialty
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            JOIN users d ON a.doctor_id = d.id 
            ORDER BY a.scheduled_date ASC
            """
        )
        print(today_appointments)
        return render_template(template, appointments=today_appointments)
    return apology("Rol not found", 403)


# ==========================================
# Administration users management
# ==========================================
@app.route("/admin/users", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_users():
    """Buy shares of stock"""
    if request.method == "POST":
        # Get form data
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "").strip()
        specialty = request.form.get("specialty", "").strip() if role == "doctor" else None

        # Validate form data
        if not all([full_name, username, password, role]):
            return apology("All fields are required", 400)

        # Check if username already exists
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if existing_user:
            return apology("Username already exists", 400)

        if role == "doctor" and not specialty:
            return apology("All fields are required", 400)

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert new user into the database
        db.execute(
            "INSERT INTO users (full_name, username, hash, role, specialty) VALUES (?, ?, ?, ?, ?)",
            full_name,
            username,
            hashed_password,
            role,
            specialty,
        )
        flash(f"Usuario {full_name} creado exitosamente.", "success")
        return redirect("/admin/users")
    users_list = db.execute("SELECT id, full_name, username, role, specialty FROM users")
    return render_template("admin_users.html", users=users_list)


# ==========================================
# Receptionist management
# ==========================================

@app.route("/patients/new", methods=["GET", "POST"])
@login_required
@role_required("receptionist", "admin")
def new_patient():
    """Show history of transactions"""
    if request.method == "POST":
        # Get form data
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        # Validate form data
        if not all([first_name, last_name, phone]):
            return apology("All fields are required", 400)
        if not phone.isdigit() or len(phone) < 7:
            return apology("Invalid contact number", 400)
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return apology("Invalid email address", 400)

        # Insert new patient into the database
        db.execute(
            "INSERT INTO patients (first_name, last_name, phone, email) VALUES (?, ?, ?, ?)",
            first_name,
            last_name,
            phone,
            email,
        )
        flash(f"Paciente {first_name} {last_name} creado exitosamente.", "success")
        return redirect("/appointments/new")
    return render_template("patient_form.html")

@app.route("/appointments/new", methods=["GET", "POST"])
@login_required
@role_required("receptionist", "admin")
def new_appointment():
    """appointment form"""
    if request.method == "POST":
        # Get form data
        patient_id = request.form.get("patient_id", "")
        doctor_id = request.form.get("doctor_id", "")
        date = request.form.get("date", "")
        time = request.form.get("time", "")
        reason = request.form.get("reason", "").strip()

        # Validate form data
        if not all([patient_id, doctor_id, date, time, reason]):
            return apology("All fields are required", 400)

        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(time, "%H:%M").time()
        except ValueError:
            return apology("Invalid appointment date or time", 400)

        opening_time = datetime.strptime("09:00", "%H:%M").time()
        closing_time = datetime.strptime(
            "14:00" if appointment_date.weekday() == 5 else "16:00", "%H:%M"
        ).time()

        if appointment_date.weekday() == 6 or not (opening_time <= appointment_time <= closing_time):
            return apology(
                "Appointments are available Monday to Friday from 09:00 to 16:00 "
                "and Saturdays from 09:00 to 14:00.",
                400,
            )

        # validate conflict with existing appointments
        conflict = db.execute(
            "SELECT id FROM appointments WHERE doctor_id = ? AND scheduled_date = ? AND scheduled_time = ?",
            doctor_id, date, time
        )

        if len(conflict) > 0:
            return apology("The doctor is already booked for this time.", 400)
        # Insert new appointment into the database
        db.execute(
            "INSERT INTO appointments (patient_id, doctor_id, scheduled_date, scheduled_time, reason) VALUES (?, ?, ?, ?, ?)",
            patient_id, doctor_id,date,time, reason
        )

        flash(f"Cita programada exitosamente.", "success")
        return redirect("/")
    patients = db.execute("SELECT id, first_name || ' ' || last_name AS name FROM patients ORDER BY last_name")
    doctors = db.execute("SELECT id, full_name, specialty FROM users WHERE role = 'doctor' ORDER BY full_name")
    return render_template("appointment_form.html" , patients=patients, doctors=doctors)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], password
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["full_name"] = rows[0]["full_name"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")
