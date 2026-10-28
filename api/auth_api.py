import sqlite3
from src import database as db

def get_password_hash(email):
    query = "SELECT password_hash FROM accounts WHERE email = ?"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (email))
            return cursor.rowcount
    except sqlite3.Error as e:
        print(f"An Error Occurred: {e}")

def make_account(email, pass_hash):
    query = "INSERT INTO accounts (email, password_hash) VALUES (?, ?);"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (email, pass_hash))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"An Error Occurred: {e}")