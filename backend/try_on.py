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


# api request for generating tryon
def post_api_request(authorization, user_image_utf8, clothes_image_utf8):
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


# api request for getting image generation status
def poll_task_status(authorization, task_id):
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


# save the generated try-on image on server
def cache_image_on_server(result_image_src, user_id, clothes_id, color):
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


@try_on.post("/image")
def try_on_clothes():
    try:
        user_id = session.get("user_id")
        clothes_id = request.form.get("clothes-id")
        color = request.form.get("color")
        clothes_img_path = request.form.get("product-img-path")
        user_image = request.files.get("user-image")  # flask FileStorage
        
        # convert user image and clothes image to base64 utf8 strings
        user_image_utf8 = base64.b64encode(user_image.read()).decode('utf-8')
        clothes_image_req = requests.get(clothes_img_path)
        clothes_image_utf8 = base64.b64encode(clothes_image_req.content).decode('utf-8')
        
        # prepares for authorization
        load_dotenv()
        kolors_api_key_id = os.getenv('KOLORS_API_KEY_ID')
        kolors_api_key_secret = os.getenv('KOLORS_API_KEY_SECRET')
        authorization = encode_jwt_token(kolors_api_key_id, kolors_api_key_secret)
        
        # send API request
        req_res = post_api_request(authorization, user_image_utf8, clothes_image_utf8)
        
        # retrieve task ID
        task_id = ""
        if req_res.status_code == 200:
            req_res_data = req_res.json()
            task_id = req_res_data["data"]["task_id"]
        else:
            return jsonify({"success": 0}), req_res.status_code
        
        # poll until task is complete
        for i in range(120):  # 2 minutes timeout
            time.sleep(1)
            poll_res = poll_task_status(authorization, task_id)
            poll_res_data = poll_res.json()
            
            if poll_res_data["data"]["task_status"] == "succeed":
                result_image_src = poll_res_data["data"]["task_result"]["images"][0]["url"]
                cache_image_on_server(result_image_src, user_id, clothes_id, color)
                return jsonify({"success": 1, "tryon_image": result_image_src})
            elif poll_res_data["data"]["task_status"] == "failed":
                return jsonify({"error": "Image generation task failed"}), 500
        
        return jsonify({"error": "Image generation timed out"}), 504
    except Exception as e:
        get_psql_conn().rollback()
        print(e)
        return jsonify({"error": str(e)}), 500

@try_on.get("/image")
def try_on_query_cache():
    try:
        user_id = session.get("user_id")
        clothes_id = request.json["clothes_id"]
        color = request.json["color"]
        
        cur = get_psql_conn().cursor()
        cur.execute(
            '''
            SELECT path
            FROM IMAGE AS I
            JOIN TRY_ON AS TRO ON I.filename = TRO.image_filename
            WHERE user_id = %s AND clothes_id = %s AND color = %s
            ''',
            [user_id, clothes_id, color]
        )
        get_psql_conn().commit()
        
        file_path_result = cur.fetchone()
        if file_path_result:
            img_path = "images/" + file_path_result[0]
            return jsonify({"cached": 1, 
                            "tryon_image": url_for("static", filename=img_path)}), 200
        else:
            return jsonify({"cached": 0}), 200
    except Exception as e:
        print(e)
        get_psql_conn().rollback()
        return jsonify({"error": str(e)}), 500
    
# Helper function to insert image metadata into DB
def insert_image_record(image_type, filename):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    image_id = str(uuid.uuid4())
    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO images (id, user_id, filename, type) VALUES (%s, %s, %s, %s)",
        (image_id, user_id, filename, image_type)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Upload successful",
        "image_id": image_id,
        "filename": filename,
        "presigned_url": get_presigned_url(filename)
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
    return jsonify(insert_image_record("clothes", res["filename"])[0])

@try_on.post("/image/avatar")
def upload_avatar():
    res, status = upload_to_s3("avatar")
    if status != 200:
        return jsonify(res), status
    return jsonify(insert_image_record("avatar", res["filename"])[0])

@try_on.post("/image/result")
def upload_result():
    data = request.json
    model_id = data.get("model_id")
    upper_id = data.get("upper_id")
    lower_id = data.get("lower_id")  # optional
    cloth_types = data.get("cloth_types", [])

    if not model_id or not upper_id or not cloth_types:
        return jsonify({"error": "Missing required fields"}), 400

    # Get filenames from DB by ID
    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM images WHERE id = %s", (model_id,))
    model_filename = cur.fetchone()
    cur.execute("SELECT filename FROM images WHERE id = %s", (upper_id,))
    upper_filename = cur.fetchone()
    lower_filename = None

    if lower_id:
        cur.execute("SELECT filename FROM images WHERE id = %s", (lower_id,))
        lower_filename = cur.fetchone()

    cur.close()
    conn.close()

    if not model_filename or not upper_filename or (lower_id and not lower_filename):
        return jsonify({"error": "Invalid image IDs"}), 404

    # Flatten the tuples
    model_filename = model_filename[0]
    upper_filename = upper_filename[0]
    if lower_filename:
        lower_filename = lower_filename[0]

    tryon_result, status = try_on(model_filename, upper_filename, lower_filename, cloth_types)
    if status != 200:
        return jsonify(tryon_result), status

    # Insert try-on result into DB
    return jsonify(insert_image_record("result", tryon_result["filename"])[0])

@try_on.delete("/image/<image_type>")
def delete_image(image_type):
    data = request.json
    image_id = data.get("image_id")
    if not image_id:
        return jsonify({"error": "Missing image_id"}), 400

    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute("SELECT filename FROM images WHERE id = %s AND type = %s", (image_id, image_type))
    result = cur.fetchone()
    if not result:
        cur.close()
        conn.close()
        return jsonify({"error": "Image not found"}), 404

    filename = result[0]

    # Delete from S3
    res, status = delete_image_from_s3(filename)
    if status != 200:
        return jsonify(res), status

    # Delete from DB
    cur.execute("DELETE FROM images WHERE id = %s", (image_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Image deleted successfully", "image_id": image_id}), 200

@try_on.get("/image/clothes")
def get_clothes_images():
    return get_images_by_type("clothes")

@try_on.get("/image/avatar")
def get_avatar_images():
    return get_images_by_type("avatar")

@try_on.get("/image/result")
def get_result_images():
    return get_images_by_type("result")