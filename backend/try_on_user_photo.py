from flask import Blueprint, request, jsonify, session
from db import get_psql_conn
from s3 import upload_to_s3, get_presigned_url, delete_image_from_s3

user_photo_bp = Blueprint("user_photo", __name__, url_prefix="/api/user-photo")

def save_user_photo_to_db(user_id, file):
    res, status = upload_to_s3(file, prefix="model")
    if status != 200:
        return res, status

    filepath = res["filename"]
    photo_id = 1  # Always 1 for each user

    conn = get_psql_conn()
    cur = conn.cursor()

    # Delete old photo if exists
    cur.execute("SELECT filepath FROM user_photo WHERE user_id = %s AND photo_id = %s", (user_id, photo_id))
    row = cur.fetchone()
    if row:
        old_filepath = row[0]
        delete_image_from_s3(old_filepath)
        cur.execute("DELETE FROM user_photo WHERE user_id = %s AND photo_id = %s", (user_id, photo_id))

    # Insert new photo
    cur.execute(
        "INSERT INTO user_photo (user_id, photo_id, filepath) VALUES (%s, %s, %s)",
        (user_id, photo_id, filepath)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "User photo saved",
        "photo_id": photo_id,
        "filepath": filepath,
        "presigned_url": get_presigned_url(filepath)
    }, 200

@user_photo_bp.post("/upload")
def upload_user_photo():
    user_id = session.get("user_id")
    file = request.files.get("user-photo")
    print(f"[DEBUG] user_id: {user_id}, file: {file}")
    if not user_id or not file:
        return jsonify({"error": "Missing user_id or file"}), 400

    res, status = save_user_photo_to_db(user_id, file)
    return jsonify(res), status

@user_photo_bp.get("/")
def get_user_photos():
    user_id = request.args.get("user_id", session.get("user_id"))
    conn = get_psql_conn()  # Always get a new connection
    try:
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
        return jsonify(photos), 200
    finally:
        conn.close()

@user_photo_bp.delete("/")
def delete_user_photo():
    print("[DEBUG] delete_user_photo called")
    user_id = session.get("user_id")
    photo_id = 1  # Always 1
    print(f"[DEBUG] user_id: {user_id}, photo_id: {photo_id}")
    conn = get_psql_conn()
    print(f"[DEBUG] conn: {conn}")
    try:
        cur = conn.cursor()
        print("[DEBUG] DB cursor created")
        cur.execute("SELECT filepath FROM user_photo WHERE user_id = %s AND photo_id = %s", (user_id, photo_id))
        row = cur.fetchone()
        print(f"[DEBUG] DB row fetched: {row}")
        if not row:
            cur.close()
            conn.close()
            print("[DEBUG] No image found, returning 404")
            return jsonify({"error": "Image not found"}), 404

        filename = row[0]
        print(f"[DEBUG] Deleting image from S3: {filename}")
        res, status = delete_image_from_s3(filename)
        print(f"[DEBUG] S3 delete result: {res}, status: {status}")
        if status != 200:
            cur.close()
            conn.close()
            print("[DEBUG] S3 delete failed, returning error")
            return jsonify(res), status

        cur.execute("DELETE FROM user_photo WHERE user_id = %s AND photo_id = %s", (user_id, photo_id))
        conn.commit()
        print("[DEBUG] DB record deleted and committed")
        cur.close()
        conn.close()
        print("[DEBUG] DB connection closed, returning success")
        return jsonify({"message": "Image deleted successfully", "photo_id": photo_id}), 200
    except Exception as e:
        print(f"[ERROR] Exception in delete_user_photo: {e}")
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
        return jsonify({"error": "Internal server error"}), 500