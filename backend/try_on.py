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