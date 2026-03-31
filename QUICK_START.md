# Quick Start Guide - Hospital EHR with MySQL

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install MySQL
- **Windows**: Download and install XAMPP from https://www.apachefriends.org/
- **Or**: Install MySQL Server from https://dev.mysql.com/downloads/mysql/

### Step 2: Configure Database
Edit `db_config.py` - Update these lines:
```python
'user': 'root',        # Your MySQL username
'password': '',        # Your MySQL password (empty for XAMPP default)
```

### Step 3: Install Python Packages
```bash
pip install mysql-connector-python
```

### Step 4: Start MySQL
- **XAMPP**: Open XAMPP Control Panel → Start MySQL
- **Standalone**: MySQL should auto-start

### Step 5: Run Application
```bash
python app.py
```

You'll see:
```
✓ Database 'electronic_health_records' created/verified
✓ All tables created/verified successfully
✓ Successfully connected to MySQL Server
```

### Step 6: Access Website
Open browser: **http://127.0.0.1:5001**

Login: `admin` / `admin123`

## ✅ What Happens Automatically

1. **Database Creation**: `electronic_health_records` database is created
2. **Table Creation**: All 8 tables are created automatically
3. **Data Storage**: Every form submission saves to MySQL

## 📊 8 Modules with MySQL Storage

| Module | Saves To Table |
|--------|----------------|
| Patient | `patients` |
| Malaria AI Detector | `malaria_ai_results` |
| Appointment | `appointments` |
| Diagnosis | `diagnosis` |
| Lab Report | `lab_reports` |
| Medical History | `medical_history` |
| Treatment | `treatment` |
| Radiology Result | `radiology_requests` |

## 🔍 View Your Data

### Option 1: MySQL Command Line
```bash
mysql -u root -p
USE electronic_health_records;
SELECT * FROM patients;
SELECT * FROM malaria_ai_results;
```

### Option 2: phpMyAdmin (if using XAMPP)
- Open: http://localhost/phpmyadmin
- Select database: `electronic_health_records`
- Click any table to view data

### Option 3: MySQL Workbench
- Download: https://dev.mysql.com/downloads/workbench/
- Connect to localhost
- Browse `electronic_health_records` database

## 🎯 Test the System

1. **Register a Patient**:
   - Click "Patient" button
   - Fill the form
   - Submit → Data saved to `patients` table
   - You'll see: "Patient registered successfully! Patient ID: PAT-20261213-ABC123"

2. **Analyze Malaria**:
   - Click "Malaria AI Detector"
   - Fill patient info
   - Upload blood smear image
   - Click "Analyze"
   - Result saved to `malaria_ai_results` table

3. **Check Statistics**:
   - In Malaria AI Detector, click "Statistics" button
   - See real-time data from MySQL database

## 🔧 Troubleshooting

**Can't connect to MySQL?**
```bash
# Check if MySQL is running
mysql -u root -p
```

**Wrong password?**
- Update `db_config.py` with correct password
- XAMPP default: username=`root`, password=`` (empty)

**Port 5001 already in use?**
- Change port in `app.py`: `app.run(debug=True, port=5002)`

## 📁 Project Files

```
├── app.py                    # Main application (MySQL integrated)
├── db_config.py              # Database configuration
├── database_schema.sql       # SQL schema
├── malaria_model.keras       # AI model
├── templates/                # All HTML pages
├── static/css/style.css      # Styling
└── requirements.txt          # Dependencies
```

## 🎉 You're Done!

Your Hospital EHR system is now:
- ✅ Connected to MySQL
- ✅ Auto-creating database and tables
- ✅ Saving all form data to MySQL
- ✅ Running AI malaria detection
- ✅ Showing real-time statistics

Enjoy your fully functional Hospital Management System with MySQL database! 🏥
