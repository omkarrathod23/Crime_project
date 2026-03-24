import sys
import os
sys.path.append(os.getcwd())

from app import app
from models.database import Department

with app.app_context():
    depts = Department.objects.all()
    print(f"Total Departments: {len(depts)}")
    for d in depts:
        print(f" - Name: '{d.name}', City: '{d.city}', District: '{d.district}'")
