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
    return apology("Rol not found", 403)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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
