import sys
import os
sys.path.append(os.getcwd())

from app import app
from models.database import User, Department

with app.app_context():
    rasayani_dept = Department.objects(name__icontains='Rasayani').first()
    if not rasayani_dept:
        print("ERROR: Rasayani Department not found.")
    else:
        print(f"Rasayani Dept ID: {rasayani_dept.id}")
        officers = User.objects(role='police', department=rasayani_dept.id).all()
        print(f"Found {len(officers)} officers linked to Rasayani Dept")
        for o in officers:
            print(f" - ID: {o.id}, Name: '{o.name}', Email: '{o.email}'")
        
        # Check officers with 'Rasayani' in text but not linked
        other_officers = User.objects(role='police', department__ne=rasayani_dept.id).all()
        for o in other_officers:
            if 'Rasayani' in str(o.name) or (o.police_station and 'Rasayani' in o.police_station):
                print(f" - UNLINKED MATCH: {o.name} (Station: {o.police_station})")
