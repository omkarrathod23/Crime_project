from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import current_user, login_required, login_user, logout_user
from models.database import User, Department
from .auth_jwt import decode_token

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for role-specific token in cookies
            cookie_name = f"{role_name}_token"
            token = request.cookies.get(cookie_name)
            
            if not token:
                flash(f'Session expired or invalid. Please log in as {role_name}.', 'error')
                return redirect(url_for(f'{role_name}_login'))
            
            payload = decode_token(token)
            if isinstance(payload, str):  # Error message
                flash(payload, 'error')
                return redirect(url_for(f'{role_name}_login'))
            
            if payload.get('role') != role_name:
                flash(f'Access denied. {role_name.capitalize()} privileges required.', 'error')
                return redirect(url_for('dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('admin_token')
        if not token:
            flash('Please log in as Admin.', 'error')
            return redirect(url_for('admin_login'))
        
        payload = decode_token(token)
        if isinstance(payload, str) or payload.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('admin_login'))
            
        return f(*args, **kwargs)
    return decorated_function

def police_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('police_token')
        if not token:
            flash('Please log in as Police.', 'error')
            return redirect(url_for('police_login'))
        
        payload = decode_token(token)
        if isinstance(payload, str) or payload.get('role') != 'police':
            flash('Access denied. Police privileges required.', 'error')
            return redirect(url_for('police_login'))
            
        return f(*args, **kwargs)
    return decorated_function

def citizen_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('citizen_token')
        if not token:
            flash('Please log in as Citizen.', 'error')
            return redirect(url_for('citizen_login'))
        
        payload = decode_token(token)
        if isinstance(payload, str) or payload.get('role') != 'citizen':
            flash('Access denied. Citizen access required.', 'error')
            return redirect(url_for('citizen_login'))
            
        return f(*args, **kwargs)
    return decorated_function

def load_user_from_request(req):
    """
    Flask-Login request_loader to pick the correct user based on the URL path
    and the corresponding role cookie.
    """
    token = None
    if req.path.startswith('/admin'):
        token = req.cookies.get('admin_token')
    elif req.path.startswith('/police'):
        token = req.cookies.get('police_token')
    elif req.path.startswith('/citizen') or req.path.startswith('/fir') or req.path.startswith('/predict') or req.path.startswith('/eda') or req.path.startswith('/hotspot'):
        token = req.cookies.get('citizen_token')
    
    if token:
        payload = decode_token(token)
        if not isinstance(payload, str):
            user_id = payload.get('user_id')
            return User.query.get(user_id)
    return None

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
