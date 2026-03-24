from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sos_service import trigger_sos, update_sos_location, resolve_sos
from services.location_service import get_nearest_stations
from services.safety_service import activate_safety_mode, check_in, deactivate_safety_mode
from src.auth import police_required

sos_bp = Blueprint('sos', __name__)

from functools import wraps

def hybrid_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Try Session (Flask-Login)
        if current_user.is_authenticated:
            print(f"AUTH: Session authenticated for {current_user.id}")
            return f(*args, **kwargs)
        
        # 2. Try JWT
        print("AUTH: Session failed, trying JWT...")
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            print(f"AUTH: JWT authenticated for {get_jwt_identity()}")
            return f(*args, **kwargs)
        except Exception as e:
            print(f"AUTH: JWT failed: {str(e)}")
            return jsonify({"msg": "Unauthorized access. Please login again.", "error": str(e)}), 401
    return decorated

@sos_bp.route('/trigger', methods=['POST'])
@hybrid_auth
def trigger():
    user_id = get_jwt_identity() or str(current_user.id)
    data = request.get_json()
    lat = data.get('lat') or data.get('latitude')
    lon = data.get('lon') or data.get('longitude')
    selected_station = data.get('selected_station')
    
    if not lat or not lon:
        return jsonify({"error": "Latitude and Longitude are required."}), 400
        
    sos_report, error = trigger_sos(user_id, lat, lon, selected_station=selected_station)
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify({
        "message": f"SOS successfully triggered. Assigned to {sos_report.assigned_station}",
        "sos_id": str(sos_report.id),
        "assigned_station": sos_report.assigned_station
    }), 201

@sos_bp.route('/nearest-stations', methods=['GET'])
@hybrid_auth
def nearest_stations():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if lat is None or lon is None:
        return jsonify({"error": "Latitude and longitude required"}), 400
        
    stations = get_nearest_stations(lat, lon)
    return jsonify(stations), 200

@sos_bp.route('/update-location', methods=['POST'])
@hybrid_auth
def update_location():
    data = request.get_json()
    print(f"DEBUG_PAYLOAD: Received from citizen: {data}")
    sos_id = data.get('sos_id')
    lat = data.get('latitude') or data.get('lat')
    lon = data.get('longitude') or data.get('lon')
    
    if not sos_id or not lat or not lon:
        return jsonify({"error": "Missing required fields."}), 400
        
    success, error = update_sos_location(sos_id, lat, lon)
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify({"message": "Location updated."}), 200

@sos_bp.route('/resolve/<sos_id>', methods=['POST'])
@login_required
@police_required
def resolve(sos_id):
    data = request.get_json() or {}
    notes = data.get('notes')
    
    success, error = resolve_sos(sos_id, notes)
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify({"message": "SOS alert resolved."}), 200

@sos_bp.route('/active-alerts', methods=['GET'])
@login_required
@police_required
def active_alerts():
    from models.database import SOSReport
    alerts = SOSReport.objects(status='Active').order_by('-created_at')
    
    alert_list = []
    for a in alerts:
        alert_list.append({
            "id": str(a.id),
            "user_name": a.user.full_name or a.user.name,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "station": a.assigned_station,
            "district": a.district,
            "city": a.city,
            "status": a.status,
            "created_at": a.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    return jsonify(alert_list), 200

@sos_bp.route('/safety-mode/activate', methods=['POST'])
@hybrid_auth
def activate_safety():
    user_id = get_jwt_identity() or str(current_user.id)
    data = request.get_json()
    duration = data.get('duration', 30)
    success, error = activate_safety_mode(user_id, duration)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Safety Mode activated."}), 200

@sos_bp.route('/safety-mode/check-in', methods=['POST'])
@hybrid_auth
def safety_check_in():
    user_id = get_jwt_identity() or str(current_user.id)
    success, error = check_in(user_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Check-in successful. Timer reset."}), 200

@sos_bp.route('/safety-mode/deactivate', methods=['POST'])
@hybrid_auth
def deactivate_safety():
    user_id = get_jwt_identity() or str(current_user.id)
    success, error = deactivate_safety_mode(user_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Safety Mode deactivated."}), 200
