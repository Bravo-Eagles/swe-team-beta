import sqlite3
from pathlib import Path

# database.py lives in src/, so go up one level to reach the
# project root, where schema.sql and attendance.db live.
BASE_DIR = Path(__file__).parent.parent
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

        # Check which columns already exist in the attendance table.
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(attendance)")
        }

        # Add the new column only if it doesn't already exist.
        if "attendance_status" not in columns:
            conn.execute("""
                ALTER TABLE attendance
                ADD COLUMN attendance_status TEXT NOT NULL DEFAULT 'Present'
                CHECK (attendance_status IN ('Present', 'Absent', 'Not recorded'))
            """)
        # Check whether the scheduled table has a cancellation column.
        scheduled_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(scheduled)")
        }

        # Add the column to existing databases if necessary.
        if "is_cancelled" not in scheduled_columns:
            conn.execute("""
                ALTER TABLE scheduled
                ADD COLUMN is_cancelled BOOLEAN NOT NULL DEFAULT 0
            """)
        conn.commit()
    finally:
        conn.close()


# Make sure the database and tables exist as soon as any page
# imports this module. Python only runs this once per server
# start, not on every Streamlit rerun
init_db()