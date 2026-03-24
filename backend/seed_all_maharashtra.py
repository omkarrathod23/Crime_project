from app import app
from models.database import Department
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comprehensive List of Maharashtra Police Commissionerates and District HQs
maharashtra_police_hubs = [
    # Commissionerates
    {"name": "Mumbai Police Commissionerate", "city": "Mumbai", "district": "Mumbai City", "latitude": 18.9438, "longitude": 72.8361},
    {"name": "Navi Mumbai Police HQ", "city": "Navi Mumbai", "district": "Thane", "latitude": 19.0330, "longitude": 73.0297},
    {"name": "Pune Police Commissionerate", "city": "Pune", "district": "Pune", "latitude": 18.5204, "longitude": 73.8567},
    {"name": "Nagpur Police Commissionerate", "city": "Nagpur", "district": "Nagpur", "latitude": 21.1458, "longitude": 79.0882},
    {"name": "Thane Police Commissionerate", "city": "Thane", "district": "Thane", "latitude": 19.2183, "longitude": 72.9781},
    {"name": "Nashik Police Commissionerate", "city": "Nashik", "district": "Nashik", "latitude": 19.9975, "longitude": 73.7898},
    {"name": "Sambhaji Nagar Police Commissionerate", "city": "Aurangabad", "district": "Aurangabad", "latitude": 19.8762, "longitude": 75.3433},
    {"name": "Solapur Police Commissionerate", "city": "Solapur", "district": "Solapur", "latitude": 17.6599, "longitude": 75.9064},
    {"name": "Amravati Police Commissionerate", "city": "Amravati", "district": "Amravati", "latitude": 20.9320, "longitude": 77.7523},
    {"name": "Pimpri-Chinchwad Police HQ", "city": "Pimpri-Chinchwad", "district": "Pune", "latitude": 18.6298, "longitude": 73.7997},
    {"name": "Mira-Bhayandar Vasai-Virar Police HQ", "city": "Mira Bhayandar", "district": "Thane", "latitude": 19.2813, "longitude": 72.8557},

    # District HQs
    {"name": "Ahmednagar Police HQ", "city": "Ahmednagar", "district": "Ahmednagar", "latitude": 19.0948, "longitude": 74.7480},
    {"name": "Akola Police HQ", "city": "Akola", "district": "Akola", "latitude": 20.7002, "longitude": 77.0082},
    {"name": "Beed Police HQ", "city": "Beed", "district": "Beed", "latitude": 18.9891, "longitude": 75.7601},
    {"name": "Bhandara Police HQ", "city": "Bhandara", "district": "Bhandara", "latitude": 21.1667, "longitude": 79.6500},
    {"name": "Buldhana Police HQ", "city": "Buldhana", "district": "Buldhana", "latitude": 20.5333, "longitude": 76.1833},
    {"name": "Chandrapur Police HQ", "city": "Chandrapur", "district": "Chandrapur", "latitude": 19.9510, "longitude": 79.2961},
    {"name": "Dhule Police HQ", "city": "Dhule", "district": "Dhule", "latitude": 20.9042, "longitude": 74.7749},
    {"name": "Gadchiroli Police HQ", "city": "Gadchiroli", "district": "Gadchiroli", "latitude": 20.1833, "longitude": 80.0000},
    {"name": "Gondia Police HQ", "city": "Gondia", "district": "Gondia", "latitude": 21.4597, "longitude": 80.1947},
    {"name": "Hingoli Police HQ", "city": "Hingoli", "district": "Hingoli", "latitude": 19.7167, "longitude": 77.1500},
    {"name": "Jalgaon Police HQ", "city": "Jalgaon", "district": "Jalgaon", "latitude": 21.0077, "longitude": 75.5626},
    {"name": "Jalna Police HQ", "city": "Jalna", "district": "Jalna", "latitude": 19.8410, "longitude": 75.8864},
    {"name": "Kolhapur Police HQ", "city": "Kolhapur", "district": "Kolhapur", "latitude": 16.7050, "longitude": 74.2433},
    {"name": "Latur Police HQ", "city": "Latur", "district": "Latur", "latitude": 18.4088, "longitude": 76.5604},
    {"name": "Nanded Police HQ", "city": "Nanded", "district": "Nanded", "latitude": 19.1628, "longitude": 77.3183},
    {"name": "Nandurbar Police HQ", "city": "Nandurbar", "district": "Nandurbar", "latitude": 21.3700, "longitude": 74.2500},
    {"name": "Osmanabad Police HQ", "city": "Osmanabad", "district": "Osmanabad", "latitude": 18.1700, "longitude": 76.0500},
    {"name": "Palghar Police HQ", "city": "Palghar", "district": "Palghar", "latitude": 19.6936, "longitude": 72.7655},
    {"name": "Parbhani Police HQ", "city": "Parbhani", "district": "Parbhani", "latitude": 19.2667, "longitude": 76.7667},
    {"name": "Ratnagiri Police HQ", "city": "Ratnagiri", "district": "Ratnagiri", "latitude": 16.9902, "longitude": 73.3120},
    {"name": "Sangli Police HQ", "city": "Sangli", "district": "Sangli", "latitude": 16.8524, "longitude": 74.5815},
    {"name": "Satara Police HQ", "city": "Satara", "district": "Satara", "latitude": 17.6805, "longitude": 73.9803},
    {"name": "Sindhudurg Police HQ", "city": "Oros", "district": "Sindhudurg", "latitude": 16.1200, "longitude": 73.6800},
    {"name": "Wardha Police HQ", "city": "Wardha", "district": "Wardha", "latitude": 20.7453, "longitude": 78.6022},
    {"name": "Washim Police HQ", "city": "Washim", "district": "Washim", "latitude": 20.1000, "longitude": 77.1333},
    {"name": "Yavatmal Police HQ", "city": "Yavatmal", "district": "Yavatmal", "latitude": 20.3888, "longitude": 78.1204},
    {"name": "Panvel Police Station", "city": "Panvel", "district": "Raigad", "latitude": 18.9894, "longitude": 73.1175},
    {"name": "Alibaug Police HQ", "city": "Alibaug", "district": "Raigad", "latitude": 18.6417, "longitude": 72.8717}
]

def seed_state_wide():
    with app.app_context():
        count = 0
        for hub in maharashtra_police_hubs:
            existing = Department.objects(name=hub["name"]).first()
            if not existing:
                dept = Department(
                    name=hub["name"],
                    city=hub["city"],
                    district=hub["district"],
                    latitude=hub["latitude"],
                    longitude=hub["longitude"],
                    state="Maharashtra"
                )
                dept.save()
                count += 1
            else:
                existing.latitude = hub["latitude"]
                existing.longitude = hub["longitude"]
                existing.district = hub["district"]
                existing.city = hub["city"]
                existing.save()
        
        logger.info(f"Maharashtra State-wide Seeding Complete: {count} new hubs added, {len(maharashtra_police_hubs) - count} updated.")

if __name__ == "__main__":
    seed_state_wide()
