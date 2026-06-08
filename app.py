import sys
import traceback

def app(environ, start_response):
    try:
        # Move imports inside the handler to catch import-time errors
        from app import create_app
        _app = create_app()
        return _app(environ, start_response)
    except Exception as e:
        status = '500 Internal Server Error'
        error_msg = f"Custom Error Catch:\n{str(e)}\n\n{traceback.format_exc()}"
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(error_msg)))]
        start_response(status, response_headers)
        return [error_msg.encode('utf-8')]
