from flask_mongoengine import MongoEngine
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import secrets

db = MongoEngine()

class Department(db.Document):
    meta = {'collection': 'departments'}
    name = db.StringField(max_length=100, required=True)
    city = db.StringField(max_length=100, required=True)
    district = db.StringField(max_length=100)
    type = db.StringField(max_length=50)
    status = db.StringField(max_length=20, default='Active')
    load = db.IntField(default=0)
    min_lat = db.FloatField()
    max_lat = db.FloatField()
    min_lon = db.FloatField()
    max_lon = db.FloatField()
    created_at = db.DateTimeField(default=datetime.utcnow)

class User(UserMixin, db.Document):
    meta = {'collection': 'users'}
    name = db.StringField(max_length=100, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    password_hash = db.StringField(max_length=255, required=True)
    role = db.StringField(max_length=20, default='citizen')
    department = db.ReferenceField(Department, reverse_delete_rule=db.NULLIFY)
    phone = db.StringField(max_length=20)
    verification_status = db.StringField(max_length=20, default='Pending')
    is_active = db.BooleanField(default=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    
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
    
    def get_id(self):
        return str(self.id)

class FIRReport(db.Document):
    meta = {'collection': 'fir_reports'}
    user = db.ReferenceField(User, required=True)
    department = db.ReferenceField(Department, reverse_delete_rule=db.NULLIFY)
    assigned_station_id = db.ReferenceField(Department, reverse_delete_rule=db.NULLIFY)
    description = db.StringField(required=True)
    crime_type = db.StringField(max_length=100, required=True)
    lat = db.FloatField(required=True)
    lon = db.FloatField(required=True)
    status = db.StringField(max_length=20, default='pending')
    evidence_file = db.StringField(max_length=255)
    admin_notes = db.StringField()
    police_notes = db.StringField()
    priority = db.StringField(max_length=20, choices=['High', 'Medium', 'Low'], default='Medium')
    location_name = db.StringField(max_length=255)
    timestamp = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

class Criminal(db.Document):
    meta = {'collection': 'criminals'}
    name = db.StringField(max_length=100, required=True)
    photo = db.StringField(max_length=255)
    crime_type = db.StringField(max_length=100)
    fir_id = db.ReferenceField(FIRReport, reverse_delete_rule=db.NULLIFY)
    last_known_location = db.StringField(max_length=255)
    status = db.StringField(max_length=50, default='Active')  # Active/Caught/Under Investigation
    priority = db.StringField(max_length=20, default='Medium')  # High/Medium/Low
    created_at = db.DateTimeField(default=datetime.utcnow)

class Alert(db.Document):
    meta = {'collection': 'alerts'}
    message = db.StringField(required=True)
    crime_id = db.ReferenceField(FIRReport, reverse_delete_rule=db.CASCADE)
    priority = db.StringField(max_length=20, default='Medium')  # High/Medium/Low
    timestamp = db.DateTimeField(default=datetime.utcnow)

class CaseUpdate(db.Document):
    meta = {'collection': 'case_updates'}
    crime_id = db.ReferenceField(FIRReport, required=True, reverse_delete_rule=db.CASCADE)
    message = db.StringField(required=True)
    updated_by = db.ReferenceField(User, required=True)
    timestamp = db.DateTimeField(default=datetime.utcnow)

class Evidence(db.Document):
    meta = {'collection': 'evidence'}
    crime_id = db.ReferenceField(FIRReport, required=True, reverse_delete_rule=db.CASCADE)
    file_url = db.StringField(required=True)
    file_type = db.StringField(max_length=50)
    uploaded_at = db.DateTimeField(default=datetime.utcnow)

class OTPCode(db.Document):
    meta = {'collection': 'otp_codes'}
    user = db.ReferenceField(User, required=True)
    otp_code = db.StringField(max_length=6, required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    expires_at = db.DateTimeField(required=True)
    is_used = db.BooleanField(default=False)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

class CrimeData(db.Document):
    meta = {'collection': 'crime_data'}
    date = db.StringField(max_length=50)
    time = db.StringField(max_length=50)
    crime_description = db.StringField(max_length=255)
    locality = db.StringField(max_length=100)
    latitude = db.FloatField()
    longitude = db.FloatField()
    victim_gender = db.StringField(max_length=20)
    victim_age = db.IntField()

class SystemLog(db.Document):
    meta = {'collection': 'system_logs'}
    timestamp = db.DateTimeField(default=datetime.utcnow)
    user = db.ReferenceField(User, reverse_delete_rule=db.NULLIFY)
    action = db.StringField(max_length=120, required=True)
    status = db.StringField(max_length=20, required=True)
    ip_address = db.StringField(max_length=45)
    meta_info = db.StringField()

def init_db(app):
    db.init_app(app)
    # Registration for app context if needed
    
    # Create default admin and department if they don't exist
    with app.app_context():
        if not User.objects(role='admin').first():
            print("Creating default admin and department...")
            # Create default department
            dept = Department(
                name='Rasayani Police Station', 
                city='Rasayani', 
                min_lat=18.80, 
                max_lat=18.90, 
                min_lon=73.15, 
                max_lon=73.20
            )
            dept.save()
            
            admin = User(
                name='Admin User', 
                email='admin@crime.gov', 
                role='admin',
                phone='1234567890',
                verification_status='Approved'
            )
            admin.set_password('admin123')
            admin.save()
            
            # Create default police officer
            police_user = User(
                name='Police Officer', 
                email='officer@rasayani.gov', 
                role='police', 
                department=dept,
                phone='9876543210'
            )
            police_user.set_password('officer123')
            police_user.save()
            
            print("Default users and department created in MongoDB!")
        
        # Import existing CSV data if crime_data is empty
        if not CrimeData.objects.first():
            import_csv_data()

def import_csv_data():
    """Import existing CSV data into MongoDB"""
    try:
        import pandas as pd
        csv_path = os.path.join('data', 'rasayani_crime_dataset', 'rasayani_crime_dataset_corrected.csv')
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"Importing {len(df)} records from CSV to MongoDB...")
            
            crime_docs = []
            for _, row in df.iterrows():
                crime_data = CrimeData(
                    date=str(row.get('Date', '')),
                    time=str(row.get('Time', '')),
                    crime_description=str(row.get('Crime Description', '')),
                    locality=str(row.get('Locality', '')),
                    latitude=float(row.get('latitude', 0)) if pd.notnull(row.get('latitude')) else None,
                    longitude=float(row.get('longitude', 0)) if pd.notnull(row.get('longitude')) else None,
                    victim_gender=str(row.get('Victim Gender', '')),
                    victim_age=int(row.get('Victim Age', 0)) if pd.notnull(row.get('Victim Age')) else None
                )
                crime_docs.append(crime_data)
            
            if crime_docs:
                CrimeData.objects.insert(crime_docs)
            
            print("CSV data imported to MongoDB successfully!")
        else:
            print(f"CSV file not found at: {csv_path}")
    except Exception as e:
        print(f"Error importing CSV data to MongoDB: {e}")

def create_otp_for_user(user):
    """Create a new OTP for a user"""
    # Delete any existing unused OTPs for this user
    OTPCode.objects(user=user, is_used=False).delete()
    
    # Create new OTP
    otp = OTPCode(
        user=user,
        otp_code=''.join(secrets.choice('0123456789') for _ in range(6)),
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    otp.save()
    return otp.otp_code

def verify_otp(user, otp_code):
    """Verify OTP for a user"""
    otp = OTPCode.objects(
        user=user, 
        otp_code=otp_code, 
        is_used=False
    ).first()
    
    if otp and not otp.is_expired():
        otp.is_used = True
        otp.save()
        return True
    return False

def get_department_for_location(lat, lon):
    """Find the appropriate department for a given location"""
    departments = Department.objects.all()
    for dept in departments:
        if dept.min_lat <= lat <= dept.max_lat and dept.min_lon <= lon <= dept.max_lon:
            return dept
    return None
