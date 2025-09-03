#!/usr/bin/env python3
"""
Local SMTP Test for Windows
Tests SMTP connection using your local .env file
"""

import os
import smtplib
import base64
from email.mime.text import MIMEText
from dotenv import load_dotenv

def test_local_smtp():
    """Test SMTP connection with local credentials"""
    
    print("🧪 Local Windows SMTP Test")
    print("=" * 40)
    
    # Force reload .env file
    load_dotenv(override=True)
    
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_username = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    
    print(f"📧 Testing SMTP connection...")
    print(f"Server: {smtp_server}:{smtp_port}")
    print(f"Username: {smtp_username}")
    print(f"Password: {'*' * len(smtp_password) if smtp_password else 'NOT_SET'}")
    print(f"Password length: {len(smtp_password)}")
    print(f"First 4 chars: {smtp_password[:4]}...")
    print(f"Last 4 chars: ...{smtp_password[-4:]}")
    
    # Check if it's the new password
    if smtp_password == 'rleg tbhv rwvb kdus':
        print("✅ Using NEW password!")
    elif smtp_password == 'rqrcbanjruuchjvm':
        print("❌ Still using OLD password - update needed!")
    else:
        print(f"⚠️  Using different password: {smtp_password}")
    
    if not smtp_password:
        print("❌ SMTP_PASSWORD not set in .env file")
        return False
    
    try:
        print("\n🔗 Attempting connection...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print("🔐 Attempting login...")
        server.login(smtp_username, smtp_password)
        
        print("✅ SMTP connection successful!")
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        
        # Decode the error if it contains base64
        if hasattr(e, 'args') and len(e.args) > 0:
            error_str = str(e.args[0])
            if 'AG1lZGEucmV2YW50aEBnbWFpbC5jb20A' in error_str:
                print("🔍 Detected base64 encoded credentials in error")
                # This means it's still using the old cached password
                print("💡 Solution: Run update_local_password.py and restart the application")
        
        return False

if __name__ == "__main__":
    test_local_smtp()