from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models.database import db, User, SystemLog
from src.auth import get_user_by_email
from datetime import datetime
from services.verification_service import validate_aadhaar, validate_pan

auth_bp = Blueprint('auth', __name__)

def log_action(user_id, action, status, meta=None):
    try:
        from flask import request
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        # Use ReferenceField correctly
        user = User.objects(id=user_id).first() if user_id else None
        log = SystemLog(user=user, action=action, status=status, ip_address=ip, meta_info=meta)
        log.save()
    except Exception as e:
        print(f"Logging error: {e}")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.is_police():
            return redirect(url_for('main.police_dashboard'))
        return redirect(url_for('main.citizen_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_by_email(email)
        
        if user and user.check_password(password):
            login_user(user)
            log_action(user.id, f'login_{user.role}', 'success')
            
            # Prepare user data for frontend (JSON response)
            user_data = {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "is_verified": user.is_verified,
                "district": user.district,
                "police_station": user.police_station,
                "dob": user.dob,
                "face_image": user.face_image
            }

            if request.is_json or request.headers.get('Accept') == 'application/json':
                from flask_jwt_extended import create_access_token
                token = create_access_token(identity=str(user.id))
                return {"access_token": token, "user": user_data}, 200
            
            if user.is_admin():
                return redirect(url_for('main.admin_dashboard'))
            elif user.is_police():
                if not user.department:
                    logout_user()
                    flash('Your account is not linked to any department. Contact admin.', 'error')
                    return render_template('login.html')
                return redirect(url_for('main.police_dashboard'))
            else:
                return redirect(url_for('main.citizen_dashboard'))
        else:
            if request.is_json:
                return {"message": "Invalid email or password"}, 401
            flash('Invalid email or password!', 'error')
            log_action(None, 'login_attempt', 'failed', meta={'email': email})

    return render_template('login.html')

@auth_bp.route('/citizen/login', methods=['GET', 'POST'])
def citizen_login():
    return redirect(url_for('auth.login'))

@auth_bp.route('/police/login', methods=['GET', 'POST'])
def police_login():
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return redirect(url_for('auth.login'))

@auth_bp.route('/register/citizen', methods=['POST'])
def register_citizen():
    # Detect if request is JSON (e.g., from mobile app) or Form (e.g., from legacy web)
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')
        district = data.get('district')
        police_station = data.get('policeStation')
        dob = data.get('dob')
        address = data.get('address')
        face_image = data.get('face_image')
        fingerprint_data = data.get('fingerprint_data')
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone', '')
        district = request.form.get('district')
        police_station = request.form.get('policeStation')
        dob = request.form.get('dob')
        address = request.form.get('address')
        face_image = None
        fingerprint_data = None
    
    if not email or not password:
        return {"message": "Email and Password are required"}, 400

    if User.objects(email=email).first():
        if request.is_json:
            return {"message": "Email already registered"}, 400
        flash('Email already registered!', 'error')
        return render_template('register_citizen.html')
    
    user = User(
        name=name, 
        email=email, 
        role='citizen', 
        phone=phone,
        district=district,
        police_station=police_station,
        dob=dob,
        address=address,
        face_image=face_image,
        is_verified=True if face_image else False
    )
    user.set_password(password)
    user.save()
    
    if request.is_json:
        return {"message": "Registration successful", "user_id": str(user.id)}, 201
        
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('auth.citizen_login'))

@auth_bp.route('/logout')
@login_required
def logout():
    log_action(current_user.id, 'logout', 'success')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verify-identity', methods=['POST'])
@login_required
def verify_identity():
    data = request.get_json()
    if not data:
        return {"error": "Invalid data"}, 400
        
    full_name = data.get('full_name')
    aadhaar = data.get('aadhaar')
    pan = data.get('pan')
    
    if not all([full_name, aadhaar, pan]):
        return {"error": "Missing required fields"}, 400
        
    # Validation and Masking
    masked_aadhaar = validate_aadhaar(aadhaar)
    if not masked_aadhaar:
        return {"error": "Invalid Aadhaar format"}, 400
        
    masked_pan = validate_pan(pan)
    if not masked_pan:
        return {"error": "Invalid PAN format"}, 400
        
    # Update User Profile
    user = User.objects(id=current_user.id).first()
    user.full_name = full_name
    user.aadhaar_number = masked_aadhaar
    user.pan_number = masked_pan
    user.is_verified = True  # Simulated instant verification
    user.verification_status = 'Approved'
    user.save()
    
    log_action(user.id, 'identity_verification', 'success')
    return {"message": "Identity verified successfully", "masked_aadhaar": masked_aadhaar}, 200

@auth_bp.route('/admin/citizens/pending')
@login_required
def admin_citizens_pending():
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    pending_citizens = User.objects(role='citizen', verification_status='Pending').all()
    return render_template('admin_dashboard.html', pending_citizens=pending_citizens)

@auth_bp.route('/admin/citizens/<user_id>/approve', methods=['POST'])
@login_required
def admin_citizen_approve(user_id):
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    user = User.objects.get_or_404(id=user_id)
    if user.role != 'citizen':
        flash('Only citizens can be approved/denied.', 'error')
        return redirect(url_for('main.admin_dashboard'))
    user.verification_status = 'Approved'
    user.save()
    log_action(current_user.id, 'citizen_approve', 'success', meta=f'user_id={user.id}')
    flash('Citizen approved successfully.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@auth_bp.route('/admin/citizens/<user_id>/deny', methods=['POST'])
@login_required
def admin_citizen_deny(user_id):
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    user = User.objects.get_or_404(id=user_id)
    if user.role != 'citizen':
        flash('Only citizens can be approved/denied.', 'error')
        return redirect(url_for('main.admin_dashboard'))
    user.verification_status = 'Denied'
    user.save()
    log_action(current_user.id, 'citizen_deny', 'success', meta=f'user_id={user.id}')
    flash('Citizen denied.', 'info')
    return redirect(url_for('main.admin_dashboard'))
