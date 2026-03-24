from models.database import User, SOSReport
from datetime import datetime, timedelta
from services.sos_service import trigger_sos
import logging

logger = logging.getLogger(__name__)

def activate_safety_mode(user_id, duration_minutes=30):
    """
    Activates Women Safety Mode with a timer.
    """
    user = User.objects(id=user_id).first()
    if not user:
        return False, "User not found."
    
    user.safety_mode_active = True
    user.safety_timer_expiry = datetime.utcnow() + timedelta(minutes=duration_minutes)
    user.save()
    
    logger.info(f"Safety Mode activated for {user.name}. Expiry in {duration_minutes}m")
    return True, None

def check_in(user_id):
    """
    User checks in to confirm they are safe, resetting/extending the timer.
    """
    user = User.objects(id=user_id).first()
    if not user or not user.safety_mode_active:
        return False, "Safety mode not active."
    
    # Reset timer for another 30 mins or mark safe
    user.safety_timer_expiry = datetime.utcnow() + timedelta(minutes=30)
    user.save()
    
    return True, None

def deactivate_safety_mode(user_id):
    """
    Turns off safety mode.
    """
    user = User.objects(id=user_id).first()
    if not user:
        return False, "User not found."
    
    user.safety_mode_active = False
    user.safety_timer_expiry = None
    user.save()
    
    return True, None

def monitor_safety_timers():
    """
    Checks for expired safety timers and triggers SOS automatically.
    This would be called by a periodic task or background thread.
    """
    expired_users = User.objects(
        safety_mode_active=True, 
        safety_timer_expiry__lte=datetime.utcnow()
    )
    
    triggered_count = 0
    for user in expired_users:
        # Get last known location (simulated or from latest SOS update if any)
        # For simplicity, we trigger with a default or last known data
        trigger_sos(user.id, 0, 0) # Real location would be stored in the session/last update
        
        user.safety_mode_active = False
        user.safety_timer_expiry = None
        user.save()
        triggered_count += 1
        
    return triggered_count
