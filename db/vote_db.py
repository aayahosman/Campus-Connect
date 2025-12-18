import cs304dbi as dbi

ITEM_MAP = {
    "event": ("events", "event_id"),
    "resource": ("resources", "resource_id")
}

def item_exists(conn, item_type, item_id):
    table, id_col = ITEM_MAP[item_type]
    curs = dbi.dict_cursor(conn)
    curs.execute(
        f"SELECT 1 FROM {table} WHERE {id_col}=%s",
        [item_id]
    )
    return curs.fetchone() is not None


def get_previous_vote(conn, user_id, item_type, item_id):
    curs = dbi.dict_cursor(conn)
    curs.execute(
        '''
        SELECT vote
        FROM votes
        WHERE user_id=%s AND item_type=%s AND item_id=%s
        ''',
        (user_id, item_type, item_id)
    )
    return curs.fetchone()


def insert_vote(conn, user_id, item_type, item_id, vote):
    curs = dbi.cursor(conn)
    curs.execute(
        '''
        INSERT INTO votes(user_id, item_type, item_id, vote)
        VALUES (%s,%s,%s,%s)
        ''',
        (user_id, item_type, item_id, vote)
    )


def update_vote(conn, user_id, item_type, item_id, vote):
    curs = dbi.cursor(conn)
    curs.execute(
        '''
        UPDATE votes
        SET vote=%s
        WHERE user_id=%s AND item_type=%s AND item_id=%s
        ''',
        (vote, user_id, item_type, item_id)
    )


def update_vote_counts(conn, item_type, item_id, old_vote, new_vote):
    table, id_col = ITEM_MAP[item_type]
    curs = dbi.cursor(conn)

    if old_vote == new_vote:
        return

    if old_vote == 'up':
        curs.execute(
            f"UPDATE {table} SET upvotes=upvotes-1 WHERE {id_col}=%s",
            [item_id]
        )
    elif old_vote == 'down':
        curs.execute(
            f"UPDATE {table} SET downvotes=downvotes-1 WHERE {id_col}=%s",
            [item_id]
        )

    if new_vote == 'up':
        curs.execute(
            f"UPDATE {table} SET upvotes=upvotes+1 WHERE {id_col}=%s",
            [item_id]
        )
    else:
        curs.execute(
            f"UPDATE {table} SET downvotes=downvotes+1 WHERE {id_col}=%s",
            [item_id]
        )


def get_vote_counts(conn, item_type, item_id):
    table, id_col = ITEM_MAP[item_type]
    curs = dbi.dict_cursor(conn)
    curs.execute(
        f"SELECT upvotes, downvotes FROM {table} WHERE {id_col}=%s",
        [item_id]
    )
    return curs.fetchone()


def apply_status_or_delete(conn, item_type, item_id, upvotes, downvotes):
    table, id_col = ITEM_MAP[item_type]
    curs = dbi.cursor(conn)

    if downvotes >= 50:
        if item_type == "event":
            curs.execute("DELETE FROM rsvp WHERE event_id=%s", [item_id])
            curs.execute("DELETE FROM comments WHERE event_id=%s", [item_id])
        else:
            curs.execute("DELETE FROM comments WHERE resource_id=%s", [item_id])

        curs.execute(
            f"DELETE FROM {table} WHERE {id_col}=%s",
            [item_id]
        )
        return "deleted"

    status = "flagged" if downvotes >= 20 else "active"
    curs.execute(
        f"UPDATE {table} SET status=%s WHERE {id_col}=%s",
        (status, item_id)
    )
    return status
