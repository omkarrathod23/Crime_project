import requests
import json

# We'll use a local request to port 5000
BASE_URL = "http://localhost:5000"

def test_api():
    # Login to get token
    login_data = {"email": "officer@panvel.gov", "password": "officer123"}
    # Wait, the user is a citizen. Let's find a citizen.
    
    # Let's try to get a citizen from DB
    from app import app
    from models.database import User
    with app.app_context():
        citizen = User.objects(role='citizen').first()
        if not citizen:
            print("No citizen found in DB!")
            return
        print(f"Testing for citizen: {citizen.email}")
        
        # We can create a token manually if we have the secret
        from extensions import jwt
        from flask_jwt_extended import create_access_token
        with app.test_request_context():
            token = create_access_token(identity=str(citizen.id))
            print(f"Token: {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}"}
    
    # Test nearest-stations
    url = f"{BASE_URL}/sos/nearest-stations?lat=18.98&lon=73.11"
    try:
        resp = requests.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Data: {resp.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
