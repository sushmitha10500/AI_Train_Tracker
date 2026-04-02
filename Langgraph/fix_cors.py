"""
Quick script to add CORS to main.py
"""

# Read the corrupted file
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The file is corrupted, let's restore the header properly
fixed_content = '''"""
🚆 SIMPLIFIED Indian Railway Route Planner
- Shows only available trains with best routes
- Clear connection details with waiting times
- AI-recommended best option
- User-friendly readable format
- OpenAI version (same logic as working Gemini code)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any, TypedDict
import re
import json
from openai import OpenAI
from langgraph.graph import StateGraph, END

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OPENAI_API_KEY = "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"
'''

# Find where the rest of the content starts (after the corrupted header)
# Look for "client = OpenAI"
import_idx = content.find('client = OpenAI(api_key=OPENAI_API_KEY)')
if import_idx != -1:
    # Get everything after this line
    rest_of_content = content[import_idx:]
    fixed_content += rest_of_content
else:
    print("ERROR: Could not find the continuation point in the file")
    print("File appears to be too corrupted. Manual intervention needed.")
    exit(1)

# Write the fixed content
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("✅ Fixed main.py with CORS support!")
