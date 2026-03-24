import pymongo
from bson import ObjectId

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["crime_management_v2"]
users = db["users"].find({}, {"name": 1, "email": 1, "role": 1})

print("--- USERS ---")
for user in users:
    print(f"Name: {user.get('name')}, Email: {user.get('email')}, Role: {user.get('role')}")
