import sqlite3
import datetime
import hashlib
from src import database as db

def get_account(email: str):
    query = "SELECT * FROM accounts WHERE email = ?"
    try:
        with db.get_connection() as conn:
            row = conn.execute(query, (email,)).fetchone()
            return row
    except sqlite3.Error as e:
        print(email)
        print(f"An Error Occurred in get_account: {e}")
        return None

def make_account(email, pass_hash):
    query = "INSERT INTO accounts (email, password_hash) VALUES (?, ?);"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (email, pass_hash))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"An Error Occurred: {e}")
        return False

def _hash_token(token: str):
    """Helper for session management"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_session(userID, token, expires):
    cleanup_query = "DELETE FROM sessions WHERE expires < ?" #Clears inactive sessions on run
    query = "INSERT INTO sessions VALUES (?, ?, ?)"
    try:
        with db.get_connection() as conn:
            conn.execute(cleanup_query, (datetime.datetime.now(datetime.timezone.utc).isoformat(),))
            conn.execute(query, (_hash_token(token), userID, expires.isoformat()))
            return token, expires
    except sqlite3.Error as e:
        print(f"An Error Occurred: {e}")
        return None

def delete_session(token):
    query = "DELETE FROM sessions WHERE token_hash = ?"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (_hash_token(token),))
            return cursor.rowcount
    except sqlite3.Error as e:
        print(f"An Error Occurred: {e}")
        return None

def get_user_by_session(token_hash, curr_time):
    query = "SELECT u.id, u.email FROM sessions s JOIN accounts u ON u.id = s.user_id WHERE s.token_hash = ? AND s.expires > ?"
    try:
        with db.get_connection() as conn:
            row = conn.execute(query, (_hash_token(token_hash), curr_time)).fetchone()
            # print("Get User by Session:" + str(row))
            return row
    except sqlite3.Error as e:
            print(f"An Error Occurred: {e}")
            return None