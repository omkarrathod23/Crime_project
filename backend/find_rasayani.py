import sys
import os
sys.path.append(os.getcwd())

from app import app
from models.database import Department

with app.app_context():
    rasayani = Department.objects(name__icontains='Rasayani').all()
    print(f"Found {len(rasayani)} matches for 'Rasayani'")
    for d in rasayani:
        print(f" - ID: {d.id}, Name: '{d.name}', City: '{d.city}'")
