# db/event_db.py
import cs304dbi as dbi

EVENT_FIELDS = """
    event_id,
    title,
    date_of_event,
    category,
    created_by,
    created_at,
    description,
    contact_info,
    address1,
    address2,
    city,
    state,
    postal_code,
    upvotes,
    downvotes,
    status
"""


def list_events(conn, q="", category=""):
    curs = dbi.dict_cursor(conn)
    sql = f"""
        SELECT {EVENT_FIELDS}
        FROM events
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND (title LIKE %s OR description LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like])

    if category:
        sql += " AND category = %s"
        params.append(category)

    sql += " ORDER BY created_at DESC"
    curs.execute(sql, params)
    return curs.fetchall()

def insert_event(conn, title, date_of_event, category, created_by, created_at,
                 description, contact_info, address1, address2, city, state, postal_code):
    curs = dbi.cursor(conn)
    curs.execute("""
        INSERT INTO events (
            title, date_of_event, category,
            created_by, created_at,
            description, contact_info,
            address1, address2, city, state, postal_code
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [title, date_of_event, category,
          created_by, created_at,
          description, contact_info,
          address1, address2, city, state, postal_code])
    conn.commit()

    curs.execute("SELECT LAST_INSERT_ID()")
    return curs.fetchone()[0]

def get_event_by_id(conn, event_id):
    curs = dbi.dict_cursor(conn)
    curs.execute(f"""
        SELECT {EVENT_FIELDS}
        FROM events
        WHERE event_id = %s
    """, [event_id])
    return curs.fetchone()

def get_event_owner(conn, event_id):
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT created_by
        FROM events
        WHERE event_id = %s
    """, [event_id])
    return curs.fetchone()

def update_event(conn, event_id, title, date_of_event, category, description, contact_info,
                 address1, address2, city, state, postal_code):
    curs = dbi.cursor(conn)
    curs.execute("""
        UPDATE events
        SET
            title=%s,
            date_of_event=%s,
            category=%s,
            description=%s,
            contact_info=%s,
            address1=%s,
            address2=%s,
            city=%s,
            state=%s,
            postal_code=%s
        WHERE event_id=%s
    """, [title, date_of_event, category, description, contact_info,
          address1, address2, city, state, postal_code, event_id])
    conn.commit()

def delete_event_and_rsvps(conn, event_id):
    curs = dbi.cursor(conn)
    curs.execute("DELETE FROM rsvp WHERE event_id=%s", [event_id])
    curs.execute("DELETE FROM events WHERE event_id=%s", [event_id])
    conn.commit()

def list_rsvps_yes_maybe(conn, event_id):
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT rsvp.status,
               rsvp.created_at,
               users.full_name AS name
        FROM rsvp
        JOIN users ON rsvp.created_by = users.user_id
        WHERE rsvp.event_id = %s
          AND rsvp.status IN ('yes', 'maybe')
        ORDER BY
          CASE rsvp.status
            WHEN 'yes' THEN 1
            WHEN 'maybe' THEN 2
          END,
          CASE rsvp.status
            WHEN 'yes' THEN rsvp.created_at
            ELSE NULL
          END ASC
    """, [event_id])
    return curs.fetchall()

def get_user_rsvp(conn, event_id, user_id):
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT status
        FROM rsvp
        WHERE event_id=%s AND created_by=%s
    """, [event_id, user_id])
    return curs.fetchone()

def get_existing_rsvp(conn, event_id, user_id):
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT event_id, created_by, status, created_at
        FROM rsvp
        WHERE event_id=%s AND created_by=%s
    """, [event_id, user_id])
    return curs.fetchone()

def update_rsvp(conn, event_id, user_id, status, created_at):
    curs = dbi.cursor(conn)
    curs.execute("""
        UPDATE rsvp
        SET status=%s, created_at=%s
        WHERE event_id=%s AND created_by=%s
    """, [status, created_at, event_id, user_id])
    conn.commit()

def insert_rsvp(conn, event_id, user_id, status, created_at):
    curs = dbi.cursor(conn)
    curs.execute("""
        INSERT INTO rsvp(event_id, created_by, status, created_at)
        VALUES (%s, %s, %s, %s)
    """, [event_id, user_id, status, created_at])
    conn.commit()

def list_events_for_calendar(conn):
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT event_id, title, date_of_event, description
        FROM events
        ORDER BY date_of_event ASC
    """)
    return curs.fetchall()
