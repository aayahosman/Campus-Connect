"""
login_db - User Authentication Database Layer

Provides database operations for user management and authentication:
  - insert_user: Create new user account with hashed password
  - get_login_row_by_email: Retrieve user for authentication

Note: Passwords are always stored as bcrypt hashes (never plaintext).
All queries use parameterized statements to prevent SQL injection.
"""

import cs304dbi as dbi


def insert_user(conn, full_name, email, password_hash, role):
    """
    Insert a new user into the users table and return the new user_id.

    Args:
        conn: Database connection
        full_name (str): User's full name
        email (str): User's email (must be unique)
        password_hash (str): Bcrypt-hashed password (never store plaintext!)
        role (str): User role (e.g., 'student', 'admin')

    Returns:
        int: The newly created user_id

    Raises:
        Exception: If email already exists (duplicate entry error)
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
    Used during authentication (password verification and session setup).

    Args:
        conn: Database connection
        email (str): The user's email address

    Returns:
        dict: User info with keys: user_id, password_hash, full_name
              Returns None if no user with that email exists
    """
    curs = dbi.dict_cursor(conn)

    # Explicitly select only required fields (no SELECT *)
    curs.execute("""
        SELECT user_id, password_hash, full_name
        FROM users
        WHERE email = %s
    """, [email])

    return curs.fetchone()
