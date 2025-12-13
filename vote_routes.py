from flask import Blueprint, request, jsonify, session
from cs304dbi import connect
import cs304dbi as dbi

votes_bp = Blueprint('votes_bp', __name__, url_prefix='/votes')

def getConn():
    return connect()

@votes_bp.route('/<item_type>/<int:item_id>', methods=['POST'])
def vote(item_type, item_id):

    if 'user_id' not in session:
        return jsonify({"error": "login required"}), 403

    user_id = session['user_id']
    vote_type = request.json.get("vote")

    if vote_type not in ["up", "down"]:
        return jsonify({"error": "invalid vote"}), 400

    if item_type not in ["event", "resource"]:
        return jsonify({"error": "invalid item type"}), 400

    # Safe table + ID mappings (NO f-strings with user input)
    if item_type == "event":
        table = "events"
        id_col = "event_id"
    else:
        table = "resources"
        id_col = "resource_id"

    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # Check item exists
    curs.execute(f"SELECT * FROM {table} WHERE {id_col}=%s", [item_id])
    item = curs.fetchone()
    if not item:
        return jsonify({"error": "item not found"}), 404

    # Check previous vote
    curs.execute('''
        SELECT vote
        FROM votes
        WHERE user_id=%s AND item_type=%s AND item_id=%s
    ''', (user_id, item_type, item_id))
    previous = curs.fetchone()

    # same vote twice = no change  
    if previous and previous['vote'] == vote_type:
        return jsonify({"message": "already voted"}), 200

    # Update or insert vote
    if previous:
        curs.execute('''
            UPDATE votes
            SET vote=%s
            WHERE user_id=%s AND item_type=%s AND item_id=%s
        ''', (vote_type, user_id, item_type, item_id))
    else:
        curs.execute('''
            INSERT INTO votes(user_id, item_type, item_id, vote)
            VALUES (%s,%s,%s,%s)
        ''', (user_id, item_type, item_id, vote_type))

    # Update counts
    if previous:
        # If switching votes, reverse the old one
        if previous['vote'] == 'up' and vote_type == 'down':
            curs.execute(f"UPDATE {table} SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE {id_col}=%s", [item_id])
        elif previous['vote'] == 'down' and vote_type == 'up':
            curs.execute(f"UPDATE {table} SET downvotes = downvotes - 1, upvotes = upvotes + 1 WHERE {id_col}=%s", [item_id])
    else:
        # First ever vote
        if vote_type == "up":
            curs.execute(f"UPDATE {table} SET upvotes = upvotes + 1 WHERE {id_col}=%s", [item_id])
        else:
            curs.execute(f"UPDATE {table} SET downvotes = downvotes + 1 WHERE {id_col}=%s", [item_id])


    # After update → check thresholds
    curs.execute(f'''
        SELECT upvotes, downvotes
        FROM {table}
        WHERE {id_col}=%s
    ''', [item_id])

    counts = curs.fetchone()
    upv = counts['upvotes']
    dnv = counts['downvotes']

    # HARD DELETE THRESHOLD
    if dnv >= 50:
        # Delete associated data first if needed
        if item_type == "event":
            curs.execute("DELETE FROM rsvp WHERE event_id=%s", [item_id])
            curs.execute("DELETE FROM comments WHERE event_id=%s", [item_id])
        else:
            curs.execute("DELETE FROM comments WHERE resource_id=%s", [item_id])

        curs.execute(f"DELETE FROM {table} WHERE {id_col}=%s", [item_id])
        conn.commit()

        flash(
            f"This {item_type} was removed by the community due to excessive downvotes.",
            "warning"
        )

        return jsonify({
            "message": "item deleted",
            "deleted": True
        }), 200

    # Otherwise: soft status updates
    if dnv >= 20:
        status = 'flagged'
    else:
        status = 'active'

    curs.execute(
        f"UPDATE {table} SET status=%s WHERE {id_col}=%s",
        (status, item_id)
    )

    conn.commit()
    return jsonify({"message": "vote recorded", "status": status}), 200