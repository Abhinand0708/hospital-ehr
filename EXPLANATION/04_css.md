# CSS (style.css) — Explanation

CSS = Cascading Style Sheets. It controls how everything LOOKS.
HTML is the skeleton. CSS is the clothes and makeup.

---

## How CSS Works

You write a "selector" (what to style) and then rules inside `{}`.

```css
selector {
    property: value;
}
```

Examples:
```css
h1 {
    color: blue;           /* text color */
    font-size: 32px;       /* text size */
}

.btn-submit {              /* . means "class" */
    background: #2563eb;   /* background color (hex code) */
    color: white;
    padding: 12px 24px;    /* space inside: top/bottom left/right */
    border-radius: 8px;    /* rounded corners */
    border: none;          /* no border */
    cursor: pointer;       /* hand cursor on hover */
}
```

---

## Selectors

```css
h1 { }           /* targets ALL <h1> tags */
.form-group { }  /* targets elements with class="form-group" */
#patient_id { }  /* targets element with id="patient_id" */
```

In HTML:
```html
<div class="form-group">   <!-- CSS .form-group applies here -->
<input id="patient_id">    <!-- CSS #patient_id applies here -->
```

---

## The Box Model (most important concept)

Every HTML element is a box:

```
┌─────────────────────────────┐
│         MARGIN              │  ← space OUTSIDE the element
│  ┌───────────────────────┐  │
│  │       BORDER          │  │  ← the border line
│  │  ┌─────────────────┐  │  │
│  │  │    PADDING      │  │  │  ← space INSIDE the border
│  │  │  ┌───────────┐  │  │  │
│  │  │  │  CONTENT  │  │  │  │  ← actual text/image
│  │  │  └───────────┘  │  │  │
│  │  └─────────────────┘  │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

```css
.form-group {
    margin-bottom: 20px;    /* space below the element */
    padding: 10px;          /* space inside the element */
}
```

---

## Flexbox — For Layout

Flexbox arranges items in a row or column.

```css
.form-row {
    display: flex;      /* arrange children side by side */
    gap: 20px;          /* space between items */
}
```

```html
<div class="form-row">
    <div class="form-group">First Name</div>   <!-- side by side -->
    <div class="form-group">Last Name</div>    <!-- because of flexbox -->
</div>
```

---

## Colors in CSS

```css
color: red;              /* named color */
color: #2563eb;          /* hex code (most common) */
color: rgb(37, 99, 235); /* RGB values */
```

Hex codes: `#RRGGBB` — each pair is Red, Green, Blue in hexadecimal (00-FF)
- `#ffffff` = white
- `#000000` = black
- `#2563eb` = blue

---

## Gradients (used in your buttons and headers)

```css
background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
```
- `135deg` — direction of the gradient (diagonal)
- `#1e3a5f 0%` — dark blue at the start
- `#2563eb 100%` — lighter blue at the end
- Result: smooth color transition from dark to light blue

---

## Hover Effects

```css
.module-card:hover {
    transform: translateY(-4px);   /* move up 4px on hover */
    box-shadow: 0 12px 30px rgba(0,0,0,0.1);  /* shadow appears */
    transition: all 0.2s;          /* animate over 0.2 seconds */
}
```
- `:hover` — applies only when mouse is over the element
- `transform: translateY(-4px)` — moves element up (negative = up)
- `transition` — makes the change smooth instead of instant

---

## Responsive Design (media queries)

```css
@media (max-width: 768px) {
    .hero-title {
        font-size: 2.2rem;   /* smaller text on mobile */
    }
    .features-section {
        padding: 50px 20px;  /* less padding on small screens */
    }
}
```
- `@media (max-width: 768px)` — these rules only apply when screen is 768px wide or less
- This makes the website look good on phones too
