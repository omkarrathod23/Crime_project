import sys
import os
sys.path.append(os.getcwd())

from app import app
from models.database import User

with app.app_context():
    user = User.objects(id='69c16796acf6612ad7be533e').first()
    if user:
        print(f"Found User: Name={user.name}, Role={user.role}")
    else:
        print("User not found.")
