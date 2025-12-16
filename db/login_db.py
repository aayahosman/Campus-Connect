# db/login_db.py
import cs304dbi as dbi


def insert_user(conn, full_name, email, password_hash, role):
    """
    Insert a new user into the users table and return the new user_id.
    """
    curs = dbi.cursor(conn)

    # Insert a new user record with a hashed password
    curs.execute("""
        INSERT INTO users (full_name, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """, [full_name, email, password_hash, role])

    conn.commit()

    # Retrieve the auto-generated user_id
    curs.execute("SELECT LAST_INSERT_ID()")
    return curs.fetchone()[0]


def get_login_row_by_email(conn, email):
    """
    Return login-related user information for a given email.
    Used during authentication.
    """
    curs = dbi.dict_cursor(conn)

    # Explicitly select only required fields (no SELECT *)
    curs.execute("""
        SELECT user_id, password_hash, full_name
        FROM users
        WHERE email = %s
    """, [email])

    return curs.fetchone()
