import sys
import os
import traceback

# Add current directory to path to help with imports
sys.path.append(os.path.dirname(__file__))

def handler(environ, start_response):
    try:
        # Import create_app from the 'app' package directory
        from app import create_app
        _app = create_app()
        return _app(environ, start_response)
    except Exception as e:
        status = '500 Internal Server Error'
        error_msg = f"Startup Error:\n{str(e)}\n\n{traceback.format_exc()}"
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(error_msg)))]
        start_response(status, response_headers)
        return [error_msg.encode('utf-8')]

# For Vercel, it often looks for 'app' or 'handler'
app = handler
