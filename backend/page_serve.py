from flask import (Blueprint, jsonify, request, session, render_template,
                   url_for, redirect)


page_serve = Blueprint("page_serve", __name__)

# index html
@page_serve.get('/')
def index():
    if session.get("login"):
        return redirect("/try-on")
    else:
        return redirect("/login")

@page_serve.route('/login', methods=['GET', 'POST'])
def serve_login_page():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Dummy credentials for now
        if username == "test" and password == "test":
            session["login"] = True
            session["username"] = username
            return redirect("/try-on")
        else:
            error = "Invalid username or password."
        # Placeholder for DB authentication logic
        # TODO: Replace with real DB check
    return render_template("login.html", error=error)

@page_serve.get('/try-on')
def serve_tryon_page():
    if not session.get("login"):
        return redirect("/login")
    return render_template("try-on.html")