# test_db_connection.py
# Save this as a separate file and run it to test your database connection

import mysql.connector
from mysql.connector import Error

def test_mysql_connection():
    """Test MySQL connection with your credentials"""
    try:
        # Test connection without database first
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Sreeraj*18*S',
            port=3306
        )
        
        if connection.is_connected():
            print("✓ Successfully connected to MySQL server")
            
            # Check if database exists
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()
            
            print("\nAvailable databases:")
            for db in databases:
                print(f"  - {db[0]}")
            
            # Check if farmcom database exists
            cursor.execute("SHOW DATABASES LIKE 'farmcom';")
            result = cursor.fetchone()
            
            if result:
                print("✓ Database 'farmcom' exists")
                
                # Test connection to farmcom database
                cursor.execute("USE farmcom;")
                cursor.execute("SHOW TABLES;")
                tables = cursor.fetchall()
                
                print("\nTables in farmcom database:")
                if tables:
                    for table in tables:
                        print(f"  - {table[0]}")
                else:
                    print("  No tables found (database is empty)")
                    
            else:
                print("✗ Database 'farmcom' does not exist")
                print("Creating database 'farmcom'...")
                cursor.execute("CREATE DATABASE farmcom;")
                print("✓ Database 'farmcom' created successfully")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        
        # Common error solutions
        if "Access denied" in str(e):
            print("\n💡 Solution: Check your MySQL password")
            print("   Your config shows password: 'Sreeraj*18*S'")
            print("   Make sure this is correct")
            
        elif "Can't connect to MySQL server" in str(e):
            print("\n💡 Solution: MySQL server is not running")
            print("   Run: net start mysql")
            print("   Or: net start mysql80")
            
        elif "Unknown database" in str(e):
            print("\n💡 Solution: Database doesn't exist")
            print("   Create it with: CREATE DATABASE farmcom;")

if __name__ == "__main__":
    print("Testing MySQL connection...")
    print("=" * 50)
    test_mysql_connection()
    print("=" * 50)
    print("\nIf connection successful, your app.py should work!")