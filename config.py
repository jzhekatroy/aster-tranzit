import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 3000))
    
    # MySQL
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'asterisk')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'asterisk')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'phone_proxy')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Phone numbers
    FAKE_NUMBER_LENGTH = 15
    FAKE_NUMBER_PREFIX = '7'  # Начало номера

    # File import worker
    INCOMING_DIR = os.getenv('INCOMING_DIR', 'data/incoming')
    ARCHIVE_DIR = os.getenv('ARCHIVE_DIR', 'data/archive')
    SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', 60))  # seconds
    MAX_FILE_MB = int(os.getenv('MAX_FILE_MB', 16))
    MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024

