from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required
from models.database import FIRReport, Department, User, get_department_for_location, Alert
from src.auth import admin_required, police_required, citizen_required
from extensions import socketio
from src.utils import save_uploaded_file
from datetime import datetime
from services.location_service import assign_nearest_police_station
import logging

logger = logging.getLogger(__name__)

fir_bp = Blueprint('fir', __name__)

@fir_bp.route('/add', methods=['GET', 'POST'])

@login_required
def add_fir():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        crime_type = request.form.get('crime_type', '').strip()
        lat_str = request.form.get('latitude', '0')
        lon_str = request.form.get('longitude', '0')
        priority = request.form.get('priority', 'Medium')
        location_name = request.form.get('location_name', '').strip()
        selected_station = request.form.get('selected_station', '').strip()
        
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            lat, lon = 0.0, 0.0
        
        if not description or not crime_type:
            flash('Please fill all required fields!', 'error')
            return redirect(url_for('main.police_dashboard' if current_user.is_police() else 'main.citizen_dashboard'))

        evidence_file = None
        if 'evidence_file' in request.files:
            file = request.files['evidence_file']
            if file.filename:
                evidence_file = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
        
        # FIR creation logic
        status = 'pending'
        department = None
        assigned_station_name = None
        district = None
        city = None
        
        # Priority 1: User Selection
        if selected_station:
            dept = Department.objects(name=selected_station).first()
            if dept:
                department = dept
                assigned_station_name = dept.name
                district = dept.district
                city = dept.city
                status = 'assigned'
                logger.info(f"Using manually selected station for FIR: {selected_station}")

        # Priority 2: Auto-assignment if not manually selected
        if not department:
            assignment = assign_nearest_police_station(lat, lon, location_name)
            if assignment:
                department = assignment['station_id']
                assigned_station_name = assignment['station_name']
                district = assignment['district']
                city = assignment['city']
                status = 'assigned'
                logger.info(f"Auto-assigned FIR to {assigned_station_name}")
        
        # Override for police filings (should be assigned to their own station if not auto-assigned)
        if current_user.is_police():
            status = 'assigned'
            if not department:
                department = current_user.department
                assigned_station_name = department.name if department else None
                district = department.district if department else None
                city = department.city if department else None

        new_fir = FIRReport(
            user=current_user.id,
            description=description,
            crime_type=crime_type,
            lat=lat,
            lon=lon,
            evidence_file=evidence_file,
            status=status,
            department=department,
            selected_station=selected_station,
            assigned_station=assigned_station_name,
            district=district,
            city=city,
            priority=priority,
            location_name=location_name
        )
        
        new_fir.save()
        
        # Create Alert
        alert_msg = f"New {crime_type} reported at {location_name or 'unknown location'}."
        if priority == 'High':
            alert_msg = f"URGENT: {alert_msg}"
            
        new_alert = Alert(
            message=alert_msg,
            crime_id=new_fir.id,
            priority=priority
        )
        new_alert.save()
        
        # Emit real-time alert via SocketIO to the assigned station room
        alert_payload = {
            'message': alert_msg,
            'priority': priority,
            'crime_id': str(new_fir.id),
            'timestamp': new_alert.timestamp.isoformat(),
            'station': assigned_station_name
        }
        
        socketio.emit('new_alert', alert_payload, namespace='/', room=assigned_station_name)
        # Also emit globally for admin monitoring
        socketio.emit('new_alert', alert_payload, namespace='/')
        
        flash('FIR submitted successfully!', 'success')
        return redirect(url_for('main.police_dashboard' if current_user.is_police() else 'main.citizen_dashboard'))

