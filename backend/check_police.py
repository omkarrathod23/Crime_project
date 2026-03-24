import sys
import os
sys.path.append(os.getcwd())

from app import app
from models.database import User

with app.app_context():
    police_users = User.objects(role='police').all()
    print(f"Total Police Users: {len(police_users)}")
    for u in police_users:
        dept_name = u.department.name if u.department else "NONE"
        print(f" - ID: {u.id}, Name: '{u.name}', Station Field: '{u.police_station}', Linked Dept: '{dept_name}'")
