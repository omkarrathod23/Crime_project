import jwt
import os
from datetime import datetime, timedelta

SECRET_KEY = os.environ.get('SECRET_KEY', 'your_jwt_secret_key_change_in_production')

def create_token(user_id, role):
    """
    Create a JWT token for a user with a specific role.
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
    """
    Decode and verify a JWT token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'
    except Exception as e:
        return str(e)
