# db/event_db.py
import cs304dbi as dbi

# Explicit list of event fields to avoid using SELECT *
# Keeps queries clear and resilient to schema changes
EVENT_FIELDS = """
    event_id,
    title,
    date_of_event,
    category,
    created_by,
    created_at,
    description,
    contact_info,
    image_filename,
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
    """
    Return a list of events, optionally filtered by
    a search query and/or category.
    """
    curs = dbi.dict_cursor(conn)

    # Base query; WHERE 1=1 allows conditional filters to be appended cleanly
    sql = f"""
        SELECT {EVENT_FIELDS}
        FROM events
        WHERE 1=1
    """
    params = []

    # Apply text search filter if provided
    if q:
        sql += " AND (title LIKE %s OR description LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like])

    # Apply category filter if provided
    if category:
        sql += " AND category = %s"
        params.append(category)

    # Show most recently created events first
    sql += " ORDER BY created_at DESC"

    curs.execute(sql, params)
    return curs.fetchall()


def insert_event(conn, title, date_of_event, category, created_by, created_at,
                 description, contact_info, address1, address2, city, state, postal_code):
    """
    Insert a new event into the database and return its event_id.
    """
    curs = dbi.cursor(conn)

    curs.execute("""
        INSERT INTO events (
            title, date_of_event, category,
            created_by, created_at,
            description, contact_info,
            address1, address2, city, state, postal_code
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        title, date_of_event, category,
        created_by, created_at,
        description, contact_info,
        address1, address2, city, state, postal_code
    ])

    conn.commit()

    # Retrieve the auto-generated event_id
    curs.execute("SELECT LAST_INSERT_ID()")
    return curs.fetchone()[0]


def get_event_by_id(conn, event_id):
    """
    Return a single event row by event_id, or None if not found.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(f"""
        SELECT {EVENT_FIELDS}
        FROM events
        WHERE event_id = %s
    """, [event_id])
    return curs.fetchone()


def get_event_owner(conn, event_id):
    """
    Return the creator (created_by) of an event.
    Used for ownership/permission checks.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT created_by
        FROM events
        WHERE event_id = %s
    """, [event_id])
    return curs.fetchone()


def update_event(conn, event_id, title, date_of_event, category, description, contact_info,
                 address1, address2, city, state, postal_code):
    """
    Update editable fields for an existing event.
    """
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
    """, [
        title, date_of_event, category, description, contact_info,
        address1, address2, city, state, postal_code, event_id
    ])
    conn.commit()


def delete_event_and_rsvps(conn, event_id):
    """
    Delete an event and all associated RSVPs.
    """
    curs = dbi.cursor(conn)

    # Remove dependent RSVP rows first to maintain referential integrity
    curs.execute("DELETE FROM rsvp WHERE event_id=%s", [event_id])
    curs.execute("DELETE FROM events WHERE event_id=%s", [event_id])

    conn.commit()


def list_rsvps_yes_maybe(conn, event_id):
    """
    Return YES and MAYBE RSVPs for an event,
    ordered by status and submission time.
    """
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
    """
    Return the current user's RSVP status for an event, if it exists.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT status
        FROM rsvp
        WHERE event_id=%s AND created_by=%s
    """, [event_id, user_id])
    return curs.fetchone()


def get_existing_rsvp(conn, event_id, user_id):
    """
    Check whether an RSVP already exists for a user and event.
    Used to decide between INSERT vs UPDATE.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT event_id, created_by, status, created_at
        FROM rsvp
        WHERE event_id=%s AND created_by=%s
    """, [event_id, user_id])
    return curs.fetchone()


def update_rsvp(conn, event_id, user_id, status, created_at):
    """
    Update an existing RSVP for a user and event.
    """
    curs = dbi.cursor(conn)
    curs.execute("""
        UPDATE rsvp
        SET status=%s, created_at=%s
        WHERE event_id=%s AND created_by=%s
    """, [status, created_at, event_id, user_id])
    conn.commit()


def insert_rsvp(conn, event_id, user_id, status, created_at):
    """
    Insert a new RSVP for a user and event.
    """
    curs = dbi.cursor(conn)
    curs.execute("""
        INSERT INTO rsvp(event_id, created_by, status, created_at)
        VALUES (%s, %s, %s, %s)
    """, [event_id, user_id, status, created_at])
    conn.commit()


def list_events_for_calendar(conn):
    """
    Return lightweight event data for the calendar view.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT event_id, title, date_of_event, description
        FROM events
        ORDER BY date_of_event ASC
    """)
    return curs.fetchall()
