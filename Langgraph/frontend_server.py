"""
Simple Flask server to serve the frontend static files
Run this instead of main.py to serve the frontend
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static')
CORS(app)

# Serve index.html at root
@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

# Serve all static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    print("🌐 Starting Frontend Server on http://localhost:3000")
    print("Make sure backend (main.py) is running on http://localhost:5000")
    app.run(host='0.0.0.0', port=3000, debug=True)
