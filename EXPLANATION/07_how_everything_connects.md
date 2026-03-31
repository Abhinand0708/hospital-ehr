# How Everything Connects — The Full Flow

This explains what happens step by step when a user does something on the website.

---

## Flow 1 — User Opens the Website

```
User types: localhost:5001
        ↓
Browser sends GET request to Flask
        ↓
Flask: @app.route('/') → index() → render_template('landing.html')
        ↓
Flask reads landing.html, fills in any {{ variables }}
        ↓
Browser receives HTML + loads style.css
        ↓
User sees the landing page
```

---

## Flow 2 — Login

```
User fills username + password → clicks Login
        ↓
Browser sends POST request to /login with form data
        ↓
Flask: request.form.get('username') → "admin"
       request.form.get('password') → "admin123"
        ↓
db_config.verify_user("admin", "admin123")
        ↓
MySQL: SELECT * FROM users WHERE username = 'admin'
       Returns: {username: 'admin', password_hash: '$2b$12$...', role: 'admin'}
        ↓
bcrypt.checkpw("admin123", "$2b$12$...") → True
        ↓
session['username'] = 'admin'
session['role'] = 'admin'
(stored in browser cookie, encrypted with secret_key)
        ↓
redirect to /dashboard
        ↓
User sees dashboard
```

---

## Flow 3 — Register a Patient

```
Doctor fills patient form → clicks "Register Patient"
        ↓
Browser POST to /patient with all form fields
        ↓
Flask reads: aadhar_number, patient_firstname, patient_lastname, etc.
        ↓
MySQL: SELECT patient_id FROM patients WHERE aadhar_number = '123456789012'
       → No result (patient doesn't exist yet)
        ↓
Generate patient_id:
  today = "20260316"
  count = 0 (no patients today yet)
  patient_id = "2026031601"
        ↓
MySQL: INSERT INTO patients (patient_id, patient_firstname, ...) VALUES (...)
MySQL: COMMIT (save permanently)
        ↓
flash("Patient registered! ID: 2026031601", "success")
redirect back to /patient
        ↓
User sees green success message at top of page
```

---

## Flow 4 — Malaria Detection

```
Doctor fills patient info + uploads blood smear image → clicks Analyze
        ↓
JavaScript intercepts form submit (e.preventDefault())
JavaScript creates FormData with all fields + image file
JavaScript: fetch('/api/predict-malaria', {method: 'POST', body: formData})
        ↓
Flask receives POST at /api/predict-malaria
        ↓
file = request.files['image']           → get the uploaded image
image = Image.open(io.BytesIO(...))     → open with PIL
image = image.resize((128, 128))        → resize to 128x128
img_array = np.array(image) / 255.0    → convert to numbers 0-1
img_array = np.expand_dims(img_array, 0) → shape: (1, 128, 128, 3)
        ↓
prediction = model.predict(img_array)  → runs through CNN
prediction[0][0] = 0.03                → a number between 0 and 1
        ↓
is_infected = 0.03 < 0.5 → True
result = "Infected"
confidence = (1 - 0.03) * 100 = 97%
severity = "Critical" (97 >= 90)
        ↓
MySQL: INSERT INTO malaria_ai_results (patient_id, result, confidence, ...)
        ↓
Flask returns JSON:
{
  "success": true,
  "result": "Infected",
  "confidence": 97.0,
  "severity": "Critical",
  "treatment": "Immediate hospitalization..."
}
        ↓
JavaScript receives JSON
JavaScript hides the form
JavaScript shows result section
JavaScript fills in: result title, confidence, patient details, treatment
        ↓
User sees the diagnosis result — no page reload!
```

---

## Flow 5 — Patient Autocomplete Search

```
Doctor types "abhi" in patient name field
        ↓
JavaScript: input event fires after 250ms debounce
JavaScript: fetch('/api/search-patients?q=abhi')
        ↓
Flask: /api/search-patients
MySQL: SELECT patient_id, full_name, patient_DOB, phone
       FROM patients
       WHERE patient_firstname LIKE '%abhi%'
          OR patient_lastname LIKE '%abhi%'
       → Returns: [
           {patient_id: "2026031601", full_name: "Abhinand K", dob: "2000-05-12"},
           {patient_id: "2026031602", full_name: "Abhijith M", dob: "1998-11-03"}
         ]
        ↓
Flask returns JSON array
        ↓
JavaScript creates dropdown items for each patient
        ↓
Doctor clicks "Abhinand K"
        ↓
JavaScript: nameInput.value = "Abhinand K"
            idInput.value = "2026031601"
            confirm.textContent = "✓ Patient ID: 2026031601"
        ↓
Form submits with correct patient_id already filled
```

---

## Flow 6 — Invite Code Registration

```
Admin goes to Manage Users → selects Doctor, 1 hour → clicks Generate
        ↓
Flask: secrets.token_hex(8).upper() → "A3F9B2C1D4E5F6A7"
expires_at = now + 1 hour
MySQL: INSERT INTO invite_codes (code, role, expires_at) VALUES (...)
        ↓
Flash message shows the code
Admin copies it and sends to doctor via WhatsApp
        ↓
Doctor opens /register
Types: invite_code="A3F9B2C1D4E5F6A7", username="dr.arun", password="mypass123"
        ↓
Flask: SELECT * FROM invite_codes
       WHERE code = 'A3F9B2C1D4E5F6A7'
       AND used_by IS NULL
       AND expires_at > NOW()
       → Found! (code is valid)
        ↓
bcrypt.hashpw("mypass123") → "$2b$12$xyz..."
MySQL: INSERT INTO users (username, password_hash, role) VALUES ('dr.arun', '$2b$12$xyz...', 'doctor')
MySQL: UPDATE invite_codes SET used_by='dr.arun', used_at=NOW() WHERE id=...
        ↓
Doctor redirected to login
Doctor logs in with dr.arun / mypass123
```

---

## The Folder Structure — Why Each Folder Exists

```
WEB/
├── app.py              ← Flask routes (the brain)
├── db_config.py        ← Database connection + auth
├── database_schema.sql ← SQL to create all tables
├── malaria_model.keras ← Trained AI model (binary file)
├── requirements.txt    ← List of Python packages needed
│
├── templates/          ← HTML pages (what user sees)
│   ├── base.html       ← Master template (navbar, flash messages, JS)
│   ├── landing.html    ← Home page (no login needed)
│   ├── login.html      ← Login form
│   ├── dashboard.html  ← Main menu with 8 buttons
│   ├── patient.html    ← Patient registration form
│   └── ...             ← Other module pages
│
└── static/             ← Files served directly (no Flask processing)
    ├── css/style.css   ← All the styling
    └── uploads/        ← Saved malaria images
```

Why `static/`?
- Flask serves these files directly without any Python processing
- CSS, images, JS files go here
- URL: `localhost:5001/static/css/style.css`

Why `templates/`?
- Flask processes these with Jinja2 (fills in {{ variables }})
- Never served directly — always goes through Flask first
