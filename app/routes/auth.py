from flask import Blueprint, render_template, request, redirect, session, jsonify
from werkzeug.security import check_password_hash
from app.models import get_user, add_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/check_password", methods=["POST"])
def check_password():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    user = get_user(username)
    if user and check_password_hash(user["password"], password):
        return jsonify({"result": "correct"})
    return jsonify({"result": "incorrect"})

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user(username)
        if user and check_password_hash(user["password"], password):
            session.permanent = True
            session["user"] = username
            return redirect("/landing")
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return render_template("signup.html", error="Please fill all fields")
        if get_user(username):
            return render_template("signup.html", error="Username already exists")
        add_user(username, password)
        session["user"] = username
        return redirect("/landing")
    return render_template("signup.html")

@auth_bp.route("/check_username", methods=["GET"])
def check_username():
    username = request.args.get("username", "").strip()
    
    if not username or len(username) < 3:
        return jsonify({"available": False})
    
    try:
        user = get_user(username)
        return jsonify({"available": user is None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
