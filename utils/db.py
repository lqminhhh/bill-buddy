from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "bill_buddy.db"


def get_db_connection():
    """Open a SQLite connection with foreign keys enabled."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_database(schema_path):
    """Create tables from the SQL schema file."""
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        schema_sql = schema_file.read()

    with get_db_connection() as connection:
        connection.executescript(schema_sql)
        connection.commit()


def execute_query(query, params=()):
    """Run a query that changes data and return the last inserted row id."""
    with get_db_connection() as connection:
        cursor = connection.execute(query, params)
        connection.commit()
        return cursor.lastrowid


def fetch_all(query, params=()):
    """Return all rows for a SELECT query."""
    with get_db_connection() as connection:
        cursor = connection.execute(query, params)
        return cursor.fetchall()


def fetch_one(query, params=()):
    """Return one row for a SELECT query."""
    with get_db_connection() as connection:
        cursor = connection.execute(query, params)
        return cursor.fetchone()
