from app import app
from services.location_service import assign_nearest_police_station
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

test_cases = [
    {
        "name": "Mumbai Test (Gateway of India)",
        "lat": 18.9220,
        "lon": 72.8347,
        "city": "Mumbai",
        "expected": "Mumbai Police HQ"
    },
    {
        "name": "Pune Test (Shaniwar Wada)",
        "lat": 18.5197,
        "lon": 73.8553,
        "city": "Pune",
        "expected": "Pune Police Station"
    },
    {
        "name": "Nagpur Test (Zero Mile Stone)",
        "lat": 21.1476,
        "lon": 79.0805,
        "city": "Nagpur",
        "expected": "Nagpur Police Station"
    },
    {
        "name": "Panvel Test",
        "lat": 18.9894,
        "lon": 73.1175,
        "city": "Panvel",
        "expected": "Panvel Police Station"
    },
    {
        "name": "Fallback Test (Unknown Coords, Known City)",
        "lat": 0,
        "lon": 0,
        "city": "Nashik",
        "expected": "Nashik Police Station"
    }
]

def verify_assignment():
    with app.app_context():
        passed = 0
        for tc in test_cases:
            logger.info(f"Testing: {tc['name']}")
            station = assign_nearest_police_station(tc['lat'], tc['lon'], tc['city'])
            if station and station["station_name"] == tc['expected']:
                logger.info(f"  PASS: Assigned to {station['station_name']}")
                passed += 1
            else:
                actual = station["station_name"] if station else "None"
                logger.error(f"  FAIL: Expected {tc['expected']}, got {actual}")
        
        logger.info(f"Verification Summary: {passed}/{len(test_cases)} cases passed.")

if __name__ == "__main__":
    verify_assignment()
