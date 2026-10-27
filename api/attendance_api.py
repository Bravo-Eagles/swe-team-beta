import sqlite3
from src import database as db

DB_FILE = "./../attendance.db"



def create_attendance_log(class_id, student_id, time):
    query = "INSERT INTO attendance (scheduled_id, student_id, check_in_time) VALUES (?, ?, ?);"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (class_id, student_id, time))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"An Error Occurred: {e}")

def update_attendance_log(row_id, time):
    #Only updates time for now, not sure if we need any other updates or will need to update these
    query = "UPDATE attendance SET check_in_time = ? WHERE id = ?"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (time, row_id))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"An error has occured: {e}")

def select_attendance_log(student_id=None, course_id=None):
    #Builds Dynamic query based on passed in values
    query = "SELECT * FROM attendance WHERE 1=1"
    params = []

    if student_id:
        query += " AND student_id = ?"
        params.append(student_id)

    if course_id:
        query += " AND course_id = ?"
        params.append(course_id)

    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"An error has occured: {e}")

def delete_attendance_log(student_id, course_id):
    #Deletes a row from the attendance table, uses a soft delete to preserve information
    query = "UPDATE attendance SET is_deleted = 1 WHERE course_id = ? AND student_id = ?"