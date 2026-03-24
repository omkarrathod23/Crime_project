from app import app
from models.database import Department
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stations_data = [
    {
        "name": "Mumbai Police HQ",
        "city": "Mumbai",
        "district": "Mumbai City",
        "latitude": 18.9438,
        "longitude": 72.8361,
        "min_lat": 18.89, "max_lat": 19.00, "min_lon": 72.77, "max_lon": 72.90
    },
    {
        "name": "Pune Police Station",
        "city": "Pune",
        "district": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "min_lat": 18.45, "max_lat": 18.60, "min_lon": 73.75, "max_lon": 73.95
    },
    {
        "name": "Nagpur Police Station",
        "city": "Nagpur",
        "district": "Nagpur",
        "latitude": 21.1458,
        "longitude": 79.0882,
        "min_lat": 21.05, "max_lat": 21.25, "min_lon": 78.95, "max_lon": 79.20
    },
    {
        "name": "Nashik Police Station",
        "city": "Nashik",
        "district": "Nashik",
        "latitude": 19.9975,
        "longitude": 73.7898,
        "min_lat": 19.90, "max_lat": 20.10, "min_lon": 73.70, "max_lon": 73.90
    },
    {
        "name": "Panvel Police Station",
        "city": "Panvel",
        "district": "Raigad",
        "latitude": 18.9894,
        "longitude": 73.1175,
        "min_lat": 18.90, "max_lat": 19.10, "min_lon": 73.00, "max_lon": 73.20
    },
    {
        "name": "Rasayani Police Station",
        "city": "Rasayani",
        "district": "Raigad",
        "latitude": 18.9044,
        "longitude": 73.1842,
        "min_lat": 18.85, "max_lat": 18.95, "min_lon": 73.15, "max_lon": 73.25
    },
    {
        "name": "Thane Police Station",
        "city": "Thane",
        "district": "Thane",
        "latitude": 19.2183,
        "longitude": 72.9781,
        "min_lat": 19.15, "max_lat": 19.30, "min_lon": 72.90, "max_lon": 73.05
    }
]

def seed_stations():
    with app.app_context():
        for s in stations_data:
            existing = Department.objects(name=s["name"]).first()
            if existing:
                logger.info(f"Station {s['name']} already exists. Updating coordinates.")
                existing.latitude = s["latitude"]
                existing.longitude = s["longitude"]
                existing.district = s["district"]
                existing.city = s["city"]
                existing.save()
            else:
                logger.info(f"Creating new station: {s['name']}")
                dept = Department(**s)
                dept.save()
        logger.info("Maharashtra police stations seeded successfully.")

if __name__ == "__main__":
    seed_stations()
