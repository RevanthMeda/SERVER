#!/usr/bin/env python3
"""
Local Flask backend for IIS integration
Runs on localhost:8080 to serve the SAT Report Generator application
IIS handles HTTPS on port 443 and serves this via iframe
"""

import os
import sys

def setup_backend_environment():
    """Set up environment for local backend with IIS frontend"""
    
    env_vars = {
        'FLASK_ENV': 'production',
        'DEBUG': 'False',
        'PORT': '8080',
        'ALLOWED_DOMAINS': '',  # Allow all for IIS proxy
        'SERVER_IP': '127.0.0.1',
        'BLOCK_IP_ACCESS': 'False',  # Disable for IIS proxy
        'SECRET_KEY': 'production-backend-key-change-immediately',
        
        # Email configuration
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'meda.revanth@gmail.com',
        'SMTP_PASSWORD': 'rleg tbhv rwvb kdus',
        'DEFAULT_SENDER': 'meda.revanth@gmail.com',
        'ENABLE_EMAIL_NOTIFICATIONS': 'True',
        
        # Backend security settings
        'SESSION_COOKIE_SECURE': 'False',  # HTTP backend behind IIS HTTPS
        'WTF_CSRF_ENABLED': 'True',
        'PERMANENT_SESSION_LIFETIME': '7200',
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Backend environment configured")

def main():
    """Flask backend for IIS reverse proxy"""
    print("🔧 SAT Report Generator - IIS Backend Service")
    print("=" * 60)
    print("Configuration:")
    print("- IIS Frontend: https://automation-reports.mobilehmi.org:443")
    print("- Flask Backend: http://127.0.0.1:8080")
    print("- IIS handles HTTPS and routes to Flask")
    print("- Corporate hosting setup")
    print("=" * 60)
    
    setup_backend_environment()
    
    # Import after environment is set
    from config import config
    from app import create_app
    
    # Create Flask app
    app = create_app('production')
    
    # Configure backend headers for IIS proxy
    @app.after_request
    def configure_backend_headers(response):
        # Basic security headers (IIS will handle HTTPS headers)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Allow IIS to handle framing (remove frame restrictions)
        response.headers.pop('X-Frame-Options', None)
        
        # Basic CSP (IIS can add additional security)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data:;"
        )
        
        return response
    
    # Add health check endpoint for monitoring
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'SAT Report Generator Backend'}
    
    print(f"🌐 Backend Port: {app.config.get('PORT')}")
    print(f"🔗 IIS Integration: Ready for reverse proxy")
    print(f"🔒 SSL/TLS: Handled by IIS")
    print()
    print("🔧 IIS Integration Status:")
    print("✅ Backend service ready for IIS proxy")
    print("✅ Domain security handled by IIS")
    print("✅ SSL certificates managed by IIS")
    print("✅ Corporate hosting setup")
    print()
    print("📋 Next Steps:")
    print("1. Deploy IIS configuration (web.config)")
    print("2. Configure IIS URL Rewrite to proxy to port 8080")
    print("3. Start this Flask backend service")
    print("4. Access via: https://automation-reports.mobilehmi.org")
    print()
    print("🔄 Starting backend service...")
    print("=" * 60)
    
    # Initialize database
    with app.app_context():
        from models import db
        try:
            db.create_all()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️  Database warning: {e}")
    
    # Start backend HTTP server for IIS proxy
    try:
        print(f"🚀 Starting Flask backend on http://127.0.0.1:8080")
        print("   IIS will proxy HTTPS requests to this backend")
        app.run(
            host='127.0.0.1',  # Localhost only (behind IIS)
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