#!/usr/bin/env python
"""
Test script to verify that users can login and access the dashboard
after the database migration fix.
"""
import requests
import json
from bs4 import BeautifulSoup

def test_login_and_dashboard():
    """Test that users can login and access dashboard without database errors."""
    
    session = requests.Session()
    base_url = "http://localhost:5000"
    
    print("🔍 Testing login and dashboard access after database migration fix...")
    print("-" * 60)
    
    # Step 1: Get the login page (to get CSRF token)
    print("\n1. Getting login page...")
    try:
        login_page = session.get(f"{base_url}/auth/login")
        if login_page.status_code == 200:
            print("   ✓ Login page accessible")
        else:
            print(f"   ✗ Login page returned status {login_page.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Could not access login page: {e}")
        return False
    
    # Step 2: Extract CSRF token
    try:
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input['value']
            print(f"   ✓ CSRF token obtained")
        else:
            print("   ✗ Could not find CSRF token")
            # Try alternative method
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                csrf_token = csrf_meta['content']
                print(f"   ✓ CSRF token obtained from meta tag")
            else:
                print("   ⚠ Proceeding without CSRF token")
                csrf_token = None
    except Exception as e:
        print(f"   ⚠ Error extracting CSRF: {e}")
        csrf_token = None
    
    # Step 3: Attempt login
    print("\n2. Attempting login as admin...")
    login_data = {
        'email': 'admin@cullyautomation.com',
        'password': 'admin123',
        'remember': 'on'
    }
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': f'{base_url}/auth/login'
    }
    
    try:
        login_response = session.post(
            f"{base_url}/auth/login",
            data=login_data,
            headers=headers,
            allow_redirects=False
        )
        
        if login_response.status_code in [302, 303]:
            print("   ✓ Login successful (redirect received)")
            redirect_location = login_response.headers.get('Location', '')
            print(f"   → Redirect to: {redirect_location}")
        elif login_response.status_code == 200:
            # Check if login was successful by looking for error messages
            if 'Invalid email or password' in login_response.text:
                print("   ✗ Login failed: Invalid credentials")
                return False
            else:
                print("   ✓ Login appears successful")
        else:
            print(f"   ⚠ Unexpected status code: {login_response.status_code}")
    except Exception as e:
        print(f"   ✗ Login request failed: {e}")
        return False
    
    # Step 4: Access dashboard
    print("\n3. Attempting to access dashboard...")
    try:
        dashboard_response = session.get(f"{base_url}/dashboard", allow_redirects=True)
        
        if dashboard_response.status_code == 200:
            # Check for database errors in response
            response_text = dashboard_response.text.lower()
            
            if 'column' in response_text and 'does not exist' in response_text:
                print("   ✗ Database column error still present!")
                # Extract error details
                if 'submitted_at' in response_text:
                    print("     - Missing column: submitted_at")
                if 'approved_at' in response_text:
                    print("     - Missing column: approved_at")
                if 'approved_by' in response_text:
                    print("     - Missing column: approved_by")
                if 'edit_count' in response_text:
                    print("     - Missing column: edit_count")
                return False
            elif 'error' in response_text and 'database' in response_text:
                print("   ✗ Other database error detected")
                return False
            elif 'admin dashboard' in response_text or 'engineer dashboard' in response_text or 'dashboard' in response_text:
                print("   ✓ Dashboard accessed successfully!")
                print("   ✓ No database errors detected")
                return True
            else:
                print("   ⚠ Dashboard page loaded but content unclear")
                # Check if we were redirected to login
                if '/auth/login' in dashboard_response.url:
                    print("   ⚠ Redirected back to login page")
                    return False
                return True
        else:
            print(f"   ✗ Dashboard returned status {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ✗ Dashboard request failed: {e}")
        return False
    
    return True

def main():
    """Run the test."""
    print("\n" + "=" * 60)
    print("DATABASE MIGRATION FIX VERIFICATION TEST")
    print("=" * 60)
    
    success = test_login_and_dashboard()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Users can login and access dashboard!")
        print("✅ Database migration fix is working correctly!")
    else:
        print("❌ TEST FAILED: Issues detected with login/dashboard access")
        print("Please check the application logs for more details.")
    print("=" * 60 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())