import logging
from app import create_app

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    app = create_app()
    logger.info("Application created successfully")
except Exception as e:
    logger.error(f"Failed to create application: {e}")
    # Create a minimal app to at least show an error message instead of a crash
    from flask import Flask
    app = Flask(__name__)
    @app.route('/')
    def error():
        return f"App Initialization Error: {e}", 500

# This file is kept as the entry point for Vercel deployment.
# All application logic has been moved to the app/ directory.
