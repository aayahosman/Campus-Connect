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

    # Build query based on event vs resource
    if item_type == "event":
        query = """
            SELECT 
                c.comment_id,
                c.content,
                c.created_at,
                u.full_name AS author
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
                u.full_name AS author
            FROM comments c
            JOIN users u ON c.created_by = u.user_id
            WHERE c.resource_id = %s
            ORDER BY c.created_at DESC
        """

    curs.execute(query, [item_id])
    comments = curs.fetchall()

    return jsonify(comments), 200
