from flask import Blueprint, request, jsonify, session
from db import get_psql_conn
from fitroom_api_virtual_try_on import try_on as fitroom_try_on
from ai_comments import get_comments
from s3 import get_presigned_url

tryon_bp = Blueprint("tryon", __name__, url_prefix="/api/try-on")

@tryon_bp.post("/")
def try_on():
    user_id = session.get("user_id")
    data = request.get_json()
    top_id = data.get("top_id")
    bottom_id = data.get("bottom_id")

    if not user_id or (not top_id and not bottom_id):
        return jsonify({"error": "Missing user_id or clothing selection"}), 400

    conn = get_psql_conn()
    cur = conn.cursor()

    # Get user photo
    cur.execute("SELECT filepath FROM user_photo WHERE user_id = %s AND photo_id = 1", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "User photo not found"}), 404
    model_filename = row[0]

    # Get top and bottom filepaths
    upper_filename = None
    lower_filename = None
    cloth_types = []
    if top_id:
        cur.execute('SELECT filepath FROM "Clothes" WHERE user_id = %s AND clothes_id = %s', (user_id, top_id))
        row = cur.fetchone()
        if row:
            upper_filename = row[0]
            cloth_types.append("upper")
    if bottom_id:
        cur.execute('SELECT filepath FROM "Clothes" WHERE user_id = %s AND clothes_id = %s', (user_id, bottom_id))
        row = cur.fetchone()
        if row:
            lower_filename = row[0]
            cloth_types.append("lower")

    if not upper_filename and not lower_filename:
        cur.close()
        conn.close()
        return jsonify({"error": "No valid clothing selected"}), 400

    # Call Fitroom API (waits for result)
    response_body, status_code = fitroom_try_on(model_filename, upper_filename, lower_filename, cloth_types)
    if not response_body or status_code != 200:
        cur.close()
        conn.close()
        return jsonify({"error": "Fitroom API failed"}), 500

    tryon_image_filename = response_body["filename"]
    tryon_image_url = response_body["presigned_url"]

    # Call AI comment API
    ai_comment, _ = get_comments(tryon_image_url)
    comments = ai_comment

    # Save result to DB
    cur.execute(
        'INSERT INTO "TryonResults" (user_id, top_id, bottom_id, comments, filepath) VALUES (%s, %s, %s, %s, %s) RETURNING try_on_id',
        (user_id, top_id, bottom_id, comments, tryon_image_filename)
    )
    try_on_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "try_on_id": try_on_id,
        "image_url": tryon_image_url,
        "comments": comments
    }), 200

@tryon_bp.get("/")
def get_user_tryon_results():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify([]), 200
    conn = get_psql_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT try_on_id, filepath, comments FROM "TryonResults" WHERE user_id = %s',
            (user_id,)
        )
        results = [
            {
                "try_on_id": row[0],
                "image_url": get_presigned_url(row[1]),
                "comments": row[2]
            }
            for row in cur.fetchall()
        ]
        cur.close()
        return jsonify(results), 200
    finally:
        conn.close()

@tryon_bp.delete("/<int:try_on_id>")
def delete_tryon_result(try_on_id):
    user_id = session.get("user_id")
    conn = get_psql_conn()
    try:
        cur = conn.cursor()
        # Optionally, delete the image from S3 if needed
        cur.execute('SELECT filepath FROM "TryonResults" WHERE user_id = %s AND try_on_id = %s', (user_id, try_on_id))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Result not found"}), 404
        # from s3 import delete_image_from_s3
        # delete_image_from_s3(row[0])
        cur.execute('DELETE FROM "TryonResults" WHERE user_id = %s AND try_on_id = %s', (user_id, try_on_id))
        conn.commit()
        return jsonify({"message": "Try-on result deleted"}), 200
    finally:
        cur.close()
        conn.close()