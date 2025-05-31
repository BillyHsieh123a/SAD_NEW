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
    cur.execute("SELECT password FROM users WHERE name = %s", (username,))
    row = cur.fetchone()

    if row:
        if row[0] == password:
            session['username'] = username
            session['login'] = True
            return jsonify({"success": True, "message": "Login successful."}), 200
        else:
            return jsonify({"success": False, "message": "Password is incorrect."}), 401
    else:
        # Insert new user, but do NOT log them in
        cur.execute("INSERT INTO users (name, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return jsonify({"success": False, "message": "Account created. Please log in."}), 201