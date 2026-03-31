# app.py — Line by Line Explanation

This is the MAIN file. The entire website runs from here.
Think of it as the "manager" of the restaurant — it receives orders and sends food.

---

## BLOCK 1 — Imports (Lines 1-10)

```python
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
```
- `Flask` — the main framework, creates the web app
- `render_template` — loads an HTML file and sends it to the browser
- `request` — reads data sent from a form (what the user typed)
- `redirect` — sends user to a different page
- `url_for` — generates a URL from a function name (safer than hardcoding)
- `session` — stores login info in the browser (like a cookie)
- `flash` — shows one-time messages like "Patient saved successfully!"
- `jsonify` — converts Python dictionary to JSON (used for API responses)

```python
import tensorflow as tf
import numpy as np
from PIL import Image
import io
```
- `tensorflow` — runs the AI malaria detection model
- `numpy` — converts image to numbers the model understands
- `PIL Image` — opens and resizes the uploaded image
- `io` — reads the image from memory (without saving to disk first)

```python
from db_config import get_db_connection, init_database, test_connection, verify_user
from mysql.connector import Error
```
- Imports database functions from db_config.py
- `Error` — catches MySQL errors so the app doesn't crash

---

## BLOCK 2 — App Setup (Lines 12-15)

```python
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
```
- `Flask(__name__)` — creates the Flask app. `__name__` tells Flask where the file is.
- `secret_key` — a password Flask uses to encrypt session data (login cookies).
  If someone knows this key they can fake a login. Change it in real production!

---

## BLOCK 3 — Database Init on Startup (Lines 17-22)

```python
if init_database():
    print("✓ Database initialization complete")
    test_connection()
else:
    print("✗ Database initialization failed")
```
- When app starts, it immediately connects to MySQL
- Creates the database and all 8 tables if they don't exist yet
- This is why you never have to manually create tables — it's automatic

---

## BLOCK 4 — Load AI Model (Line 24)

```python
model = tf.keras.models.load_model(MODEL_PATH, compile=False)
```
- Loads the trained malaria detection model from `malaria_model.keras`
- `compile=False` — skips recompiling the model (fixes version compatibility errors)
- This runs ONCE when the app starts, not every time someone uploads an image

---

## BLOCK 5 — Helper Functions (Lines 30-60)

```python
def preprocess_image(image):
    img = image.resize((128, 128))        # resize to 128x128 pixels
    img_array = np.array(img) / 255.0    # convert to numbers, scale 0-1
    return np.expand_dims(img_array, axis=0)  # add batch dimension
```
- The model expects images in a specific format: 128x128 pixels, values between 0 and 1
- `np.expand_dims` adds an extra dimension — model expects shape (1, 128, 128, 3) not (128, 128, 3)

```python
def get_severity_level(confidence):
    if confidence >= 90: return 'Critical'
    elif confidence >= 75: return 'High'
    elif confidence >= 60: return 'Moderate'
    return 'Low'
```
- Takes the confidence % and returns a severity label
- 95% confident = Critical, 80% = High, etc.

---

## BLOCK 6 — Routes (the most important part)

A "route" is a URL. When someone visits that URL, Flask runs the function below it.

```python
@app.route('/')
def index():
    return render_template('landing.html')
```
- `@app.route('/')` — this is called a "decorator". It links the URL `/` to the function below it.
- When someone visits `localhost:5001/` → Flask runs `index()` → sends `landing.html`

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':           # form was submitted
        username = request.form.get('username')  # read what user typed
        password = request.form.get('password')
        user = verify_user(username, password)   # check in database
        if user:
            session['username'] = user['username']  # save login to session
            return redirect(url_for('dashboard'))   # go to dashboard
        flash('Invalid username or password', 'error')  # show error
    return render_template('login.html')   # show the login page
```
- `methods=['GET', 'POST']` — this route accepts both visiting (GET) and form submit (POST)
- `request.form.get('username')` — reads the value from the HTML input named "username"
- `session['username']` — stores the username in a cookie so Flask remembers who's logged in
- `redirect(url_for('dashboard'))` — sends user to the dashboard page

```python
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:          # not logged in?
        return redirect(url_for('login'))  # send to login page
    return render_template('dashboard.html', username=session['username'])
```
- Every protected page checks `if 'username' not in session` first
- `username=session['username']` — passes the username to the HTML template so it can show "Welcome, admin"

---

## BLOCK 7 — Patient Registration Route

```python
@app.route('/patient', methods=['GET', 'POST'])
def patient():
    if request.method == 'POST':
        connection = get_db_connection()   # open MySQL connection
        cursor = connection.cursor()       # cursor = like a pen to write to DB

        aadhar_number = request.form.get('aadhar_number')

        # Check if patient already exists
        cursor.execute("SELECT patient_id FROM patients WHERE aadhar_number = %s", (aadhar_number,))
        existing = cursor.fetchone()
        if existing:
            flash('Patient already exists!', 'error')
            return render_template('patient.html')

        # Generate Patient ID
        today = datetime.now().strftime('%Y%m%d')  # e.g. "20260316"
        cursor.execute("SELECT COUNT(*) FROM patients WHERE patient_id LIKE %s", (f"{today}%",))
        count = cursor.fetchone()[0]
        patient_id = f"{today}{count + 1:02d}"  # e.g. "2026031601"

        # Insert into database
        cursor.execute("INSERT INTO patients (...) VALUES (...)", (values,))
        connection.commit()   # SAVE — without this nothing is stored!
        flash(f'Patient registered! ID: {patient_id}', 'success')
```
- `%s` in SQL is a placeholder — MySQL fills it in safely (prevents SQL injection attacks)
- `cursor.fetchone()` — gets one row from the query result
- `connection.commit()` — actually saves the data. Like pressing Save in Word.

---

## BLOCK 8 — Malaria AI Prediction Route

```python
@app.route('/api/predict-malaria', methods=['POST'])
def predict_malaria():
    file = request.files['image']          # get the uploaded image file
    image = Image.open(io.BytesIO(image_bytes))  # open it with PIL
    processed_image = preprocess_image(image)    # resize + normalize
    prediction = model.predict(processed_image)  # run through AI model

    confidence = float(prediction[0][0])   # model returns a number 0-1
    is_infected = confidence < 0.5         # below 0.5 = infected
    result = 'Infected' if is_infected else 'Uninfected'

    return jsonify({'success': True, 'result': result, 'confidence': ...})
```
- `request.files['image']` — gets the uploaded file from the form
- `model.predict()` — runs the image through the CNN, returns a number between 0 and 1
- Below 0.5 = Infected (the model was trained this way)
- `jsonify()` — sends the result back as JSON so JavaScript can read it

---

## BLOCK 9 — The Last Line

```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)
```
- `if __name__ == '__main__'` — only runs when you directly run `python app.py`
- `debug=True` — shows detailed errors in browser (turn OFF in production)
- `port=5001` — runs on port 5001, so URL is `localhost:5001`
