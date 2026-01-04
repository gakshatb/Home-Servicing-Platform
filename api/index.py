"""
Vercel Serverless Function Entry Point
This file wraps the Flask app for Vercel's serverless environment
"""
import sys
import os

# Add parent directory to path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from main
from main import app

# Export the app for Vercel
handler = app

