from flask import Blueprint, jsonify, request, session, render_template, url_for
from db import get_psql_conn
import base64
from dotenv import load_dotenv
import os
import requests
import json
import jwt
import time
from datetime import datetime
from s3 import delete_image_from_s3, upload_to_s3, get_presigned_url
import uuid


try_on = Blueprint("try_on", __name__, url_prefix="/api/try-on")


def encode_jwt_token(ak, sk):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 600,  # valid for 10 minutes
        "nbf": int(time.time()) - 5  # takes effect prior to 5 seconds
    }
    token = jwt.encode(payload, sk, headers=headers)
    return token


# # api request for generating tryon
# def post_api_request(authorization, user_image_utf8, clothes_image_utf8):
    req_res = requests.post(
        "https://api.klingai.com/v1/images/kolors-virtual-try-on",
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {authorization}"
        },
        json = {
            "model_name": "kolors-virtual-try-on-v1",
            "human_image": user_image_utf8,
            "cloth_image": clothes_image_utf8
        }
    )
    return req_res

# # api request for getting image generation status
# def poll_task_status(authorization, task_id):
    poll_res = requests.get(
        f"https://api.klingai.com/v1/images/kolors-virtual-try-on/{task_id}",
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {authorization}"
        },
        json = {
            "task_id": task_id
        }
    )
    return poll_res

# # save the generated try-on image on server
# def cache_image_on_server(result_image_src, user_id, clothes_id, color):
    filename = f"u{user_id}_c{clothes_id}_cc{color}.png"
    with open(f"../frontend/assets/images/tryon/{filename}", "wb") as f:
        f.write(requests.get(result_image_src).content)
    
    cur = get_psql_conn().cursor()
    cur.execute(
        '''
        SELECT image_filename
        FROM TRY_ON
        WHERE user_id = %s AND clothes_id = %s AND color = %s
        FOR UPDATE
        ''',
        [user_id, clothes_id, color]
    )
    
    if not len(cur.fetchall()):
        cur.execute(
            '''
            INSERT INTO IMAGE
            VALUES(%s, %s)
            ''',
            [filename, f"tryon/{filename}"]
        )
        
        cur.execute(
            '''
            INSERT INTO TRY_ON
            VALUES(%s, %s, %s, %s, %s)
            ''',
            [user_id, clothes_id, color, filename, datetime.now()]
        )
    get_psql_conn().commit()
    
# Helper function to insert image metadata into DB
def insert_clothes_record(filename, cloth_type):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    clothes_id = str(uuid.uuid4())
    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Clothes (user_id, clothes_id, type, filepath) VALUES (%s, %s, %s, %s)",
        (user_id, clothes_id, cloth_type, filename)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Clothing uploaded",
        "clothes_id": clothes_id,
        "url": get_presigned_url(filename)
    }, 200

def insert_photo_record(filename):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    photo_id = str(uuid.uuid4())
    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO UserPhoto (user_id, photo_id, filepath) VALUES (%s, %s, %s)",
        (user_id, photo_id, filename)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Photo uploaded",
        "photo_id": photo_id,
        "url": get_presigned_url(filename)
    }, 200
    
def get_images_by_type(image_type):
    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, filename FROM images WHERE type = %s", (image_type,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    images = []
    for row in rows:
        image_id, filename = row
        presigned_url = get_presigned_url(filename)
        images.append({
            "image_id": image_id,
            "filename": filename,
            "url": presigned_url
        })

    return jsonify(images), 200

@try_on.post("/image/clothes")
def upload_clothes():
    res, status = upload_to_s3("clothes")
    if status != 200:
        return jsonify(res), status

    cloth_type = request.form.get("type", "").lower()
    if cloth_type not in ["top", "bottom"]:
        return jsonify({"error": "Invalid cloth type"}), 400

    return jsonify(insert_clothes_record(res["filename"], cloth_type)[0])

@try_on.post("/image/avatar")
def upload_avatar():
    res, status = upload_to_s3("avatar")
    if status != 200:
        return jsonify(res), status

    user_id = session.get("user_id")
    filename = res["filename"]

    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO UserPhoto (user_id, photo_id, filepath) VALUES (%s, gen_random_uuid(), %s) RETURNING photo_id",
        (user_id, filename)
    )
    photo_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"photo_id": str(photo_id), "url": get_presigned_url(filename)}), 200

