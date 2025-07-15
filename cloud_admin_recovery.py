#!/usr/bin/env python3
"""
Cloud admin account manual recovery
For when automatic admin creation fails in cloud deployment
"""

import os
import sys
from werkzeug.security import generate_password_hash
from datetime import datetime

def get_cloud_db_connection():
    """Get cloud database connection"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return None, None
    
    if 'postgresql' in database_url:
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            result = urlparse(database_url)
            conn = psycopg2.connect(
                database=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port
            )
            return conn, 'postgresql'
        except ImportError:
            print("❌ psycopg2 not available for PostgreSQL connection")
            return None, None
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return None, None
    else:
        print("❌ Only PostgreSQL is supported for cloud deployment")
        return None, None

def check_existing_admin(cursor):
    """Check if admin account already exists"""
    try:
        cursor.execute("SELECT id, username, email, is_admin FROM users WHERE username = %s OR email = %s", 
                      ('ssss', 'seventee_0611@qq.com'))
        admin = cursor.fetchone()
        
        if admin:
            print(f"✅ Found existing account:")
            print(f"   ID: {admin[0]}")
            print(f"   Username: {admin[1]}")
            print(f"   Email: {admin[2]}")
            print(f"   Is Admin: {admin[3]}")
            return admin
        else:
            print("❌ No existing ssss admin account found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking existing admin: {e}")
        return None

def create_cloud_admin(cursor, conn):
    """Create admin account in cloud database"""
    try:
        admin_username = 'ssss'
        admin_email = 'seventee_0611@qq.com'
        admin_password = 'Ssss123!'
        
        # Generate password hash
        password_hash = generate_password_hash(admin_password)
        
        # Insert admin account
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, is_blacklisted, created_at)
            VALUES (%s, %s, %s, TRUE, FALSE, %s)
        ''', (admin_username, admin_email, password_hash, datetime.now()))
        
        conn.commit()
        
        print("✅ Cloud admin account created successfully!")
        print(f"   Username: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create admin account: {e}")
        conn.rollback()
        return False

def update_existing_admin(cursor, conn, admin_id):
    """Update existing account to have admin privileges"""
    try:
        # Reset password and ensure admin privileges
        admin_password = 'ssss123'
        password_hash = generate_password_hash(admin_password)
        
        cursor.execute('''
            UPDATE users 
            SET password_hash = %s, is_admin = TRUE, is_blacklisted = FALSE
            WHERE id = %s
        ''', (password_hash, admin_id))
        
        conn.commit()
        
        print("✅ Existing account updated with admin privileges!")
        print(f"   Password reset to: {admin_password}")
        print(f"   Admin privileges: Enabled")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update admin account: {e}")
        conn.rollback()
        return False

def verify_admin_account(cursor):
    """Verify admin account is working"""
    try:
        cursor.execute('''
            SELECT username, email, is_admin, is_blacklisted, created_at 
            FROM users WHERE username = %s
        ''', ('ssss',))
        
        admin = cursor.fetchone()
        
        if admin:
            print("\n✅ Admin Account Verification:")
            print(f"   Username: {admin[0]}")
            print(f"   Email: {admin[1]}")
            print(f"   Is Admin: {admin[2]}")
            print(f"   Is Blacklisted: {admin[3]}")
            print(f"   Created: {admin[4]}")
            
            if admin[2]:  # is_admin
                print("✅ Admin privileges confirmed!")
                return True
            else:
                print("❌ Admin privileges not set!")
                return False
        else:
            print("❌ Admin account not found after creation!")
            return False
            
    except Exception as e:
        print(f"❌ Admin verification failed: {e}")
        return False

def test_password_hash(cursor):
    """Test if password hash is working correctly"""
    try:
        from werkzeug.security import check_password_hash
        
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", ('ssss',))
        result = cursor.fetchone()
        
        if result:
            password_hash = result[0]
            test_password = 'ssss123'
            
            if check_password_hash(password_hash, test_password):
                print("✅ Password hash verification successful!")
                return True
            else:
                print("❌ Password hash verification failed!")
                return False
        else:
            print("❌ No password hash found for ssss user!")
            return False
            
    except Exception as e:
        print(f"❌ Password hash test failed: {e}")
        return False

def main():
    """Main recovery function"""
    print("=== Cloud Admin Account Recovery ===")
    print("This script will create/fix your ssss admin account in cloud deployment")
    
    # Get database connection
    conn, db_type = get_cloud_db_connection()
    if not conn:
        print("❌ Cannot connect to cloud database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Check existing admin
        existing_admin = check_existing_admin(cursor)
        
        if existing_admin:
            # Update existing account
            admin_id = existing_admin[0]
            success = update_existing_admin(cursor, conn, admin_id)
        else:
            # Create new admin account
            success = create_cloud_admin(cursor, conn)
        
        if success:
            # Verify the account
            if verify_admin_account(cursor):
                # Test password hash
                if test_password_hash(cursor):
                    print("\n🎉 Cloud admin account recovery completed successfully!")
                    print("\n📋 Login Information:")
                    print("   URL: [Your Cloud App URL]/login")
                    print("   Username: ssss")
                    print("   Password: Ssss123!")
                    print("   Email: seventee_0611@qq.com")
                    return True
        
        print("❌ Admin account recovery failed")
        return False
        
    except Exception as e:
        print(f"❌ Recovery process failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
