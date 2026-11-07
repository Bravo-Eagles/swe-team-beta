import sqlite3
from src import database as db

def create_class(class_name, course_ID):
    #Create a class
    query = "INSERT INTO class (name, course_id) VALUES (?, ?);"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (class_name, course_ID))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"An Error Occurred: {e}")

def update_class(class_name, course_ID, class_id):
    #Updates a class row name/course id
    query = "UPDATE class SET name = ?, course_id = ? WHERE id = ?"
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (class_name, course_ID, class_id))
            return cursor.rowcount  # 1 = updated, 0 = no matching record
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")




def get_classes(class_id=None):
    #
    query = "SELECT * FROM class WHERE 1=1"
    params = []

    if class_id is not None:
        query += " AND course_id = ?"
        params.append(class_id)

    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, params)

            if class_id is not None: #If searching by class_id only return one row
                print("ONLY ONE")
                return cursor.fetchone()
            else:
                return cursor.fetchall()
            
    except sqlite3.Error as e:
        print(f"An error has occured: {e}")

def delete_class(student_id, scheduled_id):
    #Deletes a row from the attendance table, uses a soft delete to preserve information
    query = "UPDATE attendance SET is_deleted = 1 WHERE scheduled_id = ? AND student_id = ?"