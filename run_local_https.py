#!/usr/bin/env python3
"""
Local HTTPS Flask application for IIS integration
Runs on localhost:8080 for iframe embedding
"""

import os
import sys
from config import config
from app import create_app

def setup_local_environment():
    """Set up environment for local IIS integration"""
    
    env_vars = {
        'FLASK_ENV': 'production',
        'DEBUG': 'False',
        'PORT': '8080',
        'ALLOWED_DOMAINS': '',  # Allow all domains for iframe embedding
        'SERVER_IP': '127.0.0.1',
        'BLOCK_IP_ACCESS': 'False',  # Disable blocking for local access
        'SECRET_KEY': 'local-secure-key-change-in-production',
        
        # Email configuration
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'meda.revanth@gmail.com',
        'SMTP_PASSWORD': 'rleg tbhv rwvb kdus',
        'DEFAULT_SENDER': 'meda.revanth@gmail.com',
        'ENABLE_EMAIL_NOTIFICATIONS': 'True',
        
        # Security settings for iframe embedding
        'SESSION_COOKIE_SECURE': 'False',  # Allow HTTP for local development
        'WTF_CSRF_ENABLED': 'True',
        'PERMANENT_SESSION_LIFETIME': '7200',
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Local environment configured for IIS integration")

def main():
    """Local Flask application for IIS embedding"""
    print("🏠 SAT Report Generator - Local IIS Integration")
    print("=" * 50)
    print("Configuration:")
    print("- Local server: http://127.0.0.1:8080")
    print("- IIS frontend: https://automation-reports.mobilehmi.org")
    print("- Mode: Iframe embedding enabled")
    print("- Domain blocking: Disabled")
    print("=" * 50)
    
    setup_local_environment()
    
    # Create Flask app
    app = create_app('production')
    
    # Add iframe support headers
    @app.after_request
    def add_iframe_headers(response):
        # Allow iframe embedding
        response.headers.pop('X-Frame-Options', None)
        
        # Set permissive iframe policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data:; "
            "frame-ancestors *;"  # Allow embedding in any frame
        )
        
        # CORS headers for cross-origin requests
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        
        return response
    
    print(f"🌐 Server: {app.config.get('PORT')}")
    print(f"🔓 Security: Local mode (iframe friendly)")
    print(f"📡 Access via IIS: https://automation-reports.mobilehmi.org")
    print()
    print("🔗 Setup Instructions:")
    print("1. Copy index.html to your IIS root directory")
    print("2. Ensure IIS has SSL certificate for automation-reports.mobilehmi.org")
    print("3. Start this Flask app (runs in background)")
    print("4. Access via https://automation-reports.mobilehmi.org")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Initialize database
    with app.app_context():
        from models import db
        try:
            db.create_all()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️  Database warning: {e}")
    
    # Start local server
    try:
        app.run(
            host='127.0.0.1',  # Localhost only
            port=8080,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()