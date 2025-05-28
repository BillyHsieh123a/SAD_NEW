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
# s3_setting = {
#     "S3_BUCKET": None,
#     "S3_REGION": None,
#     "S3_ACCESS_KEY": None,
#     "S3_SECRET_KEY": None,
# }

s3 = None
def init_s3():
    # global s3_setting
    # load_dotenv()
    # s3_setting['S3_BUCKET'] = os.getenv("S3_BUCKET")
    # s3_setting['S3_REGION'] = os.getenv("S3_REGION")
    # s3_setting['S3_ACCESS_KEY'] = os.getenv("S3_ACCESS_KEY")
    # s3_setting['S3_SECRET_KEY'] = os.getenv("S3_SECRET_KEY")

    # s3 = boto3.client('s3',
    #                 region_name=s3_setting['S3_REGION'],
    #                 aws_access_key_id=s3_setting['S3_ACCESS_KEY'],
    #                 aws_secret_access_key=s3_setting['S3_SECRET_KEY'])

    global s3
    s3 = boto3.client('s3') 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_presigned_url(filename, expires_in=300):
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': s3_setting['S3_BUCKET'],
            'Key': filename
        },
        ExpiresIn=expires_in
    )

# 通用的上傳處理函式

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

def download_image(url, label):
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"❌ Failed to download {label} image: {res.status_code}")
    img = BytesIO(res.content)
    img.name = f"{label}.jpg"
    return img

def delete_image_from_s3(filename: str):
    try:
        s3.delete_object(
            Bucket=s3_setting['S3_BUCKET'],
            Key=filename
        )
        return {'message': 'Delete successful', 'filename': filename}, 200
    except Exception as e:
        return {'error': f'Failed to delete: {str(e)}'}, 500

# @app.get('/preview/<path:filename>')
# def preview_image(filename):
#     try:
#         s3_obj = s3.get_object(Bucket=s3_setting['S3_BUCKET'], Key=filename)
#         return send_file(
#             io.BytesIO(s3_obj['Body'].read()),
#             mimetype=s3_obj['ContentType']
#         )
#     except Exception as e:
#         return jsonify({'error': str(e)}), 404
    
# if __name__ == '__main__':
#     app.run(debug=True)
