from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import tensorflow as tf
import numpy as np
from PIL import Image
import io
from datetime import datetime
import json
import uuid
from db_config import get_db_connection, init_database, test_connection, verify_user
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Run DB init when gunicorn loads the module (not just __main__)
try:
    print("Initializing database...")
    if init_database():
        print("✓ Database initialization complete")
        test_connection()
    else:
        print("✗ Database initialization failed")
except Exception as e:
    print(f"Database init error: {e}")

MODEL_PATH = 'malaria_model.keras'
model = None

def load_model_safe():
    global model
    try:
        if model is None:
            print("Loading TensorFlow model...")
            model = tf.keras.models.load_model(MODEL_PATH, compile=False)
            print("✓ Model loaded successfully")
    except Exception as e:
        print(f"Model load error: {e}")

UPLOAD_DIR = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs('data', exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def preprocess_image(image):
    img = image.resize((128, 128))
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

def get_severity_level(confidence):
    if confidence >= 90: return 'Critical'
    elif confidence >= 75: return 'High'
    elif confidence >= 60: return 'Moderate'
    return 'Low'

def get_treatment_recommendation(result, severity):
    if result == 'Infected':
        if severity == 'Critical':
            return 'Immediate hospitalization required. Start IV antimalarial therapy (Artesunate). Monitor vital signs closely.'
        elif severity == 'High':
            return 'Urgent medical attention needed. Prescribe oral antimalarial medication (Artemether-Lumefantrine). Follow-up in 24 hours.'
        elif severity == 'Moderate':
            return 'Medical consultation recommended. Consider antimalarial treatment. Monitor symptoms closely.'
        return 'Consult with physician. Further testing may be required to confirm diagnosis.'
    return 'No malaria parasites detected. If symptoms persist, consider other differential diagnoses.'

def generate_patient_id(cursor):
    """Generate YYYYMMDDNN patient ID"""
    today = datetime.now().strftime('%Y%m%d')
    cursor.execute("SELECT COUNT(*) FROM patients WHERE patient_id LIKE %s", (f"{today}%",))
    count = cursor.fetchone()[0]
    return f"{today}{count + 1:02d}"

def generate_record_id(prefix, cursor, table, id_col):
    """Generate auto ID like APT-20260316-001"""
    today = datetime.now().strftime('%Y%m%d')
    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {id_col} LIKE %s", (f"{prefix}-{today}%",))
    count = cursor.fetchone()[0]
    return f"{prefix}-{today}-{count + 1:03d}"

def lookup_patient_by_name(cursor, full_name):
    """Try to find patient_id from full name"""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        cursor.execute(
            "SELECT patient_id FROM patients WHERE patient_firstname = %s AND patient_lastname = %s LIMIT 1",
            (parts[0], parts[-1])
        )
        row = cursor.fetchone()
        return row[0] if row else None
    return None

# ── routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = verify_user(username, password)
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Doctor self-registration — requires a valid invite code from admin."""
    if request.method == 'POST':
        invite_code = request.form.get('invite_code', '').strip()
        username    = request.form.get('username', '').strip()
        full_name   = request.form.get('full_name', '').strip()
        password    = request.form.get('password', '')
        confirm     = request.form.get('confirm_password', '')

        if not invite_code or not username or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        try:
            import bcrypt as _bcrypt
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)

                # Validate invite code
                cursor.execute("""
                    SELECT * FROM invite_codes
                    WHERE code = %s AND used_by IS NULL AND expires_at > NOW()
                """, (invite_code,))
                invite = cursor.fetchone()

                if not invite:
                    flash('Invalid or expired invite code. Ask your admin for a new one.', 'error')
                    cursor.close(); connection.close()
                    return render_template('register.html')

                # Check username not taken
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash('Username already taken. Choose another.', 'error')
                    cursor.close(); connection.close()
                    return render_template('register.html')

                # Create account
                hashed = _bcrypt.hashpw(password.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, full_name) VALUES (%s,%s,%s,%s)",
                    (username, hashed, invite['role'], full_name or username)
                )

                # Mark invite code as used
                cursor.execute("""
                    UPDATE invite_codes SET used_by = %s, used_at = NOW() WHERE id = %s
                """, (username, invite['id']))

                connection.commit()
                cursor.close(); connection.close()
                flash(f'Account created! Welcome, {full_name or username}. You can now log in.', 'success')
                return redirect(url_for('login'))
        except Error as e:
            flash(f'Error creating account: {str(e)}', 'error')

    return render_template('register.html')

@app.route('/generate-invite', methods=['POST'])
def generate_invite():
    """Admin generates a one-time invite code."""
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    import secrets
    from datetime import timedelta

    role         = request.form.get('role', 'doctor')
    expiry_hours = int(request.form.get('expiry_hours', 24))

    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            code       = secrets.token_hex(8).upper()
            expires_at = datetime.now() + timedelta(hours=expiry_hours)
            cursor.execute("""
                INSERT INTO invite_codes (code, role, created_by, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (code, role, session['username'], expires_at))
            connection.commit()
            cursor.close(); connection.close()
            label = f"{expiry_hours} hour{'s' if expiry_hours != 1 else ''}"
            flash(f'Invite code generated: {code}  (valid for {label}, role: {role})', 'success')
    except Error as e:
        flash(f'Error generating code: {str(e)}', 'error')

    return redirect(url_for('manage_users'))

@app.route('/manage-users')
def manage_users():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))

    users = []
    invite_codes = []
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username, full_name, role, created_at FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
            cursor.execute("SELECT * FROM invite_codes ORDER BY created_at DESC LIMIT 20")
            invite_codes = cursor.fetchall()
            cursor.close(); connection.close()
    except Error as e:
        flash(f'Error loading users: {str(e)}', 'error')

    return render_template('manage_users.html', users=users, invite_codes=invite_codes, now=datetime.now())

