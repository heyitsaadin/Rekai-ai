from flask import Blueprint, render_template, request, redirect, session, jsonify
from app.models import get_chat_sessions, log_visit, get_shared_chat
from app.utils.helpers import get_greeting
import os
import json

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    if "user" in session:
        return redirect("/landing")
    return render_template("login.html")

@main_bp.route("/landing")
def landing():
    if "user" not in session:
        return redirect("/")
    username = session["user"]
    sessions = get_chat_sessions(username)
    log_visit()
    return render_template("landing.html", username=username, sessions=sessions)

@main_bp.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template("chat.html", username=session["user"], messages=[], is_new_reply=False)

@main_bp.route("/quiz")
def quiz():
    if "user" not in session:
        return redirect("/")
    return render_template("quiz.html", username=session["user"])

@main_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")

@main_bp.route("/shared/<share_token>")
def shared_chat(share_token):
    """View a shared chat"""
    try:
        chat = get_shared_chat(share_token)
        if not chat:
            return render_template("404.html"), 404
        
        messages = chat.get("messages", [])
        if isinstance(messages, str):
            messages = json.loads(messages)
        
        return render_template("shared_chat.html", 
                             username=chat.get("username", ""),
                             title=chat.get("title", "Shared Chat"),
                             messages=messages,
                             shared_at=chat.get("shared_at", ""),
                             share_url=request.url)
    except Exception as e:
        return render_template("404.html"), 404

@main_bp.route("/logout_now", methods=["POST"])
def logout_now():
    """Logout endpoint for AJAX requests"""
    session.clear()
    return jsonify({"ok": True})
