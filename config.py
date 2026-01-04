import os

class app_config:
    # Use environment variables for production (Vercel), fallback to defaults for local dev
    APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "your_secret_key")
    admin_code = os.getenv("ADMIN_CODE", "AS659AW52S9D9W")
    database = os.getenv("DATABASE_NAME", "database.sqlite3")
    
    # Database URL - use DATABASE_URL from environment (for Vercel Postgres) or construct SQLite path
    DATABASE_URL = os.getenv("DATABASE_URL", None)  # Will be set in main.py if None
    
    admin_name = os.getenv("ADMIN_NAME", "Akshat B Gupta")
    admin_uname = os.getenv("ADMIN_UNAME", "gakshatb")
    admin_email = os.getenv("ADMIN_EMAIL", "gakshatb@gmail.com")
    admin_phone = os.getenv("ADMIN_PHONE", "6397906947")
    admin_password = os.getenv("ADMIN_PASSWORD", "gakshatb")
    admin_street = os.getenv("ADMIN_STREET", "201 Asher Villa")
    admin_city = os.getenv("ADMIN_CITY", "Sangli")
    admin_state = os.getenv("ADMIN_STATE", "Maharashtra")
    admin_postal_code = os.getenv("ADMIN_POSTAL_CODE", "416415")
