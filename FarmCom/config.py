import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Flask-MySQLdb Configuration
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'vineesh'
    MYSQL_DB = 'farmcom'
    MYSQL_PORT = 3306
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'uploads/images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size