@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user and user['username'] == 'admin':
                flash('Cannot delete the admin account.', 'error')
            else:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                connection.commit()
                flash('User deleted.', 'success')
            cursor.close(); connection.close()
    except Error as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('manage_users'))

# ── Patient ───────────────────────────────────────────────────────────────────

@app.route('/patient', methods=['GET', 'POST'])
def patient():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                aadhar_number = request.form.get('aadhar_number', '').strip()

                if aadhar_number:
                    cursor.execute(
                        "SELECT patient_id, patient_firstname, patient_lastname FROM patients WHERE aadhar_number = %s",
                        (aadhar_number,)
                    )
                    existing = cursor.fetchone()
                    if existing:
                        flash(f'Patient already exists! ID: {existing[0]}, Name: {existing[1]} {existing[2]}', 'error')
                        cursor.close(); connection.close()
                        return render_template('patient.html')

                patient_id = generate_patient_id(cursor)

                cursor.execute("""
                    INSERT INTO patients
                    (patient_id, patient_firstname, patient_middlename, patient_lastname,
                     patient_DOB, gender, email, phone, address, medical_history, allergies,
                     aadhar_number, emergency_contact, emergency_phone, marital_status, occupation)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    patient_id,
                    request.form.get('patient_firstname'),
                    request.form.get('patient_middlename') or None,
                    request.form.get('patient_lastname'),
                    request.form.get('patient_DOB'),
                    request.form.get('gender'),
                    request.form.get('email'),
                    request.form.get('phone'),
                    request.form.get('address'),
                    request.form.get('medical_history'),
                    request.form.get('allergies'),
                    aadhar_number or None,
                    request.form.get('emergency_contact'),
                    request.form.get('emergency_phone'),
                    request.form.get('marital_status'),
                    request.form.get('occupation')
                ))
                connection.commit()
                flash(f'Patient registered successfully! Patient ID: {patient_id}', 'success')
                cursor.close(); connection.close()
        except Error as e:
            flash(f'Error saving patient data: {str(e)}', 'error')

    return render_template('patient.html')

# ── Search Patient ─────────────────────────────────────────────────────────────

@app.route('/search-patient', methods=['GET', 'POST'])
def search_patient():
    if 'username' not in session:
        return redirect(url_for('login'))

    patient_data = None
    patient_list = []
    search_performed = False

    if request.method == 'POST':
        search_performed = True
        search_by = request.form.get('search_by')
        search_value = request.form.get('search_value', '').strip()

        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)

                if search_by == 'patient_id':
                    cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (search_value,))
                    patient_list = cursor.fetchall()
                elif search_by == 'aadhar':
                    cursor.execute("SELECT * FROM patients WHERE aadhar_number = %s", (search_value,))
                    patient_list = cursor.fetchall()
                elif search_by == 'name':
                    like = f"%{search_value}%"
                    cursor.execute("""
                        SELECT * FROM patients
                        WHERE patient_firstname LIKE %s
                           OR patient_lastname LIKE %s
                           OR CONCAT(patient_firstname,' ',patient_lastname) LIKE %s
                           OR CONCAT(patient_firstname,' ',IFNULL(patient_middlename,''),' ',patient_lastname) LIKE %s
                        ORDER BY patient_firstname
                    """, (like, like, like, like))
                    patient_list = cursor.fetchall()

                # If exactly one result, load full details directly
                if len(patient_list) == 1:
                    patient_data = patient_list[0]
                    patient_list = []
                    pid = patient_data['patient_id']
                    for tbl, key, order in [
                        ('malaria_ai_results', 'malaria_results', 'analysis_date'),
                        ('appointments', 'appointments', 'appointment_date'),
                        ('diagnosis', 'diagnosis', 'diagnosis_date'),
                        ('lab_reports', 'lab_reports', 'test_date'),
                        ('treatment', 'treatments', 'treatment_date'),
                        ('radiology_requests', 'radiology', 'request_date'),
                        ('pathology_requests', 'pathology', 'request_date'),
                    ]:
                        cursor.execute(f"SELECT * FROM {tbl} WHERE patient_id = %s ORDER BY {order} DESC", (pid,))
                        patient_data[key] = cursor.fetchall()

                cursor.close()
                connection.close()
        except Error as e:
            flash(f'Error searching patient: {str(e)}', 'error')

    return render_template('search_patient.html',
                           patient=patient_data,
                           patient_list=patient_list,
                           search_performed=search_performed)

@app.route('/patient-detail/<patient_id>')
def patient_detail(patient_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    patient_data = None
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            patient_data = cursor.fetchone()
            if patient_data:
                for tbl, key, order in [
                    ('malaria_ai_results', 'malaria_results', 'analysis_date'),
                    ('appointments', 'appointments', 'appointment_date'),
                    ('diagnosis', 'diagnosis', 'diagnosis_date'),
                    ('lab_reports', 'lab_reports', 'test_date'),
                    ('treatment', 'treatments', 'treatment_date'),
                    ('radiology_requests', 'radiology', 'request_date'),
                    ('pathology_requests', 'pathology', 'request_date'),
                ]:
                    cursor.execute(f"SELECT * FROM {tbl} WHERE patient_id = %s ORDER BY {order} DESC", (patient_id,))
                    patient_data[key] = cursor.fetchall()
            cursor.close()
            connection.close()
    except Error as e:
        flash(f'Error loading patient: {str(e)}', 'error')

    return render_template('search_patient.html',
                           patient=patient_data,
                           patient_list=[],
                           search_performed=True)

# ── Malaria Detector ──────────────────────────────────────────────────────────

@app.route('/malaria-detector')
def malaria_detector():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('malaria_detector.html')

@app.route('/api/predict-malaria', methods=['POST'])
def predict_malaria():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        contact = request.form.get('contact')
        symptoms = request.form.get('symptoms', '')
        doctor_name = request.form.get('doctor_name', 'Dr. Medical Professional')
        patient_id = request.form.get('patient_id', '').strip()

        if patient_id:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT patient_id FROM patients WHERE patient_id = %s", (patient_id,))
                if not cursor.fetchone():
                    cursor.close(); connection.close()
                    return jsonify({'error': f'Patient ID {patient_id} not found.'}), 400
                cursor.close(); connection.close()

        if 'image' not in request.files or request.files['image'].filename == '':
            return jsonify({'error': 'No image provided'}), 400

        file = request.files['image']
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name.replace(' ', '_')}_{timestamp}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        image.save(filepath)

        processed_image = preprocess_image(image)
        load_model_safe()
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 500

        prediction = model.predict(processed_image, verbose=0)
        confidence = float(prediction[0][0])
        is_infected = confidence < 0.5
        result = 'Infected' if is_infected else 'Uninfected'
        confidence_percent = (1 - confidence) * 100 if is_infected else confidence * 100
        severity = get_severity_level(confidence_percent) if is_infected else 'N/A'
        treatment = get_treatment_recommendation(result, severity)

        connection = get_db_connection()
        malaria_id = None
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO malaria_ai_results
                (patient_id, patient_name, age, gender, contact, symptoms,
                 doctor_name, result, confidence, severity, treatment, image_path, analyzed_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                patient_id or None, name, int(age) if age else None, gender,
                contact, symptoms, doctor_name, result,
                round(confidence_percent, 2), severity, treatment,
                filepath, session['username']
            ))
            connection.commit()
            malaria_id = cursor.lastrowid
            cursor.close(); connection.close()

        display_id = patient_id if patient_id else f"MAL-{datetime.now().strftime('%Y%m%d')}-{malaria_id:04d}"
        return jsonify({
            'success': True, 'result': result,
            'confidence': round(confidence_percent, 2), 'severity': severity,
            'treatment': treatment, 'patient_id': display_id,
            'image_url': f'/static/uploads/{filename}',
            'analysis_date': datetime.now().strftime('%m/%d/%Y'),
            'analysis_time': datetime.now().strftime('%I:%M:%S %p')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/malaria-statistics')
def malaria_statistics():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM malaria_ai_results")
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as infected FROM malaria_ai_results WHERE result = 'Infected'")
            infected = cursor.fetchone()['infected']
            cursor.execute("""
                SELECT severity, COUNT(*) as count FROM malaria_ai_results
                WHERE result = 'Infected' AND severity != 'N/A' GROUP BY severity
            """)
            severity_counts = {'Critical': 0, 'High': 0, 'Moderate': 0, 'Low': 0}
            for row in cursor.fetchall():
                severity_counts[row['severity']] = row['count']
            cursor.close(); connection.close()
            return jsonify({
                'success': True, 'total': total, 'infected': infected,
                'uninfected': total - infected,
                'infection_rate': round((infected / total * 100) if total > 0 else 0, 2),
                'severity_counts': severity_counts
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Appointment ───────────────────────────────────────────────────────────────

@app.route('/api/search-patients')
def api_search_patients():
    """Live patient search for autocomplete dropdowns."""
    if 'username' not in session:
        return jsonify([])
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            like = f"%{q}%"
            cursor.execute("""
                SELECT patient_id,
                       CONCAT(patient_firstname, ' ',
                              IFNULL(CONCAT(patient_middlename, ' '), ''),
                              patient_lastname) AS full_name,
                       patient_DOB, phone, aadhar_number
                FROM patients
                WHERE patient_firstname LIKE %s
                   OR patient_lastname  LIKE %s
                   OR CONCAT(patient_firstname,' ',patient_lastname) LIKE %s
                ORDER BY patient_firstname
                LIMIT 10
            """, (like, like, like))
            results = cursor.fetchall()
            cursor.close(); connection.close()
            return jsonify([{
                'patient_id': r['patient_id'],
                'full_name':  r['full_name'].strip(),
                'dob':        str(r['patient_DOB']) if r['patient_DOB'] else '',
                'phone':      r['phone'] or '',
                'aadhar':     r['aadhar_number'] or ''
            } for r in results])
    except Error:
        pass
    return jsonify([])

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                patient_name = request.form.get('patient_name', '').strip()
                patient_id = request.form.get('patient_id', '').strip()

                # Auto-lookup patient_id from name if not provided
                if not patient_id and patient_name:
                    patient_id = lookup_patient_by_name(cursor, patient_name) or None

                appointment_id = generate_record_id('APT', cursor, 'appointments', 'appointment_id')
                cursor.execute("""
                    INSERT INTO appointments
                    (appointment_id, patient_id, patient_name, patient_email,
                     doctor_name, appointment_date, appointment_time)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (
                    appointment_id, patient_id or None, patient_name,
                    request.form.get('patient_email'),
                    request.form.get('doctor_name'),
                    request.form.get('appointment_date'),
                    request.form.get('appointment_time')
                ))
                connection.commit()
                flash(f'Appointment scheduled! ID: {appointment_id}', 'success')
                cursor.close(); connection.close()
        except Error as e:
            flash(f'Error scheduling appointment: {str(e)}', 'error')
    return render_template('appointment.html')

