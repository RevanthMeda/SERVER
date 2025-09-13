import os
import sys
import signal
import logging
import traceback
from flask import Flask, g, request, render_template, jsonify, make_response, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError
from flask_login import current_user, login_required, logout_user
from flask_session import Session
import sys
import os
# Add the current directory to Python path to avoid import conflicts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from config.py file (not config/ directory)
import config as config_module
Config = config_module.Config

# Import from config/ directory
from config.manager import init_config_system
from config.secrets import init_secrets_management
from middleware import init_security_middleware
from session_manager import session_manager

# Initialize CSRF protection globally
csrf = CSRFProtect()

# Import only essential modules - lazy load others
try:
    from models import db, User, init_db
    from auth import init_auth
    from session_manager import session_manager
    # Lazy import blueprints to reduce startup time
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def create_app(config_name='default'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration based on environment
    config_class = config_module.config.get(config_name, config_module.config['default'])
    app.config.from_object(config_class)
    
    # Initialize hierarchical configuration system
    try:
        config_manager = init_config_system(app)
        app.logger.info("Hierarchical configuration system initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize config system: {e}")
        # Continue with basic config if hierarchical config fails
    
    # Initialize secrets management system
    try:
        secrets_manager = init_secrets_management(app)
        app.logger.info("Secrets management system initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize secrets management: {e}")
        # Continue without secrets management if it fails
    
    # Initialize production security middleware
    # Temporarily disabled for remote access testing
    # if config_name == 'production':
    #     init_security_middleware(app)
    
    # Initialize extensions
    csrf.init_app(app)
    
    # Configure server-side sessions
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = 'instance/flask_session'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'sat:'
    app.config['SESSION_COOKIE_NAME'] = 'sat_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = app.config.get('USE_HTTPS', False)
    
    # Initialize Flask-Session for server-side session storage
    Session(app)

    # Initialize database and auth
    try:
        db_initialized = init_db(app)
        if not db_initialized:
            app.logger.warning("Database initialization returned False")

        init_auth(app)
        
        # Initialize migration system
        from database import (
            init_migrations, init_database_performance, 
            init_connection_pooling, init_backup_system
        )
        from database.cli import register_db_commands
        migration_manager = init_migrations(app)
        register_db_commands(app)
        
        # Register task management CLI commands
        try:
            from tasks.cli import tasks
            app.cli.add_command(tasks)
            app.logger.info("Task management CLI commands registered")
        except Exception as e:
            app.logger.error(f"Failed to register task CLI commands: {e}")
        
        # Initialize performance optimizations
        init_connection_pooling(app)
        init_database_performance(app)
        
        # Initialize backup system
        init_backup_system(app)
        
        # Initialize Redis caching system
        try:
            from cache.redis_client import init_cache
            from cache.session_store import RedisSessionInterface, SessionManager
            
            # Initialize cache system
            init_cache(app)
            
            # Replace Flask-Session with Redis session interface if Redis is available
            if hasattr(app, 'cache') and app.cache.redis_client.is_available():
                app.session_interface = RedisSessionInterface(
                    redis_client=app.cache.redis_client,
                    key_prefix='session:',
                    use_signer=True,
                    permanent=True
                )
                app.session_manager = SessionManager(
                    app.cache.redis_client,
                    key_prefix='session:'
                )
                app.logger.info("Redis session storage initialized")
            else:
                app.logger.warning("Redis not available, using filesystem sessions")
            
            # Initialize cache monitoring
            from cache.monitoring import init_cache_monitoring
            init_cache_monitoring(app)
            
            app.logger.info("Cache system initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize cache system: {e}")
            # Continue without caching if it fails
        
        # Initialize query caching system
        try:
            from database.query_cache import init_query_cache
            
            # Initialize query cache with Redis client
            if hasattr(app, 'cache') and app.cache.redis_client.is_available():
                query_cache_manager = init_query_cache(app.cache.redis_client, db)
                app.query_cache = query_cache_manager
                app.logger.info("Query caching system initialized")
            else:
                app.logger.warning("Redis not available, query caching disabled")
        except Exception as e:
            app.logger.error(f"Failed to initialize query caching: {e}")
        
        # Initialize CDN integration
        try:
            from cache.flask_cdn import create_cdn_extension
            
            # Create and initialize CDN extension
            cdn_extension = create_cdn_extension(app)
            app.cdn_extension = cdn_extension
            
            app.logger.info("CDN integration initialized")
        except Exception as e:
            app.logger.error(f"Failed to initialize CDN integration: {e}")
        
        # Initialize background task processing with Celery
        try:
            from tasks.celery_app import init_celery
            
            # Initialize Celery for background tasks
            celery_app = init_celery(app)
            app.celery = celery_app
            
            app.logger.info("Background task processing (Celery) initialized")
        except Exception as e:
            app.logger.error(f"Failed to initialize background task processing: {e}")
            # Continue without background tasks if it fails
        
        app.logger.info("Database, auth, migrations, performance, backup, and cache systems initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize database or auth: {e}")
        traceback.print_exc()
        db_initialized = False

    # Minimal logging for maximum performance - only critical errors
    logging.basicConfig(level=logging.CRITICAL)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Add CSRF token to g for access in templates and manage session
    @app.before_request
    def add_csrf_token():
        # Force session validation on EVERY request
        from flask import abort
        import time
        
        # Add timestamp to prevent caching
        g.request_time = time.time()
        
        # List of public endpoints that don't require authentication
        public_endpoints = ['auth.login', 'auth.register', 'auth.welcome', 'auth.logout', 
                          'auth.forgot_password', 'auth.reset_password', 'static', 
                          'index', 'refresh_csrf', 'health', 'check_auth']
        
        # Check if this is a protected endpoint
        if request.endpoint and request.endpoint not in public_endpoints:
            # This is a protected endpoint - verify session is valid
            if not session_manager.is_session_valid():
                # Session is revoked or expired - force logout
                from flask_login import logout_user
                logout_user()
                session.clear()
                session.permanent = False
                
                # Return 401 for AJAX requests
                if request.is_json or 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': 'Session expired', 'authenticated': False}), 401
                
                # Redirect to welcome for regular requests
                flash('Your session has expired. Please log in again.', 'info')
                return redirect(url_for('auth.welcome'))
            
            # Verify authentication
            if not current_user.is_authenticated:
                # User is not authenticated - clear session and abort
                session.clear()
                session.permanent = False
                
                # Return 401 for AJAX requests
                if request.is_json or 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'error': 'Not authenticated', 'authenticated': False}), 401
                
                # Redirect to welcome for regular requests
                return redirect(url_for('auth.welcome'))
            
            # Additional check: verify session validity with user_id
            if 'user_id' not in session or session.get('user_id') != current_user.id:
                # Session is invalid - force logout
                from flask_login import logout_user
                session_manager.revoke_session()
                logout_user()
                session.clear()
                return redirect(url_for('auth.welcome'))
        
        # For public endpoints, still check if a logged-in user's session is valid
        elif current_user.is_authenticated and not session_manager.is_session_valid():
            # User appears logged in but session is invalid - force logout
            from flask_login import logout_user
            logout_user()
            session.clear()
            session.permanent = False
        
        # Make session non-permanent to avoid persistence
        session.permanent = False
        
        token = generate_csrf()
        g.csrf_token = token
        
        # Close any leftover database connections to prevent hanging
        try:
            db.session.close()
        except:
            pass
    
    # Performance optimization - remove slow session checks

    # Inject CSRF token into all responses and add security headers
    @app.after_request
    def set_csrf_cookie(response):
        import time
        
        if response.mimetype == 'text/html' and hasattr(g, 'csrf_token'):
            response.set_cookie(
                'csrf_token', g.csrf_token,
                httponly=False, samesite='Lax', secure=app.config.get('USE_HTTPS', False)
            )
        
        # EXTREME cache prevention for ALL pages
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0, s-maxage=0, proxy-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Last-Modified'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT')
        response.headers['Vary'] = '*'
        response.headers['X-Cache'] = 'BYPASS'
        
        # Add unique ETag to force revalidation
        response.headers['ETag'] = f'"{time.time()}"'
        
        # Enforce HTTPS security headers
        if app.config.get('USE_HTTPS', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
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

    # API endpoint to check authentication status
    @app.route('/api/check-auth')
    def check_auth():
        """Check if user is authenticated and session is valid"""
        # First check if session is valid
        if not session_manager.is_session_valid():
            return jsonify({'authenticated': False, 'reason': 'Session invalid or expired'}), 401
        
        # Then check Flask-Login authentication
        if current_user.is_authenticated:
            return jsonify({'authenticated': True, 'user': current_user.email}), 200
        else:
            return jsonify({'authenticated': False, 'reason': 'Not logged in'}), 401
    
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
                'Automation Manager': [],
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
                elif user.role in ['Automation Manager']:
                    users_by_role['Automation Manager'].append(user_data)
                elif user.role in ['PM', 'Project Manager', 'Project_Manager']:
                    users_by_role['PM'].append(user_data)

            app.logger.info(f"Found {len(users)} total users")
            app.logger.info(f"Users by role: Automation Manager={len(users_by_role['Automation Manager'])}, PM={len(users_by_role['PM'])}, Admin={len(users_by_role['Admin'])}, Engineer={len(users_by_role['Engineer'])}")

            return jsonify({'success': True, 'users': users_by_role})
        except Exception as e:
            app.logger.error(f"Error in get_users_by_role endpoint: {e}")
            return jsonify({'success': False, 'error': 'Unable to fetch users at this time'}), 500

    # Custom CSRF error handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.error(f"CSRF Error occurred: {str(e)}")
        app.logger.error(f"Request Method: {request.method}")
        app.logger.error(f"Request Form Keys: {list(request.form.keys()) if request.form else []}")
        app.logger.error(f"CSRF Token Submitted: {request.form.get('csrf_token') if request.form else 'No form data'}")

        # For AJAX requests, return JSON error
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'error': 'CSRF token expired',
                'message': 'Please refresh the page and try again',
                'csrf_token': generate_csrf()
            }), 400

        # Ensure we have a CSRF token for the error page
        if not hasattr(g, 'csrf_token'):
            g.csrf_token = generate_csrf()

        return render_template('csrf_error.html', reason=str(e)), 400

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
        from routes.templates import templates_bp
        from routes.compare import compare_bp
        from routes.webhooks import webhooks_bp
        from routes.collaboration import collaboration_bp
        from routes.search import search_bp
        from routes.bulk import bulk_bp
        from routes.audit import audit_bp
        from routes.analytics import analytics_bp
        
        # Import new RESTful API
        from api import api_bp as restful_api_bp
        
        # Import legacy API (will be deprecated)
        from routes.api import api_bp as legacy_api_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        app.register_blueprint(reports_bp, url_prefix='/reports')
        app.register_blueprint(notifications_bp, url_prefix='/notifications')
        app.register_blueprint(io_builder_bp, url_prefix='/io-builder')
        app.register_blueprint(main_bp)
        app.register_blueprint(approval_bp, url_prefix='/approve')
        app.register_blueprint(status_bp, url_prefix='/status')
        app.register_blueprint(templates_bp, url_prefix='/templates')
        app.register_blueprint(compare_bp, url_prefix='/compare')
        app.register_blueprint(webhooks_bp, url_prefix='/webhooks')
        app.register_blueprint(collaboration_bp, url_prefix='/collaboration')
        app.register_blueprint(search_bp, url_prefix='/search')
        app.register_blueprint(bulk_bp, url_prefix='/bulk')
        app.register_blueprint(audit_bp, url_prefix='/audit')
        app.register_blueprint(analytics_bp, url_prefix='/analytics')
        
        # Register new RESTful API at /api/v1
        app.register_blueprint(restful_api_bp)
        
        # Register legacy API at /api/legacy (for backward compatibility)
        app.register_blueprint(legacy_api_bp, url_prefix='/api/legacy')
        
        # Register CDN management blueprint if CDN extension is available
        if hasattr(app, 'cdn_extension') and app.cdn_extension:
            try:
                from cache.flask_cdn import CDNBlueprint
                cdn_blueprint_manager = CDNBlueprint(app.cdn_extension)
                cdn_bp = cdn_blueprint_manager.create_blueprint()
                app.register_blueprint(cdn_bp)
                app.logger.info("CDN management blueprint registered")
            except Exception as e:
                app.logger.error(f"Failed to register CDN blueprint: {e}")

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

    try:
        print("🔧 Initializing SAT Report Generator...")
        
        # Determine environment
        flask_env = os.environ.get('FLASK_ENV', 'development')
        config_name = 'production' if flask_env == 'production' else 'development'
        
        # Create the app with appropriate configuration
        app = create_app(config_name)
        
        # Log security status for production
        if config_name == 'production':
            print("🔒 Production mode: Domain security enabled")
            print(f"🌐 Allowed domain: {app.config.get('ALLOWED_DOMAINS', [])}")
            print(f"🚫 IP access blocking: {app.config.get('BLOCK_IP_ACCESS', False)}")

        # Print startup information
        print(f"🚀 Starting {app.config.get('APP_NAME', 'SAT Report Generator')}...")
        print(f"Debug Mode: {app.config.get('DEBUG', False)}")
        protocol = "http"  # Temporarily using HTTP for testing
        print(f"Running on {protocol}://0.0.0.0:{app.config.get('PORT', 5000)}")
        print("ℹ️  Testing with HTTP - SSL disabled temporarily")

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
            
            return jsonify({
                'status': 'healthy', 
                'message': 'SAT Report Generator is running',
                'database': db_status
            })

        print("🌐 Health check endpoint available at /health")

        # Run the server
        try:
            # Production server configuration
            host = '0.0.0.0'  # Bind to all interfaces
            port = app.config['PORT']
            debug = False  # Force debug off for performance
            
            if config_name == 'production':
                print(f"🚀 Starting production server on port {port}")
                print("⚠️  Production mode: Use a WSGI server like Gunicorn for deployment")
            
            # Enable SSL/HTTPS for secure connections
            if app.config.get('USE_HTTPS', False):
                ssl_cert_path = app.config.get('SSL_CERT_PATH', '')
                
                # Check if it's a .pfx file (contains both cert and key)
                if ssl_cert_path.endswith('.pfx') and os.path.exists(ssl_cert_path):
                    try:
                        import ssl
                        from cryptography.hazmat.primitives import serialization
                        from cryptography.hazmat.primitives.serialization import pkcs12
                        import tempfile
                        
                        # Get password from config
                        cert_password = app.config.get('SSL_CERT_PASSWORD', '').encode() if app.config.get('SSL_CERT_PASSWORD') else None
                        
                        # Load the .pfx file
                        with open(ssl_cert_path, 'rb') as f:
                            pfx_data = f.read()
                        
                        # Parse the PKCS#12 file
                        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                            pfx_data, cert_password
                        )
                        
                        # Create temporary files for cert and key
                        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as cert_file:
                            cert_file.write(certificate.public_bytes(serialization.Encoding.PEM))
                            cert_temp_path = cert_file.name
                        
                        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.key') as key_file:
                            key_file.write(private_key.private_bytes(
                                encoding=serialization.Encoding.PEM,
                                format=serialization.PrivateFormat.PKCS8,
                                encryption_algorithm=serialization.NoEncryption()
                            ))
                            key_temp_path = key_file.name
                        
                        # Create optimized SSL context with extracted cert and key
                        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                        ssl_context.load_cert_chain(cert_temp_path, key_temp_path)
                        
                        # Performance optimizations for SSL (compatible with Flask dev server)
                        ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
                        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2  # Use modern method instead of deprecated options
                        ssl_context.options |= ssl.OP_SINGLE_DH_USE | ssl.OP_SINGLE_ECDH_USE
                        
                        print("🔒 HTTPS enabled with password-protected .pfx SSL certificate")
                        
                        # Clean up temporary files after loading
                        import atexit
                        def cleanup_temp_files():
                            try:
                                os.unlink(cert_temp_path)
                                os.unlink(key_temp_path)
                            except:
                                pass
                        atexit.register(cleanup_temp_files)
                        
                    except Exception as e:
                        print(f"⚠️  Error loading .pfx certificate: {e}")
                        print("💡 Make sure SSL_CERT_PASSWORD is set in your .env file")
                        ssl_context = None
                        print("ℹ️  Falling back to HTTP mode")
                # Check for separate cert and key files  
                elif (ssl_cert_path and os.path.exists(ssl_cert_path) and 
                      app.config.get('SSL_KEY_PATH') and os.path.exists(app.config.get('SSL_KEY_PATH', ''))):
                    ssl_context = (ssl_cert_path, app.config['SSL_KEY_PATH'])
                    print("🔒 HTTPS enabled with separate SSL certificate and key files")
                else:
                    ssl_context = None
                    print("ℹ️  SSL certificate not found - running in HTTP mode")
            else:
                ssl_context = None
                print("ℹ️  HTTPS disabled - running in HTTP mode")

            app.run(
                host=host,
                port=port,
                debug=False,  # Always disable debug for performance
                threaded=True,
                ssl_context=ssl_context,
                use_reloader=False,  # Disable reloader for performance
                processes=1,  # Single process for stability
                request_handler=None,  # Use default handler
                passthrough_errors=False  # Prevent hanging on errors
            )
        except OSError as e:
            if "Address already in use" in str(e):
                print("⚠️  Port 5000 is already in use. Trying to kill existing processes...")
                import os
                os.system('pkill -f "python app.py"')
                import time
                time.sleep(2)
                print("🔄 Retrying on port 5000...")
                app.run(
                    host='0.0.0.0',
                    port=app.config['PORT'],
                    debug=app.config['DEBUG']
                )
            else:
                raise

    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        traceback.print_exc()
        sys.exit(1)