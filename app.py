from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Jarvis AI is currently undergoing maintenance. Please check back soon!"

@app.route('/health')
def health():
    return "OK", 200
