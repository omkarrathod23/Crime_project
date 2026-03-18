from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models.database import FIRReport, Department, User, SystemLog
from src.auth import admin_required, police_required, citizen_required
from mongoengine import Q
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.is_police():
        return redirect(url_for('main.police_dashboard'))
    else:
        return redirect(url_for('main.citizen_dashboard'))

@main_bp.route('/citizen/dashboard')
@login_required
@citizen_required
def citizen_dashboard():
    fir_reports = FIRReport.objects(user=current_user.id).order_by('-timestamp')
    
    if fir_reports:
        latest_fir = fir_reports[0]
        status_map = {
            'pending': (25, 'Submitted'),
            'verified': (40, 'Verified'),
            'assigned': (55, 'Assigned'),
            'in_progress': (75, 'In Progress'),
            'closed': (100, 'Resolved'),
            'rejected': (100, 'Closed (Rejected)')
        }
        fir_status_percent, fir_status_text = status_map.get(latest_fir.status, (25, 'Submitted'))
        notifications = []
        if latest_fir.admin_notes:
            notifications.append(f"Admin: {latest_fir.admin_notes}")
        if latest_fir.police_notes:
            notifications.append(f"Police: {latest_fir.police_notes}")
        complaint_timeline = [
            { 'status': 'Submitted', 'date': latest_fir.timestamp.strftime('%Y-%m-%d %H:%M'), 'note': 'Complaint filed' }
        ]
        if latest_fir.updated_at and latest_fir.updated_at != latest_fir.timestamp:
            complaint_timeline.append({ 'status': fir_status_text, 'date': latest_fir.updated_at.strftime('%Y-%m-%d %H:%M'), 'note': 'Status updated' })
    else:
        fir_status_percent, fir_status_text = 0, 'No Complaints Yet'
        notifications = []
        complaint_timeline = []

    return render_template(
        'citizen_dashboard.html',
        fir_reports=fir_reports,
        fir_status_percent=fir_status_percent,
        fir_status_text=fir_status_text,
        notifications=notifications,
        complaint_timeline=complaint_timeline
    )

@main_bp.route('/api/police/stats')
@login_required
@police_required
def police_stats():
    fir_reports = FIRReport.objects(department=current_user.department).order_by('-timestamp')
    
    # Statistics for this department
    pending_count = len([fir for fir in fir_reports if fir.status == 'pending'])
    in_progress_count = len([fir for fir in fir_reports if fir.status == 'in_progress'])
    closed_count = len([fir for fir in fir_reports if fir.status == 'closed'])
    total_count = len(fir_reports)
    
    # Top 5 new reports for the list
    fir_new_filtered = [f for f in fir_reports if f.status in ['pending', 'assigned']][:5]
    fir_new_data = [{
        "id": str(f.id)[:8],
        "user_name": f.user.name if f.user else "Anonymous",
        "crime_type": f.crime_type,
        "timestamp": f.timestamp.strftime('%H:%M | %d %b')
    } for f in fir_new_filtered]

    return {
        "pending_count": pending_count,
        "in_progress_count": in_progress_count,
        "closed_count": closed_count,
        "total_count": total_count,
        "fir_new": fir_new_data
    }

@main_bp.route('/api/citizen/stats')
@login_required
@citizen_required
def citizen_stats():
    fir_reports = FIRReport.objects(user=current_user.id).order_by('-timestamp')
    if fir_reports:
        latest_fir = fir_reports[0]
        status = latest_fir.status
    else:
        status = 'no_reports'
    
    return {
        "total_reports": len(fir_reports),
        "latest_status": status
    }

@main_bp.route('/police/dashboard')

