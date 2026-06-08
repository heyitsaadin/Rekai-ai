from flask import Blueprint, request, session, jsonify, redirect
from werkzeug.security import check_password_hash
from app.models import (
    get_user, update_username_db, update_password_db, 
    delete_all_chat_sessions, get_chat_session, get_chat_sessions,
    pin_chat_session
)
import uuid

account_bp = Blueprint('account', __name__, url_prefix='/account')

@account_bp.route("/change_password", methods=["POST"])
def change_password():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    
    if not current_password or not new_password:
        return jsonify({"error": "Missing fields"}), 400
    
    user = get_user(session["user"])
    if not user or not check_password_hash(user["password"], current_password):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    try:
        update_password_db(session["user"], new_password)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@account_bp.route("/change_username", methods=["POST"])
def change_username():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    new_username = data.get("new_username", "").strip()
    password = data.get("password", "")
    
    if not new_username or not password:
        return jsonify({"error": "Missing fields"}), 400
    
    if len(new_username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    user = get_user(session["user"])
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Password is incorrect"}), 401
    
    if get_user(new_username):
        return jsonify({"error": "Username already exists"}), 409
    
    try:
        update_username_db(session["user"], new_username)
        session["user"] = new_username
        return jsonify({"ok": True, "new_username": new_username})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@account_bp.route("/delete", methods=["POST"])
def delete_account():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    password = data.get("password", "")
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    user = get_user(session["user"])
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Password is incorrect"}), 401
    
    try:
        delete_all_chat_sessions(session["user"])
        session.clear()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@account_bp.route("/chats", methods=["GET"])
def get_chats():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        sessions = get_chat_sessions(session["user"])
        chats = []
        for s in sessions:
            messages = s.get("messages", "[]")
            if isinstance(messages, str):
                import json
                try:
                    messages = json.loads(messages)
                except:
                    messages = []
            preview = ""
            if messages and len(messages) > 0:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    preview = last_msg.get("content", "")[:100]
            chats.append({
                "session_key": s["session_key"],
                "preview": preview,
                "updated_at": s.get("updated_at", ""),
                "created_at": s.get("created_at", ""),
                "is_pinned": s.get("is_pinned", False)
            })
        return jsonify({"chats": chats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@account_bp.route("/chats/delete_all", methods=["POST"])
def delete_all_chats():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        delete_all_chat_sessions(session["user"])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@account_bp.route("/chat/<session_key>", methods=["GET"])
def view_chat(session_key):
    if "user" not in session:
        return redirect("/")
    
    try:
        chat = get_chat_session(session["user"], session_key)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        
        messages = chat.get("messages", "[]")
        if isinstance(messages, str):
            import json
            try:
                messages = json.loads(messages)
            except:
                messages = []
        
        return jsonify({
            "session_key": chat["session_key"],
            "messages": messages,
            "created_at": chat.get("created_at", ""),
            "updated_at": chat.get("updated_at", ""),
            "is_pinned": chat.get("is_pinned", False)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@account_bp.route("/chat/<session_key>/pin", methods=["POST"])
def pin_chat(session_key):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    is_pinned = data.get("is_pinned", True)
    
    try:
        pin_chat_session(session["user"], session_key, is_pinned)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@account_bp.route("/check_username", methods=["GET"])
def check_username():
    username = request.args.get("username", "").strip()
    
    if not username or len(username) < 3:
        return jsonify({"available": False})
    
    try:
        user = get_user(username)
        return jsonify({"available": user is None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
