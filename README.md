# Bill Buddy

## I. Overview

Bill Buddy is a Flask MVP for tracking shared trip expenses. It helps a group create trips, add members, record expenses, view balances, and generate a final settlement summary in a simple server-rendered interface.

[Demo Video](https://github.com/user-attachments/assets/d5b64d77-c972-4fc3-9e10-12ce908f0689)


## II. Features

- Create trips with a trip name and currency
- Use a two-step trip creation flow with participant count first
- Add all trip members and mark exactly one member as yourself
- View all trips from the home page
- Delete trips with a confirmation page
- Add expenses with description, amount, date, payer, participants, and optional notes
- Edit expenses
- Delete expenses
- View per-member balances:
  - total paid
  - total share
  - net balance
- View final settlement suggestions in plain language
- Open a dedicated trip summary page
- View total spending, total expenses, total members, highest spender, highest share, and member who owes the most
- Filter expense history by payer
- Export expense history to an Excel-friendly CSV file
- See flash messages for successful actions and validation errors

## III. Project Structure

```text
bill-buddy/
├── app.py
├── assets/
│   └── demo-video.mov
├── init_db.py
├── README.md
├── requirements.txt
├── schema.sql
├── static/
│   └── style.css
├── templates/
│   ├── add_expense.html
│   ├── base.html
│   ├── create_trip.html
│   ├── delete_trip.html
│   ├── edit_expense.html
│   ├── index.html
│   ├── trip_detail.html
│   └── trip_summary.html
└── utils/
    ├── calculations.py
    ├── db.py
    └── helpers.py
```

## IV. How to Setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
```

2. Activate it:

```bash
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Initialize the database:

```bash
python3 init_db.py
```

5. Run the app:

```bash
python3 app.py
```

6. Open the app in your browser:

```text
http://127.0.0.1:5001
```

## V. Tech Stack

- Python
- Flask
- SQLite
- Jinja Templates
- HTML/CSS

## VI. Contact Info

- Project owner: Minh Le
- For questions or feedback, open an issue in this repository.
