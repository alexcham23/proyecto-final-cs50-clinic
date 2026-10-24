-- Usuarios del sistema con roles: 'admin', 'receptionist', 'doctor'
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'receptionist', 'doctor')),
    full_name TEXT NOT NULL,
    specialty TEXT, -- Solo aplica si role == 'doctor'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pacientes registrados por la recepcionista o admin
CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Citas médicas
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    scheduled_date TEXT NOT NULL, -- Formato YYYY-MM-DD
    scheduled_time TEXT NOT NULL, -- Formato HH:MM
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'completed', 'cancelled')),
    notes TEXT, -- Notas clínicas agregadas por el doctor
    FOREIGN KEY(patient_id) REFERENCES patients(id),
    FOREIGN KEY(doctor_id) REFERENCES users(id)
);