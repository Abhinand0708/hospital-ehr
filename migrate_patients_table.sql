USE electronic_health_records;

-- Step 1: Rename existing columns
ALTER TABLE patients
    CHANGE COLUMN first_name  patient_firstname  VARCHAR(100) NOT NULL,
    CHANGE COLUMN last_name   patient_lastname   VARCHAR(100) NOT NULL,
    CHANGE COLUMN dob         patient_DOB        DATE NOT NULL;

-- Step 2: Add middle name column (no IF NOT EXISTS — just run once)
ALTER TABLE patients
    ADD COLUMN patient_middlename VARCHAR(100) AFTER patient_firstname;

-- Step 3: Add unique index on aadhar (ignore error if already exists)
ALTER TABLE patients
    ADD UNIQUE INDEX idx_aadhar_unique (aadhar_number);

-- Step 4: Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    role ENUM('admin', 'doctor', 'nurse') DEFAULT 'doctor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 5: Add full_name to users if it already existed without it
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(150) AFTER password_hash;

SELECT 'Migration complete!' AS status;
