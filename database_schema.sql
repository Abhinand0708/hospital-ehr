-- Create Database
CREATE DATABASE IF NOT EXISTS electronic_health_records;
USE electronic_health_records;

-- Table 0: Users (for bcrypt login)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    role ENUM('admin', 'doctor', 'nurse') DEFAULT 'doctor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 0b: Invite codes (admin generates, doctor uses once)
CREATE TABLE IF NOT EXISTS invite_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    role ENUM('doctor', 'nurse') DEFAULT 'doctor',
    created_by VARCHAR(100),
    used_by VARCHAR(100) DEFAULT NULL,
    used_at DATETIME DEFAULT NULL,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 1: Patients
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(50) PRIMARY KEY,
    patient_firstname VARCHAR(100) NOT NULL,
    patient_middlename VARCHAR(100),
    patient_lastname VARCHAR(100) NOT NULL,
    patient_DOB DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(20),
    address TEXT,
    medical_history TEXT,
    allergies TEXT,
    aadhar_number VARCHAR(20) UNIQUE,
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(20),
    marital_status ENUM('Single', 'Married', 'Divorced', 'Widowed'),
    occupation VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table 2: Malaria AI Results
CREATE TABLE IF NOT EXISTS malaria_ai_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(50),
    patient_name VARCHAR(200) NOT NULL,
    age INT,
    gender ENUM('Male', 'Female', 'Other'),
    contact VARCHAR(20),
    symptoms TEXT,
    doctor_name VARCHAR(150),
    result ENUM('Infected', 'Uninfected') NOT NULL,
    confidence DECIMAL(5,2),
    severity ENUM('Critical', 'High', 'Moderate', 'Low', 'N/A'),
    treatment TEXT,
    image_path VARCHAR(255),
    analyzed_by VARCHAR(100),
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);

-- Table 3: Appointments
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50),
    patient_name VARCHAR(200) NOT NULL,
    patient_email VARCHAR(150),
    doctor_name VARCHAR(150) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);

-- Table 4: Diagnosis
CREATE TABLE IF NOT EXISTS diagnosis (
    diagnosis_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50),
    patient_name VARCHAR(200) NOT NULL,
    diagnosis_date DATE NOT NULL,
    symptoms TEXT,
    observations TEXT,
    provisional_diagnosis TEXT,
    tests TEXT,
    final_diagnosis TEXT,
    treatment_plan TEXT,
    follow_up TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);

-- Table 5: Lab Reports
CREATE TABLE IF NOT EXISTS lab_reports (
    report_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50),
    patient_name VARCHAR(200) NOT NULL,
    test_date DATE NOT NULL,
    physician VARCHAR(150),
    hemoglobin VARCHAR(20),
    rbc VARCHAR(20),
    wbc VARCHAR(20),
    platelets VARCHAR(20),
    glucose VARCHAR(20),
    urea VARCHAR(20),
    creatinine VARCHAR(20),
    cholesterol VARCHAR(20),
    microbiology_findings TEXT,
    xray VARCHAR(100),
    ct_scan VARCHAR(100),
    mri VARCHAR(100),
    ultrasound VARCHAR(100),
    other_tests TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);

-- Table 6: Medical History
CREATE TABLE IF NOT EXISTS medical_history (
    record_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50),
    patient_name VARCHAR(200) NOT NULL,
    chronic_illnesses TEXT,
    surgeries TEXT,
    current_medications TEXT,
    allergies TEXT,
    hospitalizations TEXT,
    family_history TEXT,
    immunizations TEXT,
    social_history TEXT,
    other_conditions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);

-- Table 7: Treatment
CREATE TABLE IF NOT EXISTS treatment (
    treatment_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50),
    patient_name VARCHAR(200) NOT NULL,
    treatment_date DATE NOT NULL,
    diagnosis TEXT,
    medications TEXT NOT NULL,
    procedures TEXT,
    therapy_plan TEXT,
    diet TEXT,
    lifestyle TEXT,
    follow_up TEXT,
    additional_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);

-- Table 8: Radiology Requests
CREATE TABLE IF NOT EXISTS radiology_requests (
    request_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50),
    patient_name VARCHAR(200),
    request_date DATE NOT NULL,
    laboratory VARCHAR(150),
    test_type ENUM('X-Ray', 'CT Scan', 'MRI', 'Ultrasound', 'Other'),
    side_left VARCHAR(100),
    side_right VARCHAR(100),
    region VARCHAR(100),
    other_region VARCHAR(100),
    requests_printed VARCHAR(100),
    other_test TEXT,
    clinical_details TEXT NOT NULL,
    details_form TEXT,
    add_entry VARCHAR(100),
    due_date DATE,
    radiologist_findings TEXT,
    image_path VARCHAR(500),
    reported_by VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);

-- Table 9: Pathology Requests
CREATE TABLE IF NOT EXISTS pathology_requests (
    pathology_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50),
    patient_name VARCHAR(100),
    doctor_name VARCHAR(100),
    test_date DATE,
    request_date DATE,
    lab VARCHAR(100),
    favourite_tests TEXT,
    test_list TEXT,
    clinical_details TEXT,
    last_cytology TINYINT(1) DEFAULT 0,
    cytology_date DATE,
    hpv_not_required TINYINT(1) DEFAULT 0,
    hpv_reason VARCHAR(255),
    pregnancy_status VARCHAR(50),
    contraception_method VARCHAR(50),
    abnormal_bleeding ENUM('Yes','No'),
    clinical_notes TEXT,
    copy_to VARCHAR(255),
    collection_by VARCHAR(100),
    fasting_status VARCHAR(50),
    billing_type ENUM('Private','Concession','Direct Bill'),
    result_notes TEXT,
    result_image VARCHAR(500),
    reported_by VARCHAR(150),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL
);
CREATE INDEX idx_patient_name ON patients(patient_firstname, patient_lastname);
CREATE INDEX idx_appointment_date ON appointments(appointment_date);
CREATE INDEX idx_diagnosis_date ON diagnosis(diagnosis_date);
CREATE INDEX idx_test_date ON lab_reports(test_date);
CREATE INDEX idx_treatment_date ON treatment(treatment_date);
CREATE INDEX idx_malaria_analysis ON malaria_ai_results(analysis_date);
