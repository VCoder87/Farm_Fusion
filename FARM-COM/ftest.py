# flask_db_test.py
# Test your Flask app's database connection

from flask import Flask
from config import Config
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.config.from_object(Config)

def test_flask_mysql_connection():
    """Test Flask MySQL connection using your config"""
    try:
        # Method 1: Using mysql.connector (like your test)
        connection = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            port=app.config.get('MYSQL_PORT', 3306)
        )
        
        if connection.is_connected():
            print("✓ Flask config MySQL connection successful")
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            result = cursor.fetchone()
            print(f"✓ Found {result[0]} users in the database")
            cursor.close()
            connection.close()
            return True
        else:
            print("✗ Flask config MySQL connection failed")
            return False
            
    except Error as e:
        print(f"✗ Flask config MySQL connection error: {e}")
        return False

def test_flask_mysql_extension():
    """Test Flask-MySQL extension"""
    try:
        from flask_mysqldb import MySQL
        
        mysql = MySQL()
        mysql.init_app(app)
        
        # Test connection
        with app.app_context():
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
        print("✓ Flask-MySQL extension working")
        return True
        
    except Exception as e:
        print(f"✗ Flask-MySQL extension error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Flask database connection...")
    print("=" * 50)
    
    print("Config values:")
    print(f"  MYSQL_HOST: {Config.MYSQL_HOST}")
    print(f"  MYSQL_USER: {Config.MYSQL_USER}")
    print(f"  MYSQL_PASSWORD: {'*' * len(Config.MYSQL_PASSWORD)}")
    print(f"  MYSQL_DB: {Config.MYSQL_DB}")
    print(f"  MYSQL_PORT: {Config.MYSQL_PORT}")
    print()
    
    # Test direct connection
    success1 = test_flask_mysql_connection()
    
    # Test Flask-MySQL extension
    success2 = test_flask_mysql_extension()
    
    print("=" * 50)
    
    if success1 and success2:
        print("✓ All tests passed! Your Flask app should work.")
    else:
        print("✗ Some tests failed. Check the errors above.")
        
        if not success2:
            print("\n💡 Try installing Flask-MySQL:")
            print("   pip install flask-mysqldb")