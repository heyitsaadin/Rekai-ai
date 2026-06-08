from flask import Flask
import os
import secrets
from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
    
    # Import and register blueprints/routes
    # (To be implemented as routes are moved)
    
    return app
