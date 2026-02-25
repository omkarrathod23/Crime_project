from app import app
from models.database import db, User

with app.app_context():
    users = User.query.all()
    for u in users:
        print(f"{u.email} ({u.role})")
