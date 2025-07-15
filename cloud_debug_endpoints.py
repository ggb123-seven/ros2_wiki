#!/usr/bin/env python3
"""
Cloud deployment debug endpoints
Add these routes to app.py for troubleshooting
"""

import os
import json
from flask import Blueprint, jsonify, current_app
from werkzeug.security import check_password_hash

# Create debug blueprint
debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/env')
def debug_environment():
    """Debug environment variables"""
    # Only show non-sensitive environment variables
    safe_env = {
        'ADMIN_USERNAME': os.environ.get('ADMIN_USERNAME', 'Not set'),
        'ADMIN_EMAIL': os.environ.get('ADMIN_EMAIL', 'Not set'),
        'AUTO_CREATE_ADMIN': os.environ.get('AUTO_CREATE_ADMIN', 'Not set'),
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'Not set'),
        'DATABASE_URL_TYPE': 'PostgreSQL' if 'postgresql' in os.environ.get('DATABASE_URL', '') else 'SQLite',
        'MIN_PASSWORD_LENGTH': os.environ.get('MIN_PASSWORD_LENGTH', 'Not set'),
        'REQUIRE_SPECIAL_CHARS': os.environ.get('REQUIRE_SPECIAL_CHARS', 'Not set'),
    }
    
    return jsonify({
        'status': 'success',
        'environment': safe_env
    })

@debug_bp.route('/db')
def debug_database():
    """Debug database connection"""
    try:
        # Get database connection
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test query
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # Get table information
        tables = []
        try:
            if 'postgresql' in os.environ.get('DATABASE_URL', ''):
                cursor.execute('''
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                ''')
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                
            tables = [table[0] for table in cursor.fetchall()]
        except Exception as e:
            tables = [f"Error listing tables: {e}"]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'connection': 'PostgreSQL' if 'postgresql' in os.environ.get('DATABASE_URL', '') else 'SQLite',
            'user_count': user_count,
            'tables': tables
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@debug_bp.route('/admin')
def debug_admin():
    """Debug admin account"""
    try:
        # Get database connection
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for admin accounts
        admin_username = os.environ.get('ADMIN_USERNAME', 'ssss')
        admin_email = os.environ.get('ADMIN_EMAIL', 'seventee_0611@qq.com')
        
        if 'postgresql' in os.environ.get('DATABASE_URL', ''):
            cursor.execute('''
                SELECT id, username, email, is_admin, created_at 
                FROM users 
                WHERE username = %s OR email = %s
            ''', (admin_username, admin_email))
        else:
            cursor.execute('''
                SELECT id, username, email, is_admin, created_at 
                FROM users 
                WHERE username = ? OR email = ?
            ''', (admin_username, admin_email))
            
        admin = cursor.fetchone()
        
        # Check all admins
        if 'postgresql' in os.environ.get('DATABASE_URL', ''):
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
        else:
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
            
        admin_count = cursor.fetchone()[0]
        
        # Test password if admin exists
        password_status = 'Not tested'
        if admin:
            try:
                admin_password = os.environ.get('ADMIN_PASSWORD', 'ssss123')
                if 'postgresql' in os.environ.get('DATABASE_URL', ''):
                    cursor.execute('SELECT password_hash FROM users WHERE username = %s', (admin_username,))
                else:
                    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (admin_username,))
                    
                password_hash = cursor.fetchone()[0]
                password_status = 'Valid' if check_password_hash(password_hash, admin_password) else 'Invalid'
            except Exception as e:
                password_status = f'Error: {e}'
        
        cursor.close()
        conn.close()
        
        if admin:
            return jsonify({
                'status': 'success',
                'admin_found': True,
                'username': admin[1],
                'email': admin[2],
                'is_admin': bool(admin[3]),
                'created_at': str(admin[4]),
                'password_status': password_status,
                'total_admins': admin_count
            })
        else:
            return jsonify({
                'status': 'warning',
                'admin_found': False,
                'expected_username': admin_username,
                'expected_email': admin_email,
                'total_admins': admin_count
            })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add these routes to app.py
def add_debug_endpoints(app):
    """Add debug endpoints to Flask app"""
    app.register_blueprint(debug_bp)
    print("✅ Debug endpoints registered at /debug/*")
    
    return app
