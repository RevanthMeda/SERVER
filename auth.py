
from functools import wraps
from flask import redirect, url_for, flash, session, request
from flask_login import LoginManager, current_user
from models import User

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_auth(app):
    """Initialize authentication with app"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

def login_required(f):
    """Require login and active status - enforce session validity"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            session.clear()  # Clear any stale session data
            return redirect(url_for('auth.login'))
        if not current_user.is_active:
            flash('Your account is not active. Contact your administrator.', 'error')
            session.clear()  # Clear session for inactive users
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Require admin role with strict session enforcement"""
    @wraps(f)
    @login_required  # Enforce login_required first
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            flash('Access denied. Admin privileges required.', 'error')
            session.clear()
            return redirect(url_for('auth.welcome'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Require specific roles with strict session enforcement"""
    def decorator(f):
        @wraps(f)
        @login_required  # Enforce login_required first
        def decorated_function(*args, **kwargs):
            # Double-check authentication (belt and suspenders approach)
            if not current_user.is_authenticated:
                session.clear()
                return redirect(url_for('auth.welcome'))
            
            # Check if user is active
            if not current_user.is_active:
                flash('Your account is not active. Contact your administrator.', 'error')
                session.clear()
                return redirect(url_for('auth.welcome'))
            
            # Check role permissions
            if current_user.role not in allowed_roles:
                flash(f'Access denied. Required roles: {", ".join(allowed_roles)}', 'error')
                return redirect(url_for('auth.welcome'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Duplicate role_required function removed
