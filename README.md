# Bill Buddy

Bill Buddy is a beginner-friendly Flask MVP for tracking shared trip expenses.

## Tech Stack

- Python
- Flask
- SQLite
- Jinja templates
- HTML/CSS

## Project Structure

- `app.py` starts the Flask app.
- `init_db.py` creates the SQLite database from `schema.sql`.
- `schema.sql` defines the starter database tables.
- `templates/` stores Jinja HTML templates.
- `static/` stores CSS and other static files.
- `utils/` stores helper modules for database access and calculations.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Initialize the database:

```bash
python init_db.py
```

4. Run the Flask app:

```bash
python app.py
```

5. Open `http://127.0.0.1:5000` in your browser.

## MVP Scope

This scaffold only includes the basic structure:

- Flask app entry point
- Home page
- Base template
- Placeholder pages
- CSS file
- SQLite helper files

More trip and expense features can be added on top of this structure.
