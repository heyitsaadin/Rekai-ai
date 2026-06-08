from flask import Blueprint, request, session, jsonify, render_template
from app.services.jarvis_service import ask_jarvis, ask_jarvis_brain
from app.models import save_chat_session, get_chat_sessions, delete_chat_session, save_shared_chat, get_shared_chat
import json
import uuid
import secrets

chat_bp = Blueprint('chat_routes', __name__)

@chat_bp.route("/ask", methods=["POST"])
def ask():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    prompt = data.get("prompt")
    history = data.get("history", [])
    session_key = data.get("session_key")
    
    if not prompt:
        return jsonify({"error": "Prompt required"}), 400
    
    try:
        response = ask_jarvis(prompt, history)
        
        # Save chat session if session_key is provided
        if session_key:
            messages = history + [{"role": "user", "content": prompt}, {"role": "assistant", "content": response}]
            save_chat_session(session["user"], session_key, messages)
        
        return jsonify({"reply": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/get_sessions")
def get_sessions():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        sessions = get_chat_sessions(session["user"])
        return jsonify(sessions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/delete_session", methods=["POST"])
def delete_session():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    session_key = data.get("session_key")
    
    if not session_key:
        return jsonify({"error": "Session key required"}), 400
    
    try:
        delete_chat_session(session["user"], session_key)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/get_chat_key", methods=["GET"])
def get_chat_key():
    """Generate and return a unique chat session key"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        chat_key = str(uuid.uuid4())
        return jsonify({"chat_key": chat_key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/share_chat", methods=["POST"])
def share_chat():
    """Create a shareable link for a chat session"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    session_key = data.get("session_key")
    title = data.get("title", "Shared Chat")
    
    if not session_key:
        return jsonify({"error": "Session key required"}), 400
    
    try:
        # Get the chat session
        from app.models import get_chat_session
        chat = get_chat_session(session["user"], session_key)
        
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
        
        # Generate share token
        share_token = secrets.token_urlsafe(32)
        
        # Save shared chat
        messages = chat.get("messages", [])
        if isinstance(messages, str):
            messages = json.loads(messages)
        
        save_shared_chat(session["user"], session_key, messages, title, share_token)
        
        return jsonify({
            "ok": True,
            "share_token": share_token,
            "share_url": f"/shared/{share_token}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route("/new_session", methods=["POST"])
def new_session():
    """Create a new chat session"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        session_key = str(uuid.uuid4())
        save_chat_session(session["user"], session_key, [])
        return jsonify({"ok": True, "session_key": session_key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
