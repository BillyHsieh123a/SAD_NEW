import os
from flask import Flask, render_template, session, redirect
from db import init_db_conn, close_psql_conn
from flask_cors import CORS

from try_on import try_on
from page_serve import page_serve

serverURL = "http://127.0.0.1:5000"

# Global Flask app (SUBJECT TO CHANGE)
app = Flask(__name__, template_folder="../frontend/html", static_folder="../frontend/assets")
CORS(app)
app.register_blueprint(try_on)
app.register_blueprint(page_serve)


# Initialize the app and connect to the database.
def init_app():
    init_db_conn()
    app.secret_key = os.urandom(32)  # session key

def finish_app():
    close_psql_conn()

if __name__ == '__main__':
    try:
        init_app()
        app.run(host='0.0.0.0', port=5000)
    finally:
        finish_app()