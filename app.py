import os

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
            SELECT a.id, p.first_name || ' ' || p.last_name AS patient_name, 
                d.full_name AS doctor_name, d.specialty, 
                a.scheduled_date 
            FROM appointments a 
            JOIN patients p ON a.patient_id = p.id 
            JOIN users d ON a.doctor_id = d.id 
            WHERE DATE(a.scheduled_date) = DATE('now')
            ORDER BY a.scheduled_date ASC
            """
        )
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
    return render_template("new_patient.html")


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
