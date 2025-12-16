# db/vote_db.py
import cs304dbi as dbi


def _table_for_item_type(item_type):
    """
    Map item type to its table name and id column.
    Prevents unsafe SQL from user input.
    """
    if item_type == "event":
        return "events", "event_id"
    if item_type == "resource":
        return "resources", "resource_id"
    raise ValueError("invalid item_type")


def item_exists(conn, item_type, item_id):
    """Return True if the target event/resource exists."""
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.dict_cursor(conn)

    # Explicit column selection (no SELECT *)
    curs.execute(
        f"SELECT {id_col} FROM {table} WHERE {id_col}=%s",
        [item_id]
    )
    return curs.fetchone() is not None


def get_previous_vote(conn, user_id, item_type, item_id):
    """Return the user's previous vote for this item, or None."""
    curs = dbi.dict_cursor(conn)
    curs.execute(
        """
        SELECT vote
        FROM votes
        WHERE user_id=%s AND item_type=%s AND item_id=%s
        """,
        [user_id, item_type, item_id]
    )
    return curs.fetchone()


def insert_vote(conn, user_id, item_type, item_id, vote_type):
    """Insert a new vote row."""
    curs = dbi.cursor(conn)
    curs.execute(
        """
        INSERT INTO votes (user_id, item_type, item_id, vote)
        VALUES (%s, %s, %s, %s)
        """,
        [user_id, item_type, item_id, vote_type]
    )


def update_vote(conn, user_id, item_type, item_id, vote_type):
    """Update an existing vote row."""
    curs = dbi.cursor(conn)
    curs.execute(
        """
        UPDATE votes
        SET vote=%s
        WHERE user_id=%s AND item_type=%s AND item_id=%s
        """,
        [vote_type, user_id, item_type, item_id]
    )


def apply_vote_count_change(conn, item_type, item_id, previous_vote, new_vote):
    """
    Update aggregate upvote/downvote counts on the target item.
    Handles first-time votes and vote switches.
    """
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.cursor(conn)

    # First-ever vote
    if previous_vote is None:
        if new_vote == "up":
            curs.execute(
                f"UPDATE {table} SET upvotes = upvotes + 1 WHERE {id_col}=%s",
                [item_id]
            )
        else:
            curs.execute(
                f"UPDATE {table} SET downvotes = downvotes + 1 WHERE {id_col}=%s",
                [item_id]
            )
        return

    # Switching vote direction
    if previous_vote == "up" and new_vote == "down":
        curs.execute(
            f"""
            UPDATE {table}
            SET upvotes = upvotes - 1,
                downvotes = downvotes + 1
            WHERE {id_col}=%s
            """,
            [item_id]
        )
    elif previous_vote == "down" and new_vote == "up":
        curs.execute(
            f"""
            UPDATE {table}
            SET downvotes = downvotes - 1,
                upvotes = upvotes + 1
            WHERE {id_col}=%s
            """,
            [item_id]
        )


def get_vote_counts(conn, item_type, item_id):
    """Return current upvote and downvote counts for an item."""
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.dict_cursor(conn)

    curs.execute(
        f"""
        SELECT upvotes, downvotes
        FROM {table}
        WHERE {id_col}=%s
        """,
        [item_id]
    )
    return curs.fetchone()


def update_item_status(conn, item_type, item_id, status):
    """Update the status field on an event or resource."""
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.cursor(conn)
    curs.execute(
        f"UPDATE {table} SET status=%s WHERE {id_col}=%s",
        [status, item_id]
    )


def delete_item_and_dependencies(conn, item_type, item_id):
    """
    Hard delete an event/resource and its dependent rows
    (comments, RSVPs).
    """
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.cursor(conn)

    if item_type == "event":
        curs.execute("DELETE FROM rsvp WHERE event_id=%s", [item_id])
        curs.execute("DELETE FROM comments WHERE event_id=%s", [item_id])
    else:
        curs.execute("DELETE FROM comments WHERE resource_id=%s", [item_id])

    curs.execute(f"DELETE FROM {table} WHERE {id_col}=%s", [item_id])