@fir_bp.route('/add/api', methods=['POST'])
@jwt_required()
def add_fir_api():
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    
    # Handle both JSON and Multipart Form Data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    description = data.get('description')
    crime_type = data.get('crime_type')
    lat = float(data.get('latitude', 0))
    lon = float(data.get('longitude', 0))
    location_name = data.get('location_name', '')
    selected_station = data.get('selected_station', '')
    priority = data.get('priority', 'Medium')

    evidence_file = None
    if 'evidence_file' in request.files:
        file = request.files['evidence_file']
        if file.filename:
            evidence_file = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

    status = 'pending'
    department = None
    assigned_station_name = None
    district = None
    city = None

    if selected_station and selected_station != 'AUTO':
        dept = Department.objects(name=selected_station).first()
        if dept:
            department = dept
            assigned_station_name = dept.name
            district = dept.district
            city = dept.city
            status = 'assigned'

    if not department:
        assignment = assign_nearest_police_station(lat, lon, location_name)
        if assignment:
            department = assignment['station_id']
            assigned_station_name = assignment['station_name']
            district = assignment['district']
            city = assignment['city']
            status = 'assigned'

    new_fir = FIRReport(
        user=user,
        description=description,
        crime_type=crime_type,
        lat=lat,
        lon=lon,
        evidence_file=evidence_file,
        status=status,
        department=department,
        selected_station=selected_station,
        assigned_station=assigned_station_name,
        district=district,
        city=city,
        priority=priority,
        location_name=location_name
    )
    new_fir.save()

    # Emit Socket.IO
    alert_payload = {
        'message': f"New {crime_type} reported from Mobile.",
        'priority': priority,
        'crime_id': str(new_fir.id),
        'station': assigned_station_name
    }
    socketio.emit('new_alert', alert_payload, namespace='/', room=assigned_station_name)
    socketio.emit('new_alert', alert_payload, namespace='/')

    return jsonify({"message": "FIR filed successfully", "fir_id": str(new_fir.id)}), 201
    
    return render_template('add_fir.html')


