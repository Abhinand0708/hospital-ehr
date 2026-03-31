import mysql.connector
from mysql.connector import Error

print("=" * 50)
print("MySQL Connection Test")
print("=" * 50)

# Test different password scenarios
passwords_to_try = ['', 'root', 'password', '123456', 'admin']

for pwd in passwords_to_try:
    try:
        print(f"\nTrying password: '{pwd}' (empty string if blank)")
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=pwd
        )
        
        if connection.is_connected():
            print(f"✓ SUCCESS! Password is: '{pwd}'")
            print(f"✓ MySQL Server version: {connection.get_server_info()}")
            
            # Show databases
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()
            print(f"✓ Available databases:")
            for db in databases:
                print(f"  - {db[0]}")
            
            cursor.close()
            connection.close()
            
            print("\n" + "=" * 50)
            print(f"UPDATE db_config.py with password: '{pwd}'")
            print("=" * 50)
            break
            
    except Error as e:
        print(f"✗ Failed with password '{pwd}': {e}")

print("\nTest complete!")
