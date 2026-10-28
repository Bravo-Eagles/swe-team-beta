from src.database import get_connection #using get_connection function 


def create_student(id, first_name, last_name, email, password_hash, active):
    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO student (id, first_name, last_name, email, password_hash, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (id, first_name, last_name, email, password_hash, active)
        )

        conn.commit()

    finally:
        conn.close()





def get_student(id):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            SELECT * FROM student
            WHERE id = ?
            """,
            (id,)
        )

        return cursor.fetchone()

    finally:
        conn.close()






def update_student(id, new_email):
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE student
            SET email = ?
            WHERE id = ?
            """,
            (new_email, id)
        )

        conn.commit()

    finally:
        conn.close()






def delete_student(id):
    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM student
            WHERE id = ?
            """,
            (id,)
        )

        conn.commit()

    finally:
        conn.close()





def create_teacher(id, first_name, last_name, email, password_hash):
    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO teacher (id, first_name, last_name, email, password_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (id, first_name, last_name, email, password_hash)
        )

        conn.commit()

    finally:
        conn.close()





def get_teacher(id):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            SELECT * FROM teacher
            WHERE id = ?
            """,
            (id,)
        )

        return cursor.fetchone()

    finally:
        conn.close()






def update_teacher(id, new_email):
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE teacher
            SET email = ?
            WHERE id = ?
            """,
            (new_email, id)
        )

        conn.commit()

    finally:
        conn.close()




def delete_teacher(id):
    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM teacher
            WHERE id = ?
            """,
            (id,)
        )
        conn.commit()

    finally:
        conn.close()