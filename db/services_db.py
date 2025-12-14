# db/services_db.py
import cs304dbi as dbi

# Keep this list in sync with your schema and templates
SERVICE_FIELDS = """
    service_id,
    service_name,
    category,
    description,
    price_range,
    service_location_type,
    availability,
    contact_method,
    created_by,
    created_at
"""

def list_services(conn, q="", category=""):
    """
    Returns a list of services (dict rows), optionally filtered by keyword and category.
    """
    curs = dbi.dict_cursor(conn)

    sql = f"""
        SELECT {SERVICE_FIELDS}
        FROM services
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND (service_name LIKE %s OR description LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like])

    if category:
        sql += " AND category = %s"
        params.append(category)

    sql += " ORDER BY created_at DESC"

    curs.execute(sql, params)
    return curs.fetchall()

def insert_service(conn, service_name, category, description, price_range,
                   location_type, availability, contact_method, created_by):
    """
    Inserts a service row. Returns new service_id.
    """
    curs = dbi.cursor(conn)
    curs.execute("""
        INSERT INTO services (
            service_name, category, description, price_range,
            service_location_type, availability, contact_method,
            created_by, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """, [service_name, category, description, price_range,
          location_type, availability, contact_method, created_by])
    conn.commit()

    curs.execute("SELECT LAST_INSERT_ID()")
    return curs.fetchone()[0]

def get_service_by_id(conn, service_id):
    """
    Returns one service dict row (explicit fields), or None.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(f"""
        SELECT {SERVICE_FIELDS}
        FROM services
        WHERE service_id = %s
    """, [service_id])
    return curs.fetchone()

def update_service(conn, service_id, service_name, category, description, price_range,
                   location_type, availability, contact_method):
    """
    Updates a service row by id.
    """
    curs = dbi.cursor(conn)
    curs.execute("""
        UPDATE services
        SET service_name=%s,
            category=%s,
            description=%s,
            price_range=%s,
            service_location_type=%s,
            availability=%s,
            contact_method=%s
        WHERE service_id=%s
    """, [service_name, category, description, price_range,
          location_type, availability, contact_method, service_id])
    conn.commit()

def get_service_owner(conn, service_id):
    """
    Returns created_by for a service, or None.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT created_by
        FROM services
        WHERE service_id = %s
    """, [service_id])
    return curs.fetchone()

def delete_service(conn, service_id):
    """
    Deletes a service by id.
    """
    curs = dbi.cursor(conn)
    curs.execute("""
        DELETE FROM services
        WHERE service_id = %s
    """, [service_id])
    conn.commit()
