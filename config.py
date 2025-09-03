import os
import logging
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""

    # Application settings
    APP_NAME = 'SAT Report Generator'
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 14400  # Increased to 4 hours

    # Database - Use absolute path for SQLite
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "instance", "sat_reports.db")}'

    # Lazy directory creation and optimized database settings
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': False,  # Disable for faster startup
        'pool_recycle': 600,
    }

    # File upload settings
    UPLOAD_ROOT = os.path.join(BASE_DIR, 'static', 'uploads')
    SIGNATURES_FOLDER = os.path.join(BASE_DIR, 'static', 'signatures')

    # Output directory for generated reports
    OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')

    # Ensure directories exist
    os.makedirs(UPLOAD_ROOT, exist_ok=True)
    os.makedirs(SIGNATURES_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Email configuration - Dynamic loading (no caching)
    # Static config for server/port/username (these rarely change)
    SMTP_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or 587)
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME') or ''
    DEFAULT_SENDER = os.environ.get('DEFAULT_SENDER') or ''
    
    # Dynamic password loading - always fresh from environment
    @staticmethod
    def get_smtp_credentials():
        """
        Always fetch fresh SMTP credentials from environment variables.
        This prevents password caching issues when credentials change.
        """
        import os
        from dotenv import load_dotenv
        
        # Force refresh environment variables
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        # If not found in environment, try .env file (for local development)
        if not smtp_password:
            load_dotenv(override=True)
            smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        print(f"🔄 Fresh SMTP credentials loaded - Password length: {len(smtp_password)}")
        if smtp_password:
            print(f"🔐 Password: {smtp_password[:4]}...{smtp_password[-4:]}")
        
        return {
            'server': Config.SMTP_SERVER,
            'port': Config.SMTP_PORT,
            'username': Config.SMTP_USERNAME,
            'password': smtp_password,
            'sender': Config.DEFAULT_SENDER
        }

    # PDF export
    ENABLE_PDF_EXPORT = os.environ.get('ENABLE_PDF_EXPORT', 'False').lower() == 'true'

    # Default approvers configuration
    DEFAULT_APPROVERS = [
        {
            "stage": 1,
            "title": "Technical Manager",
            "approver_email": "tm@cullyautomation.com"
        },
        {
            "stage": 2,
            "title": "Project Manager",
            "approver_email": "pm@cullyautomation.com"
        }
    ]

    # Max content length (16MB default)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}

    # Template file for SAT reports
    TEMPLATE_FILE = os.getenv('TEMPLATE_FILE', 'templates/SAT_Template.docx')
    OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'outputs/SAT_Report_Final.docx')

    # Feature Flags
    ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'True').lower() == 'true'

    # Security Settings
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', '3600'))  # 1 hour

    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///sat_reports_dev.db')

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @staticmethod
    def init_app(app):
        Config.init_app(app)

        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}