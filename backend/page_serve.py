from flask import (Blueprint, jsonify, request, session, render_template,
                   url_for, redirect)


page_serve = Blueprint("page_serve", __name__)

# index html
@page_serve.get('/')
def index():
    if session.get("login"):
        return redirect("/try-on")
    else:
        return redirect("/login")  # redirect to login page if not logged in

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
    # Only allow access if logged in
    if not session.get("login"):
        return redirect("/login")
    return render_template("try-on.html")


# # index html
# @page_serve.get('/')
# def index():
#     if session.get("login"):
#         return redirect("/category")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in


# @page_serve.get('/bag')
# def serve_bag_page():
#     if session.get("login"):
#         return render_template("bag.html")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in


# @page_serve.get('/category')
# def serve_category_page():
#     return render_template("category.html")


# @page_serve.get('/checkout')
# def serve_checkout_page():
#     if session.get("login"):
#         return render_template("checkout.html")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in


# @page_serve.get('/favorite')
# def serve_favorite_page():
#     if session.get("login"):
#         return render_template("favorite.html")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in


# @page_serve.get('/item')
# def serve_item_page():
#     if session.get("login"):
#         return render_template("item.html")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in


# @page_serve.get('/login')
# def serve_login_page():
#     return render_template("login.html")


# @page_serve.get('/ordered')
# def serve_ordered_page():
#     if session.get("login"):
#         return render_template("ordered.html")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in


# @page_serve.get('/signin')
# def serve_signin_page():
#     return render_template("signin.html")


# @page_serve.get('/try-on')
# def serve_tryon_page():
#     # For now, just always render the try-on page
#     return render_template("try-on.html")


# @page_serve.get('/user_account_base')
# def serve_user_account_base_page():
#     if session.get("login"):
#         return render_template("user_account_base.html")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in


# @page_serve.get('/user_details')
# def serve_user_details_page():
#     if session.get("login"):
#         return render_template("user_details.html")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in


# @page_serve.get('/user_orders')
# def serve_user_orders__page():
#     if session.get("login"):
#         return render_template("user_orders.html")
#     else:
#         return redirect("/login")  # redirect to login page if not logged in