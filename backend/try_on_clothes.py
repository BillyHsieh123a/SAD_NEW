from flask import Blueprint, request, jsonify, session
from db import get_psql_conn
from s3 import upload_to_s3, get_presigned_url, delete_image_from_s3

user_clothes_bp = Blueprint("user_clothes", __name__, url_prefix="/api/user-clothes")

def save_user_clothes_to_db(user_id, file, clothes_type):
    res, status = upload_to_s3(file, prefix="clothes")
    if status != 200:
        return res, status

    filepath = res["filename"]

    conn = get_psql_conn()
    cur = conn.cursor()
    try:
        print(f"[DEBUG] Inserting into DB: user_id={user_id}, type={clothes_type}, filepath={filepath}")
        cur.execute(
            'INSERT INTO "Clothes" (user_id, type, filepath) VALUES (%s, %s, %s) RETURNING clothes_id',
            (user_id, clothes_type, filepath)
        )
        clothes_id = cur.fetchone()[0]
        conn.commit()
        print(f"[DEBUG] Insert successful, clothes_id={clothes_id}")
        return {
            "message": "Clothing item saved",
            "clothes_id": clothes_id,
            "type": clothes_type,
            "filepath": filepath,
            "presigned_url": get_presigned_url(filepath)
        }, 200
    except Exception as e:
        print(f"[ERROR] Failed to insert into Clothes: {e}")
        conn.rollback()
        return {"error": str(e)}, 500
    finally:
        cur.close()
        conn.close()

@user_clothes_bp.post("/upload")
def upload_user_clothes():
    user_id = session.get("user_id")
    file = request.files.get("clothes-photo")
    clothes_type = request.form.get("type")  # Should be 'Tops' or 'Bottoms'
    print(f"[DEBUG] user_id: {user_id}, file: {file}, type: {clothes_type}")
    if not user_id or not file or clothes_type not in ("Tops", "Bottoms"):
        return jsonify({"error": "Missing user_id, file, or type"}), 400

    res, status = save_user_clothes_to_db(user_id, file, clothes_type)
    return jsonify(res), status

@user_clothes_bp.post("/bulk-upload")
def bulk_upload_clothes():
    user_id = session.get("user_id")
    files = request.files.getlist("clothes-photos")
    clothes_type = request.form.get("type")  # 'Tops' or 'Bottoms'
    if not user_id or not files or clothes_type not in ("Tops", "Bottoms"):
        return jsonify({"error": "Missing user_id, files, or type"}), 400

    results = []
    for file in files:
        res, status = save_user_clothes_to_db(user_id, file, clothes_type)
        if status == 200:
            results.append(res)
        else:
            results.append({"error": res.get("error", "Unknown error")})
    return jsonify(results), 200

@user_clothes_bp.get("/")
def get_user_clothes():
    user_id = request.args.get("user_id", session.get("user_id"))
    conn = get_psql_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT clothes_id, type, filepath FROM "Clothes" WHERE user_id = %s',
            (user_id,)
        )
        clothes = [
            {
                "clothes_id": row[0],
                "type": row[1],
                "url": get_presigned_url(row[2])
            }
            for row in cur.fetchall()
        ]
        cur.close()
        return jsonify(clothes), 200
    finally:
        conn.close()

@user_clothes_bp.delete("/<int:clothes_id>")
def delete_clothing_item(clothes_id):
    user_id = session.get("user_id")
    conn = get_psql_conn()
    try:
        cur = conn.cursor()
        # Get filepath for S3 deletion
        cur.execute('SELECT filepath FROM "Clothes" WHERE user_id = %s AND clothes_id = %s', (user_id, clothes_id))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Item not found"}), 404
        filepath = row[0]
        delete_image_from_s3(filepath)
        cur.execute('DELETE FROM "Clothes" WHERE user_id = %s AND clothes_id = %s', (user_id, clothes_id))
        conn.commit()
        return jsonify({"message": "Clothing item deleted"}), 200
    finally:
        cur.close()
        conn.close()