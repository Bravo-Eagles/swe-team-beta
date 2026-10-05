import sqlite3
from pathlib import Path

# Build paths relative to this file, so they work no matter
# which folder the app is started from
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "attendance.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection():
    """Open a connection to the app's SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Create the database file and any missing tables."""
    schema = SCHEMA_PATH.read_text()
    conn = get_connection()
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()