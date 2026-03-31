# database_schema.sql — Explanation

This file creates all the MySQL tables. It runs automatically when app starts.

---

## What is SQL?

SQL = Structured Query Language. It's how you talk to a database.

4 main commands:
```sql
SELECT * FROM patients          -- read data
INSERT INTO patients VALUES ... -- add data
UPDATE patients SET name = ...  -- change data
DELETE FROM patients WHERE ...  -- remove data
```

---

## CREATE TABLE Syntax

```sql
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(50) PRIMARY KEY,
    -- VARCHAR(50) = text up to 50 characters
    -- PRIMARY KEY = unique identifier, no two rows can have same value

    patient_firstname VARCHAR(100) NOT NULL,
    -- NOT NULL = this field is required, can't be empty

    patient_middlename VARCHAR(100),
    -- no NOT NULL = optional field, can be empty (NULL)

    patient_DOB DATE NOT NULL,
    -- DATE = stores date in YYYY-MM-DD format

    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    -- ENUM = only these exact values allowed

    email VARCHAR(150),
    -- optional email

    aadhar_number VARCHAR(20) UNIQUE,
    -- UNIQUE = no two patients can have same aadhar number

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    -- TIMESTAMP = stores date AND time
    -- DEFAULT CURRENT_TIMESTAMP = automatically fills with current time
);
```

---

## Foreign Keys — Linking Tables

```sql
CREATE TABLE appointments (
    appointment_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50),

    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
    -- FOREIGN KEY = this column links to another table
    -- patient_id here must exist in the patients table
    -- ON DELETE SET NULL = if patient is deleted, set this to NULL (don't delete appointment)
);
```

Think of it like this:
- patients table = main table
- appointments, diagnosis, lab_reports etc. = child tables
- They all have `patient_id` that points back to the patient

---

## The 8 Tables

```
patients              ← main table, all other tables link to this
├── malaria_ai_results
├── appointments
├── diagnosis
├── lab_reports
├── medical_history
├── treatment
├── radiology_requests
└── users             ← separate, for login (not linked to patients)
invite_codes          ← for doctor registration
```

---

## Data Types Used

| Type | What it stores | Example |
|------|---------------|---------|
| `VARCHAR(n)` | Text up to n chars | "John Smith" |
| `TEXT` | Long text, no limit | Medical notes |
| `INT` | Whole number | 25 (age) |
| `DECIMAL(5,2)` | Number with decimals | 95.74 (confidence %) |
| `DATE` | Date only | 2026-03-16 |
| `DATETIME` | Date + time | 2026-03-16 14:30:00 |
| `TIMESTAMP` | Auto date+time | created_at |
| `ENUM(...)` | One of fixed options | 'Male','Female','Other' |
| `BOOLEAN` | True/False | 1 or 0 |

---

## Indexes — Making Search Faster

```sql
CREATE INDEX idx_patient_name ON patients(patient_firstname, patient_lastname);
```
- An index is like a book's index — helps MySQL find rows faster
- Without index: MySQL reads EVERY row to find "Abhinand"
- With index: MySQL jumps directly to "Abhinand" rows
- Trade-off: slightly slower INSERT, much faster SELECT

---

## The users Table (for login)

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- AUTO_INCREMENT = MySQL automatically assigns 1, 2, 3...

    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    -- stores the bcrypt hash, NOT the real password

    full_name VARCHAR(150),
    role ENUM('admin', 'doctor', 'nurse') DEFAULT 'doctor',
    -- DEFAULT 'doctor' = if role not specified, use 'doctor'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## invite_codes Table

```sql
CREATE TABLE invite_codes (
    code VARCHAR(32) NOT NULL UNIQUE,   -- the random code like "A3F9B2C1"
    role ENUM('doctor', 'nurse'),        -- what role the new user gets
    created_by VARCHAR(100),             -- which admin created it
    used_by VARCHAR(100) DEFAULT NULL,   -- NULL = not used yet
    used_at DATETIME DEFAULT NULL,       -- when it was used
    expires_at DATETIME NOT NULL         -- when it expires
);
```
- When admin generates a code: `used_by = NULL`
- When doctor registers: `used_by = 'dr.arun'`, `used_at = now()`
- Flask checks: `WHERE code = ? AND used_by IS NULL AND expires_at > NOW()`
