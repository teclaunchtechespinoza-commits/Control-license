import os
from pymongo import MongoClient

URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "licenser")
COLS = ["licenses","notifications","notification_queue","users"]

client = MongoClient(URI)
db = client[DB_NAME]

print(f"== Audit DB: {DB_NAME}")
for col in COLS:
    if col not in db.list_collection_names():
        continue
    missing = db[col].count_documents({"$or":[{"tenant_id":{"$exists":False}},{"tenant_id":None}]})
    print(f"[{col}] missing tenant_id: {missing}")
