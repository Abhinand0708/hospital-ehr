import mysql.connector
from mysql.connector import Error
import bcrypt
import os

DB_CONFIG = {
    'host':     os.environ.get('DB_HOST', 'localhost'),
    'user':     os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'root'),
    'database': os.environ.get('DB_NAME', 'electronic_health_records'),
    'port':     int(os.environ.get('DB_PORT', 3306))
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            with open('database_schema.sql', 'r') as f:
                sql_script = f.read()
            for statement in sql_script.split(';'):
                stmt = statement.strip()
                if stmt and 'CREATE DATABASE' not in stmt and 'USE ' not in stmt:
                    try:
                        cursor.execute(stmt)
                    except Error as e:
                        if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                            print(f"SQL warning: {e}")
            connection.commit()
            print("✓ All tables created/verified successfully")
            _run_migrations(cursor, connection)
            _seed_default_users(cursor, connection)
            cursor.close()
            connection.close()
            return True
    except Error as e:
        print(f"Error initializing database: {e}")
        return False

def _run_migrations(cursor, connection):
    migrations = [
        "ALTER TABLE radiology_requests ADD COLUMN patient_name VARCHAR(200) AFTER patient_id",
        "ALTER TABLE radiology_requests ADD COLUMN radiologist_findings TEXT AFTER due_date",
        "ALTER TABLE radiology_requests ADD COLUMN image_path VARCHAR(500) AFTER radiologist_findings",
        "ALTER TABLE radiology_requests ADD COLUMN reported_by VARCHAR(150) AFTER image_path",
        "ALTER TABLE pathology_requests ADD COLUMN result_notes TEXT AFTER billing_type",
        "ALTER TABLE pathology_requests ADD COLUMN result_image VARCHAR(500) AFTER result_notes",
        "ALTER TABLE pathology_requests ADD COLUMN reported_by VARCHAR(150) AFTER result_image",
    ]
    for sql in migrations:
        try:
            cursor.execute(sql)
            connection.commit()
        except Error as e:
            if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                pass
            else:
                print(f"Migration warning: {e}")

def _seed_default_users(cursor, connection):
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        if count == 0:
            defaults = [
                ('admin', 'admin123', 'admin', 'System Admin'),
                ('doctor', 'doctor123', 'doctor', 'Demo Doctor'),
            ]
            for username, password, role, full_name in defaults:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, full_name) VALUES (%s, %s, %s, %s)",
                    (username, hashed, role, full_name)
                )
            connection.commit()
            print("✓ Default users seeded (admin/admin123, doctor/doctor123)")
    except Error as e:
        print(f"Warning seeding users: {e}")

def verify_user(username, password):
    connection = get_db_connection()
    if not connection:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return user
        return None
    except Error as e:
        print(f"Error verifying user: {e}")
        return None

def test_connection():
    connection = get_db_connection()
    if connection and connection.is_connected():
        db_info = connection.get_server_info()
        print(f"✓ Connected to MySQL Server version {db_info}")
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        record = cursor.fetchone()
        print(f"✓ Connected to database: {record[0]}")
        cursor.close()
        connection.close()
        return True
    print("✗ Failed to connect to MySQL")
    return False
