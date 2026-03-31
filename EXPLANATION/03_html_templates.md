# HTML Templates — Explanation

Templates are the pages the user actually sees in the browser.
They are HTML files with special Flask/Jinja2 tags mixed in.

---

## What is HTML?

HTML = HyperText Markup Language. It's just tags that describe content.

```html
<h1>Big Heading</h1>
<h3>Smaller Heading</h3>
<p>A paragraph of text</p>
<a href="/dashboard">Click here</a>   <!-- a link -->
<button>Submit</button>
<input type="text" name="username">   <!-- text box -->
<select>                               <!-- dropdown -->
    <option value="Male">Male</option>
</select>
<textarea rows="3"></textarea>         <!-- multi-line text box -->
```

---

## base.html — The Master Template

Every page extends base.html. It contains the common structure.

```html
<!DOCTYPE html>          <!-- tells browser this is HTML5 -->
<html lang="en">
<head>
    <title>{% block title %}{% endblock %}</title>   <!-- page title -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <!-- loads the CSS file. url_for generates the correct path automatically -->
</head>
<body>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    <!-- This shows flash messages like "Patient saved!" at the top of every page -->

    {% block content %}{% endblock %}
    <!-- Each child page fills in this block with its own content -->
</body>
```

`{% block content %}{% endblock %}` is like a placeholder.
Each page fills it in.

---

## How a Child Template Works (e.g. dashboard.html)

```html
{% extends "base.html" %}          <!-- use base.html as the wrapper -->

{% block title %}Dashboard{% endblock %}   <!-- fill in the title -->

{% block content %}                <!-- fill in the main content -->
<div class="dashboard-container">
    <h1>Welcome, {{ username }}</h1>   <!-- {{ }} = show a Python variable -->

    {% if session.get('role') == 'admin' %}   <!-- {% %} = Python logic -->
        <a href="/manage-users">Admin Panel</a>
    {% endif %}
</div>
{% endblock %}
```

The two special syntaxes:
- `{{ variable }}` — display a value (like print in Python)
- `{% statement %}` — run logic (if, for, etc.)

---

## Forms — How Data Gets to Flask

```html
<form method="POST" action="{{ url_for('patient') }}">
    <!-- method="POST" = send data to Flask -->
    <!-- action = which Flask route to send it to -->

    <input type="text" name="patient_firstname" required>
    <!-- name="patient_firstname" is how Flask reads it:
         request.form.get('patient_firstname') -->

    <button type="submit">Register Patient</button>
</form>
```

The flow:
1. User fills form and clicks Submit
2. Browser sends POST request to Flask with all the form data
3. Flask reads it with `request.form.get('field_name')`
4. Flask saves to MySQL
5. Flask sends back a page with flash message

---

## Jinja2 Loops (used in search results)

```html
{% for patient in patient_list %}
<tr>
    <td>{{ patient.patient_id }}</td>
    <td>{{ patient.patient_firstname }}</td>
</tr>
{% endfor %}
```
- Flask passes a list of patients from MySQL
- Jinja2 loops through each one and creates a table row
- Same as a Python for loop, just inside HTML

---

## The Navbar (in every page)

```html
<nav class="navbar">
    <div class="navbar-brand">
        <h2>🏥 Hospital Management System</h2>
    </div>
    <div class="navbar-user">
        <a href="{{ url_for('dashboard') }}" class="btn-back">← Back</a>
        <a href="{{ url_for('logout') }}" class="btn-logout">Logout</a>
    </div>
</nav>
```
- `url_for('dashboard')` generates `/dashboard` — safer than hardcoding
- `class="btn-back"` — CSS will style this as a button (defined in style.css)
