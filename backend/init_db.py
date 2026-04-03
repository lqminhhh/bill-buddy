from pathlib import Path

from utils.db import initialize_database


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"


def init_db():
    initialize_database(SCHEMA_PATH)
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_db()
