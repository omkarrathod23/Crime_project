import sys
import os
sys.path.append(os.getcwd())

from app import app
from models.database import SOSReport

with app.app_context():
    count = SOSReport.objects.count()
    print(f"Total SOS: {count}")
    for s in SOSReport.objects.order_by('-created_at').limit(10):
        print(f" - ID: {s.id}, User: {s.user.name}, Station: {s.assigned_station}, Status: '{s.status}', Created: {s.created_at}")
