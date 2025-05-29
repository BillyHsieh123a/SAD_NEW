import requests
# from pathlib import Path
import os
from dotenv import load_dotenv
import time
# from io import BytesIO
from s3 import download_image, upload_image_from_url, get_presigned_url

API_KEY = None

def init_fitroom_api_key():
    global API_KEY
    load_dotenv()
    API_KEY =  os.getenv("FITROOM_API_KEY")

# AVATAR_PATH = Path("avatar.jpg")
# GARMENT_PATH = Path("strpshirt_white.jpg")

# check the validity of avatar
# def avatar_check(image_path, api_key):
#     url = "https://platform.fitroom.app/api/tryon/input_check/v1/model"
#     headers = {
#         "X-API-KEY": api_key
#     }

#     with image_path.open("rb") as img_file:
#         files = {
#             "input_image": img_file
#         }
#         res = requests.post(url, headers=headers, files=files)

#     print("Status Code:", res.status_code)
#     try:
#         print("Response JSON:", res.json())
#     except Exception:
#         print("Response Text:", res.text)

# # 執行檢查
# avatar_check(AVATAR_PATH, API_KEY)

# check the validity of clothes
# def clothes_check(image_path, api_key):
    # url = "https://platform.fitroom.app/api/tryon/input_check/v1/clothes"
    # headers = {
    #     "X-API-KEY": api_key
    # }

    # with image_path.open("rb") as img_file:
    #     files = {
    #         "input_image": img_file
    #     }
    #     res = requests.post(url, headers=headers, files=files)

    # print("Status Code:", res.status_code)
    # try:
    #     print("Response JSON:", res.json())
    # except Exception:
    #     print("Response Text:", res.text)

# # 執行衣服圖片檢查
# clothes_check(GARMENT_PATH, API_KEY)

# get tryon result
def poll_tryon_result(task_id, poll_interval=2, max_retries=10):
    url = f"https://platform.fitroom.app/api/tryon/v2/tasks/{task_id}"
    headers = {
        "X-API-KEY": API_KEY
    }

    for attempt in range(max_retries):
        res = requests.get(url, headers=headers)
        print(f"[Try {attempt+1}] Status Code:", res.status_code)

        if res.status_code == 200:
            data = res.json()
            status = data.get("status", "")
            progress = data.get("progress", "")
            print("Current status:", status)
            print("Progress:", progress)

            if status == "COMPLETED" and "download_signed_url" in data:
                image_url = data["download_signed_url"]
                # print("✅ Download URL:", image_url)

                # 下載圖片
                # img_data = requests.get(image_url).content
                # output_path = Path("tryon_result_v2.jpg")
                # with open(output_path, "wb") as f:
                #     f.write(img_data)

                # print(f"✅ Image saved to: {output_path.resolve()}")
                response_body, status_code = upload_image_from_url(image_url = image_url, prefix = "try_on", filename_hint= "try_on.jpg")

                # print(response_body['message'])        # 'Upload successful'
                # print(response_body['presigned_url'])  # S3 URL
                # print(status_code)                     # 200
                return response_body, status_code

            elif status in ("FAILED", "CANCELLED"):
                print("❌ Task failed or was cancelled.")
                return None, None

        else:
            print("❌ Unexpected response:", res.text)

        time.sleep(poll_interval)

    print("❌ Gave up polling after retries.")
    return None, None

# ✅ 執行輪詢與下載
# poll_tryon_result(task_id=TASK_ID, api_key=API_KEY)

# create tryon task and get the result using poll_tryon_result() 
def create_tryon_task(model_url, cloth_type, upper_url=None, lower_url=None, waittime_to_poll=12):
    url = "https://platform.fitroom.app/api/tryon/v2/tasks"
    headers = {"X-API-KEY": API_KEY}
    model_file = download_image(model_url, "model")

    files = {
        "model_image": (model_file.name, model_file, "image/jpeg")
    }

    # 判斷上傳欄位
    if cloth_type == "combo":
        if not upper_url or not lower_url:
            raise ValueError("❗ combo requires both upper_url and lower_url.")
        upper_file = download_image(upper_url, "upper_cloth")
        lower_file = download_image(lower_url, "lower_cloth")

        files["cloth_image"] = (upper_file.name, upper_file, "image/jpeg")
        files["lower_cloth_image"] = (lower_file.name, lower_file, "image/jpeg")
    else:
        if not upper_url:
            raise ValueError(f"❗ cloth_type '{cloth_type}' requires upper_url as cloth_image.")
        cloth_file = download_image(upper_url, "cloth")
        files["cloth_image"] = (cloth_file.name, cloth_file, "image/jpeg")

    data = {
        "cloth_type": cloth_type  # upper / lower / full / combo
    }

    res = requests.post(url, headers=headers, files=files, data=data)
    print("Status Code:", res.status_code)

    try:
        response_json = res.json()
        print("Response JSON:", response_json)
        task_id = response_json["task_id"]
        time.sleep(waittime_to_poll)
        response_body, status_code = poll_tryon_result(task_id=task_id, api_key=API_KEY)
        if response_body and status_code:
            return response_body, status_code
        else:
            return None, None
    except Exception as e:
        print("❌ Failed to parse response:", e)
        print("Raw response:", res.text)
        return None, None

# example
# create_tryon_task_v2(
#     cloth_path=GARMENT_PATH,
#     model_path=AVATAR_PATH,
#     cloth_type="upper"
# )

# try on pass in model_filename, upper_filename, lower_filename
# return {'message', 'filename', 'presigned_url'}, status_code
def try_on(model_filename, upper_filename, lower_filename, cloth_types: list):
    model_url = get_presigned_url(model_filename)
    upper_url = get_presigned_url(upper_filename)
    lower_url = None
    cloth_type = cloth_types[0]
    if len(cloth_types) > 1:
        lower_url = get_presigned_url(lower_filename)
        cloth_type = "combo"

    response_body, status_code = create_tryon_task(
        model_url = model_url, 
        cloth_type = cloth_type, 
        upper_url = upper_url, 
        lower_url = lower_url
    )

    return response_body, status_code # 'message', 'filename', 'presigned_url', status_code

# init_fitroom_api_key()
# model_filename = None
# upper_filename = None
# lower_filename = None
# cloth_types = []
# import time
# start = time.time()
# response_body, status_code = try_on(model_filename, upper_filename, lower_filename, cloth_types)
# end = time.time()
# print(response_body, status_code) #{'message': , 'presigned_url':}, 200
# print(end - start)