@try_on.post("/image/result")
def upload_result():
    data = request.json
    model_id = data.get("model_id")
    upper_id = data.get("upper_id")
    lower_id = data.get("lower_id")
    cloth_types = data.get("cloth_types", [])

    if not model_id or not upper_id or not cloth_types:
        return jsonify({"error": "Missing required fields"}), 400

    user_id = session.get("user_id")
    conn = get_psql_conn()
    cur = conn.cursor()

    # Fetch filenames
    cur.execute("SELECT filepath FROM UserPhoto WHERE user_id = %s AND photo_id = %s", (user_id, model_id))
    model = cur.fetchone()
    cur.execute("SELECT filepath FROM Clothes WHERE user_id = %s AND clothes_id = %s", (user_id, upper_id))
    upper = cur.fetchone()
    lower = None
    if lower_id:
        cur.execute("SELECT filepath FROM Clothes WHERE user_id = %s AND clothes_id = %s", (user_id, lower_id))
        lower = cur.fetchone()

    if not model or not upper or (lower_id and not lower):
        cur.close()
        conn.close()
        return jsonify({"error": "Invalid image IDs"}), 404

    model_filename = model[0]
    upper_filename = upper[0]
    lower_filename = lower[0] if lower else None

    tryon_result, status = try_on(model_filename, upper_filename, lower_filename, cloth_types)
    if status != 200:
        return jsonify(tryon_result), status

    filepath = tryon_result["filename"]
    comments = tryon_result.get("comments", "")

    cur.execute("""
        INSERT INTO TryonResults (user_id, try_on_id, tops_id, bottom_id, comments, filepath)
        VALUES (%s, gen_random_uuid(), %s, %s, %s, %s) RETURNING try_on_id
    """, (user_id, upper_id, lower_id, comments, filepath))

    try_on_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"try_on_id": str(try_on_id), "url": get_presigned_url(filepath)}), 200

@try_on.delete("/image/<image_type>")
def delete_image(image_type):
    data = request.json
    image_id = data.get("image_id")
    user_id = session.get("user_id")

    if not image_id:
        return jsonify({"error": "Missing image_id"}), 400

    conn = get_psql_conn()
    cur = conn.cursor()

    table_map = {
        "avatar": ("UserPhoto", "photo_id"),
        "clothes": ("Clothes", "clothes_id"),
        "result": ("TryonResults", "try_on_id")
    }

    if image_type not in table_map:
        return jsonify({"error": "Invalid image_type"}), 400

    table, id_col = table_map[image_type]

    cur.execute(f"SELECT filepath FROM {table} WHERE user_id = %s AND {id_col} = %s", (user_id, image_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "Image not found"}), 404

    filename = row[0]
    res, status = delete_image_from_s3(filename)
    if status != 200:
        return jsonify(res), status

    cur.execute(f"DELETE FROM {table} WHERE user_id = %s AND {id_col} = %s", (user_id, image_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Image deleted successfully", "image_id": image_id}), 200

@try_on.get("/image/clothes")
def get_clothes_images():
    user_id = request.args.get("user_id", session.get("user_id"))
    cloth_type = request.args.get("type")

    conn = get_psql_conn()
    cur = conn.cursor()

    if cloth_type:
        cur.execute(
            "SELECT clothes_id, type, filepath FROM Clothes WHERE user_id = %s AND type = %s",
            (user_id, cloth_type)
        )
    else:
        cur.execute(
            "SELECT clothes_id, type, filepath FROM Clothes WHERE user_id = %s",
            (user_id,)
        )

    clothes = [
        {"clothes_id": row[0], "type": row[1], "url": get_presigned_url(row[2])}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return jsonify(clothes), 200

@try_on.get("/image/avatar")
def get_avatar_images():
    user_id = request.args.get("user_id", session.get("user_id"))

    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT photo_id, filepath FROM UserPhoto WHERE user_id = %s",
        (user_id,)
    )

    photos = [
        {"photo_id": row[0], "url": get_presigned_url(row[1])}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return jsonify(photos), 200

@try_on.get("/image/result")
def get_result_images():
    user_id = request.args.get("user_id", session.get("user_id"))

    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT try_on_id, tops_id, bottom_id, comments, filepath
        FROM TryonResults
        WHERE user_id = %s
        """,
        (user_id,)
    )

    results = [
        {
            "try_on_id": row[0],
            "tops_id": row[1],
            "bottom_id": row[2],
            "comments": row[3],
            "url": get_presigned_url(row[4])
        }
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()
    return jsonify(results), 200