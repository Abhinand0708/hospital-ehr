# JavaScript — Explanation

JavaScript (JS) runs IN THE BROWSER. It makes pages interactive without reloading.
Flask runs on the server. JS runs on the client (user's computer).

---

## Where JS is in your project

1. Inside `base.html` — the patient autocomplete search
2. Inside `malaria_detector.html` — image upload, form submit, show results

---

## PART 1 — Patient Autocomplete (base.html)

### What it does:
User types "abhi" → JS asks Flask for matching patients → shows dropdown → user clicks → Patient ID fills automatically.

```javascript
function initPatientSearch(nameInputId, idInputId, confirmId) {
    const nameInput = document.getElementById(nameInputId);
    // document.getElementById() = find an HTML element by its id
    // Like: find the input box with id="patient_name"
```

```javascript
    nameInput.addEventListener('input', () => {
        // addEventListener = "watch for an event"
        // 'input' event = fires every time user types a character
        // () => { } = arrow function (runs when event happens)

        const q = nameInput.value.trim();
        // .value = what's currently typed in the box
        // .trim() = remove spaces from start/end

        if (q.length < 2) {
            dropdown.classList.remove('open');
            return;   // stop here if less than 2 characters typed
        }

        debounce = setTimeout(() => fetchPatients(q), 250);
        // setTimeout = wait 250ms before running
        // This prevents sending a request on EVERY keystroke
        // User types "a", "b", "h", "i" — only sends after they pause
    });
```

```javascript
    function fetchPatients(q) {
        fetch(`/api/search-patients?q=${encodeURIComponent(q)}`)
        // fetch() = make an HTTP request from JavaScript
        // This calls the Flask route /api/search-patients
        // encodeURIComponent() = makes the text URL-safe

        .then(r => r.json())
        // .then() = when response arrives, do this
        // r.json() = parse the response as JSON

        .then(data => {
            // data = array of patient objects from Flask
            // e.g. [{patient_id: "2026031601", full_name: "Abhinand", ...}]

            data.forEach(p => {
                const div = document.createElement('div');
                // createElement = create a new HTML element in memory

                div.innerHTML = `
                    <div class="pd-name">${p.full_name}</div>
                    <div class="pd-meta">ID: ${p.patient_id} · DOB: ${p.dob}</div>
                `;
                // innerHTML = set the HTML content of the div
                // Template literals (backticks) allow variables inside ${}

                div.addEventListener('click', () => {
                    nameInput.value = p.full_name;   // fill name box
                    idInput.value = p.patient_id;    // fill ID box
                    dropdown.classList.remove('open'); // close dropdown
                });

                dropdown.appendChild(div);
                // appendChild = add this div inside the dropdown
            });
        });
    }
```

---

## PART 2 — Malaria Form Submission (malaria_detector.html)

### Why JS instead of normal form submit?
Normal form submit = page reloads. With JS we can show results on the SAME page without reloading.

```javascript
document.getElementById('malariaForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    // e.preventDefault() = STOP the normal form submission
    // Without this, the page would reload

    const formData = new FormData(this);
    // FormData = collects all form fields including the image file
    // 'this' = the form element itself
```

```javascript
    const response = await fetch('/api/predict-malaria', {
        method: 'POST',      // POST request (sending data)
        body: formData,      // attach the form data
        credentials: 'same-origin'  // send cookies (for session/login check)
    });
    // await = wait for the response before continuing
    // async function = allows using await inside it
```

```javascript
    const data = await response.json();
    // Parse the JSON response from Flask
    // data = {success: true, result: "Infected", confidence: 95.7, ...}

    if (data.success) {
        document.getElementById('analysisForm').style.display = 'none';
        // hide the form

        document.getElementById('resultContainer').style.display = 'block';
        // show the results section

        document.getElementById('resultTitle').textContent = data.result;
        // set the text of the result heading to "Infected" or "Uninfected"

        document.getElementById('patientId').textContent = data.patient_id;
        // fill in the patient ID in the results card
    }
```

---

## PART 3 — Image Preview

```javascript
document.getElementById('blood_image').addEventListener('change', function(e) {
    // 'change' event fires when user selects a file

    const reader = new FileReader();
    // FileReader = reads file content in the browser

    reader.onload = function(e) {
        const img = document.getElementById('previewImg');
        img.src = e.target.result;   // set image source to the file data
        img.style.display = 'block'; // make image visible
    }

    reader.readAsDataURL(e.target.files[0]);
    // readAsDataURL = converts image to a base64 string
    // e.target.files[0] = the first selected file
});
```

---

## Key JS Concepts Summary

| Concept | What it does |
|---------|-------------|
| `document.getElementById('id')` | Find HTML element by id |
| `element.addEventListener('event', fn)` | Watch for user action |
| `fetch('/url')` | Make HTTP request to Flask |
| `async/await` | Wait for response without freezing page |
| `element.style.display = 'none'` | Hide an element |
| `element.textContent = 'text'` | Change text of an element |
| `e.preventDefault()` | Stop default browser behavior |
| `JSON` | Data format for Flask ↔ JS communication |
