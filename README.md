# Hospital Management System

A simple and clean hospital management website built with Python Flask.

## Features

- User authentication (Login/Logout)
- Dashboard with 8 modules:
  - Patient Management
  - Malaria AI Detector (ready for AI model integration)
  - Appointment Management
  - Diagnosis
  - Lab Report
  - Medical History
  - Treatment
  - Radiology Result

## Project Structure

```
hospital-management/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── dashboard.html    # Dashboard page
│   ├── patient.html      # Patient module
│   ├── malaria_detector.html  # Malaria AI Detector
│   ├── appointment.html  # Appointment module
│   ├── diagnosis.html    # Diagnosis module
│   ├── lab_report.html   # Lab Report module
│   ├── medical_history.html  # Medical History module
│   ├── treatment.html    # Treatment module
│   └── radiology.html    # Radiology module
│
└── static/               # Static files
    └── css/
        └── style.css     # CSS styling
```

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Step 1: Install Python
Make sure Python is installed on your system. Check by running:
```bash
python --version
```

### Step 2: Install Flask
Install the required dependencies:
```bash
pip install -r requirements.txt
```

Or install Flask directly:
```bash
pip install Flask
```

### Step 3: Run the Application
```bash
python app.py
```

The application will start on `http://127.0.0.1:5000/`

### Step 4: Access the Website
Open your browser and go to:
```
http://127.0.0.1:5000/
```

## Login Credentials

Use these demo credentials to login:

- **Admin Account**
  - Username: `admin`
  - Password: `admin123`

- **Doctor Account**
  - Username: `doctor`
  - Password: `doctor123`

## How to Integrate Malaria AI Model

The Malaria AI Detector module is ready for integration. To add your AI model:

1. Install required ML libraries (e.g., TensorFlow, PyTorch)
2. Add your trained model file to the project
3. Update `app.py` to add model loading and prediction logic
4. Update `templates/malaria_detector.html` to add image upload form
5. Create prediction route to handle image processing

Example integration code:
```python
from tensorflow import keras
import numpy as np

# Load model
model = keras.models.load_model('malaria_model.h5')

@app.route('/predict-malaria', methods=['POST'])
def predict_malaria():
    if 'image' in request.files:
        image = request.files['image']
        # Process image and make prediction
        # Return results
    return render_template('malaria_detector.html', result=result)
```

## Customization

### Adding New Users
Edit the `USERS` dictionary in `app.py`:
```python
USERS = {
    'admin': 'admin123',
    'doctor': 'doctor123',
    'newuser': 'password'
}
```

### Changing Colors
Edit `static/css/style.css` to customize the color scheme.

### Adding Database
For production use, replace the simple dictionary with a proper database:
- SQLite (simple, file-based)
- PostgreSQL (production-ready)
- MySQL (popular choice)

Use Flask-SQLAlchemy for easy database integration.

## Future Enhancements

- Database integration for data persistence
- User registration system
- Role-based access control
- Complete CRUD operations for each module
- File upload functionality
- Report generation (PDF)
- Email notifications
- Search and filter functionality
- Data visualization with charts

## Security Notes

- Change the `secret_key` in `app.py` before deployment
- Use environment variables for sensitive data
- Implement proper password hashing (use werkzeug.security)
- Add CSRF protection
- Use HTTPS in production

## License

This project is open source and available for educational purposes.
