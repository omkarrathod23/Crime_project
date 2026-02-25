import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import random
import joblib
from models.model import predict_crime_type
from src.eda import load_data
from sklearn.cluster import KMeans
import folium
from models.database import db, User, Department, FIRReport, CrimeData, init_db, create_otp_for_user, verify_otp
from src.auth import admin_required, police_required, citizen_required, get_user_by_email, get_department_for_location, load_user_from_request
from src.auth_jwt import create_token
from flask import make_response

app = Flask(__name__, template_folder='src/templates')
app.secret_key = 'your_secret_key'  # Change this in production

# Database configuration
# Use a fresh DB filename to avoid old schema conflicts
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crime_management_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OTP SMS configuration (demo: fixed number override)
OTP_TEST_PHONE = os.environ.get('OTP_TEST_PHONE', '7249398891')

def send_sms_otp(phone_number: str, otp_code: str) -> None:
    """Send OTP via SMS. Uses Twilio if configured; never displays OTP in UI."""
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_FROM_NUMBER')
    # Always send to the configured test phone, per requirement
    target = OTP_TEST_PHONE
    try:
        if account_sid and auth_token and from_number:
            # Lazy import; avoid hard dependency when not configured
            from twilio.rest import Client  # type: ignore
            client = Client(account_sid, auth_token)
            client.messages.create(to=target, from_=from_number, body=f"Your OTP is: {otp_code}")
        else:
            # No SMS provider configured; do not expose OTP in UI
            # Optionally log to server for testing only (remove in production)
            print(f"[OTP DEMO - no SMS provider] OTP generated and would be sent to {target}.")
    except Exception as e:
        print(f"Failed to send SMS OTP: {e}")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# We use request_loader for isolated role cookies
login_manager.request_loader(load_user_from_request)
login_manager.login_view = 'citizen_login'

# Initialize database
init_db(app)

# @login_manager.user_loader is replaced by request_loader for token support
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

DATA_PATH = os.path.join('data', 'rasayani_crime_dataset')
STATIC_IMG_PATH = os.path.join('static', 'images')
os.makedirs(STATIC_IMG_PATH, exist_ok=True)

# Utility to load data
def load_crime_data(folder_path=None):
    import glob, re, os
    if folder_path is None:
        folder_path = os.path.join('data', 'rasayani_crime_dataset')
    search_path = os.path.join(folder_path, 'rasayani_crime_dataset_corrected.csv')
    print('Looking for file in:', search_path)
    all_files = glob.glob(search_path)
    print('Found files:', all_files)
    df_list = [pd.read_csv(f) for f in all_files]
    if not df_list:
        print('No files found to load!')
    df = pd.concat(df_list, ignore_index=True)
    df.columns = [re.sub(r'\s+', '_', c.strip().lower()) for c in df.columns]
    return df

def get_top_crime_types(df, n=5):
    return df['crime_description'].value_counts().head(n)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid filename conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

# Load model and data once
model = joblib.load('models/crime_type_rf.joblib')
data = load_crime_data()

@app.route('/')
def home():
    # Redirect to citizen login as the new primary entry point
    return redirect(url_for('citizen_login'))

@app.route('/citizen')
def citizen_portal():
    return redirect(url_for('citizen_login'))

@app.route('/police')
def police_portal():
    return redirect(url_for('police_login'))

@app.route('/admin')
def admin_portal():
    return redirect(url_for('admin_login'))

# Authentication routes
@app.route('/citizen/login', methods=['GET', 'POST'])
def citizen_login():
    if current_user.is_authenticated:
        if current_user.is_citizen():
            return redirect(url_for('citizen_dashboard'))
        flash(f'You are currently logged in with a {current_user.role} account. Please logout to switch to Citizen.', 'info')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        
        if user and user.check_password(password) and user.is_citizen():
            # Create JWT token for citizen
            token = create_token(user.id, 'citizen')
            
            # Setup response with cookie
            response = make_response(redirect(url_for('citizen_dashboard')))
            response.set_cookie('citizen_token', token, httponly=True, max_age=86400)
            
            flash('Logged in as Citizen successfully!', 'success')
            return response
        else:
            flash('Invalid credentials or insufficient privileges!', 'error')
    
    return render_template('login_citizen.html')

