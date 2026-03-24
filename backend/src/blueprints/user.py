from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import current_user
from models.database import User
from functools import wraps
import base64
import os

user_bp = Blueprint('user', __name__)

def hybrid_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Try Session (Flask-Login)
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # 2. Try JWT
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception:
            return jsonify({"msg": "Unauthorized process. Please login again."}), 401
    return decorated

@user_bp.route('/upload-photo', methods=['POST'])
@hybrid_auth
def upload_photo():
    user_id = get_jwt_identity() or str(current_user.id)
    data = request.get_json()
    face_image = data.get('face_image')

    if not face_image:
        return jsonify({"error": "No face image provided."}), 400

    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found."}), 404

    # Save the base64 image directly to the database user record
    # For a high-scale production app, we would save to S3/Cloudinary and store the URL.
    # Here we store the base64 string for simplicity and modularity.
    user.face_image = face_image
    user.save()

    return jsonify({"message": "Identification photo uploaded successfully."}), 200
