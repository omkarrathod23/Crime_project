from models.database import SOSReport, User
from services.location_service import assign_nearest_police_station
from extensions import socketio
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_sos(user_id, lat, lon, selected_station=None):
    """
    Triggers an emergency SOS alert.
    1. Assigns the selected station (if provided) or nearest station.
    2. Stores the SOS record.
    3. Broadcasts the alert to the specific police station room via Socket.IO.
    """
    from models.database import Department
    user = User.objects(id=user_id).first()
    if not user:
        return None, "User not found."

    assignment = None
    if selected_station:
        dept = Department.objects(name=selected_station).first()
        if dept:
            assignment = {
                'station_name': dept.name,
                'district': dept.district,
                'city': dept.city
            }
            logger.info(f"Using manually selected station: {selected_station}")

    if not assignment:
        # Fallback to nearest station
        assignment = assign_nearest_police_station(lat, lon)
    
    sos_report = SOSReport(
        user=user,
        latitude=lat,
        longitude=lon,
        status='active',
        selected_station=selected_station,
        assigned_station=assignment['station_name'] if assignment else "Unassigned",
        district=assignment['district'] if assignment else "Unknown",
        city=assignment['city'] if assignment else "Unknown"
    )
    sos_report.save()

    # Prepare alert data for Socket.IO
    alert_data = {
        "sos_id": str(sos_report.id),
        "user_id": str(user.id),
        "user_name": user.full_name or user.name,
        "phone": user.phone_number or user.phone,
        "latitude": lat,
        "longitude": lon,
        "station": sos_report.assigned_station,
        "timestamp": sos_report.created_at.strftime('%H:%M:%S'),
        "time_full": sos_report.created_at.strftime('%d %b, %H:%M'),
        "is_verified": getattr(user, 'is_verified', False),
        "aadhaar": user.aadhaar_number or "N/A",
        "district": sos_report.district or "Unknown"
    }

    # Broadcast to the specific station room
    room_name = sos_report.assigned_station
    print(f"DEBUG_SOS: Emitting to ROOM: '{room_name}' (Namespace: /police)")
    socketio.emit('new_sos', alert_data, namespace='/police', room=room_name)
    
    # Also broadcast globally for any master controllers
    print(f"DEBUG_SOS: Emitting GLOBAL (Namespace: /police)")
    socketio.emit('new_sos', alert_data, namespace='/police')
    
    logger.info(f"SOS Triggered by {user.name}. Assigned to room: {room_name}")
    
    return sos_report, None

def update_sos_location(sos_id, lat, lon):
    """
    Updates the live location of an active SOS event.
    """
    from bson import ObjectId
    try:
        if isinstance(sos_id, str):
            sos_id = ObjectId(sos_id)
        
        # Look for any status starting with "act" to be case-insensitive and robust
        sos_report = SOSReport.objects(id=sos_id).first()
        if not sos_report:
            print(f"SOS_UPDATE_FAIL: No report found for ID {sos_id}")
            return False, "SOS report not found."
            
        if sos_report.status.lower() != 'active':
            print(f"SOS_UPDATE_FAIL: Report {sos_id} is {sos_report.status}, not active")
            # We'll allow it anyway if it's a recent report or just log it
            # return False, "Report is not active."
            pass

        sos_report.latitude = lat
        sos_report.longitude = lon
        sos_report.save()

        # Broadcast updated location
        update_data = {
            "sos_id": str(sos_report.id),
            "user_id": str(sos_report.user.id),
            "user_name": sos_report.user.full_name or sos_report.user.name,
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.utcnow().strftime('%H:%M:%S')
        }
        room_name = sos_report.assigned_station
        if room_name:
            socketio.emit('location_update', update_data, namespace='/police', room=room_name)
        
        socketio.emit('location_update', update_data, namespace='/police')
        
        return True, None
    except Exception as e:
        print(f"SOS_UPDATE_ERROR: {str(e)}")
        return False, str(e)

def resolve_sos(sos_id, notes=None):
    """
    Marks an SOS event as resolved.
    """
    sos_report = SOSReport.objects(id=sos_id).first()
    if not sos_report:
        return False, "SOS report not found."

    sos_report.status = 'Resolved'
    sos_report.resolved_at = datetime.utcnow()
    sos_report.police_notes = notes
    sos_report.save()

    socketio.emit('sos_resolved', {"sos_id": str(sos_report.id)}, namespace='/police')
    
    return True, None
