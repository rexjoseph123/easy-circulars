import pymongo
import os
from dotenv import load_dotenv


load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")

MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"

try:
    mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()
    print("Successfully connected to MongoDB")

except Exception as e:
    print(f"Error connecting to MongoDB: {str(e)}")
    mongo_client = None
    db = None
    conversations_collection = None