@login_required
@police_required
def police_dashboard():
    fir_reports = FIRReport.objects(department=current_user.department).order_by('-timestamp')
    department = current_user.department
    
    # Statistics for this department
    pending_count = len([fir for fir in fir_reports if fir.status == 'pending'])
    in_progress_count = len([fir for fir in fir_reports if fir.status == 'in_progress'])
    closed_count = len([fir for fir in fir_reports if fir.status == 'closed'])
    total_count = len(fir_reports)
    
    fir_new = [f for f in fir_reports if f.status in ['pending', 'assigned']]
    fir_active = [f for f in fir_reports if f.status == 'in_progress']
    fir_closed = [f for f in fir_reports if f.status in ['closed', 'rejected']]

    # Filter CrimeData (Criminal Database) by department boundaries
    # If no coordinates, fall back to empty list
    criminals_data = []
    heatmap_coords = []
    if department and department.min_lat is not None:
        crimes = CrimeData.objects(
            latitude__gte=department.min_lat,
            latitude__lte=department.max_lat,
            longitude__gte=department.min_lon,
            longitude__lte=department.max_lon
        )
        
        # Map CrimeData for the template "Target Database"
        # Since CrimeData doesn't have names, we'll use crime type + locality
        for crime in crimes.limit(10):
            criminals_data.append({
                "name": f"Suspect - {crime.crime_description[:15]}",
                "crimes": f"{crime.crime_description} at {crime.locality}",
                "risk_level": "Medium" if crime.victim_age and crime.victim_age > 18 else "High"
            })
            
        # Get all coords for heatmap
        heatmap_coords = [[c.latitude, c.longitude] for c in crimes.only('latitude', 'longitude')]

    return render_template('police_dashboard.html', 
                         fir_reports=fir_reports, 
                         department=department,
                         pending_count=pending_count,
                         in_progress_count=in_progress_count,
                         closed_count=closed_count,
                         total_count=total_count,
                         criminals=criminals_data,
                         heatmap_coords=heatmap_coords,
                         fir_new=fir_new,
                         fir_active=fir_active,
                         fir_closed=fir_closed)

@main_bp.route('/daily-report')
@login_required
@police_required
def daily_report():
    from datetime import datetime, timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get FIR reports for this department filed today
    fir_today = FIRReport.objects(
        department=current_user.department,
        timestamp__gte=today
    ).order_by('-timestamp')
    
    # Calculate stats for the report
    stats = {
        'total': len(fir_today),
        'pending': len([f for f in fir_today if f.status == 'pending']),
        'active': len([f for f in fir_today if f.status == 'in_progress']),
        'closed': len([f for f in fir_today if f.status == 'closed']),
        'date': today.strftime('%d %B %Y')
    }
    
    return render_template('daily_report.html', 
                         firs=fir_today, 
                         stats=stats, 
                         department=current_user.department)

@main_bp.route('/admin/dashboard')

@login_required
@admin_required
def admin_dashboard():
    if current_user.department:
        pending_firs = (
            FIRReport.objects(
                status='pending',
                department__in=[current_user.department, None]
            )
            .order_by('-timestamp')
        )
        departments = [current_user.department]
        users = User.objects(department=current_user.department)
        total_fir_count = FIRReport.objects(
            department__in=[current_user.department, None]
        ).count()
    else:
        pending_firs = FIRReport.objects(status='pending').order_by('-timestamp')
        departments = Department.objects.all()
        users = User.objects.all()
        total_fir_count = FIRReport.objects.count()
    
    pending_count = len(pending_firs)
    department_count = len(departments)
    user_count = len(users)
    
    dept_to_workload = {}
    max_workload = 0
    for dept in departments:
        workload = FIRReport.objects(department=dept).count()
        dept_to_workload[dept.id] = workload
        if workload > max_workload:
            max_workload = workload
    for dept in departments:
        workload = dept_to_workload.get(dept.id, 0)
        percent = int((workload / max_workload) * 100) if max_workload > 0 else 0
        try:
            # MongoEngine objects are not exactly like SQLAlchemy objects, 
            # we need to handle them carefully if using on-the-fly attributes
            dept.workload = workload
            dept.workload_percent = percent
        except Exception:
            pass

    officers = [u for u in users if u.role == 'police']
    for o in officers:
        o.shift = getattr(o, 'shift', 'Day')
        o.case_load = FIRReport.objects(department=o.department, status='in_progress').count()

    system_logs = [
        {
            'time': log.timestamp.strftime('%Y-%m-%d %H:%M'),
            'user': (log.user.name if log.user else 'System'),
            'action': log.action,
            'status': log.status
        }
        for log in SystemLog.objects.order_by('-timestamp').limit(20)
    ]

    return render_template('admin_dashboard.html',
                         pending_firs=pending_firs,
                         departments=departments,
                         users=users,
                         total_fir_count=total_fir_count,
                         pending_count=pending_count,
                         department_count=department_count,
                         user_count=user_count,
                         officers=officers,
                         system_logs=system_logs)
