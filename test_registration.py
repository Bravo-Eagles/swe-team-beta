
from src.database import get_connection


conn = get_connection()

try:
    # Add a sample class
    cursor = conn.execute("""
        INSERT INTO classes
        (course_code, class_name, professor_id, semester, year, join_code)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("CS 35101", "Software Engineering", "P100", "Fall", 2026, "TEST123"))

    class_id = cursor.lastrowid

    # Registers a student for the class
    conn.execute("""
        INSERT INTO class_registrations (class_id, student_id)
        VALUES (?, ?)
    """, (class_id, "S101"))

    # Find the registered student
    results = conn.execute("""
        SELECT classes.class_name, class_registrations.student_id
        FROM class_registrations
        JOIN classes ON classes.class_id = class_registrations.class_id
        WHERE classes.class_id = ?
    """, (class_id,)).fetchall()

    for row in results:
        print("Class:", row["class_name"])
        print("Student:", row["student_id"])

    print("Registration test successful!")

finally:
    
    conn.rollback()

   
    conn.close()
