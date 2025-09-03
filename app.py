import os
import sys
import signal
import logging
import traceback
from flask import Flask, g, request, render_template, jsonify, make_response, redirect, url_for
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError
from flask_login import current_user, login_required
from config import Config, config
from middleware import init_security_middleware

# Initialize CSRF protection globally
csrf = CSRFProtect()

# Import only essential modules - lazy load others
try:
    from models import db, User, init_db
    from auth import init_auth
    # Lazy import blueprints to reduce startup time
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def create_app(config_name='default'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration based on environment
    config_class = config.get(config_name, config['default'])
    app.config.from_object(config_class)
    
    # Initialize production security middleware - DISABLED FOR TESTING
    # if config_name == 'production':
    #     init_security_middleware(app)
    
    # Initialize extensions
    csrf.init_app(app)

    # Initialize database and auth
    try:
        db_initialized = init_db(app)
        if not db_initialized:
            app.logger.warning("Database initialization returned False")

        init_auth(app)
        app.logger.info("Database and auth initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize database or auth: {e}")
        traceback.print_exc()
        db_initialized = False

    # Simplified logging for better performance
    logging.basicConfig(level=logging.WARNING)

    # Add CSRF token to g for access in templates and refresh on each request
    @app.before_request
    def add_csrf_token():
        from flask import session
        
        # Ensure session is properly configured
        session.permanent = True
        
        # Force session to be saved (Flask sometimes doesn't save empty sessions)
        if not session.get('_csrf_initialized'):
            session['_csrf_initialized'] = True
        
        # Generate token and ensure it's stored in session
        token = generate_csrf()
        g.csrf_token = token
        
        # Debug: Log session info
        if app.debug or app.logger.isEnabledFor(logging.INFO):
            app.logger.info(f"Session ID: {session.get('_csrf_token', 'None')[:20] if session.get('_csrf_token') else 'Missing'}...")
            app.logger.info(f"Generated Token: {token[:20]}...")

    # Inject CSRF token into all responses and disable compression for IIS
    @app.after_request
    def set_csrf_cookie(response):
        if response.mimetype == 'text/html' and hasattr(g, 'csrf_token'):
            response.set_cookie(
                'csrf_token', g.csrf_token,
                httponly=False, 
                samesite='Lax',
                max_age=28800  # 8 hours to match session lifetime
            )
        
        # Disable compression for IIS compatibility
        response.headers['Content-Encoding'] = 'identity'
        response.headers['Vary'] = 'Accept-Encoding'
        
        # Add cache control for better CSRF token handling
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response

    # Make CSRF token available in all templates
    @app.context_processor
    def inject_csrf():
        return dict(csrf_token=getattr(g, 'csrf_token', generate_csrf()))

    # CSRF token refresh endpoint
    @app.route('/refresh_csrf')
    def refresh_csrf():
        """Refresh CSRF token via AJAX"""
        return jsonify({'csrf_token': generate_csrf()})

    # API endpoint for getting users by role
    @app.route('/api/get-users-by-role')
    @login_required
    def get_users_by_role():
        """API endpoint to get users by role for dropdowns"""
        try:
            # Only get active users
            users = User.query.filter_by(status='Active').all()
            users_by_role = {
                'Admin': [],
                'Engineer': [],
                'TM': [],
                'PM': []
            }

            for user in users:
                user_data = {
                    'name': user.full_name,
                    'email': user.email
                }

                # Map database roles to frontend role categories
                if user.role == 'Admin':
                    users_by_role['Admin'].append(user_data)
                elif user.role == 'Engineer':
                    users_by_role['Engineer'].append(user_data)
                elif user.role in ['TM', 'Technical Manager', 'Tech Manager', 'Automation Manager']:
                    users_by_role['TM'].append(user_data)
                elif user.role in ['PM', 'Project Manager', 'Project_Manager']:
                    users_by_role['PM'].append(user_data)

            app.logger.info(f"Found {len(users)} total users")
            app.logger.info(f"Users by role: TM={len(users_by_role['TM'])}, PM={len(users_by_role['PM'])}, Admin={len(users_by_role['Admin'])}, Engineer={len(users_by_role['Engineer'])}")

            return jsonify({'success': True, 'users': users_by_role})
        except Exception as e:
            app.logger.error(f"Error in get_users_by_role endpoint: {e}")
            return jsonify({'success': False, 'error': 'Unable to fetch users at this time'}), 500

    # Custom CSRF error handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import session
        
        app.logger.warning(f"🔒 CSRF Error: {str(e)}")
        app.logger.warning(f"🔍 Session Token: {'EXISTS' if session.get('_csrf_token') else 'MISSING'}")
        app.logger.warning(f"🔍 Form Token: {request.form.get('csrf_token', 'MISSING')[:20]}...")
        
        # Force session refresh
        session['_csrf_initialized'] = True
        session.permanent = True
        
        # Generate a completely fresh token
        new_token = generate_csrf()
        g.csrf_token = new_token
        
        app.logger.info(f"✅ Generated new token: {new_token[:20]}...")
        
        # For AJAX requests, return JSON with new token
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'error': 'CSRF token refreshed',
                'message': 'Token automatically refreshed. Please retry.',
                'csrf_token': new_token,
                'auto_retry': True
            }), 200

        # For form submissions, show user-friendly error with auto-refresh
        return render_template('csrf_error.html', reason='Session issue - auto-fixing'), 400

    # Root route - redirect to welcome or dashboard
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.home'))
        return redirect(url_for('auth.welcome'))

    # Legacy redirects
    @app.route('/sat_form')
    def legacy_sat_form():
        return redirect(url_for('reports.new'))

    @app.route('/sat')
    @app.route('/sat/start')
    def legacy_sat():
        return redirect(url_for('reports.new_sat'))

    @app.route('/generate_sat')
    def legacy_generate_sat():
        return redirect(url_for('reports.new_sat'))

    # Lazy import and register blueprints for faster startup
    def register_blueprints():
        from routes.auth import auth_bp
        from routes.dashboard import dashboard_bp
        from routes.reports import reports_bp
        from routes.notifications import notifications_bp
        from routes.io_builder import io_builder_bp
        from routes.main import main_bp
        from routes.approval import approval_bp
        from routes.status import status_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        app.register_blueprint(reports_bp, url_prefix='/reports')
        app.register_blueprint(notifications_bp, url_prefix='/notifications')
        app.register_blueprint(io_builder_bp, url_prefix='/io-builder')
        app.register_blueprint(main_bp)
        app.register_blueprint(approval_bp, url_prefix='/approve')
        app.register_blueprint(status_bp, url_prefix='/status')

    register_blueprints()

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('404.html'), 500

    @app.errorhandler(400)
    def csrf_error(error):
        """Handle CSRF token errors"""
        return render_template('csrf_error.html'), 400

    # 404 Error handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # Minimal response logging for performance
    @app.after_request
    def log_response(response):
        return response

    if not db_initialized:
        app.logger.warning("Database initialization failed - running without database")

    return app

