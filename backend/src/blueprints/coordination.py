from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models.database import db, Criminal, Department, Alert, FIRReport, CaseUpdate, Evidence, User
from datetime import datetime
import os
from werkzeug.utils import secure_filename

coordination_bp = Blueprint('coordination', __name__)

@coordination_bp.route('/login', methods=['POST'])
def api_login():
    print("LOG: Login attempt received")
    try:
        data = request.get_json()
        print(f"LOG: Login data: {data}")
        email = data.get('email')
        password = data.get('password')
        
        user = User.objects(email=email).first()
        if user:
            print(f"LOG: User found: {user.name}, checking password...")
            if user.check_password(password):
                print("LOG: Password correct, creating token...")
                access_token = create_access_token(identity=str(user.id))
                return jsonify(
                    access_token=access_token, 
                    role=user.role, 
                    name=user.name,
                    district=user.district,
                    police_station=user.police_station
                ), 200
            else:
                print("LOG: Password incorrect")
        else:
            print(f"LOG: User not found: {email}")
            
        return jsonify({"msg": "Bad email or password"}), 401
    except Exception as e:
        print(f"LOG: Login ERROR: {str(e)}")
        return jsonify({"msg": "Server processing error", "error": str(e)}), 400

@coordination_bp.route('/add-criminal', methods=['POST'])
@jwt_required()
def add_criminal():
    data = request.get_json()
    try:
        criminal = Criminal(
            name=data.get('name'),
            photo=data.get('photo'),
            crime_type=data.get('crime_type'),
            fir_id=data.get('fir_id'),
            last_known_location=data.get('last_known_location'),
            status=data.get('status', 'Active'),
            priority=data.get('priority', 'Medium')
        )
        criminal.save()
        return jsonify({"msg": "Criminal added successfully", "id": str(criminal.id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@coordination_bp.route('/all-criminals', methods=['GET'])
@jwt_required()
def all_criminals():
    criminals = Criminal.objects.all()
    return jsonify([{
        "id": str(c.id),
        "name": c.name,
        "crime_type": c.crime_type,
        "status": c.status,
        "priority": c.priority,
        "last_known_location": c.last_known_location,
        "created_at": c.created_at.isoformat()
    } for c in criminals]), 200

@coordination_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    alerts = Alert.objects.order_by('-timestamp').limit(10).all()
    return jsonify([{
        "id": str(a.id),
        "message": a.message,
        "crime_id": str(a.crime_id.id) if a.crime_id else None,
        "priority": a.priority,
        "timestamp": a.timestamp.isoformat()
    } for a in alerts]), 200

@coordination_bp.route('/add-update', methods=['POST'])
@jwt_required()
def add_update():
    data = request.get_json()
    user_id = get_jwt_identity()
    try:
        update = CaseUpdate(
            crime_id=data.get('crime_id'),
            message=data.get('message'),
            updated_by=user_id
        )
        update.save()
        return jsonify({"msg": "Update added successfully", "id": str(update.id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@coordination_bp.route('/updates/<crime_id>', methods=['GET'])
@jwt_required()
def get_updates(crime_id):
    updates = CaseUpdate.objects(crime_id=crime_id).order_by('-timestamp')
    return jsonify([{
        "id": str(u.id),
        "message": u.message,
        "updated_by": u.updated_by.name,
        "timestamp": u.timestamp.isoformat()
    } for u in updates]), 200

@coordination_bp.route('/search-criminals', methods=['GET'])
@jwt_required()
def search_criminals():
    name = request.args.get('name')
    crime_type = request.args.get('crime_type')
    location = request.args.get('location')
    fir_id = request.args.get('fir_id')
    
    query = {}
    if name: query['name__icontains'] = name
    if crime_type: query['crime_type__icontains'] = crime_type
    if location: query['last_known_location__icontains'] = location
    if fir_id: query['fir_id'] = fir_id
    
    criminals = Criminal.objects(**query)
    return jsonify([{
        "id": str(c.id),
        "name": c.name,
        "crime_type": c.crime_type,
        "status": c.status,
        "priority": c.priority
    } for c in criminals]), 200

@coordination_bp.route('/upload-evidence', methods=['POST'])
@jwt_required()
def upload_evidence():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    crime_id = request.form.get('crime_id')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and crime_id:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        evidence = Evidence(
            crime_id=crime_id,
            file_url=filename,
            file_type=file.content_type
        )
        evidence.save()
        return jsonify({"msg": "Evidence uploaded successfully", "id": str(evidence.id)}), 201
    return jsonify({"error": "Missing file or crime_id"}), 400

@coordination_bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    total_crimes = FIRReport.objects.count()
    active_criminals = Criminal.objects(status='Active').count()
    caught_criminals = Criminal.objects(status='Caught').count()
    total_alerts = Alert.objects.count()
    
    return jsonify({
        "total_crimes": total_crimes,
        "active_criminals": active_criminals,
        "caught_criminals": caught_criminals,
        "total_alerts": total_alerts
    }), 200

@coordination_bp.route('/police/stations', methods=['GET'])
def get_police_stations():
    stations = Department.objects.all()
    return jsonify([{
        "id": str(s.id),
        "name": s.name,
        "city": s.city,
        "district": s.district
    } for s in stations]), 200
