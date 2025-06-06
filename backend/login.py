import bcrypt
from flask import Blueprint, request, jsonify, session
from db import get_psql_conn

login_bp = Blueprint("login", __name__, url_prefix="/api/login")

@login_bp.post("/")
def login_():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required."}), 400

    conn = get_psql_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, password FROM users WHERE name = %s", (username,))
    row = cur.fetchone()

    if row:
        user_id, hashed_pw = row
        if bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
            session['username'] = username
            session['user_id'] = user_id
            session['login'] = True
            return jsonify({"success": True, "message": "Login successful."}), 200
        else:
            return jsonify({"success": False, "message": "Password is incorrect."}), 401
    else:
        # Register new user with hashed password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("INSERT INTO users (name, password) VALUES (%s, %s) RETURNING user_id", (username, hashed_pw))
        user_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"success": False, "message": "Account created. Please log in."}), 201
