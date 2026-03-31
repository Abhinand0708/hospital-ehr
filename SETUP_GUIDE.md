# Hospital EHR System — Setup Guide

## Requirements
- Python 3.9+
- MySQL Server 8.0+
- MySQL Workbench (optional but recommended)

---

## Step 1 — Install Python dependencies

Open terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

---

## Step 2 — Setup MySQL Database

Open MySQL Workbench and run the migration script:

1. Open `migrate_patients_table.sql`
2. Run the full script (it creates all tables)

OR if setting up fresh, just run `database_schema.sql` first.

**MySQL credentials used in this project:**
- Host: localhost
- User: root
- Password: root

If your MySQL password is different, edit `db_config.py` line 7:
```python
'password': 'your_password_here',
```

---

## Step 3 — Run the application

```bash
python app.py
```

The app starts at: **http://localhost:5001**

---

## Step 4 — Login

| Username | Password | Role  |
|----------|----------|-------|
| admin    | admin123 | Admin |
| doctor   | doctor123| Doctor|

---

## Project Structure

```
WEB/
├── app.py                  # Main Flask application
├── db_config.py            # MySQL connection + bcrypt auth
├── database_schema.sql     # Full DB schema
├── migrate_patients_table.sql  # Migration for existing DB
├── malaria_model.keras     # AI model for malaria detection
├── requirements.txt        # Python dependencies
├── templates/              # HTML pages
│   ├── landing.html        # Landing page
│   ├── login.html          # Login
│   ├── dashboard.html      # Main dashboard
│   ├── patient.html        # Patient registration
│   ├── search_patient.html # Patient search
│   ├── malaria_detector.html
│   ├── appointment.html
│   ├── diagnosis.html
│   ├── lab_report.html
│   ├── medical_history.html
│   ├── treatment.html
│   ├── radiology.html
│   ├── register.html       # Doctor self-registration (invite code)
│   └── manage_users.html   # Admin user management
└── static/
    ├── css/style.css
    └── uploads/            # Uploaded malaria images
```

---

## Key Features

- **AI Malaria Detection** — Upload blood smear image, get instant diagnosis
- **Patient Registration** — Auto-generated Patient ID (YYYYMMDDNN format)
- **Aadhar Uniqueness** — Prevents duplicate patient registration
- **Patient Search** — Search by ID, Aadhar, or partial name with live autocomplete
- **8 Clinical Modules** — Patient, Appointment, Diagnosis, Lab Report, Medical History, Treatment, Radiology, Malaria AI
- **Secure Login** — bcrypt password hashing
- **Invite Code System** — Admin generates one-time codes for doctor registration
- **User Management** — Admin can view/delete staff accounts
