from flask import Flask
import os
import secrets
from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import init_db_pool, init_db

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
    app.config["MAX_COOKIE_SIZE"] = 4093
    
    # Initialize extensions
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["500 per day"],
        storage_uri="memory://"
    )
    
    # Initialize Database
    try:
        init_db_pool()
        init_db()
    except Exception as e:
        # Silently fail if DB is not available, app will handle it lazily
        pass
    
    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    from app.routes.account import account_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(admin_bp)
    
    return app
