"""
comment_db - Comments Database Layer

Provides database operations for managing comments on events and resources:
  - insert_comment: Add a new comment
  - list_comments_for_event: Retrieve all comments on an event
  - list_comments_for_resource: Retrieve all comments on a resource
  - get_comment_owner: Check who created a comment (for delete authorization)

Comments are always tied to a user and exactly one target (event or resource).
Timestamps are managed by the database (NOW() at insertion).
"""

import cs304dbi as dbi


def insert_comment(conn, content, user_id, event_id=None, resource_id=None):
    """
    Insert a new comment for an event or resource.
    Exactly one of event_id/resource_id should be non-null (enforced in routes).

    Args:
        conn: Database connection
        content (str): The comment text
        user_id (int): The user creating the comment
        event_id (int, optional): Target event (mutually exclusive with resource_id)
        resource_id (int, optional): Target resource (mutually exclusive with event_id)

    Note: Routes enforce that exactly one target is provided.
    """
    curs = dbi.cursor(conn)
    curs.execute(
        """
        INSERT INTO comments (content, event_id, resource_id, created_by, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        [content, event_id, resource_id, user_id]
    )
    conn.commit()


def list_comments_for_event(conn, event_id, current_user_id):
    """
    Return comments for an event as dict rows.
    Includes an `owned` flag indicating if current user created each comment.

    Args:
        conn: Database connection
        event_id (int): The event to fetch comments for
        current_user_id (int): The logged-in user (for ownership flags)

    Returns:
        list: Comment dicts with keys: comment_id, content, created_at, author, owned
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(
        """
        SELECT
            c.comment_id,
            c.content,
            c.created_at,
            u.full_name AS author,
            (c.created_by = %s) AS owned
        FROM comments c
        JOIN users u ON c.created_by = u.user_id
        WHERE c.event_id = %s
        ORDER BY c.created_at DESC
        """,
        [current_user_id, event_id]
    )
    return curs.fetchall()


def list_comments_for_resource(conn, resource_id, current_user_id):
    """
    Return comments for a resource as dict rows.
    Includes an `owned` flag indicating if current user created each comment.

    Args:
        conn: Database connection
        resource_id (int): The resource to fetch comments for
        current_user_id (int): The logged-in user (for ownership flags)

    Returns:
        list: Comment dicts with keys: comment_id, content, created_at, author, owned
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(
        """
        SELECT
            c.comment_id,
            c.content,
            c.created_at,
            u.full_name AS author,
            (c.created_by = %s) AS owned
        FROM comments c
        JOIN users u ON c.created_by = u.user_id
        WHERE c.resource_id = %s
        ORDER BY c.created_at DESC
        """,
        [current_user_id, resource_id]
    )
    return curs.fetchall()


def get_comment_owner(conn, comment_id):
    """
    Return the user_id who created a comment (used for delete authorization).

    Args:
        conn: Database connection
        comment_id (int): The comment to look up

    Returns:
        dict: Single row with 'created_by' field (int user_id)
              Returns None if the comment does not exist
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(
        "SELECT created_by FROM comments WHERE comment_id = %s",
        [comment_id]
    )
    return curs.fetchone()


def delete_comment(conn, comment_id):
    """Delete a comment by id."""
    curs = dbi.cursor(conn)
    curs.execute("DELETE FROM comments WHERE comment_id = %s", [comment_id])
    conn.commit()


def update_comment(conn, comment_id, new_content):
    """Update a comment's content by id."""
    curs = dbi.cursor(conn)
    curs.execute(
        "UPDATE comments SET content=%s WHERE comment_id=%s",
        [new_content, comment_id]
    )
    conn.commit()
