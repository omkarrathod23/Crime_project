from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import secrets
import string

db = SQLAlchemy()

def generate_tracking_id():
    """Generates a unique 12-character alphanumeric tracking ID."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(12))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='citizen')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    department = db.relationship('Department', backref='users')
    fir_reports = db.relationship('FIRReport', backref='user', lazy='dynamic')
    otp_codes = db.relationship('OTPCode', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_police(self):
        return self.role == 'police'
    
    def is_citizen(self):
        return self.role == 'citizen'

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    min_lat = db.Column(db.Float, nullable=False)
    max_lat = db.Column(db.Float, nullable=False)
    min_lon = db.Column(db.Float, nullable=False)
    max_lon = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fir_reports = db.relationship('FIRReport', backref='department', lazy='dynamic')

class FIRReport(db.Model):
    __tablename__ = 'fir_reports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    crime_type = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, assigned, in_progress, closed
    evidence_file = db.Column(db.String(255), nullable=True)  # Path to uploaded file
    admin_notes = db.Column(db.Text, nullable=True)
    police_notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnonymousReport(db.Model):
    __tablename__ = 'anonymous_reports'
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(12), unique=True, nullable=False, default=generate_tracking_id)
    crime_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    evidence_file = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending') # pending, reviewed, assigned, closed
    admin_notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OTPCode(db.Model):
    __tablename__ = 'otp_codes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

class CrimeData(db.Model):
    __tablename__ = 'crime_data'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=True)
    time = db.Column(db.String(50), nullable=True)
    crime_description = db.Column(db.String(255), nullable=True)
    locality = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    victim_gender = db.Column(db.String(20), nullable=True)
    victim_age = db.Column(db.Integer, nullable=True)

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
        # Create default admin and department users if they don't exist
        if not User.query.filter_by(role='admin').first():
            admin = User(
                name='Admin User', 
                email='admin@crime.gov', 
                role='admin',
                phone='1234567890'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create default department
            dept = Department(
                name='Rasayani Police Station', 
                city='Rasayani', 
                min_lat=18.80, 
                max_lat=18.90, 
                min_lon=73.15, 
                max_lon=73.20
            )
            db.session.add(dept)
            db.session.flush()  # Get the ID
            
            # Create default police officer
            police_user = User(
                name='Police Officer', 
                email='officer@rasayani.gov', 
                role='police', 
                department_id=dept.id,
                phone='9876543210'
            )
            police_user.set_password('officer123')
            db.session.add(police_user)
            
            db.session.commit()
            print("Default users and department created!")
        
        # Import existing CSV data if crime_data table is empty
        if not CrimeData.query.first():
            import_csv_data()

def import_csv_data():
    """Import existing CSV data into CrimeData table"""
    try:
        import pandas as pd
        csv_path = os.path.join('data', 'rasayani_crime_dataset', 'rasayani_crime_dataset_corrected.csv')
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"Importing {len(df)} records from CSV...")
            
            for _, row in df.iterrows():
                crime_data = CrimeData(
                    date=row.get('Date', ''),
                    time=row.get('Time', ''),
                    crime_description=row.get('Crime Description', ''),
                    locality=row.get('Locality', ''),
                    latitude=row.get('latitude', None),
                    longitude=row.get('longitude', None),
                    victim_gender=row.get('Victim Gender', ''),
                    victim_age=row.get('Victim Age', None)
                )
                db.session.add(crime_data)
            
            db.session.commit()
            print("CSV data imported successfully!")
        else:
            print(f"CSV file not found at: {csv_path}")
    except Exception as e:
        print(f"Error importing CSV data: {e}")
        db.session.rollback()

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def create_otp_for_user(user_id):
    """Create a new OTP for a user"""
    # Delete any existing unused OTPs for this user
    OTPCode.query.filter_by(user_id=user_id, is_used=False).delete()
    
    # Create new OTP
    otp = OTPCode(
        user_id=user_id,
        otp_code=generate_otp(),
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.session.add(otp)
    db.session.commit()
    return otp.otp_code

def verify_otp(user_id, otp_code):
    """Verify OTP for a user"""
    otp = OTPCode.query.filter_by(
        user_id=user_id, 
        otp_code=otp_code, 
        is_used=False
    ).first()
    
    if otp and not otp.is_expired():
        otp.is_used = True
        db.session.commit()
        return True
    return False

def verify_location(lat, lon, dept_coords):
    """Verify if location falls within department boundaries"""
    min_lat, max_lat, min_lon, max_lon = dept_coords
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon

def get_department_for_location(lat, lon):
    """Find the appropriate department for a given location"""
    departments = Department.query.all()
    for dept in departments:
        if verify_location(lat, lon, (dept.min_lat, dept.max_lat, dept.min_lon, dept.max_lon)):
            return dept
    return None
