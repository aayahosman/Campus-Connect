from flask import Blueprint, request, jsonify, session
import cs304dbi as dbi
from db import vote_db

votes_bp = Blueprint('votes_bp', __name__, url_prefix='/votes')


def getConn():
    """Return a database connection."""
    return dbi.connect()


@votes_bp.route('/<item_type>/<int:item_id>', methods=['POST'])
def vote(item_type, item_id):
    """
    Record an upvote or downvote on an event or resource.
    Enforces login, prevents duplicate same-votes, updates counts,
    and applies status or deletion thresholds.
    """
    # Enforce login
    if 'user_id' not in session:
        return jsonify({"error": "login required"}), 403

    user_id = session['user_id']

    # Read JSON payload safely
    data = request.get_json() or {}
    vote_type = data.get("vote")

    # Validate inputs
    if vote_type not in ["up", "down"]:
        return jsonify({"error": "invalid vote"}), 400

    if item_type not in ["event", "resource"]:
        return jsonify({"error": "invalid item type"}), 400

    conn = getConn()

    # Ensure the target item exists
    if not vote_db.item_exists(conn, item_type, item_id):
        return jsonify({"error": "item not found"}), 404

    # Check for an existing vote by this user
    previous = vote_db.get_previous_vote(conn, user_id, item_type, item_id)

    # Same vote twice → no change
    if previous and previous["vote"] == vote_type:
        return jsonify({"message": "already voted"}), 200

    # Insert or update vote record
    if previous:
        vote_db.update_vote(conn, user_id, item_type, item_id, vote_type)
    else:
        vote_db.insert_vote(conn, user_id, item_type, item_id, vote_type)

    # Update aggregate vote counts
    vote_db.apply_vote_count_change(
        conn,
        item_type,
        item_id,
        previous_vote=(previous["vote"] if previous else None),
        new_vote=vote_type
    )

    # Fetch updated counts
    counts = vote_db.get_vote_counts(conn, item_type, item_id)
    dnv = counts["downvotes"]

    # Hard delete threshold
    if dnv >= 50:
        vote_db.delete_item_and_dependencies(conn, item_type, item_id)
        conn.commit()
        return jsonify({"message": "item deleted", "deleted": True}), 200

    # Soft status update
    status = "flagged" if dnv >= 20 else "active"
    vote_db.update_item_status(conn, item_type, item_id, status)

    conn.commit()
    return jsonify({"message": "vote recorded", "status": status}), 200
