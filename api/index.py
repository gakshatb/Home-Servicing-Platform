"""
Vercel Serverless Function Entry Point
This file wraps the Flask app for Vercel's serverless environment
"""
import sys
import os
import traceback

# Add parent directory to path so we can import main
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    # Import the Flask app from main
    from main import app, init_db
    
    # Initialize database on first import (safe for serverless)
    # This will only create tables if they don't exist
    try:
        init_db()
    except Exception as e:
        # Log but don't fail - database might already be initialized
        # or connection might be established later
        import logging
        logging.warning(f"Database initialization note: {e}")
    
    # Export the app for Vercel
    handler = app
    
except ImportError as e:
    # Import error - show helpful message
    error_details = traceback.format_exc()
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return f"""
        <html>
        <head><title>Import Error</title></head>
        <body>
            <h1>Application Import Error</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>This usually means:</p>
            <ul>
                <li>Missing dependencies - check requirements.txt</li>
                <li>Python path issues</li>
                <li>Syntax errors in code</li>
            </ul>
            <pre>{error_details}</pre>
        </body>
        </html>
        """, 500
    
    handler = error_app
    
except Exception as e:
    # Other errors during initialization
    error_details = traceback.format_exc()
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return f"""
        <html>
        <head><title>Application Error</title></head>
        <body>
            <h1>Application Initialization Error</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Please check:</p>
            <ul>
                <li>DATABASE_URL environment variable is set in Vercel</li>
                <li>All dependencies are installed (check build logs)</li>
                <li>Check Vercel function logs for details</li>
            </ul>
            <details>
                <summary>Error Details</summary>
                <pre>{error_details}</pre>
            </details>
        </body>
        </html>
        """, 500
    
    handler = error_app

