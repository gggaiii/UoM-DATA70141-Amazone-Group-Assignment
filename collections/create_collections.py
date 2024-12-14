import json
import pandas as pd
import pprint
import os
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime


# Connect to the server:
con ="mongodb+srv://admin:admin@amazone.dodun.mongodb.net/"
client = MongoClient(con, serverSelectionTimeoutMS=5000)
try:
    print("Connected to the Server")
except Exception:
    print("Unable to connect to the server.")

db = client['Amazone']

#Reset the database
collections = {
    "warehouses": "warehouses.json",
    # "products": "products.json",
    # "freshProducts": "freshProducts.json",
    # "others": "others.json",
    # "books": "books.json",
    # "cds": "cds.json",
    # "mobilePhones": "mobilePhones.json",
    # "homeAppliances": "homeAppliances.json",
    # "dailyInventory": "dailyInventory.json",
    "stores": "stores.json",
    # "customerAddresses": "customerAddresses.json",
    "partners": "partners.json",
    # "customers": "customers.json",
    # "customerRatings": "customerRatings.json",
    # "pastOrders": "pastOrders.json",
    # "pastOrderItems": "pastOrderItems.json"
}

for collection in collections.keys():
    db[collection].drop()



#Load the data

def convert_ids_to_objectid(data):
    if isinstance(data, list):
        return [convert_ids_to_objectid(item) for item in data]
    elif isinstance(data, dict):
        for key, value in data.items():
            if key.endswith("ID") or key.endswith("id"):
                try:
                    data[key] = ObjectId(value)
                except Exception:
                    pass
            else:
                data[key] = convert_ids_to_objectid(value)
        return data
    else:
        return data

def convert_dates_to_isodate(data):
    if isinstance(data, list):
        return [convert_dates_to_isodate(item) for item in data]
    elif isinstance(data, dict):
        for key, value in data.items():
            if key.lower().endswith("date"):
                try:
                    data[key] = datetime.fromisoformat(value.replace("Z", ""))
                except Exception:
                    pass
            else:
                data[key] = convert_dates_to_isodate(value)
        return data
    else:
        return data
    
for collection, file in collections.items():
    file = open(f"Amazone-Group-Assignment/collections/{file}")
    data = json.load(file)
    data = convert_ids_to_objectid(data)
    data = convert_dates_to_isodate(data)
    if data:
        db[f"{collection}"].insert_many(data)

print("Data has been loaded successfully")

    
