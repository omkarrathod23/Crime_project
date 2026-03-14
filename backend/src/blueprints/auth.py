from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models.database import db, User, SystemLog
from src.auth import get_user_by_email
from datetime import datetime

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

@auth_bp.route('/login', methods=['GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@auth_bp.route('/citizen/login', methods=['GET', 'POST'])
def citizen_login():
    logout_user()
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        if user and user.check_password(password) and user.is_citizen():
            login_user(user)
            log_action(user.id, 'login_citizen', 'success')
            return redirect(url_for('main.citizen_dashboard'))
        else:
            flash('Invalid credentials or insufficient privileges!', 'error')
            log_action(user.id if user else None, 'login_citizen', 'failed')
    return render_template('login_citizen.html')

@auth_bp.route('/police/login', methods=['GET', 'POST'])
def police_login():
    logout_user()
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        if user and user.check_password(password) and user.is_police():
            if not user.department:
                flash('Your account is not linked to any department. Contact admin.', 'error')
                return render_template('login_police.html')
            login_user(user)
            log_action(user.id, 'login_police', 'success')
            return redirect(url_for('main.police_dashboard'))
        else:
            flash('Invalid credentials or insufficient privileges!', 'error')
            log_action(user.id if user else None, 'login_police', 'failed')
    return render_template('login_police.html')

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    logout_user()
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        if user and user.check_password(password) and user.is_admin():
            login_user(user)
            log_action(user.id, 'login_admin', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
            log_action(user.id if user else None, 'login_admin', 'failed')
    return render_template('login_admin.html')

@auth_bp.route('/register/citizen', methods=['GET', 'POST'])
def register_citizen():
    if current_user.is_authenticated:
        return redirect(url_for('main.citizen_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        
        if User.objects(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register_citizen.html')
        
        user = User(name=name, email=email, role='citizen', phone=phone)
        user.set_password(password)
        user.save()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.citizen_login'))
    
    return render_template('register_citizen.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_action(current_user.id, 'logout', 'success')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

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
