import os
import sys
# Add current dir to path
sys.path.append(os.getcwd())

from mongoengine import connect
from models.database import User

connect(host='mongodb://localhost:27017/crime_management')

email = 'ommiee@gmail.com'
u = User.objects(email=email).first()

if u:
    print(f"USER_FOUND: {u.name}")
    print(f"ROLE: {u.role}")
else:
    print("USER_NOT_FOUND")