# ── Diagnosis ─────────────────────────────────────────────────────────────────

@app.route('/diagnosis', methods=['GET', 'POST'])
def diagnosis():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                patient_name = request.form.get('patient_name', '').strip()
                patient_id = request.form.get('patient_id', '').strip()
                if not patient_id and patient_name:
                    patient_id = lookup_patient_by_name(cursor, patient_name) or None

                diagnosis_id = generate_record_id('DIA', cursor, 'diagnosis', 'diagnosis_id')
                cursor.execute("""
                    INSERT INTO diagnosis
                    (diagnosis_id, patient_id, patient_name, diagnosis_date, symptoms,
                     observations, provisional_diagnosis, tests, final_diagnosis,
                     treatment_plan, follow_up)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    diagnosis_id, patient_id or None, patient_name,
                    request.form.get('diagnosis_date'),
                    request.form.get('symptoms'), request.form.get('observations'),
                    request.form.get('provisional_diagnosis'), request.form.get('tests'),
                    request.form.get('final_diagnosis'), request.form.get('treatment_plan'),
                    request.form.get('follow_up')
                ))
                connection.commit()
                flash(f'Diagnosis saved! ID: {diagnosis_id}', 'success')
                cursor.close(); connection.close()
        except Error as e:
            flash(f'Error saving diagnosis: {str(e)}', 'error')
    return render_template('diagnosis.html')

# ── Lab Report ────────────────────────────────────────────────────────────────

@app.route('/lab-report', methods=['GET', 'POST'])
def lab_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                patient_name = request.form.get('patient_name', '').strip()
                patient_id = request.form.get('patient_id', '').strip()
                if not patient_id and patient_name:
                    patient_id = lookup_patient_by_name(cursor, patient_name) or None

                report_id = generate_record_id('LAB', cursor, 'lab_reports', 'report_id')
                cursor.execute("""
                    INSERT INTO lab_reports
                    (report_id, patient_id, patient_name, test_date, physician,
                     hemoglobin, rbc, wbc, platelets, glucose, urea, creatinine,
                     cholesterol, microbiology_findings, xray, ct_scan, mri,
                     ultrasound, other_tests)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    report_id, patient_id or None, patient_name,
                    request.form.get('test_date'), request.form.get('physician'),
                    request.form.get('hemoglobin'), request.form.get('rbc'),
                    request.form.get('wbc'), request.form.get('platelets'),
                    request.form.get('glucose'), request.form.get('urea'),
                    request.form.get('creatinine'), request.form.get('cholesterol'),
                    request.form.get('microbiology_findings'), request.form.get('xray'),
                    request.form.get('ct_scan'), request.form.get('mri'),
                    request.form.get('ultrasound'), request.form.get('other_tests')
                ))
                connection.commit()
                flash(f'Lab report saved! ID: {report_id}', 'success')
                cursor.close(); connection.close()
        except Error as e:
            flash(f'Error saving lab report: {str(e)}', 'error')
    return render_template('lab_report.html')