def sigint_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n📡 Shutting down server...")
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handling
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)

    # Setup environment for production on port 443
    env_vars = {
        'FLASK_ENV': 'production',
        'DEBUG': 'False',
        'PORT': '8000',
        'ALLOWED_DOMAINS': 'automation-reports.mobilehmi.org',
        'SERVER_IP': '172.16.18.21',
        'BLOCK_IP_ACCESS': 'False',  # Disable IP blocking for testing
        'SECRET_KEY': 'production-key-change-immediately',
        
        # Email configuration
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'meda.revanth@gmail.com',
        'SMTP_PASSWORD': 'rleg tbhv rwvb kdus',
        'DEFAULT_SENDER': 'meda.revanth@gmail.com',
        'ENABLE_EMAIL_NOTIFICATIONS': 'True',
        
        # Production security settings
        'SESSION_COOKIE_SECURE': 'False',  # HTTP backend, HTTPS handled by IIS
        'WTF_CSRF_ENABLED': 'True',
        'PERMANENT_SESSION_LIFETIME': '7200',
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value

    try:
        print("🔧 SAT Report Generator - Flask Backend for IIS")
        print("=" * 60)
        print("Configuration:")
        print("- IIS Frontend: https://automation-reports.mobilehmi.org:443 (HTTPS)")
        print("- Flask Backend: http://127.0.0.1:8000 (HTTP)")
        print("- IIS routes HTTPS traffic to Flask backend")
        print("- Corporate hosting setup")
        print("=" * 60)
        
        # Create the app with production configuration
        app = create_app('production')
        
        # Configure production security headers
        @app.after_request
        def production_security_headers(response):
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

        print(f"🌐 Port: 5000")
        print(f"🛡️  Domain Security: {app.config.get('BLOCK_IP_ACCESS', False)}")
        print(f"🔒 HTTPS: Handled by IIS")
        print(f"📡 Access URL: https://automation-reports.mobilehmi.org")
        print()

        # Create required directories if they don't exist
        try:
            upload_root = app.config.get('UPLOAD_ROOT', 'static/uploads')
            signatures_folder = app.config.get('SIGNATURES_FOLDER', 'static/signatures')
            submissions_file = app.config.get('SUBMISSIONS_FILE', 'data/submissions.json')

            os.makedirs(upload_root, exist_ok=True)
            os.makedirs(signatures_folder, exist_ok=True)
            os.makedirs(os.path.dirname(submissions_file), exist_ok=True)
            os.makedirs('instance', exist_ok=True)
            os.makedirs('logs', exist_ok=True)
            # Ensure upload directory exists
            upload_dir = app.config.get('UPLOAD_FOLDER')
            if upload_dir and not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)

            # Ensure output directory exists
            output_dir = app.config.get('OUTPUT_DIR')
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            print("✅ Required directories created successfully")
        except Exception as dir_error:
            print(f"⚠️  Warning: Could not create some directories: {dir_error}")

        # Initialize database
        with app.app_context():
            from models import db
            try:
                db.create_all()
                print("✅ Database initialized")
            except Exception as e:
                print(f"⚠️  Database warning: {e}")

        # Test session functionality
        @app.route('/debug/session')
        def debug_session():
            from flask import session
            session['test'] = 'session_working'
            
            return jsonify({
                'session_id': session.get('_csrf_token', 'None')[:20] if session.get('_csrf_token') else 'Missing',
                'session_data': dict(session),
                'csrf_token': generate_csrf(),
                'test_value': session.get('test'),
                'permanent': session.permanent
            })
        
        # Test a simple route to ensure app is working
        @app.route('/health')
        def health_check():
            try:
                # Test database connection
                from models import db
                with db.engine.connect() as connection:
                    connection.execute(db.text('SELECT 1'))
                db_status = 'connected'
            except Exception as e:
                app.logger.error(f"Database health check failed: {e}")
                db_status = 'disconnected'
            
            # Include CSRF token for AJAX requests (for automatic token refresh)
            response_data = {
                'status': 'healthy', 
                'message': 'SAT Report Generator is running',
                'database': db_status
            }
            
            # Add CSRF token if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response_data['csrf_token'] = generate_csrf()
            
            return jsonify(response_data)

        # Check for SSL certificates
        ssl_cert_path = 'ssl/server.crt'
        ssl_key_path = 'ssl/server.key'
        
        # Create SSL directory if it doesn't exist
        os.makedirs('ssl', exist_ok=True)
        
        print()
        print("🚀 Starting SAT Report Generator - Direct Access")
        print("   No IIS needed - Simple Flask deployment!")
        print("   Health check available at: /health")
        print()

        # Simple solution: Use port 8443 (no admin rights needed)
        port = 8443
        print(f"🚀 Starting SAT Report Generator on port {port}...")
        print(f"   Access: http://automation-reports.mobilehmi.org:{port}")
        print(f"   Or: http://127.0.0.1:{port}")
        print("   No IIS needed - Direct Flask access!")
        
        try:
            app.run(
                host='0.0.0.0',
                port=port,
                debug=False,
                threaded=True,
                use_reloader=False
            )
        except Exception as e:
            print(f"❌ Server error: {e}")
            print("   Check if port 8000 is available")

    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        traceback.print_exc()
        sys.exit(1)