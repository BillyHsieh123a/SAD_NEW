from flask import Blueprint, request, jsonify, session
from db import get_psql_conn
from s3 import upload_to_s3, get_presigned_url, delete_image_from_s3
import uuid

user_photo_bp = Blueprint("user_photo", __name__, url_prefix="/api/user-photo")

def save_model_photo_to_db(user_id, file):
    res, status = upload_to_s3(file, prefix="avatar")
    if status != 200:
        return res, status

    filepath = res["filename"]
    photo_id = str(uuid.uuid4())

    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_photo (user_id, photo_id, filepath) VALUES (%s, %s, %s)",
        (user_id, photo_id, filepath)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Model photo saved",
        "photo_id": photo_id,
        "filepath": filepath,
        "presigned_url": get_presigned_url(filepath)
    }, 200

@user_photo_bp.post("/upload")
def upload_model_photo():
    user_id = session.get("user_id")
    file = request.files.get("model-photo")
    print(f"[DEBUG] user_id: {user_id}, file: {file}")
    if not user_id or not file:
        return jsonify({"error": "Missing user_id or file"}), 400

    res, status = save_model_photo_to_db(user_id, file)
    return jsonify(res), status

@user_photo_bp.get("/")
def get_avatar_images():
    user_id = request.args.get("user_id", session.get("user_id"))
    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT photo_id, filepath FROM user_photo WHERE user_id = %s",
        (user_id,)
    )
    photos = [
        {"photo_id": row[0], "url": get_presigned_url(row[1])}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return jsonify(photos), 200

@user_photo_bp.delete("/")
def delete_avatar_image():
    user_id = session.get("user_id")
    photo_id = request.json.get("photo_id")
    if not user_id or not photo_id:
        return jsonify({"error": "Missing user_id or photo_id"}), 400

    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute("SELECT filepath FROM user_photo WHERE user_id = %s AND photo_id = %s", (user_id, photo_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "Image not found"}), 404

    filename = row[0]
    res, status = delete_image_from_s3(filename)
    if status != 200:
        return jsonify(res), status

    cur.execute("DELETE FROM user_photo WHERE user_id = %s AND photo_id = %s", (user_id, photo_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Image deleted successfully", "photo_id": photo_id}), 200