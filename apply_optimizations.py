#!/usr/bin/env python
"""
Apply all performance optimizations to the SAT Report Generator
"""
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_database_optimizations():
    """Apply database query optimizations and create indexes"""
    logger.info("Applying database optimizations...")
    
    # Import the Flask app
    from app import create_app
    from models import db
    from sqlalchemy import text
    
    app = create_app('production')
    
    with app.app_context():
        # Create indexes for frequently queried columns
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);",
            "CREATE INDEX IF NOT EXISTS idx_reports_user_email ON reports(user_email);",
            "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_reports_status_created ON reports(status, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_email, read);",
            "CREATE INDEX IF NOT EXISTS idx_sat_reports_report_id ON sat_reports(report_id);",
        ]
        
        for index_sql in indexes:
            try:
                db.session.execute(text(index_sql))
                db.session.commit()
                logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"Index might already exist: {e}")
        
        # Analyze tables for better query planning (SQLite/PostgreSQL)
        try:
            db.session.execute(text("ANALYZE;"))
            db.session.commit()
            logger.info("Database statistics updated")
        except Exception as e:
            logger.warning(f"Could not analyze database: {e}")
        
        # Vacuum database (SQLite only)
        if 'sqlite' in str(db.engine.url):
            try:
                db.session.execute(text("VACUUM;"))
                db.session.commit()
                logger.info("Database vacuumed")
            except Exception as e:
                logger.warning(f"Could not vacuum database: {e}")
    
    logger.info("Database optimizations applied successfully")

def update_app_configuration():
    """Update app.py to use optimized middleware and caching"""
    logger.info("Updating application configuration...")
    
    app_file = Path('app.py')
    if not app_file.exists():
        logger.error("app.py not found")
        return False
    
    content = app_file.read_text()
    
    # Check if optimizations are already applied
    if 'middleware_optimized' in content:
        logger.info("Optimizations already applied to app.py")
        return True
    
    # Add import for optimized middleware
    import_line = "from middleware_optimized import init_optimized_middleware"
    if import_line not in content:
        # Find the imports section and add our import
        import_marker = "from middleware import init_security_middleware"
        content = content.replace(import_marker, f"{import_marker}\n{import_line}")
    
    # Add middleware initialization in create_app function
    init_line = "    # Initialize optimized middleware\n    init_optimized_middleware(app)"
    if init_line not in content:
        # Add after CSRF initialization
        csrf_marker = "    csrf.init_app(app)"
        content = content.replace(csrf_marker, f"{csrf_marker}\n{init_line}")
    
    # Write back the modified content
    app_file.write_text(content)
    logger.info("Application configuration updated")
    return True

def optimize_wsgi_configuration():
    """Optimize Waitress server configuration in wsgi.py"""
    logger.info("Optimizing WSGI configuration...")
    
    wsgi_file = Path('wsgi.py')
    if not wsgi_file.exists():
        logger.error("wsgi.py not found")
        return False
    
    # Create optimized wsgi configuration
    optimized_wsgi = '''"""
Production WSGI server configuration for SAT Report Generator
Optimized for performance
"""
import os
import sys
from waitress import serve
from app import create_app

# Create the Flask application
app = create_app('production')

def run_production_server():
    """Run the application with optimized Waitress production server"""
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    print(f"Starting SAT Report Generator on {host}:{port}")
    print("Using optimized Waitress production server")
    
    # Optimized Waitress configuration for better performance
    serve(
        app,
        host=host,
        port=port,
        threads=6,  # Optimal thread count for most systems
        connection_limit=50,  # Prevent connection overload
        cleanup_interval=10,  # Frequent cleanup of idle connections
        channel_timeout=60,  # Reasonable timeout for idle connections
        ident='SAT-Report-Generator',
        asyncore_use_poll=True,  # Better performance than select()
        backlog=128,  # Handle more pending connections
        recv_bytes=8192,  # Larger receive buffer
        send_bytes=16384,  # Larger send buffer
        outbuf_overflow=104857600,  # 100MB overflow buffer
        max_request_body_size=10485760,  # 10MB max request
    )

if __name__ == '__main__':
    # Run production server
    run_production_server()
'''
    
    wsgi_file.write_text(optimized_wsgi)
    logger.info("WSGI configuration optimized")
    return True

def clean_session_files():
    """Clean up old session files"""
    logger.info("Cleaning up old session files...")
    
    session_dir = Path('instance/flask_session')
    if not session_dir.exists():
        logger.info("No session directory found")
        return
    
    import time
    current_time = time.time()
    
    # Remove session files older than 24 hours
    cleaned = 0
    for session_file in session_dir.glob('*'):
        if session_file.is_file():
            file_age = current_time - session_file.stat().st_mtime
            if file_age > 86400:  # 24 hours
                try:
                    session_file.unlink()
                    cleaned += 1
                except Exception as e:
                    logger.warning(f"Could not remove session file {session_file}: {e}")
    
    logger.info(f"Cleaned {cleaned} old session files")

def update_pooling_configuration():
    """Update database pooling configuration for better performance"""
    logger.info("Updating database pooling configuration...")
    
    pooling_file = Path('database/pooling.py')
    if not pooling_file.exists():
        logger.warning("pooling.py not found")
        return False
    
    content = pooling_file.read_text()
    
    # Update production pool settings for better performance
    old_settings = """                pool_size = min(20, cpu_count + 4)
                max_overflow = min(10, cpu_count)"""
    
    new_settings = """                pool_size = min(5, cpu_count)  # Reduced for better performance
                max_overflow = min(2, cpu_count // 2)  # Minimal overflow"""
    
    if old_settings in content:
        content = content.replace(old_settings, new_settings)
        
        # Also update timeouts
        content = content.replace("'pool_timeout': 30", "'pool_timeout': 10")
        content = content.replace("'pool_recycle': 3600", "'pool_recycle': 900")
        content = content.replace("'statement_timeout=30000'", "'statement_timeout=10000'")
        
        pooling_file.write_text(content)
        logger.info("Database pooling configuration updated")
        return True
    else:
        logger.info("Pooling configuration already optimized or has different settings")
        return False

def main():
    """Apply all optimizations"""
    logger.info("Starting SAT Report Generator optimization process...")
    
    # Apply database optimizations
    try:
        apply_database_optimizations()
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
    
    # Update application configuration
    try:
        update_app_configuration()
    except Exception as e:
        logger.error(f"App configuration update failed: {e}")
    
    # Optimize WSGI configuration
    try:
        optimize_wsgi_configuration()
    except Exception as e:
        logger.error(f"WSGI optimization failed: {e}")
    
    # Update pooling configuration
    try:
        update_pooling_configuration()
    except Exception as e:
        logger.error(f"Pooling configuration update failed: {e}")
    
    # Clean old session files
    try:
        clean_session_files()
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
    
    logger.info("Optimization process completed!")
    logger.info("Please restart the application for changes to take effect.")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)