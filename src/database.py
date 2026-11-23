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
    """Create missing tables and migrate existing databases."""
    schema = SCHEMA_PATH.read_text()
    conn = get_connection()

    try:
        scheduled_exists = conn.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'scheduled'
        """).fetchone()

        if scheduled_exists:
            scheduled_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(scheduled)")
            }

            if "is_cancelled" not in scheduled_columns:
                conn.execute("""
                    ALTER TABLE scheduled
                    ADD COLUMN is_cancelled BOOLEAN NOT NULL DEFAULT 0
                """)

        # Remove the old unrestricted unique index.
        existing_index = conn.execute("""
            SELECT sql FROM sqlite_master
            WHERE type = 'index'
              AND name = 'unique_class_meeting'
        """).fetchone()

        if existing_index:
            index_sql = existing_index["sql"] or ""

            if "WHERE IS_CANCELLED = 0" not in " ".join(
                index_sql.upper().split()
            ):
                conn.execute("DROP INDEX unique_class_meeting")

        # Create missing tables and the corrected index.
        conn.executescript(schema)

        # Migrate older attendance tables.
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(attendance)")
        }

        if "attendance_status" not in columns:
            conn.execute("""
                ALTER TABLE attendance
                ADD COLUMN attendance_status TEXT NOT NULL DEFAULT 'Present'
                CHECK (attendance_status IN ('Present', 'Absent', 'Not recorded'))
            """)

        conn.commit()

    finally:
        conn.close()

# Make sure the database and tables exist as soon as any page
# imports this module. Python only runs this once per server
# start, not on every Streamlit rerun
init_db()