# Hospital EHR System - MySQL Database Setup

## Prerequisites

1. **Install MySQL Server**
   - Download from: https://dev.mysql.com/downloads/mysql/
   - Or use XAMPP/WAMP which includes MySQL
   - Default port: 3306

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Database Configuration

### Step 1: Configure MySQL Credentials

Edit `db_config.py` and update your MySQL credentials:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',          # Your MySQL username
    'password': '',          # Your MySQL password
    'database': 'electronic_health_records'
}
```

### Step 2: Start MySQL Server

**Windows (XAMPP):**
- Open XAMPP Control Panel
- Click "Start" next to MySQL

**Windows (Standalone MySQL):**
- MySQL should start automatically as a service
- Or run: `net start MySQL80`

**Linux/Mac:**
```bash
sudo systemctl start mysql
# or
sudo service mysql start
```

### Step 3: Run the Application

The application will automatically:
1. Create the database `electronic_health_records`
2. Create all required tables
3. Set up indexes

```bash
python app.py
```

You should see:
```
Initializing database...
✓ Database 'electronic_health_records' created/verified
✓ All tables created/verified successfully
✓ Successfully connected to MySQL Server version X.X.X
✓ Connected to database: electronic_health_records
```

## Database Schema

The system creates 8 tables:

1. **patients** - Patient registration data
2. **malaria_ai_results** - AI malaria detection results
3. **appointments** - Appointment scheduling
4. **diagnosis** - Patient diagnosis records
5. **lab_reports** - Laboratory test results
6. **medical_history** - Patient medical history
7. **treatment** - Treatment plans
8. **radiology_requests** - Radiology/imaging requests

## Manual Database Setup (Optional)

If automatic setup fails, you can manually create the database:

```bash
# Login to MySQL
mysql -u root -p

# Run the schema file
source database_schema.sql
```

Or using MySQL Workbench:
1. Open MySQL Workbench
2. Connect to your MySQL server
3. File → Run SQL Script
4. Select `database_schema.sql`
5. Execute

## Verify Database Setup

### Using MySQL Command Line:
```sql
mysql -u root -p

USE electronic_health_records;
SHOW TABLES;
DESCRIBE patients;
```

### Using Python:
```python
python -c "from db_config import test_connection; test_connection()"
```

## Access the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Open browser: http://127.0.0.1:5001

3. Login credentials:
   - Username: `admin` | Password: `admin123`
   - Username: `doctor` | Password: `doctor123`

## How Data is Saved

When you submit any form:

1. **Patient Form** → Saves to `patients` table
2. **Malaria AI Detector** → Saves to `malaria_ai_results` table
3. **Appointment Form** → Saves to `appointments` table
4. **Diagnosis Form** → Saves to `diagnosis` table
5. **Lab Report Form** → Saves to `lab_reports` table
6. **Medical History Form** → Saves to `medical_history` table
7. **Treatment Form** → Saves to `treatment` table
8. **Radiology Form** → Saves to `radiology_requests` table

After submission, you'll see a success message with the generated ID.

## View Saved Data

### Using MySQL Command Line:
```sql
USE electronic_health_records;

-- View all patients
SELECT * FROM patients;

-- View malaria results
SELECT * FROM malaria_ai_results;

-- View appointments
SELECT * FROM appointments;

-- View all tables
SELECT * FROM diagnosis;
SELECT * FROM lab_reports;
SELECT * FROM medical_history;
SELECT * FROM treatment;
SELECT * FROM radiology_requests;
```

### Using MySQL Workbench:
1. Connect to your database
2. Select `electronic_health_records` database
3. Right-click on any table → "Select Rows"

## Troubleshooting

### Error: "Access denied for user 'root'@'localhost'"
- Check your MySQL username and password in `db_config.py`
- Make sure MySQL server is running

### Error: "Can't connect to MySQL server"
- Verify MySQL is running
- Check if port 3306 is open
- Try: `mysql -u root -p` to test connection

### Error: "Database already exists"
- This is normal, the system will use the existing database

### Error: "Table already exists"
- This is normal, the system will use existing tables

### Reset Database:
```sql
DROP DATABASE electronic_health_records;
```
Then restart the application to recreate everything.

## Project Structure

```
hospital-ehr/
├── app.py                      # Main Flask application
├── db_config.py                # Database configuration
├── database_schema.sql         # SQL schema for all tables
├── malaria_model.keras         # AI model for malaria detection
├── requirements.txt            # Python dependencies
├── templates/                  # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── patient.html
│   ├── malaria_detector.html
│   ├── appointment.html
│   ├── diagnosis.html
│   ├── lab_report.html
│   ├── medical_history.html
│   ├── treatment.html
│   └── radiology.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── uploads/                # Uploaded images
└── data/                       # Backup JSON files (optional)
```

## Features

✅ Automatic database creation
✅ Automatic table creation
✅ Form data validation
✅ Auto-generated IDs for all records
✅ Foreign key relationships
✅ Timestamps for all records
✅ AI-powered malaria detection with MySQL storage
✅ Statistics dashboard with real-time data
✅ Success/error flash messages
✅ Session-based authentication

## Security Notes

⚠️ **For Production:**
1. Change the Flask secret key in `app.py`
2. Use strong MySQL passwords
3. Don't commit `db_config.py` with real credentials
4. Use environment variables for sensitive data
5. Enable MySQL SSL connections
6. Implement proper user authentication
7. Add input validation and sanitization
8. Use prepared statements (already implemented)

## Support

If you encounter any issues:
1. Check MySQL is running
2. Verify credentials in `db_config.py`
3. Check console output for error messages
4. Review `MYSQL_SETUP_INSTRUCTIONS.md`
