#!/usr/bin/env python3
"""
Cloud deployment startup script
Ensures admin account is created before starting the application
"""

import os
import sys
import subprocess
from cloud_init_db import init_cloud_database

def ensure_admin_account():
    """Ensure admin account exists in cloud deployment"""
    print("=== Cloud Startup: Admin Account Check ===")
    
    # Check if we're in cloud environment
    if os.environ.get('DATABASE_URL') and 'postgresql' in os.environ.get('DATABASE_URL', ''):
        print("✅ Detected cloud PostgreSQL environment")
        
        # Force admin creation in cloud
        os.environ['AUTO_CREATE_ADMIN'] = 'true'
        
        # Initialize database and create admin
        success = init_cloud_database()
        
        if success:
            print("✅ Cloud admin account setup completed")
            return True
        else:
            print("❌ Cloud admin account setup failed")
            return False
    else:
        print("ℹ️ Local environment detected, skipping cloud admin setup")
        return True

def start_application():
    """Start the Flask application"""
    print("=== Starting ROS2 Wiki Application ===")
    
    # Ensure admin account exists
    if not ensure_admin_account():
        print("❌ Failed to setup admin account, exiting")
        sys.exit(1)
    
    # Import and run the Flask app
    try:
        from app import app
        
        # Get port from environment (for cloud deployment)
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"🚀 Starting application on {host}:{port}")
        
        # Run the application
        app.run(host=host, port=port, debug=False)
        
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_application()
