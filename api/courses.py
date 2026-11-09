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
        return []

def get_teaching_classes(teacher_id):
    #
    query = """SELECT t.id AS teaching_id, t.semester, t.year,
                      c.id AS class_id, c.name, c.course_id
                    FROM teaching t 
                    JOIN class c ON c.id = t.class_id 
                    WHERE t.teacher_id = ?"""

    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (teacher_id,))
            return cursor.fetchall()
            
    except sqlite3.Error as e:
        print(f"An error has occured: {e}")
        return []

def get_teacher_id(account_id):
    query = "SELECT id FROM teacher WHERE account_id = ?"
    try:
        with db.get_connection() as conn:
            row = conn.execute(query, (account_id,)).fetchone()
            return row["id"] if row else None
    except sqlite3.Error as e:
        print(f"An error has occurred in get_teacher_id: {e}")
        return None

def delete_class(student_id, scheduled_id):
    #Deletes a row from the attendance table, uses a soft delete to preserve information
    query = "UPDATE attendance SET is_deleted = 1 WHERE scheduled_id = ? AND student_id = ?"

    try:
        with db.get_connection() as conn:
            cursor = conn.execute(query, (scheduled_id, student_id))

            return cursor.rowcount()
    except sqlite3.Error as e:
        print(f"An error has occured: {e}")
        return []
        


def get_class_roster(teaching_id):
    query = """SELECT s.id, s.first_name, s.middle_name, s.last_name, s.active
               FROM student s
               JOIN enrolled e ON e.student_id = s.id
               WHERE e.teaching_id = ?
               ORDER BY s.last_name, s.first_name"""
    try:
        with db.get_connection() as conn:
            return conn.execute(query, (teaching_id,)).fetchall()
    except sqlite3.Error as e:
        print(f"An error has occurred in get_class_roster: {e}")
        return []


def get_teaching_section(teaching_id, teacher_id):
    #Accepts in a teachingID and teacherID and validates that the teacher owns that section.
    query = """SELECT t.id AS teaching_id, t.semester, t.year,
                      c.name, c.course_id
               FROM teaching t
               JOIN class c ON c.id = t.class_id
               WHERE t.id = ? AND t.teacher_id = ?"""
    try:
        with db.get_connection() as conn:
            return conn.execute(query, (teaching_id, teacher_id)).fetchone()
    except sqlite3.Error as e:
        print(f"An error occurred in get_teaching_section: {e}")
        return None