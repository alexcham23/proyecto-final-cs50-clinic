# CS50 MediCare — Medical Clinic Appointment System

#### Video Demo: https://youtu.be/CWl51ovbasA

#### Description:

CS50 MediCare is a web-based medical clinic management system built as the final project for Harvard's CS50x Introduction to Computer Science course. The application streamlines the day-to-day operations of a small medical clinic by providing a centralized platform where administrators, receptionists, and doctors can each carry out their specific responsibilities through a role-based access control system. The application was built using Python and the Flask web framework on the back end, SQLite as the database engine, and Bootstrap 5 on the front end for a clean and responsive user interface.

## Project Overview

The core problem this application solves is the fragmented, paper-based workflow that many small clinics still use to manage patients and appointments. By replacing manual processes with a digital system, CS50 MediCare allows clinic staff to:

- Register and look up patients quickly.
- Schedule, view, and manage medical appointments without double-bookings.
- Give doctors immediate visibility into their own appointment schedule.
- Allow an administrator to manage all system users (doctors and receptionists) from a single panel.

The system enforces strict role-based permissions so that each user type sees only the data and actions relevant to their job. A doctor cannot create patients, and a receptionist cannot attend appointments or view clinical notes written by other doctors. This separation of concerns mirrors how a real clinic operates and prevents accidental or unauthorized data modification.

## Design Decisions

### Role-Based Access Control (RBAC)

One of the most important design decisions made early in development was implementing a role-based access control system with three distinct roles: `admin`, `receptionist`, and `doctor`. An alternative approach would have been to build a single unified dashboard with visibility controlled purely by conditional rendering in the templates. However, this would have led to a single bloated template and would have made it trivially easy for a user to bypass UI-level restrictions by navigating directly to a URL.

Instead, the `role_required` decorator in `helpers.py` enforces access at the route level on the server side. Even if a receptionist knew the URL for the "attend appointment" page, the server would reject their request with a 403 Forbidden error. This server-side enforcement is more secure and easier to reason about than purely front-end access control.

### Session Storage on the Filesystem

Flask sessions are configured to use the filesystem (`flask_session`) rather than signed cookies. This means that session data such as the logged-in user's ID is stored on the server, and the client only holds a session token. This approach was chosen because it prevents session data from being tampered with on the client side and is more appropriate for a multi-user application where session state must be reliably controlled by the server.

### Appointment Conflict Validation

The application includes business-logic validation for appointment scheduling. Before inserting a new appointment into the database, the system checks whether the selected doctor already has an appointment at the exact same date and time. This prevents double-bookings at the database query level, providing a reliable safety net beyond what a front-end form might enforce. Additionally, the system enforces clinic operating hours: Monday through Friday from 09:00 to 16:00, and Saturdays from 09:00 to 14:00. Appointments on Sundays or outside these hours are rejected.

### Separate Dashboards Per Role

Rather than using one generic dashboard with conditional blocks, the project uses entirely separate HTML templates for each role (`admin_dashboard.html`, `receptionist_dashboard.html`, `doctor_dashboard.html`). This keeps each template focused, readable, and maintainable. The route logic in `app.py` selects the correct template based on `g.user["role"]`, keeping the server-side logic clean and the templates specialized.

## File Descriptions

### `app.py`

This is the main application file and the heart of the project. It initializes the Flask application, configures the session, and connects to the SQLite database using CS50's SQL library. It contains all route definitions:

- **`/` (index)**: The root route that acts as a smart dashboard dispatcher. Depending on the authenticated user's role, it queries the relevant data (total patients/doctors/appointments for admin; upcoming appointments for receptionist or doctor) and renders the appropriate dashboard template.
- **`/admin/users` (manage_users)**: Accessible only by admins. Handles creation of new system users (receptionists and doctors). On POST, it validates all form fields, checks for duplicate usernames, and stores a bcrypt-hashed password via Werkzeug's `generate_password_hash`.
- **`/patients/new` (new_patient)**: Accessible by receptionists and admins. Registers a new patient into the `patients` table after validating the phone number format and optionally the email format using a regular expression.
- **`/appointments/new` (new_appointment)**: Accessible by receptionists and admins. Schedules a new appointment after performing date/time parsing, business-hours validation, and a conflict check against existing appointments in the database.
- **`/appointments/<id>/attend` (attend_appointment)**: Accessible only by doctors. Allows a doctor to view the details of one of their scheduled appointments and update its status (to `completed` or `cancelled`) along with optional clinical notes.
- **`/login`** and **`/logout`**: Standard authentication routes. Login validates credentials against the stored password hash and stores the user ID in the session. Logout clears the session.