# ── Medical History ───────────────────────────────────────────────────────────

@app.route('/medical-history', methods=['GET', 'POST'])
def medical_history():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                patient_name = request.form.get('patient_name', '').strip()
                patient_id = request.form.get('patient_id', '').strip()
                if not patient_id and patient_name:
                    patient_id = lookup_patient_by_name(cursor, patient_name) or None

                record_id = generate_record_id('MED', cursor, 'medical_history', 'record_id')
                cursor.execute("""
                    INSERT INTO medical_history
                    (record_id, patient_id, patient_name, chronic_illnesses, surgeries,
                     current_medications, allergies, hospitalizations, family_history,
                     immunizations, social_history, other_conditions)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    record_id, patient_id or None, patient_name,
                    request.form.get('chronic_illnesses'), request.form.get('surgeries'),
                    request.form.get('current_medications'), request.form.get('allergies'),
                    request.form.get('hospitalizations'), request.form.get('family_history'),
                    request.form.get('immunizations'), request.form.get('social_history'),
                    request.form.get('other_conditions')
                ))
                connection.commit()
                flash(f'Medical history saved! ID: {record_id}', 'success')
                cursor.close(); connection.close()
        except Error as e:
            flash(f'Error saving medical history: {str(e)}', 'error')
    return render_template('medical_history.html')

# ── Treatment ─────────────────────────────────────────────────────────────────

@app.route('/treatment', methods=['GET', 'POST'])
def treatment():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                patient_name = request.form.get('patient_name', '').strip()
                patient_id = request.form.get('patient_id', '').strip()
                if not patient_id and patient_name:
                    patient_id = lookup_patient_by_name(cursor, patient_name) or None

                treatment_id = generate_record_id('TRT', cursor, 'treatment', 'treatment_id')
                cursor.execute("""
                    INSERT INTO treatment
                    (treatment_id, patient_id, patient_name, treatment_date, diagnosis,
                     medications, procedures, therapy_plan, diet, lifestyle,
                     follow_up, additional_notes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    treatment_id, patient_id or None, patient_name,
                    request.form.get('treatment_date'), request.form.get('diagnosis'),
                    request.form.get('medications'), request.form.get('procedures'),
                    request.form.get('therapy_plan'), request.form.get('diet'),
                    request.form.get('lifestyle'), request.form.get('follow_up'),
                    request.form.get('additional_notes')
                ))
                connection.commit()
                flash(f'Treatment plan saved! ID: {treatment_id}', 'success')
                cursor.close(); connection.close()
        except Error as e:
            flash(f'Error saving treatment: {str(e)}', 'error')
    return render_template('treatment.html')

