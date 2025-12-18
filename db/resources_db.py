# db/resources_db.py
import cs304dbi as dbi

# Explicit list of resource fields to avoid SELECT *
# Includes vote counts to match what templates expect
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
    """
    Return a list of resources, optionally filtered by
    a search query and/or category.
    """
    curs = dbi.dict_cursor(conn)

    # Base query; WHERE 1=1 allows optional filters to be appended
    sql = f"""
        SELECT {RESOURCE_FIELDS}
        FROM resources
        WHERE 1=1
    """
    params = []

    # Apply text search filter if provided
    if q:
        sql += " AND (title LIKE %s OR description LIKE %s OR category LIKE %s)"
        like = f"%{q}%"
        params.extend([like, like, like])

    # Apply category filter if provided
    if category:
        sql += " AND category = %s"
        params.append(category)

    # Show most recently created resources first
    sql += " ORDER BY created_at DESC"

    curs.execute(sql, params)
    return curs.fetchall()


def insert_resource(conn, title, category, description, contact_info, status, created_by):
    """
    Insert a new resource into the database and return its resource_id.
    """
    curs = dbi.cursor(conn)

    curs.execute("""
        INSERT INTO resources
            (title, category, description, contact_info, status, created_by, created_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, NOW())
    """, [title, category, description, contact_info, status, created_by])

    conn.commit()

    # Retrieve the auto-generated resource_id
    curs.execute("SELECT LAST_INSERT_ID()")
    return curs.fetchone()[0]


def get_resource_by_id(conn, resource_id):
    """
    Return a single resource by resource_id, or None if not found.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(f"""
        SELECT {RESOURCE_FIELDS}
        FROM resources
        WHERE resource_id = %s
    """, [resource_id])
    return curs.fetchone()


def get_resource_owner(conn, resource_id):
    """
    Return the creator (created_by) of a resource.
    Used for ownership and permission checks.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute("""
        SELECT created_by
        FROM resources
        WHERE resource_id = %s
    """, [resource_id])
    return curs.fetchone()


def update_resource(conn, resource_id, title, category, description, contact_info, status):
    """
    Update editable fields for an existing resource.
    """
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
    """
    Delete a resource by resource_id.
    """
    curs = dbi.cursor(conn)
    curs.execute("""
        DELETE FROM resources
        WHERE resource_id=%s
    """, [resource_id])
    conn.commit()
