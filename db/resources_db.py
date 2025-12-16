# db/resources_db.py
import cs304dbi as dbi

# Keep this list aligned with what templates need.
# Include upvotes/downvotes to avoid Jinja errors.
RESOURCE_FIELDS = """
    resource_id,
    title,
    description,
    category,
    contact_info,
    status,
    created_by,
    created_at,
    upvotes,
    downvotes
"""

def list_resources(conn, q="", category=""):
    curs = dbi.dict_cursor(conn)

    sql = f"""
        SELECT {RESOURCE_FIELDS}
        FROM resources
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND (title LIKE %s OR description LIKE %s OR category LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like, like])

    if category:
        sql += " AND category = %s"
        params.append(category)

    sql += " ORDER BY created_at DESC"
    curs.execute(sql, params)
    return curs.fetchall()

def insert_resource(conn, title, category, description, contact_info, status, created_by):
    curs = dbi.cursor(conn)
    curs.execute("""
        INSERT INTO resources
            (title, category, description, contact_info, status, created_by, created_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, NOW())
    """, [title, category, description, contact_info, status, created_by])
    conn.commit()

    curs.execute("SELECT LAST_INSERT_ID()")
    return curs.fetchone()[0]

def get_resource_by_id(conn, resource_id):
    curs = dbi.dict_cursor(conn)
    curs.execute(f"""
        SELECT {RESOURCE_FIELDS}
        FROM resources
        WHERE resource_id = %s
    """, [resource_id])
    return curs.fetchone()

def get_resource_owner(conn, resource_id):
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT created_by
        FROM resources
        WHERE resource_id = %s
    """, [resource_id])
    return curs.fetchone()

def update_resource(conn, resource_id, title, category, description, contact_info, status):
    curs = dbi.cursor(conn)
    curs.execute("""
        UPDATE resources
        SET title=%s,
            category=%s,
            description=%s,
            contact_info=%s,
            status=%s
        WHERE resource_id=%s
    """, [title, category, description, contact_info, status, resource_id])
    conn.commit()

def delete_resource(conn, resource_id):
    curs = dbi.cursor(conn)
    curs.execute("""
        DELETE FROM resources
        WHERE resource_id=%s
    """, [resource_id])
    conn.commit()