@app.route('/citizen/otp', methods=['GET', 'POST'])
def citizen_otp_verification():
    if 'pending_user_id' not in session or not session.get('otp_sent'):
        return redirect(url_for('citizen_login'))
    if request.method == 'POST':
        otp = request.form['otp']
        user_id = session['pending_user_id']
        if verify_otp(user_id, otp):
            user = User.query.get(user_id)
            login_user(user)
            session.pop('pending_user_id', None)
            session.pop('otp_sent', None)
            flash('OTP verified successfully!', 'success')
            return redirect(url_for('citizen_dashboard'))
        else:
            flash('Invalid or expired OTP!', 'error')
    return render_template('citizen_otp.html')

@app.route('/police/login', methods=['GET', 'POST'])
def police_login():
    if current_user.is_authenticated:
        # If already logged in as police, go to dashboard
        if current_user.is_police():
            return redirect(url_for('police_dashboard'))
        flash(f'You are currently logged in with a {current_user.role} account. Please logout to switch to Police.', 'info')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        
        if user and user.check_password(password) and user.is_police():
            # Create JWT token for police
            token = create_token(user.id, 'police')
            
            # Setup response with cookie
            response = make_response(redirect(url_for('police_dashboard')))
            response.set_cookie('police_token', token, httponly=True, max_age=86400)
            
            flash('Logged in as Police successfully!', 'success')
            return response
        else:
            flash('Invalid credentials or insufficient privileges!', 'error')
    
    return render_template('login_police.html')