The file also includes two important hooks: `load_current_user` (a `before_request` hook that fetches the current user from the database and attaches it to Flask's `g` object) and `after_request` (which sets cache-control headers to prevent browsers from caching protected pages).

### `helpers.py`

This file contains three utility functions that are imported and used throughout `app.py`:

- **`apology(message, code)`**: Renders a user-friendly error page (`apology.html`) with a descriptive message and HTTP status code. This follows the CS50 finance project convention and provides a consistent error-handling UX across the entire application.
- **`login_required(f)`**: A Python decorator that wraps a route function and redirects unauthenticated users to `/login` before they can access a protected route.
- **`role_required(*allowed_roles)`**: A parametrized decorator factory that accepts one or more role names and returns a decorator. The inner decorator checks that the current user exists in `g.user` and that their role is in the list of allowed roles. If not, it returns a 403 Forbidden apology. This is the core of the RBAC system.

### `DDL.sql`

This file contains the SQL Data Definition Language (DDL) statements used to create the database schema. It defines three tables:

- **`users`**: Stores all system users (admins, receptionists, and doctors) with a `role` column constrained by a `CHECK` to only allow valid values. Doctors additionally store their `specialty`.
- **`patients`**: Stores patient records including first and last name, phone number, and optional email address.
- **`appointments`**: The central relational table that links a patient to a doctor for a specific date and time. It includes a `status` column (constrained to `scheduled`, `completed`, or `cancelled`) and a `notes` column for clinical notes added by the attending doctor.

The use of foreign keys between `appointments` and both `patients` and `users` ensures referential integrity across the dataset.

### `requirements.txt`

Lists the Python package dependencies required to run the application:

- **`cs50`**: The CS50 library, which provides a convenient `SQL` class for executing parameterized SQLite queries.
- **`Flask`**: The core web framework.
- **`Flask-Session`**: Extension that enables server-side session storage on the filesystem.
- **`pytz`**: Library for timezone-aware datetime handling.
- **`requests`**: HTTP library included as a dependency.

### `clinicMedic.db`

The SQLite database file that stores all persistent data for the application — users, patients, and appointments. It is generated from the schema defined in `DDL.sql`.

### `templates/` Directory

Contains all ten Jinja2 HTML templates rendered by Flask:

- **`layout.html`**: The base template that all other templates extend. It defines the `<head>`, navigation bar, flash message display area, main content block, and footer. The navigation bar dynamically renders links based on the logged-in user's role, ensuring that receptionists see patient/appointment links and admins additionally see the user management link.
- **`login.html`**: Simple login form with username and password fields.
- **`admin_dashboard.html`**: Displays summary statistics for the administrator — total registered patients, total doctors, and total appointments in the system.
- **`admin_users.html`**: Shows a table of all system users and a form to create a new user. The specialty field appears or disappears dynamically based on the selected role.
- **`receptionist_dashboard.html`**: Shows a table of all scheduled appointments ordered by date, including patient name, doctor name, specialty, and current status.
- **`doctor_dashboard.html`**: Displays the appointments assigned to the currently logged-in doctor, showing patient name, contact phone, appointment time, reason, and status.
- **`patient_form.html`**: Form for registering a new patient.
- **`appointment_form.html`**: Form for scheduling a new appointment. It dynamically loads all registered patients and available doctors from the database into dropdown selects.
- **`attend_appointment.html`**: Form that allows a doctor to view the full details of a specific appointment and submit clinical notes and a final status update.
- **`apology.html`**: A reusable error page template that displays a descriptive error message when something goes wrong.

### `static/` Directory

Contains static assets served directly to the browser:

- **`styles.css`**: Custom CSS rules that complement the Bootstrap framework, including brand color classes used in the navbar logo.
- **`favicon.ico`**: The browser tab icon for the application.
- **`I_heart_validator.png`**: An image button in the footer that submits the current page's HTML to the W3C validator, following the CS50 course convention.

## How to Run

1. Clone or download the project into a directory.
2. Create and activate a Python virtual environment: `python3 -m venv .venv && source .venv/bin/activate`.
3. Install dependencies: `pip install -r requirements.txt`.
4. If the database does not yet exist, initialize it by running the DDL: `sqlite3 clinicMedic.db < DDL.sql`.
5. Start the development server: `flask run`.
6. Navigate to `http://127.0.0.1:5000` in your browser.

An administrator account must be inserted directly into the database to bootstrap the system, after which the admin can create all other users through the web interface.

## Conclusion

CS50 MediCare represents a complete, working web application that addresses a real-world need: organizing clinic operations digitally. Through this project, core concepts from CS50x were applied in practice — HTTP, SQL, Python, Flask, HTML/CSS, session management, and cryptographic password hashing. The RBAC system, conflict-aware scheduling, and server-side validation demonstrate an awareness of both usability and security, building a system that would be reliable and trustworthy in a real clinical environment.
