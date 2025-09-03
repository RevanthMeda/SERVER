#!/usr/bin/env python3
"""
Local Flask backend for IIS integration
Runs on localhost:8080 to serve the SAT Report Generator application
IIS handles HTTPS on port 443 and serves this via iframe
"""

import os
import sys
from config import config
from app import create_app

def setup_backend_environment():
    """Set up environment for local backend with IIS frontend"""
    
    env_vars = {
        'FLASK_ENV': 'production',
        'DEBUG': 'False',
        'PORT': '8080',
        'ALLOWED_DOMAINS': '',  # Allow all for iframe embedding
        'SERVER_IP': '127.0.0.1',
        'BLOCK_IP_ACCESS': 'False',  # Disable for localhost access
        'SECRET_KEY': 'production-backend-key-change-immediately',
        
        # Email configuration
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'meda.revanth@gmail.com',
        'SMTP_PASSWORD': 'rleg tbhv rwvb kdus',
        'DEFAULT_SENDER': 'meda.revanth@gmail.com',
        'ENABLE_EMAIL_NOTIFICATIONS': 'True',
        
        # Backend security settings
        'SESSION_COOKIE_SECURE': 'False',  # HTTP for local backend
        'WTF_CSRF_ENABLED': 'True',
        'PERMANENT_SESSION_LIFETIME': '7200',
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Backend environment configured")

def main():
    """Flask backend for IIS integration"""
    print("🔧 SAT Report Generator - Backend Service")
    print("=" * 55)
    print("Configuration:")
    print("- Backend: http://127.0.0.1:8080 (Flask Application)")
    print("- Frontend: https://automation-reports.mobilehmi.org:443 (IIS)")
    print("- Mode: Backend service for IIS iframe integration")
    print("- Security: Optimized for localhost iframe embedding")
    print("=" * 55)
    
    setup_backend_environment()
    
    # Create Flask app
    app = create_app('production')
    
    # Configure for iframe embedding
    @app.after_request
    def configure_iframe_headers(response):
        # Remove frame blocking for iframe support
        response.headers.pop('X-Frame-Options', None)
        
        # Set permissive CSP for iframe embedding
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data:; "
            "frame-ancestors *;"  # Allow any parent frame
        )
        
        # CORS headers for IIS integration
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        
        return response
    
    # Add health check endpoint for monitoring
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'SAT Report Generator Backend'}
    
    print(f"🌐 Backend Port: {app.config.get('PORT')}")
    print(f"🔓 Security Mode: Localhost iframe embedding")
    print(f"📡 Access via: https://automation-reports.mobilehmi.org")
    print()
    print("🔗 IIS Integration Status:")
    print("✅ Backend service ready for iframe embedding")
    print("✅ CORS headers configured")
    print("✅ Frame ancestors allowed")
    print("✅ Health check endpoint: /health")
    print()
    print("📋 Next Steps:")
    print("1. Copy files from 'iis_files/' to C:\\inetpub\\wwwroot\\REPORT_GENERATOR\\")
    print("2. Ensure IIS site is running on port 443")
    print("3. Access: https://automation-reports.mobilehmi.org")
    print()
    print("🔄 Starting backend service...")
    print("=" * 55)
    
    # Initialize database
    with app.app_context():
        from models import db
        try:
            db.create_all()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️  Database warning: {e}")
    
    # Start backend server
    try:
        print(f"🚀 Backend service running on http://127.0.0.1:8080")
        app.run(
            host='127.0.0.1',  # Localhost only
            port=8080,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Backend service error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()