# START HERE — How to Use These Explanation Files

Read them in this order:

1. 07_how_everything_connects.md  ← Read this FIRST. Big picture of how it all works.
2. 01_app_py.md                   ← The main Flask file, route by route
3. 02_db_config_py.md             ← Database connection and bcrypt
4. 03_html_templates.md           ← How HTML and Jinja2 work
5. 04_css.md                      ← How styling works
6. 05_javascript.md               ← Autocomplete and malaria form
7. 06_database_schema.md          ← SQL tables explained

---

## One-Line Summary of Each Technology

| Technology | What it does in your project |
|------------|------------------------------|
| Flask (Python) | Receives browser requests, runs logic, sends back pages |
| HTML | Structure of each page (forms, buttons, text) |
| CSS | Makes pages look good (colors, layout, animations) |
| JavaScript | Makes pages interactive without reloading |
| MySQL | Stores all patient data permanently |
| Jinja2 | Puts Python variables into HTML templates |
| bcrypt | Hashes passwords so they can't be stolen |
| TensorFlow | Runs the malaria detection AI model |

---

## If Someone Asks You...

"What is Flask?"
→ A Python web framework. It maps URLs to Python functions.
  When someone visits /patient, Flask runs the patient() function and returns the HTML page.

"How does the malaria detection work?"
→ User uploads a blood smear image. Flask passes it to a trained CNN model (TensorFlow).
  The model returns a number between 0 and 1. Below 0.5 = Infected. The confidence
  percentage and severity level are calculated from that number.

"How is the database connected?"
→ db_config.py uses mysql-connector-python to connect to MySQL.
  On startup, it auto-creates the database and 8 tables from database_schema.sql.
  Every form submission does an INSERT INTO the correct table.

"How is login secure?"
→ Passwords are hashed with bcrypt before storing. On login, bcrypt.checkpw()
  compares the entered password with the stored hash. The session stores the
  username in an encrypted cookie using Flask's secret_key.

"What is the invite code system?"
→ Admin generates a random one-time code with a 1-hour expiry.
  Doctor uses that code at /register to create their own account.
  The code is marked as used immediately — nobody else can use it.
