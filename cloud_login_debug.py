#!/usr/bin/env python3
"""
Cloud deployment login debugging tool
Comprehensive diagnosis for admin account login issues
"""

import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import json
import http.cookiejar
from datetime import datetime

def test_cloud_environment_variables(base_url):
    """Test if environment variables are properly set in cloud"""
    print("=== Testing Cloud Environment Variables ===")
    
    # Test environment endpoint (if available)
    try:
        env_url = f"{base_url}/debug/env"
        response = urllib.request.urlopen(env_url)
        if response.getcode() == 200:
            data = response.read().decode('utf-8')
            print("✅ Environment variables endpoint accessible")
            return True
    except:
        print("⚠️ Environment variables endpoint not available")
    
    return False

def test_database_connection(base_url):
    """Test database connection and admin account existence"""
    print("\n=== Testing Database Connection ===")
    
    try:
        # Test database health endpoint
        db_url = f"{base_url}/debug/db"
        response = urllib.request.urlopen(db_url)
        if response.getcode() == 200:
            print("✅ Database connection successful")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("⚠️ Database debug endpoint not found")
        else:
            print(f"❌ Database connection error: {e.code}")
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    
    return False

def test_admin_account_creation(base_url):
    """Test if admin account was created during deployment"""
    print("\n=== Testing Admin Account Creation ===")
    
    try:
        # Test admin check endpoint
        admin_url = f"{base_url}/debug/admin"
        response = urllib.request.urlopen(admin_url)
        if response.getcode() == 200:
            data = response.read().decode('utf-8')
            print("✅ Admin account check endpoint accessible")
            print(f"Response: {data}")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ Admin check failed: {e.code}")
    except Exception as e:
        print(f"❌ Admin check error: {e}")
    
    return False

def test_login_page_access(base_url):
    """Test login page accessibility"""
    print("\n=== Testing Login Page Access ===")
    
    try:
        login_url = f"{base_url}/login"
        response = urllib.request.urlopen(login_url)
        
        if response.getcode() == 200:
            print("✅ Login page accessible")
            content = response.read().decode('utf-8')
            
            # Check for login form elements
            if 'username' in content.lower() and 'password' in content.lower():
                print("✅ Login form elements found")
                return True
            else:
                print("⚠️ Login form elements missing")
                return False
        else:
            print(f"❌ Login page returned status: {response.getcode()}")
            return False
            
    except Exception as e:
        print(f"❌ Login page access failed: {e}")
        return False

def test_admin_login_attempt(base_url):
    """Test actual admin login attempt"""
    print("\n=== Testing Admin Login Attempt ===")
    
    try:
        # Create cookie jar for session management
        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        
        # First, get the login page to establish session
        login_url = f"{base_url}/login"
        response = opener.open(login_url)
        print(f"✅ Login page loaded (status: {response.getcode()})")
        
        # Prepare login data
        login_data = {
            'username': 'ssss',
            'password': 'ssss123'
        }
        
        # Attempt login
        data = urllib.parse.urlencode(login_data).encode('utf-8')
        request = urllib.request.Request(login_url, data=data, method='POST')
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            response = opener.open(request)
            status = response.getcode()
            
            if status == 200:
                content = response.read().decode('utf-8')
                if 'dashboard' in content.lower() or 'admin' in content.lower():
                    print("✅ Login successful - redirected to dashboard")
                    return True
                elif 'error' in content.lower() or 'invalid' in content.lower():
                    print("❌ Login failed - invalid credentials")
                    return False
                else:
                    print("⚠️ Login response unclear")
                    return False
                    
            elif status == 302:
                # Check redirect location
                redirect_url = response.headers.get('Location', '')
                if 'dashboard' in redirect_url or 'admin' in redirect_url:
                    print("✅ Login successful - redirected to admin area")
                    return True
                elif 'login' in redirect_url:
                    print("❌ Login failed - redirected back to login")
                    return False
                else:
                    print(f"⚠️ Login redirected to: {redirect_url}")
                    return False
            else:
                print(f"❌ Unexpected login response status: {status}")
                return False
                
        except urllib.error.HTTPError as e:
            if e.code == 302:
                print("✅ Login attempt resulted in redirect (likely successful)")
                return True
            else:
                print(f"❌ Login HTTP error: {e.code}")
                return False
                
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

def test_admin_dashboard_access(base_url):
    """Test admin dashboard direct access"""
    print("\n=== Testing Admin Dashboard Access ===")
    
    try:
        dashboard_url = f"{base_url}/admin_dashboard"
        response = urllib.request.urlopen(dashboard_url)
        
        if response.getcode() == 200:
            print("✅ Admin dashboard accessible without login")
            return True
        else:
            print(f"⚠️ Admin dashboard status: {response.getcode()}")
            return False
            
    except urllib.error.HTTPError as e:
        if e.code == 302:
            print("✅ Admin dashboard requires login (expected)")
            return True
        elif e.code == 403:
            print("⚠️ Admin dashboard access forbidden")
            return False
        else:
            print(f"❌ Admin dashboard error: {e.code}")
            return False
    except Exception as e:
        print(f"❌ Admin dashboard test failed: {e}")
        return False

def generate_debug_report(base_url, results):
    """Generate comprehensive debug report"""
    print("\n" + "="*60)
    print("🔍 CLOUD LOGIN DEBUG REPORT")
    print("="*60)
    
    print(f"\n📋 Test Results for: {base_url}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n✅ Successful Tests:")
    for test, result in results.items():
        if result:
            print(f"   ✅ {test}")
    
    print(f"\n❌ Failed Tests:")
    for test, result in results.items():
        if not result:
            print(f"   ❌ {test}")
    
    print(f"\n🔧 Troubleshooting Recommendations:")
    
    if not results.get('login_page', False):
        print("   1. Check if application deployed successfully")
        print("   2. Verify URL is correct")
        print("   3. Check deployment logs for startup errors")
    
    if not results.get('admin_login', False):
        print("   4. Verify admin account was created during deployment")
        print("   5. Check environment variables in cloud platform")
        print("   6. Review database initialization logs")
        print("   7. Test with different credentials")
    
    if not results.get('database', False):
        print("   8. Check PostgreSQL database connection")
        print("   9. Verify DATABASE_URL environment variable")
        print("   10. Review cloud database service status")
    
    print(f"\n📞 Next Steps:")
    print("   1. Check deployment logs on your cloud platform")
    print("   2. Verify environment variables are set correctly")
    print("   3. Test database connectivity")
    print("   4. Consider manual admin account creation")
    
    print("="*60)

def main():
    """Main debugging function"""
    if len(sys.argv) < 2:
        print("Usage: python cloud_login_debug.py <cloud_app_url>")
        print("Example: python cloud_login_debug.py https://ros2-wiki-xxx.onrender.com")
        return
    
    base_url = sys.argv[1].rstrip('/')
    
    print(f"🔍 Starting Cloud Login Debug for: {base_url}")
    print("="*60)
    
    # Run all tests
    results = {}
    results['environment'] = test_cloud_environment_variables(base_url)
    results['database'] = test_database_connection(base_url)
    results['admin_creation'] = test_admin_account_creation(base_url)
    results['login_page'] = test_login_page_access(base_url)
    results['admin_login'] = test_admin_login_attempt(base_url)
    results['dashboard'] = test_admin_dashboard_access(base_url)
    
    # Generate report
    generate_debug_report(base_url, results)

if __name__ == '__main__':
    main()
