from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import current_user, login_required
from models.database import User, Department

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('citizen_login'))
            if role_name == 'admin' and not current_user.is_admin():
                flash('Access denied. Admin privileges required.', 'error')
                return redirect(url_for('dashboard'))
            elif role_name == 'police' and not current_user.is_police():
                flash('Access denied. Police privileges required.', 'error')
                return redirect(url_for('dashboard'))
            elif role_name == 'citizen' and not current_user.is_citizen():
                flash('Access denied. Citizen access required.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('citizen_login'))
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def police_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('citizen_login'))
        if not current_user.is_police():
            flash('Access denied. Police privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def citizen_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('citizen_login'))
        if not current_user.is_citizen():
            flash('Access denied. Citizen access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_by_email(email):
    """Get user by email"""
    return User.query.filter_by(email=email).first()

def get_department_for_location(lat, lon):
    """Find the appropriate department for a given location"""
    departments = Department.query.all()
    for dept in departments:
        if verify_location(lat, lon, (dept.min_lat, dept.max_lat, dept.min_lon, dept.max_lon)):
            return dept
    return None

def verify_location(lat, lon, dept_coords):
    """Verify if location falls within department boundaries"""
    min_lat, max_lat, min_lon, max_lon = dept_coords
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
