from flask import Blueprint, request, jsonify, session
import cs304dbi as dbi
from db import comments_db

comment_routes = Blueprint("comment_routes", __name__)

def get_conn():
    return dbi.connect()

# CREATE COMMENT
@comment_routes.route("/comments", methods=["POST"])
def create_comment():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json() or {}

    user_id = session["user_id"]
    content = (data.get("content") or "").strip()
    event_id = data.get("event_id")
    resource_id = data.get("resource_id")

    if not content:
        return jsonify({"error": "Content required"}), 400

    # Require exactly one target
    if bool(event_id) == bool(resource_id):
        return jsonify({"error": "Provide exactly one of event_id or resource_id"}), 400

    conn = get_conn()
    comments_db.insert_comment(
        conn,
        content=content,
        user_id=user_id,
        event_id=event_id,
        resource_id=resource_id
    )

    return jsonify({"message": "Comment added!"}), 201

# GET COMMENTS
@comment_routes.route("/comments/<item_type>/<int:item_id>")
def get_comments(item_type, item_id):
    if item_type not in ["event", "resource"]:
        return jsonify({"error": "Invalid type"}), 400

    conn = get_conn()
    user_id = session.get("user_id", -1)

    if item_type == "event":
        comments = comments_db.list_comments_for_event(conn, item_id, user_id)
    else:
        comments = comments_db.list_comments_for_resource(conn, item_id, user_id)

    return jsonify(comments), 200

# DELETE COMMENT
@comment_routes.route("/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    conn = get_conn()
    row = comments_db.get_comment_owner(conn, comment_id)

    if not row:
        return jsonify({"error": "Comment not found"}), 404

    if row["created_by"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    comments_db.delete_comment(conn, comment_id)
    return jsonify({"message": "Comment deleted"}), 200

# EDIT COMMENT
@comment_routes.route("/comments/<int:comment_id>", methods=["PUT"])
def edit_comment(comment_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json() or {}
    new_content = (data.get("content") or "").strip()

    if not new_content:
        return jsonify({"error": "Content cannot be empty"}), 400

    conn = get_conn()
    row = comments_db.get_comment_owner(conn, comment_id)

    if not row:
        return jsonify({"error": "Comment not found"}), 404

    if row["created_by"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    comments_db.update_comment(conn, comment_id, new_content)
    return jsonify({"message": "Comment updated"}), 200
