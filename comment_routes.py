from flask import Blueprint, request, jsonify, session
import cs304dbi as dbi

comment_routes = Blueprint("comment_routes", __name__)

def get_conn():
    return dbi.connect()

# CREATE COMMENT
@comment_routes.route("/comments", methods=["POST"])
def create_comment():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()

    user_id = session["user_id"]             # matches users.user_id
    content = data.get("content")
    event_id = data.get("event_id")
    resource_id = data.get("resource_id")

    if not content:
        return jsonify({"error": "Content required"}), 400

    conn = get_conn()
    curs = dbi.dict_cursor(conn)

    # Insert comment using correct schema
    curs.execute(
        """
        INSERT INTO comments (content, event_id, resource_id, created_by, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        [content, event_id, resource_id, user_id]
    )

    conn.commit()
    return jsonify({"message": "Comment added!"}), 201



# GET COMMENTS
@comment_routes.route("/comments/<item_type>/<item_id>")
def get_comments(item_type, item_id):

    if item_type not in ["event", "resource"]:
        return jsonify({"error": "Invalid type"}), 400

    conn = get_conn()
    curs = dbi.dict_cursor(conn)

    # current user (or -1 if not logged in)
    user_id = session.get("user_id", -1)

    # Build query based on event vs resource
    if item_type == "event":
        query = """
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
        """
    else:  # resource
        query = """
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
        """

    # NOTE: Pass user_id FIRST, then item_id
    curs.execute(query, [user_id, item_id])

    comments = curs.fetchall()
    return jsonify(comments), 200


@comment_routes.route("/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    conn = get_conn()
    curs = dbi.dict_cursor(conn)

    # check ownership
    curs.execute("SELECT created_by FROM comments WHERE comment_id = %s", [comment_id])
    row = curs.fetchone()

    if not row:
        return jsonify({"error": "Comment not found"}), 404

    if row["created_by"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    # delete
    curs.execute("DELETE FROM comments WHERE comment_id = %s", [comment_id])
    conn.commit()

    return jsonify({"message": "Comment deleted"}), 200


@comment_routes.route("/comments/<int:comment_id>", methods=["PUT"])
def edit_comment(comment_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    new_content = data.get("content", "").strip()

    if not new_content:
        return jsonify({"error": "Content cannot be empty"}), 400

    conn = get_conn()
    curs = dbi.dict_cursor(conn)

    # check ownership
    curs.execute("SELECT created_by FROM comments WHERE comment_id = %s", [comment_id])
    row = curs.fetchone()

    if not row:
        return jsonify({"error": "Comment not found"}), 404

    if row["created_by"] != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    # update
    curs.execute(
        "UPDATE comments SET content=%s WHERE comment_id=%s",
        [new_content, comment_id]
    )
    conn.commit()

    return jsonify({"message": "Comment updated"}), 200


