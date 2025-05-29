from flask import request, jsonify
import boto3
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError
import os
from dotenv import load_dotenv
import uuid
from io import BytesIO
import requests

# S3 設定
s3_setting = {
    "S3_BUCKET": None,
    "S3_REGION": None,
    # "S3_ACCESS_KEY": None,
    # "S3_SECRET_KEY": None,
}

s3 = None
def init_s3():
    global s3
    global s3_setting
    load_dotenv()
    s3_setting['S3_BUCKET'] = os.getenv("S3_BUCKET")
    s3_setting['S3_REGION'] = os.getenv("S3_REGION")
    # s3_setting['S3_ACCESS_KEY'] = os.getenv("S3_ACCESS_KEY")
    # s3_setting['S3_SECRET_KEY'] = os.getenv("S3_SECRET_KEY")

    # s3 = boto3.client('s3',
    #                 region_name=s3_setting['S3_REGION'],
    #                 aws_access_key_id=s3_setting['S3_ACCESS_KEY'],
    #                 aws_secret_access_key=s3_setting['S3_SECRET_KEY'])

    s3 = boto3.client('s3', region_name=s3_setting['S3_REGION']) 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# get presigned url from filename
def get_presigned_url(filename, expires_in=300):
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': s3_setting['S3_BUCKET'],
            'Key': filename
        },
        ExpiresIn=expires_in
    )

# 通用的上傳s3處理函式
# return {'message', 'filename', 'presigned_url'}, status_code
def _upload_bytes_to_s3(prefix, data_bytes, content_type, filename_hint):
    unique_id = uuid.uuid4().hex
    filename = f"{prefix}/{unique_id}_{secure_filename(filename_hint)}"

    try:
        s3.upload_fileobj(
            BytesIO(data_bytes),
            s3_setting['S3_BUCKET'],
            filename,
            ExtraArgs={'ContentType': content_type}
        )

        return {
            'message': 'Upload successful',
            'filename': filename,
            'presigned_url': get_presigned_url(filename, expires_in=300)
        }, 200

    except NoCredentialsError:
        return {'error': 'AWS credentials not found'}, 500

# upload image from frontend, prefix = clothes/avatar
def upload_to_s3(prefix):
    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['photo']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        return _upload_bytes_to_s3(
            prefix=prefix,
            data_bytes=file.read(),
            content_type=file.content_type,
            filename_hint=file.filename
        )

    return jsonify({'error': 'Invalid file type'}), 400

# upload image using url/presigned url 
def upload_image_from_url(image_url: str, prefix: str, filename_hint: str = "try_on.jpg"):
    try:
        response = requests.get(image_url)
        if response.status_code != 200:
            return {'error': 'Failed to download image'}, 400

        content_type = response.headers.get("Content-Type", "image/jpeg")
        return _upload_bytes_to_s3(
            prefix=prefix,
            data_bytes=response.content,
            content_type=content_type,
            filename_hint=filename_hint
        )

    except Exception as e:
        return {'error': str(e)}, 500

# download image from url/presigned url
def download_image(url, label):
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"❌ Failed to download {label} image: {res.status_code}")
    img = BytesIO(res.content)
    img.name = f"{label}.jpg"
    return img

# delete image from s3
def delete_image_from_s3(filename: str):
    try:
        s3.delete_object(
            Bucket=s3_setting['S3_BUCKET'],
            Key=filename
        )
        return {'message': 'Delete successful', 'filename': filename}, 200
    except Exception as e:
        return {'error': f'Failed to delete: {str(e)}'}, 500

# example
# init_s3()
# sample_image_url = "https://shoplineimg.com/5f4760ee70e52e003f4199b5/657bfa1a28b4fe001af779e3/800x.jpg"
# response, status_code = upload_image_from_url(image_url = sample_image_url, prefix = "avatar", filename_hint = "avatar.jpg")
# print(response, status_code)

# print(delete_image_from_s3('avatar/84a49a0c11fe4128996d1e3507c101b1_avatar.jpg'))