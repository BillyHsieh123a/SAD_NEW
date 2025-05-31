import os
from flask import Flask, render_template, session, redirect
from db import init_db_conn, close_psql_conn
from flask_cors import CORS

from login import login_bp
from try_on import try_on
from page_serve import page_serve
from s3 import init_s3
from fitroom_api_virtual_try_on import init_fitroom_api_key
from ai_comments import init_get_ai_comments
serverURL = "http://127.0.0.1:5000"

# Global Flask app (SUBJECT TO CHANGE)
app = Flask(__name__, template_folder="../frontend/html", static_folder="../frontend/assets")
CORS(app)
app.register_blueprint(login_bp)
app.register_blueprint(try_on)
app.register_blueprint(page_serve)

# Initialize the app and connect to the database.
def init_app():
    init_db_conn()
    app.secret_key = os.urandom(32)  # session key
    init_s3()
    init_fitroom_api_key()
    init_get_ai_comments()

def finish_app():
    close_psql_conn()

if __name__ == '__main__':
    try:
        init_app()
        app.run(host='0.0.0.0', port=5000)
    finally:
        finish_app()