@fir_bp.route('/admin/fir/<fir_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_fir_location(fir_id):
    fir = FIRReport.objects.get_or_404(id=fir_id)
    if current_user.department and fir.department and fir.department != current_user.department:
        flash('Access denied: FIR belongs to a different department.', 'error')
        return redirect(url_for('main.admin_dashboard'))
    if fir.status != 'pending':
        flash('FIR is not in pending status!', 'error')
        return redirect(url_for('main.admin_dashboard'))
    department = get_department_for_location(fir.lat, fir.lon)
    if department:
        if current_user.department and department != current_user.department:
            flash('Cannot assign FIR to another department.', 'error')
            return redirect(url_for('main.admin_dashboard'))
        fir.department = department
        fir.status = 'assigned'
        fir.updated_at = datetime.utcnow()
        fir.admin_notes = f"Location verified and assigned to {department.name}"
        flash(f'FIR assigned to {department.name}', 'success')
    else:
        fir.status = 'verified'
        fir.updated_at = datetime.utcnow()
        fir.admin_notes = "Location verified but no department found in area"
        flash('Location verified but no department found in area', 'warning')
    fir.save()
    return redirect(url_for('main.admin_dashboard'))

@fir_bp.route('/admin/fir/<fir_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_fir_department(fir_id):
    fir = FIRReport.objects.get_or_404(id=fir_id)
    department_id = request.form.get('department_id')
    if current_user.department and fir.department and fir.department != current_user.department:
        flash('Access denied: FIR belongs to a different department.', 'error')
        return redirect(url_for('main.admin_dashboard'))
    if department_id:
        department = Department.objects.get(id=department_id)
        if current_user.department and department and department != current_user.department:
            flash('You can only assign FIRs within your department.', 'error')
            return redirect(url_for('main.admin_dashboard'))
        fir.department = department
        fir.status = 'assigned'
        fir.updated_at = datetime.utcnow()
        fir.admin_notes = f"Manually assigned to {department.name}"
        flash(f'FIR assigned to {department.name}', 'success')
    else:
        fir.department = None
        fir.status = 'verified'
        fir.admin_notes = "Department assignment removed"
        flash('Department assignment removed', 'info')
    fir.save()
    return redirect(url_for('main.admin_dashboard'))

@fir_bp.route('/admin/fir/<fir_id>/verify-assign', methods=['POST'])
@login_required
@admin_required
def verify_and_assign_fir(fir_id):
    fir = FIRReport.objects.get_or_404(id=fir_id)
    department_id = request.form.get('department_id')
    admin_notes = request.form.get('admin_notes', '')

    if current_user.department and fir.department and fir.department != current_user.department:
        flash('Access denied: FIR belongs to a different department.', 'error')
        return redirect(url_for('main.admin_dashboard'))

    if department_id:
        department = Department.objects.get(id=department_id)
        if department:
            if current_user.department and department != current_user.department:
                flash('You can only assign FIRs within your department.', 'error')
                return redirect(url_for('main.admin_dashboard'))
            fir.department = department
            fir.status = 'assigned'
            fir.updated_at = datetime.utcnow()
            fir.admin_notes = admin_notes or f"Verified and assigned to {department.name}"
            flash(f'FIR verified and assigned to {department.name}', 'success')
        else:
            flash('Selected department not found.', 'error')
    else:
        fir.status = 'verified'
        fir.updated_at = datetime.utcnow()
        fir.admin_notes = admin_notes or 'Verified by admin'
        flash('FIR verified. No department selected.', 'info')

    fir.save()
    return redirect(url_for('main.admin_dashboard'))

@fir_bp.route('/admin/fir/<fir_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_fir(fir_id):
    fir = FIRReport.objects.get_or_404(id=fir_id)
    reason = request.form.get('rejection_reason', '').strip()

    if current_user.department and fir.department and fir.department != current_user.department:
        flash('Access denied: FIR belongs to a different department.', 'error')
        return redirect(url_for('main.admin_dashboard'))

    fir.status = 'rejected'
    fir.updated_at = datetime.utcnow()
    fir.admin_notes = f"Rejected: {reason}" if reason else 'Rejected by admin'
    fir.save()

    flash('FIR rejected successfully.', 'info')
    return redirect(url_for('main.admin_dashboard'))

@fir_bp.route('/police/fir/<fir_id>/update', methods=['POST'])
@login_required
@police_required
def update_fir_status(fir_id):
    fir = FIRReport.objects.get_or_404(id=fir_id)
    
    if fir.department != current_user.department:
        flash('Access denied!', 'error')
        return redirect(url_for('main.police_dashboard'))
    
    status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    if status in ['in_progress', 'closed']:
        fir.status = status
        fir.police_notes = notes
        fir.save()
        flash(f'FIR status updated to {status}', 'success')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('main.police_dashboard'))

@fir_bp.route('/fir/records')
@login_required
def fir_records():
    if current_user.is_admin():
        firs = FIRReport.objects.order_by('-timestamp')
    elif current_user.is_police():
        firs = FIRReport.objects(department=current_user.department).order_by('-timestamp')
    else:
        firs = FIRReport.objects(user=current_user.id).order_by('-timestamp')
    
    fir_list = []
    for fir in firs:
        fir_dict = {
            'ID': str(fir.id),
            'Description': fir.description,
            'Crime Type': fir.crime_type,
            'Status': fir.status,
            'Location': f"{fir.lat:.4f}, {fir.lon:.4f}",
            'Submitted': fir.timestamp.strftime('%Y-%m-%d %H:%M'),
            'User': fir.user.name,
            'Department': fir.department.name if fir.department else 'Unassigned',
            'Notes': fir.admin_notes or fir.police_notes or ''
        }
        fir_list.append(fir_dict)
    
    headers = ['ID', 'Description', 'Crime Type', 'Status', 'Location', 'Submitted', 'User', 'Department', 'Notes']
    return render_template('fir_records.html', firs=fir_list, headers=headers)