@app.route('/police/otp', methods=['GET', 'POST'])
def police_otp_verification():
    if 'pending_user_id' not in session or not session.get('otp_sent'):
        return redirect(url_for('police_login'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        user_id = session['pending_user_id']
        
        if verify_otp(user_id, otp):
            user = User.query.get(user_id)
            login_user(user)
            session.pop('pending_user_id', None)
            session.pop('otp_sent', None)
            flash('OTP verified successfully!', 'success')
            return redirect(url_for('police_dashboard'))
        else:
            flash('Invalid or expired OTP!', 'error')
    
    return render_template('police_otp.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        flash(f'You are currently logged in with a {current_user.role} account. Please logout to switch to Admin.', 'info')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)
        
        if user and user.check_password(password) and user.is_admin():
            # Create JWT token for admin
            token = create_token(user.id, 'admin')
            
            # Setup response with cookie
            response = make_response(redirect(url_for('admin_dashboard')))
            response.set_cookie('admin_token', token, httponly=True, max_age=86400)
            
            flash('Logged in as Admin successfully!', 'success')
            return response
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login_admin.html')

@app.route('/admin/otp', methods=['GET', 'POST'])
def admin_otp_verification():
    if 'pending_user_id' not in session or not session.get('otp_sent'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        user_id = session['pending_user_id']
        
        if verify_otp(user_id, otp):
            user = User.query.get(user_id)
            login_user(user)
            session.pop('pending_user_id', None)
            session.pop('otp_sent', None)
            flash('OTP verified successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid or expired OTP!', 'error')
    
    return render_template('admin_otp.html')

@app.route('/register/citizen', methods=['GET', 'POST'])
def register_citizen():
    if current_user.is_authenticated:
        return redirect(url_for('citizen_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register_citizen.html')
        
        user = User(name=name, email=email, role='citizen', phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('citizen_login'))
    
    return render_template('register_citizen.html')

# Dashboard routes
@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('login_citizen'))
    
    # Redirect to appropriate dashboard based on role
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_police():
        return redirect(url_for('police_dashboard'))
    else:
        return redirect(url_for('citizen_dashboard'))

@app.route('/citizen/dashboard')
@login_required
@citizen_required
def citizen_dashboard():
    # Get user's FIR reports
    fir_reports = FIRReport.query.filter_by(user_id=current_user.id).order_by(FIRReport.timestamp.desc()).all()
    return render_template('citizen_dashboard.html', fir_reports=fir_reports)

@app.route('/police/dashboard')
@login_required
@police_required
def police_dashboard():
    # Get FIR reports for this department
    fir_reports = FIRReport.query.filter_by(department_id=current_user.department_id).order_by(FIRReport.timestamp.desc()).all()
    
    # Get department info
    department = Department.query.get(current_user.department_id)
    
    # Calculate counts for dashboard stats
    pending_count = len([fir for fir in fir_reports if fir.status == 'pending'])
    in_progress_count = len([fir for fir in fir_reports if fir.status == 'in_progress'])
    closed_count = len([fir for fir in fir_reports if fir.status == 'closed'])
    total_count = len(fir_reports)
    
    return render_template('police_dashboard.html', 
                         fir_reports=fir_reports, 
                         department=department,
                         pending_count=pending_count,
                         in_progress_count=in_progress_count,
                         closed_count=closed_count,
                         total_count=total_count)

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get pending FIR reports
    pending_firs = FIRReport.query.filter_by(status='pending').order_by(FIRReport.timestamp.desc()).all()
    
    # Get all departments
    departments = Department.query.all()
    
    # Get all users
    users = User.query.all()
    
    # Get statistics
    total_fir_count = FIRReport.query.count()
    pending_count = len(pending_firs)
    department_count = Department.query.count()
    user_count = User.query.count()
    
    return render_template('admin_dashboard.html',
                         pending_firs=pending_firs,
                         departments=departments,
                         users=users,
                         total_fir_count=total_fir_count,
                         pending_count=pending_count,
                         department_count=department_count,
                         user_count=user_count)

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    df = data
    locations = sorted(df['locality'].unique())
    prediction = None
    if request.method == 'POST':
        location = request.form['location']
        date = request.form['date']
        hour = request.form['hour']
        features = {'locality': location, 'hour': hour, 'date': date}
        prediction = predict_crime_type(model, features, df)
    return render_template('predict.html', locations=locations, prediction=prediction)

@app.route('/eda')
@login_required
def eda():
    df = load_data()
    if df is None:
        return render_template('eda.html', error='Could not load crime data.', total_crimes=None, top_types_labels=[], top_types_values=[], trend_labels=[], trend_values=[], recent_cases=[], summary_stats={})
    total_crimes = len(df)
    # Top 5 crime types
    top_types = df['crime_description'].value_counts().head(5)
    top_types_labels = [str(x) for x in top_types.index]
    top_types_values = [int(x) for x in top_types.values]
    # No date column, so skip monthly trend
    trend_labels = []
    trend_values = []
    # Prepare recent cases (last 10 by date if possible)
    recent_cases = []
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        try:
            df_sorted = df.sort_values('date', ascending=False)
        except Exception:
            df_sorted = df
        recent_cases = df_sorted.head(10).to_dict(orient='records')
    else:
        recent_cases = df.head(10).to_dict(orient='records')
    # Basic summary statistics
    num_unique_crime_types = df['crime_description'].nunique() if 'crime_description' in df.columns else 0
    most_common_crime_types = df['crime_description'].value_counts().head(3).to_dict() if 'crime_description' in df.columns else {}
    most_affected_areas = df['locality'].value_counts().head(3).to_dict() if 'locality' in df.columns else {}
    # Crimes by time of day
    def get_time_of_day(hour):
        try:
            h = int(hour)
            if 5 <= h < 12:
                return 'Morning'
            elif 12 <= h < 18:
                return 'Afternoon'
            else:
                return 'Night'
        except:
            return 'Unknown'
    if 'hour' in df.columns:
        df['time_of_day'] = df['hour'].apply(get_time_of_day)
        crimes_by_time_of_day = df['time_of_day'].value_counts().to_dict()
    else:
        crimes_by_time_of_day = {}
    summary_stats = {
        'total_crimes': total_crimes,
        'num_unique_crime_types': num_unique_crime_types,
        'most_common_crime_types': most_common_crime_types,
        'most_affected_areas': most_affected_areas,
        'crimes_by_time_of_day': crimes_by_time_of_day
    }
    return render_template(
        'eda.html',
        total_crimes=total_crimes,
        top_types_labels=top_types_labels,
        top_types_values=top_types_values,
        trend_labels=trend_labels,
        trend_values=trend_values,
        error=None,
        recent_cases=recent_cases,
        summary_stats=summary_stats
    )

@app.route('/hotspot', methods=['GET', 'POST'])
@login_required
def hotspot():
    df = load_data()
    if df is None or 'latitude' not in df.columns or 'longitude' not in df.columns:
        return render_template('hotspot.html', error='Could not load location data.', map_path=None, localities=[], selected_locality=None, criminals=[])
    df = df.dropna(subset=['latitude', 'longitude'])
    all_localities = sorted(df['locality'].dropna().unique())
    selected_locality = None
    if request.method == 'POST':
        selected_locality = request.form.get('locality')
    else:
        selected_locality = request.args.get('locality')
    filtered_df = df
    if selected_locality and selected_locality != 'All':
        filtered_df = df[df['locality'] == selected_locality]
    # Cluster filtered locations
    coords = filtered_df[['latitude', 'longitude']].values
    n_clusters = 3 if len(filtered_df) >= 3 else max(1, len(filtered_df))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    filtered_df['cluster'] = kmeans.fit_predict(coords) if len(filtered_df) > 0 else 0
    centers = kmeans.cluster_centers_ if len(filtered_df) > 0 else []
    # Always center on Rasayani, fit bounds to data if available
    rasayani_center = [18.8600, 73.1500]
    m = folium.Map(location=rasayani_center, zoom_start=14, max_bounds=True)
    if len(filtered_df) > 0:
        min_lat, max_lat = filtered_df['latitude'].min(), filtered_df['latitude'].max()
        min_lon, max_lon = filtered_df['longitude'].min(), filtered_df['longitude'].max()
        bounds = [[min_lat, min_lon], [max_lat, max_lon]]
        m.fit_bounds(bounds)
    # Optionally, add a marker for Rasayani center
    folium.Marker(
        location=rasayani_center,
        icon=folium.Icon(color='blue', icon='home'),
        popup='Rasayani City Center'
    ).add_to(m)
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    for idx, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=4,
            color=colors[row['cluster'] % len(colors)] if len(filtered_df) > 0 else 'gray',
            fill=True,
            fill_opacity=0.7,
            popup=row.get('locality', '')
        ).add_to(m)
    # Mark cluster centers
    if len(filtered_df) > 0:
        for i, center in enumerate(centers):
            folium.Marker(
                location=center,
                icon=folium.Icon(color=colors[i % len(colors)], icon='star'),
                popup=f'Hotspot Center {i+1}'
            ).add_to(m)
    map_path = 'static/hotspot_map.html'
    m.save(map_path)
    # Prepare criminal table data
    criminals = filtered_df[['crime_description', 'crime_domain', 'weapon_used', 'victim_age', 'victim_gender', 'criminal_name', 'hour', 'locality']].to_dict(orient='records') if len(filtered_df) > 0 else []
    return render_template('hotspot.html', error=None, map_path=map_path, localities=all_localities, selected_locality=selected_locality, criminals=criminals)

@app.route('/fir/add', methods=['GET', 'POST'])
@login_required
@citizen_required
def add_fir():
    if request.method == 'POST':
        # Get form data
        description = request.form.get('description', '').strip()
        crime_type = request.form.get('crime_type', '').strip()
        lat = float(request.form.get('latitude', 0))
        lon = float(request.form.get('longitude', 0))
        
        # Basic validation
        if not description or not crime_type or lat == 0 or lon == 0:
            flash('Please fill all required fields!', 'error')
            return render_template('add_fir.html')
        
        # Handle file upload
        evidence_file = None
        if 'evidence_file' in request.files:
            file = request.files['evidence_file']
            if file.filename:
                evidence_file = save_uploaded_file(file)
        
        # Create new FIR report
        fir = FIRReport(
            user_id=current_user.id,
            description=description,
            crime_type=crime_type,
            lat=lat,
            lon=lon,
            evidence_file=evidence_file,
            status='pending'
        )
        
        db.session.add(fir)
        db.session.commit()
        
        flash('FIR submitted successfully! It will be reviewed by an admin.', 'success')
        return redirect(url_for('citizen_dashboard'))
    
    return render_template('add_fir.html')

# Admin FIR management routes
@app.route('/admin/fir/<int:fir_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_fir_location(fir_id):
    fir = FIRReport.query.get_or_404(fir_id)
    
    if fir.status != 'pending':
        flash('FIR is not in pending status!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Find appropriate department for the location
    department = get_department_for_location(fir.lat, fir.lon)
    
    if department:
        fir.department_id = department.id
        fir.status = 'assigned'
        fir.updated_at = datetime.utcnow()
        fir.admin_notes = f"Location verified and assigned to {department.name}"
        flash(f'FIR assigned to {department.name}', 'success')
    else:
        fir.status = 'verified'
        fir.updated_at = datetime.utcnow()
        fir.admin_notes = "Location verified but no department found in area"
        flash('Location verified but no department found in area', 'warning')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/fir/<int:fir_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_fir_department(fir_id):
    fir = FIRReport.query.get_or_404(fir_id)
    department_id = request.form.get('department_id')
    
    if department_id:
        department = Department.query.get(department_id)
        fir.department_id = department.id
        fir.status = 'assigned'
        fir.updated_at = datetime.utcnow()
        fir.admin_notes = f"Manually assigned to {department.name}"
        flash(f'FIR assigned to {department.name}', 'success')
    else:
        fir.department_id = None
        fir.status = 'verified'
        fir.admin_notes = "Department assignment removed"
        flash('Department assignment removed', 'info')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Admin: verify and assign (combined action used by admin dashboard)
@app.route('/admin/fir/<int:fir_id>/verify-assign', methods=['POST'])
@login_required
@admin_required
def verify_and_assign_fir(fir_id):
    fir = FIRReport.query.get_or_404(fir_id)
    department_id = request.form.get('department_id')
    admin_notes = request.form.get('admin_notes', '')

    # If department chosen, verify + assign
    if department_id:
        department = Department.query.get(department_id)
        if department:
            fir.department_id = department.id
            fir.status = 'assigned'
            fir.updated_at = datetime.utcnow()
            fir.admin_notes = admin_notes or f"Verified and assigned to {department.name}"
            flash(f'FIR verified and assigned to {department.name}', 'success')
        else:
            flash('Selected department not found.', 'error')
    else:
        # Only verify if no department provided
        fir.status = 'verified'
        fir.updated_at = datetime.utcnow()
        fir.admin_notes = admin_notes or 'Verified by admin'
        flash('FIR verified. No department selected.', 'info')

    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Admin: reject FIR
@app.route('/admin/fir/<int:fir_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_fir(fir_id):
    fir = FIRReport.query.get_or_404(fir_id)
    reason = request.form.get('rejection_reason', '').strip()

    fir.status = 'rejected'
    fir.updated_at = datetime.utcnow()
    fir.admin_notes = f"Rejected: {reason}" if reason else 'Rejected by admin'
    db.session.commit()

    flash('FIR rejected successfully.', 'info')
    return redirect(url_for('admin_dashboard'))

# Police FIR management routes
@app.route('/police/fir/<int:fir_id>/update', methods=['POST'])
@login_required
@police_required
def update_fir_status(fir_id):
    fir = FIRReport.query.get_or_404(fir_id)
    
    # Check if FIR belongs to this department
    if fir.department_id != current_user.department_id:
        flash('Access denied!', 'error')
        return redirect(url_for('police_dashboard'))
    
    status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    if status in ['in_progress', 'closed']:
        fir.status = status
        fir.police_notes = notes
        db.session.commit()
        flash(f'FIR status updated to {status}', 'success')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('police_dashboard'))

@app.route('/fir/records')
@login_required
def fir_records():
    # Get FIR reports based on user role
    if current_user.is_admin():
        # Admin sees all FIR reports
        firs = FIRReport.query.order_by(FIRReport.timestamp.desc()).all()
    elif current_user.is_police():
        # Police users see only their department's FIR reports
        firs = FIRReport.query.filter_by(department_id=current_user.department_id).order_by(FIRReport.timestamp.desc()).all()
    else:
        # Citizens see only their own FIR reports
        firs = FIRReport.query.filter_by(user_id=current_user.id).order_by(FIRReport.timestamp.desc()).all()
    
    # Convert to list of dictionaries for template compatibility
    fir_list = []
    for fir in firs:
        fir_dict = {
            'ID': fir.id,
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

@app.route('/analytics')
@login_required
def analytics():
    df = load_data()
    if df is None:
        # Pass empty lists to avoid template errors
        return render_template(
            'analytics.html',
            top_types_labels=[], top_types_values=[],
            area_labels=[], area_values=[],
            gender_labels=[], gender_values=[],
            weapon_labels=[], weapon_values=[],
            hourly_labels=[], hourly_values=[],
            agegroup_labels=[], agegroup_values=[],
            domain_labels=[], domain_values=[],
            heatmap_coords=[],
            suspect_labels=[], suspect_values=[]
        )
    # Top crime types
    top_types = df['crime_description'].value_counts().head(10)
    top_types_labels = list(top_types.index)
    top_types_values = [int(x) for x in top_types.values]
    # Area-wise breakdown
    area_counts = df['locality'].value_counts().head(10)
    area_labels = list(area_counts.index)
    area_values = [int(x) for x in area_counts.values]
    # Victim gender (for pie chart)
    gender_counts = df['victim_gender'].value_counts()
    gender_labels = list(gender_counts.index)
    gender_values = [int(x) for x in gender_counts.values]
    # Weapon usage
    weapon_counts = df['weapon_used'].value_counts().head(10)
    weapon_labels = list(weapon_counts.index)
    weapon_values = [int(x) for x in weapon_counts.values]
    # Hourly crime distribution
    if 'hour' in df.columns:
        hourly = df['hour'].value_counts().sort_index()
        hourly_labels = [str(int(h)) for h in hourly.index]
        hourly_values = [int(x) for x in hourly.values]
    else:
        hourly_labels, hourly_values = [], []
    # Victim age group
    if 'victim_age' in df.columns:
        bins = [0, 18, 35, 60, 100]
        labels = ['0-18', '19-35', '36-60', '60+']
        df['age_group'] = pd.cut(df['victim_age'], bins=bins, labels=labels, right=False)
        agegroup_counts = df['age_group'].value_counts().sort_index()
        agegroup_labels = list(agegroup_counts.index.astype(str))
        agegroup_values = [int(x) for x in agegroup_counts.values]
    else:
        agegroup_labels, agegroup_values = [], []
    # Crime domain breakdown
    if 'crime_domain' in df.columns:
        domain_counts = df['crime_domain'].value_counts().head(10)
        domain_labels = list(domain_counts.index)
        domain_values = [int(x) for x in domain_counts.values]
    else:
        domain_labels, domain_values = [], []
    # Heatmap data (lat/lon)
    if 'latitude' in df.columns and 'longitude' in df.columns:
        heatmap_coords = df[['latitude', 'longitude']].dropna().values.tolist()
    else:
        heatmap_coords = []
    # Top suspects (by criminal name)
    if 'criminal_name' in df.columns:
        suspect_counts = df['criminal_name'].value_counts().head(10)
        suspect_labels = list(suspect_counts.index)
        suspect_values = [int(x) for x in suspect_counts.values]
    else:
        suspect_labels, suspect_values = [], []
    return render_template(
        'analytics.html',
        top_types_labels=top_types_labels,
        top_types_values=top_types_values,
        area_labels=area_labels,
        area_values=area_values,
        gender_labels=gender_labels,
        gender_values=gender_values,
        weapon_labels=weapon_labels,
        weapon_values=weapon_values,
        hourly_labels=hourly_labels,
        hourly_values=hourly_values,
        agegroup_labels=agegroup_labels,
        agegroup_values=agegroup_values,
        domain_labels=domain_labels,
        domain_values=domain_values,
        heatmap_coords=heatmap_coords,
        suspect_labels=suspect_labels,
        suspect_values=suspect_values
    )

@app.route('/ml-insights')
@login_required
def ml_insights():
    from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import os
    import base64
    from io import BytesIO
    from src.model import train_crime_type_model
    df = load_data()
    if df is None:
        return render_template('ml_insights.html', metrics=None, confusion=None, features=None, report_table=None, roc_img=None, report_csv=None, shap_img=None)
    # Train/test split and model
    model, X_test, y_test = train_crime_type_model(df)
    y_pred = model.predict(X_test)
    # Classification report
    report = classification_report(y_test, y_pred, output_dict=True)
    metrics = {
        'accuracy': report['accuracy'],
        'macro avg': report['macro avg'],
        'weighted avg': report['weighted avg']
    }
    # Full report as table
    report_table = []
    for label in model.classes_:
        row = report.get(str(label), report.get(label, {}))
        if row:
            report_table.append({
                'label': label,
                'precision': row.get('precision', 0),
                'recall': row.get('recall', 0),
                'f1': row.get('f1-score', 0),
                'support': row.get('support', 0)
            })
    # Save report as CSV
    static_dir = os.path.join('static', 'ml_insights')
    os.makedirs(static_dir, exist_ok=True)
    report_csv_path = os.path.join(static_dir, 'classification_report.csv')
    pd.DataFrame(report_table).to_csv(report_csv_path, index=False)
    report_csv = '/static/ml_insights/classification_report.csv'
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    confusion = {
        'labels': list(model.classes_),
        'matrix': cm.tolist()
    }
    confusion_rows = list(zip(confusion['matrix'], confusion['labels']))
    # Feature importance (for tree-based models)
    if hasattr(model, 'feature_importances_'):
        features = sorted(zip(X_test.columns, model.feature_importances_), key=lambda x: -x[1])
    else:
        features = []
    # ROC curve (multi-class, one-vs-rest)
    try:
        from sklearn.preprocessing import label_binarize
        y_test_bin = label_binarize(y_test, classes=model.classes_)
        y_pred_prob = model.predict_proba(X_test)
        fpr = dict()
        tpr = dict()
        roc_auc = dict()
        for i, label in enumerate(model.classes_):
            fpr[label], tpr[label], _ = roc_curve(y_test_bin[:, i], y_pred_prob[:, i])
            roc_auc[label] = auc(fpr[label], tpr[label])
        plt.figure(figsize=(7,5))
        for label in model.classes_:
            plt.plot(fpr[label], tpr[label], label=f"{label} (AUC={roc_auc[label]:.2f})")
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve (One-vs-Rest)')
        plt.legend()
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        roc_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        roc_img = None
    # SHAP summary plot (optional)
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        plt.figure(figsize=(8,5))
        shap.summary_plot(shap_values, X_test, show=False)
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        shap_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        shap_img = None
    return render_template('ml_insights.html', metrics=metrics, confusion=confusion, features=features, report_table=report_table, roc_img=roc_img, report_csv=report_csv, shap_img=shap_img, confusion_rows=confusion_rows)

@app.route('/logout/citizen')
def logout_citizen():
    response = make_response(redirect(url_for('citizen_login')))
    response.delete_cookie('citizen_token')
    flash('Citizen logged out.', 'info')
    return response

@app.route('/logout/police')
def logout_police():
    response = make_response(redirect(url_for('police_login')))
    response.delete_cookie('police_token')
    flash('Police officer logged out.', 'info')
    return response

@app.route('/logout/admin')
def logout_admin():
    response = make_response(redirect(url_for('admin_login')))
    response.delete_cookie('admin_token')
    flash('Admin logged out.', 'info')
    return response

@app.route('/logout')
def logout():
    # Global logout for all portals
    response = make_response(redirect(url_for('home')))
    response.delete_cookie('citizen_token')
    response.delete_cookie('police_token')
    response.delete_cookie('admin_token')
    logout_user()
    flash('Logged out from all portals.', 'info')
    return response

if __name__ == '__main__':
    app.run(debug=True)