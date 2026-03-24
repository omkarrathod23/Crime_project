import os
import sys
# Add current dir to path
sys.path.append(os.getcwd())

from mongoengine import connect
from models.database import User
from werkzeug.security import generate_password_hash

connect(host='mongodb://localhost:27017/crime_management')

email = 'ommiee@gmail.com'
u = User.objects(email=email).first()

if not u:
    print(f"Creating new user {email}...")
    u = User(name='Ommiee', email=email)

u.password_hash = generate_password_hash('password123')
u.role = 'citizen'
u.save()

print(f"SUCCESS: User {email} reset with password 'password123' and role 'citizen'")
