"""
vote_db - Voting/Rating System Database Layer

Provides database operations for the upvote/downvote system:
  - item_exists: Check if target exists
  - get_previous_vote: Retrieve user's existing vote
  - insert_vote: Create a new vote
  - update_vote: Change a user's vote (e.g., up → down)
  - apply_vote_count_change: Update aggregate vote counts
  - set_status_based_on_votes: Handle auto-flagging/removal by vote thresholds

Votes support both upvotes and downvotes. When vote counts cross thresholds,
items can be automatically flagged or removed (configurable per feature).
"""

import cs304dbi as dbi


def _table_for_item_type(item_type):
    """
    Map item type to its table name and id column.
    Prevents unsafe SQL from user input by using a whitelist.

    Args:
        item_type (str): Either 'event' or 'resource'

    Returns:
        tuple: (table_name, id_column_name)

    Raises:
        ValueError: If item_type is not recognized
    """
    if item_type == "event":
        return "events", "event_id"
    if item_type == "resource":
        return "resources", "resource_id"
    raise ValueError("invalid item_type")


def item_exists(conn, item_type, item_id):
    """
    Check if a target event or resource exists.

    Args:
        conn: Database connection
        item_type (str): 'event' or 'resource'
        item_id (int): The target item's id

    Returns:
        bool: True if the item exists, False otherwise
    """
    table, id_col = _table_for_item_type(item_type)
    curs = dbi.dict_cursor(conn)

    # Explicit column selection (no SELECT *)
    curs.execute(
        f"SELECT {id_col} FROM {table} WHERE {id_col}=%s",
        [item_id]
    )
    return curs.fetchone() is not None


def get_previous_vote(conn, user_id, item_type, item_id):
    """
    Retrieve a user's existing vote on an item.
    Used to detect vote changes (e.g., switching from up to down).

    Args:
        conn: Database connection
        user_id (int): The voting user
        item_type (str): 'event' or 'resource'
        item_id (int): The target item

    Returns:
        dict: Vote record with 'vote' field ('up' or 'down')
              Returns None if no vote exists yet
    """
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
    """
    Record a new vote for a user on an item.

    Args:
        conn: Database connection
        user_id (int): The voting user
        item_type (str): 'event' or 'resource'
        item_id (int): The target item
        vote_type (str): 'up' or 'down'
    """
    curs = dbi.cursor(conn)
    curs.execute(
        """
        INSERT INTO votes (user_id, item_type, item_id, vote)
        VALUES (%s, %s, %s, %s)
        """,
        [user_id, item_type, item_id, vote_type]
    )


def update_vote(conn, user_id, item_type, item_id, vote_type):
    """
    Change a user's existing vote (e.g., switch from up to down).

    Args:
        conn: Database connection
        user_id (int): The voting user
        item_type (str): 'event' or 'resource'
        item_id (int): The target item
        vote_type (str): New vote type ('up' or 'down')
    """
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
    Handles three scenarios: first-time votes, vote switches, and vote reversals.

    Args:
        conn: Database connection
        item_type (str): 'event' or 'resource'
        item_id (int): The target item
        previous_vote (str or None): User's prior vote ('up', 'down', or None)
        new_vote (str): New vote type ('up' or 'down')

    Examples:
        - previous_vote=None, new_vote='up' → upvotes += 1
        - previous_vote='up', new_vote='down' → upvotes -= 1, downvotes += 1
        - previous_vote='up', new_vote='up' → no change (prevented at route level)
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
