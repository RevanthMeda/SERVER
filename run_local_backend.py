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
        'PORT': '443',
        'ALLOWED_DOMAINS': 'automation-reports.mobilehmi.org',
        'SERVER_IP': '172.16.18.21',
        'BLOCK_IP_ACCESS': 'True',  # Enable domain security
        'SECRET_KEY': 'production-backend-key-change-immediately',
        
        # Email configuration
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'meda.revanth@gmail.com',
        'SMTP_PASSWORD': 'rleg tbhv rwvb kdus',
        'DEFAULT_SENDER': 'meda.revanth@gmail.com',
        'ENABLE_EMAIL_NOTIFICATIONS': 'True',
        
        # HTTPS security settings
        'SESSION_COOKIE_SECURE': 'True',  # HTTPS required
        'WTF_CSRF_ENABLED': 'True',
        'PERMANENT_SESSION_LIFETIME': '7200',
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Backend environment configured")

def main():
    """Direct HTTPS Flask application on port 443"""
    print("🔒 SAT Report Generator - Direct HTTPS Server")
    print("=" * 60)
    print("Configuration:")
    print("- HTTPS Server: https://automation-reports.mobilehmi.org:443")
    print("- Direct access (no IIS needed)")
    print("- SSL/TLS encryption: Required")
    print("- Domain security: ENABLED")
    print("=" * 60)
    
    setup_backend_environment()
    
    # Import after environment is set
    from config import config
    from app import create_app
    
    # Create Flask app
    app = create_app('production')
    
    # Configure production security headers
    @app.after_request
    def configure_security_headers(response):
        # Production security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data:;"
        )
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    # Add health check endpoint for monitoring
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'SAT Report Generator Backend'}
    
    print(f"🌐 HTTPS Port: {app.config.get('PORT')}")
    print(f"🛡️  Domain Security: {app.config.get('BLOCK_IP_ACCESS')}")
    print(f"🔒 SSL/TLS: Required")
    print()
    print("🔒 Security Status:")
    print("✅ Domain-only access: automation-reports.mobilehmi.org")
    print("❌ Direct IP access: 172.16.18.21 (blocked)")
    print("✅ SSL/TLS encryption: Required")
    print("✅ Production security headers: Enabled")
    print()
    print("📋 SSL Certificate Requirements:")
    print("- Valid SSL certificate for automation-reports.mobilehmi.org")
    print("- Certificate files: ssl/server.crt and ssl/server.key")
    print("- Or use self-signed certificate for testing")
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
    
    # Check for SSL certificates
    ssl_cert_path = 'ssl/server.crt'
    ssl_key_path = 'ssl/server.key'
    
    # Create SSL directory if it doesn't exist
    os.makedirs('ssl', exist_ok=True)
    
    # Start HTTPS server
    try:
        if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
            print("✅ SSL certificates found - using production certificates")
            ssl_context = (ssl_cert_path, ssl_key_path)
        else:
            print("⚠️  SSL certificates not found - using self-signed certificate")
            print("   For production, place your SSL certificate files in:")
            print("   - ssl/server.crt (certificate)")
            print("   - ssl/server.key (private key)")
            ssl_context = 'adhoc'  # Self-signed for development
        
        print(f"🚀 Starting HTTPS server on port 443...")
        app.run(
            host='0.0.0.0',  # Bind to all interfaces
            port=443,
            debug=False,
            threaded=True,
            use_reloader=False,
            ssl_context=ssl_context
        )
    except PermissionError:
        print("❌ Permission denied for port 443!")
        print("   Port 443 requires administrator privileges.")
        print("   Solution: Run Command Prompt as Administrator")
        sys.exit(1)
    except Exception as e:
        print(f"❌ HTTPS server error: {e}")
        print("   Check SSL certificate configuration")
        sys.exit(1)

if __name__ == '__main__':
    main()