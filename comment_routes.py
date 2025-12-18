from flask import Blueprint, request, jsonify, session
import cs304dbi as dbi
from db import comment_db

comment_routes = Blueprint("comment_routes", __name__)


def get_conn():
    """Return a database connection."""
    return dbi.connect()


@comment_routes.route("/comments", methods=["POST"])
def create_comment():
    """
    Create a new comment on either an event or a resource.
    Requires login. Expects JSON with: content and exactly one of event_id/resource_id.
    """
    # Enforce login: comments must be tied to a user
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    # Read JSON payload safely
    data = request.get_json() or {}

    user_id = session["user_id"]
    content = (data.get("content") or "").strip()
    event_id = data.get("event_id")
    resource_id = data.get("resource_id")

    # Basic validation: comment text required
    if not content:
        return jsonify({"error": "Content required"}), 400

    # Require exactly one target: event OR resource
    if bool(event_id) == bool(resource_id):
        return jsonify({"error": "Provide exactly one of event_id or resource_id"}), 400

    conn = get_conn()

    # Insert the comment using the DB helper
    comment_db.insert_comment(
        conn,
        content=content,
        user_id=user_id,
        event_id=event_id,
        resource_id=resource_id
    )

    return jsonify({"message": "Comment added!"}), 201


@comment_routes.route("/comments/<item_type>/<int:item_id>")
def get_comments(item_type, item_id):
    """
    Return comments for an event or resource as JSON.
    Includes an `owned` flag so the UI can show edit/delete buttons to the author.
    """
    # Validate item type to keep the API predictable
    if item_type not in ["event", "resource"]:
        return jsonify({"error": "Invalid type"}), 400

    conn = get_conn()

    # Current user id (or -1 if not logged in), used to compute `owned`
    user_id = session.get("user_id", -1)

    # Fetch the appropriate comment list
    if item_type == "event":
        comments = comment_db.list_comments_for_event(conn, item_id, user_id)
    else:
        comments = comment_db.list_comments_for_resource(conn, item_id, user_id)

    return jsonify(comments), 200


@comment_routes.route("/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    """
    Delete a comment by id.
    Only the user who created the comment may delete it.
    """
    # Enforce login
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    conn = get_conn()

    # Ownership check before deleting
    row = comment_db.get_comment_owner(conn, comment_id)
    if not row:
        return jsonify({"error": "Comment not found"}), 404

    if row["created_by"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    comment_db.delete_comment(conn, comment_id)
    return jsonify({"message": "Comment deleted"}), 200


@comment_routes.route("/comments/<int:comment_id>", methods=["PUT"])
def edit_comment(comment_id):
    """
    Update the content of an existing comment.
    Only the user who created the comment may edit it.
    """
    # Enforce login
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json() or {}
    new_content = (data.get("content") or "").strip()

    # Basic validation: do not allow empty updates
    if not new_content:
        return jsonify({"error": "Content cannot be empty"}), 400

    conn = get_conn()

    # Ownership check before updating
    row = comment_db.get_comment_owner(conn, comment_id)
    if not row:
        return jsonify({"error": "Comment not found"}), 404

    if row["created_by"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    comment_db.update_comment(conn, comment_id, new_content)
    return jsonify({"message": "Comment updated"}), 200
