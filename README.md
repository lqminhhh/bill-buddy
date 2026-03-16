# Bill Buddy

Bill Buddy is a simple Flask web app for tracking shared trip expenses. It is designed as an MVP that focuses on one clear workflow: create a trip, add members, log expenses, and see balances and final settlement suggestions.

## Overview

This project was built as a lightweight Splitwise-style expense-sharing app for small groups. It uses server-rendered Flask pages, SQLite for storage, and pure Python calculation utilities for splitting costs and generating settlement recommendations.

The goal is clarity over complexity. There is no login system, no JavaScript-heavy frontend, and no unnecessary features for the MVP.

## MVP Features

- Create trips with a trip name and currency
- Add trip members and mark one member as yourself
- View all trips from the home page
- Add expenses with:
  - description
  - amount
  - date
  - payer
  - selected participants
  - optional notes
- Edit existing expenses
- Delete expenses
- View per-member totals:
  - total paid
  - total share
  - net balance
- View a final settlement summary in plain language

## Tech Stack

- Python
- Flask
- SQLite
- Jinja templates
- HTML/CSS

## Local Setup

1. Clone the project and move into the folder.
2. Create a virtual environment:

```bash
python3 -m venv .venv
```

3. Activate it:

```bash
source .venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

## Initialize the Database

Run:

```bash
python3 init_db.py
```

This creates the SQLite database file using the schema in `schema.sql`.

## Run the App

Start the Flask app with:

```bash
python3 app.py
```

The app runs on:

```text
http://127.0.0.1:5001
```

If your browser blocks `127.0.0.1`, try:

```text
http://localhost:5001
```

## Project Structure

```text
bill-buddy/
├── app.py
├── init_db.py
├── schema.sql
├── requirements.txt
├── README.md
├── static/
│   └── style.css
├── templates/
│   ├── add_expense.html
│   ├── base.html
│   ├── create_trip.html
│   ├── edit_expense.html
│   ├── index.html
│   └── trip_detail.html
└── utils/
    ├── calculations.py
    ├── db.py
    └── helpers.py
```

## Suggested Next Features

- Add trip editing and deletion
- Add member editing and deletion
- Add filtering or sorting for expenses
- Add expense categories
- Add a trip summary dashboard
- Add export to CSV or PDF
- Add validation for duplicate member names
- Add tests for routes and calculations
- Add authentication if the app grows beyond a single-user MVP

## Notes

- Money is stored as integer cents in the database to avoid floating point errors.
- Expense splits and settlement logic are handled with pure Python helper functions in `utils/calculations.py`.
- Participant rows are linked through a normalized join table: `expense_participants`.
