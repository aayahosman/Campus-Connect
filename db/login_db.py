# db/login_db.py
import cs304dbi as dbi

def insert_user(conn, full_name, email, password_hash, role):
    curs = dbi.cursor(conn)
    curs.execute("""
        INSERT INTO users (full_name, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """, [full_name, email, password_hash, role])
    conn.commit()

    curs.execute("SELECT LAST_INSERT_ID()")
    return curs.fetchone()[0]

def get_login_row_by_email(conn, email):
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT user_id, password_hash, full_name
        FROM users
        WHERE email = %s
    """, [email])
    return curs.fetchone()
