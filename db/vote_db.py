"""
vote_db - Voting/Rating System Database Layer

Handles upvotes/downvotes for events and resources.
Supports:
- vote tracking per user
- aggregate vote counts
- auto-flagging
- auto-deletion with dependency cleanup (comments, RSVPs)
"""

import cs304dbi as dbi


def _table_for_item_type(item_type):
    """Map item type to table name and id column."""
    if item_type == "event":
        return "events", "event_id"
    if item_type == "resource":
        return "resources", "resource_id"
    raise ValueError("invalid item_type")


def item_exists(conn, item_type, item_id):
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.dict_cursor(conn)
    curs.execute(
        f"SELECT {id_col} FROM {table} WHERE {id_col}=%s",
        [item_id]
    )
    return curs.fetchone() is not None


def get_previous_vote(conn, user_id, item_type, item_id):
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
    curs = dbi.cursor(conn)
    curs.execute(
        """
        INSERT INTO votes (user_id, item_type, item_id, vote)
        VALUES (%s, %s, %s, %s)
        """,
        [user_id, item_type, item_id, vote_type]
    )


def update_vote(conn, user_id, item_type, item_id, vote_type):
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
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.cursor(conn)

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


def apply_status_or_delete(conn, item_type, item_id):
    """
    - 50+ downvotes → delete item + dependencies
    - 20+ downvotes → flag item
    """
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.cursor(conn)

    counts = get_vote_counts(conn, item_type, item_id)
    if not counts:
        return None

    upvotes = counts["upvotes"]
    downvotes = counts["downvotes"]

    if downvotes >= 50:
        if item_type == "event":
            curs.execute("DELETE FROM rsvp WHERE event_id=%s", [item_id])
            curs.execute("DELETE FROM comments WHERE event_id=%s", [item_id])
        else:
            curs.execute("DELETE FROM comments WHERE resource_id=%s", [item_id])

        curs.execute(f"DELETE FROM {table} WHERE {id_col}=%s", [item_id])
        return "deleted"

    status = "flagged" if downvotes >= 20 else "active"
    curs.execute(
        f"UPDATE {table} SET status=%s WHERE {id_col}=%s",
        [status, item_id]
    )
    return status
