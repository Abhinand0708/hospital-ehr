# db_config.py — Line by Line Explanation

This file handles everything related to the MySQL database.
Think of it as the "storage manager" — app.py asks it to save/get data.

---

## BLOCK 1 — Imports

```python
import mysql.connector
from mysql.connector import Error
import bcrypt
```
- `mysql.connector` — the library that lets Python talk to MySQL
- `Error` — catches database errors
- `bcrypt` — for hashing passwords (explained in Block 4)

---

## BLOCK 2 — Database Config

```python
DB_CONFIG = {
    'host': 'localhost',      # MySQL is on this same computer
    'user': 'root',           # MySQL username
    'password': 'root',       # MySQL password
    'database': 'electronic_health_records'  # which database to use
}
```
- This is a Python dictionary — just key-value pairs
- `localhost` means the database is on the same machine as the Flask app
- If your MySQL password is different, change it here

---

## BLOCK 3 — get_db_connection()

```python
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection    # return the open connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None             # return nothing if failed
```
- `**DB_CONFIG` — the `**` unpacks the dictionary as keyword arguments
  Same as writing: `connect(host='localhost', user='root', ...)`
- `try/except` — if connection fails, don't crash the app, just print the error
- Every route in app.py calls this to get a fresh connection

---

## BLOCK 4 — init_database()

```python
def init_database():
    # Step 1: Connect WITHOUT specifying a database
    connection = mysql.connector.connect(host=..., user=..., password=...)
    cursor.execute("CREATE DATABASE IF NOT EXISTS electronic_health_records")
    # "IF NOT EXISTS" = only create if it doesn't already exist

    # Step 2: Connect TO the database and create tables
    connection = get_db_connection()
    with open('database_schema.sql', 'r') as f:
        sql_script = f.read()          # read the entire SQL file as text

    for statement in sql_script.split(';'):   # split by semicolon = each SQL command
        if statement.strip():
            cursor.execute(statement)  # run each CREATE TABLE command
```
- This runs ONCE when app.py starts
- It reads `database_schema.sql` and runs every CREATE TABLE command
- `IF NOT EXISTS` means it's safe to run multiple times — won't duplicate tables

---

## BLOCK 5 — bcrypt Password Hashing

```python
def _seed_default_users(cursor, connection):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
```

What is bcrypt?
- Normal storage (BAD):  password = "admin123"  ← anyone who sees DB knows password
- bcrypt storage (GOOD): password = "$2b$12$xK9mN..." ← impossible to reverse

Step by step:
```python
password.encode('utf-8')   # convert string to bytes: "admin123" → b"admin123"
bcrypt.gensalt()           # generate a random "salt" (extra random data)
bcrypt.hashpw(...)         # combine password + salt and hash it
.decode('utf-8')           # convert bytes back to string for storing in MySQL
```

---

## BLOCK 6 — verify_user()

```python
def verify_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()   # get the user row from database

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return user    # password matches — return user data
    return None        # wrong password — return nothing
```
- Fetches the user from database by username
- `bcrypt.checkpw()` — hashes the entered password and compares with stored hash
- Returns the user dict if correct, None if wrong
- app.py login route calls this: `user = verify_user(username, password)`

---

## BLOCK 7 — test_connection()

```python
def test_connection():
    connection = get_db_connection()
    if connection and connection.is_connected():
        print(f"✓ Connected to MySQL Server version {db_info}")
```
- Just a diagnostic function — prints confirmation that DB is connected
- Called once at startup in app.py
