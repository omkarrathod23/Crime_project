from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import current_user, login_required, login_user, logout_user
from models.database import User, Department
# from .auth_jwt import decode_token

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login' if role_name == 'citizen' else f'auth.{role_name}_login'))
            
            # Simple role check based on standard methods I likely added to User Document
            # If they don't exist, I'll fix them in models/database.py
            is_authorized = False
            if role_name == 'admin' and hasattr(current_user, 'is_admin') and current_user.is_admin():
                is_authorized = True
            elif role_name == 'police' and hasattr(current_user, 'is_police') and current_user.is_police():
                is_authorized = True
            elif role_name == 'citizen' and hasattr(current_user, 'is_citizen') and current_user.is_citizen():
                is_authorized = True
            
            if not is_authorized:
                flash(f'Access denied. {role_name.capitalize()} privileges required.', 'error')
                return redirect(url_for('main.home'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (hasattr(current_user, 'is_admin') and current_user.is_admin()):
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def police_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (hasattr(current_user, 'is_police') and current_user.is_police()):
            flash('Access denied. Police privileges required.', 'error')
            return redirect(url_for('auth.police_login'))
        return f(*args, **kwargs)
    return decorated_function

def citizen_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (hasattr(current_user, 'is_citizen') and current_user.is_citizen()):
            flash('Access denied. Citizen access required.', 'error')
            return redirect(url_for('auth.citizen_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_user_from_request(req):
    """
    Placeholder for request-based user loading.
    """
    return None

def get_user_by_email(email):
    """Get user by email"""
    return User.objects(email=email).first()
