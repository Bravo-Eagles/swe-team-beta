import sqlite3
from src import database as db

def create_attendance_log(scheduled_id, student_id, time):
    query = "INSERT INTO attendance (scheduled_id, student_id, check_in_time) VALUES (?, ?, ?);"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (scheduled_id, student_id, time))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"An Error Occurred: {e}")

def update_attendance_log(check_in_time, student_id, scheduled_id):
    #Updates a rows check in time, not sure if these is needed.

    query = "UPDATE attendance SET check_in_time = ? WHERE student_id = ? AND scheduled_id = ?"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (check_in_time, student_id, scheduled_id))
            return cursor.rowcount  # 1 = updated, 0 = no matching record
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")


def select_attendance_log(student_id=None, scheduled_id=None):
    #Builds Dynamic query based on passed in values
    query = "SELECT * FROM attendance WHERE 1=1"
    params = []

    if student_id:
        query += " AND student_id = ?"
        params.append(student_id)

    if scheduled_id:
        query += " AND scheduled_id = ?"
        params.append(scheduled_id)

    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"An error has occured: {e}")

def delete_attendance_log(student_id, scheduled_id):
    #Deletes a row from the attendance table, uses a soft delete to preserve information
    query = "UPDATE attendance SET is_deleted = 1 WHERE scheduled_id = ? AND student_id = ?"