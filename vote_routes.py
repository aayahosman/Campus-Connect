from flask import Blueprint, request, jsonify, session
from cs304dbi import connect
from db import vote_db

votes_bp = Blueprint('votes_bp', __name__, url_prefix='/votes')

def getConn():
    return connect()

@votes_bp.route('/<item_type>/<int:item_id>', methods=['POST'])
def vote(item_type, item_id):

    if 'user_id' not in session:
        return jsonify({"error": "login required"}), 403

    vote_type = request.json.get("vote")
    if vote_type not in ["up", "down"]:
        return jsonify({"error": "invalid vote"}), 400

    if item_type not in ["event", "resource"]:
        return jsonify({"error": "invalid item type"}), 400

    conn = getConn()
    user_id = session['user_id']

    if not votes_db.item_exists(conn, item_type, item_id):
        return jsonify({"error": "item not found"}), 404

    previous = votes_db.get_previous_vote(conn, user_id, item_type, item_id)

    if previous and previous['vote'] == vote_type:
        return jsonify({"message": "already voted"}), 200

    if previous:
        votes_db.update_vote(conn, user_id, item_type, item_id, vote_type)
        votes_db.update_vote_counts(conn, item_type, item_id, previous['vote'], vote_type)
    else:
        votes_db.insert_vote(conn, user_id, item_type, item_id, vote_type)
        votes_db.update_vote_counts(conn, item_type, item_id, None, vote_type)

    counts = votes_db.get_vote_counts(conn, item_type, item_id)
    result = votes_db.apply_status_or_delete(
        conn, item_type, item_id, counts['upvotes'], counts['downvotes']
    )

    conn.commit()

    return jsonify({
        "message": "vote recorded",
        "result": result
    }), 200