# ── Radiology ─────────────────────────────────────────────────────────────────

@app.route('/radiology-update/<request_id>', methods=['POST'])
def radiology_update(request_id):
    """Upload result image and findings to an existing radiology request."""
    if 'username' not in session:
        return redirect(url_for('login'))
    patient_id = request.form.get('patient_id', '').strip()
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            # Verify request exists
            cursor.execute("SELECT * FROM radiology_requests WHERE request_id = %s", (request_id,))
            rec = cursor.fetchone()
            if not rec:
                flash(f'Radiology request {request_id} not found.', 'error')
                cursor.close(); connection.close()
                return redirect(url_for('patient_detail', patient_id=patient_id))

            image_path = rec['image_path']  # keep existing if no new upload
            if 'result_image' in request.files and request.files['result_image'].filename != '':
                file = request.files['result_image']
                rad_dir = os.path.join('static', 'uploads', 'radiology')
                os.makedirs(rad_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{request_id}_{timestamp}{os.path.splitext(file.filename)[1]}"
                filepath = os.path.join(rad_dir, filename)
                file.save(filepath)
                image_path = filepath.replace('\\', '/')

            cursor.execute("""
                UPDATE radiology_requests
                SET radiologist_findings = %s, reported_by = %s, image_path = %s
                WHERE request_id = %s
            """, (
                request.form.get('radiologist_findings'),
                request.form.get('reported_by'),
                image_path,
                request_id
            ))
            connection.commit()
            flash(f'Radiology result updated for {request_id}', 'success')
            cursor.close(); connection.close()
    except Error as e:
        flash(f'Error updating radiology result: {str(e)}', 'error')

    return redirect(url_for('patient_detail', patient_id=patient_id))


@app.route('/pathology-update/<pathology_id>', methods=['POST'])
def pathology_update(pathology_id):
    """Upload result notes and image to an existing pathology request."""
    if 'username' not in session:
        return redirect(url_for('login'))
    patient_id = request.form.get('patient_id', '').strip()
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM pathology_requests WHERE pathology_id = %s", (pathology_id,))
            rec = cursor.fetchone()
            if not rec:
                flash(f'Pathology request {pathology_id} not found.', 'error')
                cursor.close(); connection.close()
                return redirect(url_for('patient_detail', patient_id=patient_id))

            result_image = rec.get('result_image')
            if 'result_image' in request.files and request.files['result_image'].filename != '':
                file = request.files['result_image']
                path_dir = os.path.join('static', 'uploads', 'pathology')
                os.makedirs(path_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{pathology_id}_{timestamp}{os.path.splitext(file.filename)[1]}"
                filepath = os.path.join(path_dir, filename)
                file.save(filepath)
                result_image = filepath.replace('\\', '/')

            cursor.execute("""
                UPDATE pathology_requests
                SET result_notes = %s, reported_by = %s, result_image = %s
                WHERE pathology_id = %s
            """, (
                request.form.get('result_notes'),
                request.form.get('reported_by'),
                result_image,
                pathology_id
            ))
            connection.commit()
            flash(f'Pathology result updated for {pathology_id}', 'success')
            cursor.close(); connection.close()
    except Error as e:
        flash(f'Error updating pathology result: {str(e)}', 'error')
    return redirect(url_for('patient_detail', patient_id=patient_id))


@app.route('/pathology', methods=['GET', 'POST'])
def pathology():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                patient_id = request.form.get('patient_id', '').strip() or None
                patient_name = request.form.get('patient_name', '').strip()
                if not patient_id and patient_name:
                    patient_id = lookup_patient_by_name(cursor, patient_name) or None
                pathology_id = generate_record_id('PATH', cursor, 'pathology_requests', 'pathology_id')
                cursor.execute("""
                    INSERT INTO pathology_requests
                    (pathology_id, patient_id, patient_name, doctor_name, test_date, request_date,
                     lab, favourite_tests, test_list, clinical_details,
                     last_cytology, cytology_date, hpv_not_required, hpv_reason,
                     pregnancy_status, contraception_method, abnormal_bleeding,
                     clinical_notes, copy_to, collection_by, fasting_status, billing_type)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    pathology_id, patient_id, patient_name,
                    request.form.get('doctor_name'),
                    request.form.get('test_date') or None,
                    request.form.get('request_date') or None,
                    request.form.get('lab'),
                    request.form.get('favourite_tests'),
                    request.form.get('test_list'),
                    request.form.get('clinical_details'),
                    1 if request.form.get('last_cytology') else 0,
                    request.form.get('cytology_date') or None,
                    1 if request.form.get('hpv_not_required') else 0,
                    request.form.get('hpv_reason'),
                    request.form.get('pregnancy_status'),
                    request.form.get('contraception_method'),
                    request.form.get('abnormal_bleeding') or None,
                    request.form.get('clinical_notes'),
                    request.form.get('copy_to'),
                    request.form.get('collection_by'),
                    request.form.get('fasting_status'),
                    request.form.get('billing_type') or None
                ))
                connection.commit()
                flash(f'Pathology request saved! ID: {pathology_id}', 'success')
                cursor.close(); connection.close()
        except Error as e:
            flash(f'Error saving pathology request: {str(e)}', 'error')
    return render_template('pathology.html')


@app.route('/radiology', methods=['GET', 'POST'])
def radiology():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                patient_id = request.form.get('patient_id', '').strip() or None
                patient_name = request.form.get('patient_name', '').strip()
                request_id = generate_record_id('RAD', cursor, 'radiology_requests', 'request_id')

                # Handle image upload
                image_path = None
                if 'result_image' in request.files and request.files['result_image'].filename != '':
                    file = request.files['result_image']
                    rad_dir = os.path.join('static', 'uploads', 'radiology')
                    os.makedirs(rad_dir, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_name = (patient_name or 'unknown').replace(' ', '_')
                    filename = f"{safe_name}_{request_id}_{timestamp}{os.path.splitext(file.filename)[1]}"
                    filepath = os.path.join(rad_dir, filename)
                    file.save(filepath)
                    image_path = filepath.replace('\\', '/')

                cursor.execute("""
                    INSERT INTO radiology_requests
                    (request_id, patient_id, patient_name, request_date, laboratory, test_type,
                     side_left, side_right, region, other_region, requests_printed,
                     other_test, clinical_details, details_form, add_entry, due_date,
                     radiologist_findings, image_path, reported_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    request_id, patient_id, patient_name,
                    request.form.get('request_date'), request.form.get('laboratory'),
                    request.form.get('test_type'), request.form.get('side_left'),
                    request.form.get('side_right'), request.form.get('region'),
                    request.form.get('other_region'), request.form.get('requests_printed'),
                    request.form.get('other_test'), request.form.get('clinical_details'),
                    request.form.get('details_form'), request.form.get('add_entry'),
                    request.form.get('due_date') or None,
                    request.form.get('radiologist_findings'),
                    image_path, request.form.get('reported_by')
                ))
                connection.commit()
                flash(f'Radiology record saved! ID: {request_id}', 'success')
                cursor.close(); connection.close()
        except Error as e:
            flash(f'Error saving radiology request: {str(e)}', 'error')
    return render_template('radiology.html')

# ── API: register user (for Postman testing) ──────────────────────────────────

@app.route('/api/register-user', methods=['POST'])
def api_register_user():
    """Create a new user — test via Postman. Body: {username, password, role}"""
    import bcrypt as _bcrypt
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'username and password required'}), 400
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            hashed = _bcrypt.hashpw(data['password'].encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (data['username'], hashed, data.get('role', 'doctor'))
            )
            connection.commit()
            cursor.close(); connection.close()
            return jsonify({'success': True, 'message': f"User '{data['username']}' created"}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def api_login():
    """Test login via Postman. Body: {username, password}"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    user = verify_user(data.get('username', ''), data.get('password', ''))
    if user:
        return jsonify({'success': True, 'username': user['username'], 'role': user['role']})
    return jsonify({'error': 'Invalid credentials'}), 401

# ── Analytics Dashboard ───────────────────────────────────────────────────────

@app.route('/analytics')
def analytics():
    if 'username' not in session:
        return redirect(url_for('login'))

    period = request.args.get('period', '1')  # months
    try:
        period = int(period)
    except:
        period = 1

    data = {}
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)

            # Total patients (all time)
            cursor.execute("SELECT COUNT(*) as total FROM patients")
            data['total_patients'] = cursor.fetchone()['total']

            # Patients in selected period
            cursor.execute("SELECT COUNT(*) as cnt FROM patients WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s MONTH)", (period,))
            data['period_patients'] = cursor.fetchone()['cnt']

            # Patients per month (last 12 months) for line chart
            cursor.execute("""
                SELECT DATE_FORMAT(created_at, '%Y-%m') as month, COUNT(*) as cnt
                FROM patients WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                GROUP BY month ORDER BY month
            """)
            data['patients_by_month'] = cursor.fetchall()

            # Malaria stats
            cursor.execute("SELECT COUNT(*) as total FROM malaria_ai_results")
            data['total_malaria'] = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as cnt FROM malaria_ai_results WHERE result='Infected'")
            data['malaria_infected'] = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) as cnt FROM malaria_ai_results WHERE result='Uninfected'")
            data['malaria_uninfected'] = cursor.fetchone()['cnt']

            # Malaria by severity
            cursor.execute("""
                SELECT severity, COUNT(*) as cnt FROM malaria_ai_results
                WHERE result='Infected' GROUP BY severity
            """)
            data['malaria_severity'] = cursor.fetchall()

            # Malaria per month
            cursor.execute("""
                SELECT DATE_FORMAT(analysis_date,'%Y-%m') as month,
                       SUM(result='Infected') as infected,
                       SUM(result='Uninfected') as uninfected
                FROM malaria_ai_results WHERE analysis_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                GROUP BY month ORDER BY month
            """)
            data['malaria_by_month'] = cursor.fetchall()

            # Gender distribution
            cursor.execute("SELECT gender, COUNT(*) as cnt FROM patients GROUP BY gender")
            data['gender_dist'] = cursor.fetchall()

            # Appointments by status
            cursor.execute("SELECT status, COUNT(*) as cnt FROM appointments GROUP BY status")
            data['apt_status'] = cursor.fetchall()

            # Module activity counts
            cursor.execute("SELECT COUNT(*) as cnt FROM appointments WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s MONTH)", (period,))
            data['period_appointments'] = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) as cnt FROM diagnosis WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s MONTH)", (period,))
            data['period_diagnosis'] = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) as cnt FROM lab_reports WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s MONTH)", (period,))
            data['period_labs'] = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) as cnt FROM treatment WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s MONTH)", (period,))
            data['period_treatments'] = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) as cnt FROM radiology_requests WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s MONTH)", (period,))
            data['period_radiology'] = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) as cnt FROM pathology_requests WHERE submitted_at >= DATE_SUB(NOW(), INTERVAL %s MONTH)", (period,))
            data['period_pathology'] = cursor.fetchone()['cnt']

            # Top 5 recent patients
            cursor.execute("SELECT patient_id, patient_firstname, patient_lastname, gender, created_at FROM patients ORDER BY created_at DESC LIMIT 5")
            data['recent_patients'] = cursor.fetchall()

            cursor.close(); connection.close()
    except Error as e:
        flash(f'Error loading analytics: {str(e)}', 'error')

    return render_template('analytics.html', data=data, period=period)


# ── Edit routes ───────────────────────────────────────────────────────────────

# Map: record_type -> (table, primary_key_col, redirect_col)
EDIT_CONFIG = {
    'appointment': ('appointments', 'appointment_id', 'patient_id'),
    'diagnosis':   ('diagnosis',    'diagnosis_id',   'patient_id'),
    'lab_report':  ('lab_reports',  'report_id',      'patient_id'),
    'treatment':   ('treatment',    'treatment_id',   'patient_id'),
    'medical_history': ('medical_history', 'record_id', 'patient_id'),
}

@app.route('/edit-patient/<patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    cursor = connection.cursor(dictionary=True)
    if request.method == 'POST':
        try:
            cursor.execute("""
                UPDATE patients SET
                    patient_firstname=%s, patient_middlename=%s, patient_lastname=%s,
                    patient_DOB=%s, gender=%s, email=%s, phone=%s, address=%s,
                    medical_history=%s, allergies=%s, aadhar_number=%s,
                    emergency_contact=%s, emergency_phone=%s,
                    marital_status=%s, occupation=%s
                WHERE patient_id=%s
            """, (
                request.form.get('patient_firstname'),
                request.form.get('patient_middlename') or None,
                request.form.get('patient_lastname'),
                request.form.get('patient_DOB'),
                request.form.get('gender'),
                request.form.get('email'),
                request.form.get('phone'),
                request.form.get('address'),
                request.form.get('medical_history'),
                request.form.get('allergies'),
                request.form.get('aadhar_number') or None,
                request.form.get('emergency_contact'),
                request.form.get('emergency_phone'),
                request.form.get('marital_status'),
                request.form.get('occupation'),
                patient_id
            ))
            connection.commit()
            flash('Patient details updated successfully.', 'success')
            cursor.close(); connection.close()
            return redirect(url_for('patient_detail', patient_id=patient_id))
        except Error as e:
            flash(f'Error updating patient: {str(e)}', 'error')
    cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
    patient = cursor.fetchone()
    cursor.close(); connection.close()
    if not patient:
        flash('Patient not found.', 'error')
        return redirect(url_for('search_patient'))
    return render_template('edit_patient.html', patient=patient)


@app.route('/edit/<record_type>/<record_id>', methods=['GET', 'POST'])
def edit_record(record_type, record_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if record_type not in EDIT_CONFIG:
        flash('Unknown record type.', 'error')
        return redirect(url_for('dashboard'))

    table, pk_col, pid_col = EDIT_CONFIG[record_type]
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed.', 'error')
        return redirect(url_for('dashboard'))
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            fields = {k: (v if v != '' else None) for k, v in request.form.items() if k != pk_col}
            set_clause = ', '.join(f"`{k}` = %s" for k in fields)
            values = list(fields.values()) + [record_id]
            cursor.execute(f"UPDATE `{table}` SET {set_clause} WHERE `{pk_col}` = %s", values)
            connection.commit()
            patient_id = request.form.get('patient_id', '')
            flash(f'Record updated successfully.', 'success')
            cursor.close(); connection.close()
            return redirect(url_for('patient_detail', patient_id=patient_id))
        except Error as e:
            flash(f'Error updating record: {str(e)}', 'error')

    cursor.execute(f"SELECT * FROM `{table}` WHERE `{pk_col}` = %s", (record_id,))
    record = cursor.fetchone()
    cursor.close(); connection.close()
    if not record:
        flash('Record not found.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('edit_record.html', record=record, record_type=record_type, record_id=record_id)


if __name__ == '__main__':
    port = int(os.environ.get("PORT") or 5001)
    app.run(host="0.0.0.0", port=port, debug=False)
