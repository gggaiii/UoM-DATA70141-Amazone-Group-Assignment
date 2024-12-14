import json
import os
import pprint
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# Connect to MongoDB
def connect_to_db():
    connection_str = "mongodb+srv://admin:admin@amazone.dodun.mongodb.net/"
    client = MongoClient(connection_str, serverSelectionTimeoutMS=5000)
    print("Connected to the server")
    return client['Amazone']

def get_customer_address(db, customer_id):
    """Retrieve customer shipping address."""
    pipeline = [
        {"$match": {"_id": ObjectId(customer_id)}},
        {"$lookup": {
            "from": "customerAddresses",
            "localField": "addresstype.shippingAddressID",
            "foreignField": "_id",
            "as": "shipping_address"
        }},
        {"$unwind": {"path": "$shipping_address", "preserveNullAndEmptyArrays": True}},
        {"$project": {"shipping_address": 1}}
    ]
    result = list(db.customers.aggregate(pipeline))
    return result[0]["shipping_address"] if result else None


def find_nearest_stores(db, customer_location, limit=5):
    """Find nearest stores to a customer's location."""
    pipeline = [
        {"$geoNear": {
            "near": {"type": "Point", "coordinates": [customer_location["longitude"], customer_location["latitude"]]},
            "distanceField": "distance",
            "spherical": True
        }},
        {"$limit": limit}
    ]
    return list(db.stores.aggregate(pipeline))

def main():
    client = connect_to_db()
    db = client["Amazone"]

    customers = ['John Doe', 'Kim Jane']
    all_results = []

    for customer_data in customers:
        customer = db.customers.find_one({"name": customer_data})

        customer_address = get_customer_address(db, customer["_id"])
        # print(customer_address) 

        customer_location = customer_address

        nearest_stores = find_nearest_stores(db, customer_location)

        if not nearest_stores:
            print("No nearby stores found.")
            continue

        store_ids = [store["_id"] for store in nearest_stores]

        # Fetch fresh products from the nearest stores
        fresh_products = []
        for store in nearest_stores:
            store_products = db.stores.find_one({"_id": store["_id"]}, {"groceryItems": 1})
            if store_products and "groceryItems" in store_products:
                product_ids = [item["productID"] for item in store_products["groceryItems"]]
                products = list(db.freshProducts.find({"_id": {"$in": product_ids}}))
                fresh_products.append({
                    "store_id": store["_id"],
                    "store_address": store["storeAddress"],
                    "products": products
                })

        # Display results
        result = {
            "customer": customer_data,
            "nearest 5 stores": [
                {
                    #"store_id": str(store["_id"]),
                    "address": store["storeAddress"]["streetName"],
                    "postcode": store["storeAddress"]["postCode"]
                } for store in nearest_stores
            ],
            "fresh products available": [
                {
                    "productName": product["productName"],
                    "description": product["description"],
                    "price": product["productSpecifics"]["costInMorrizon"]
                }
                for store in fresh_products
                for product in store["products"]
            ]
        }
        all_results.append(result)

    # Path to the directory and file
    directory = "jsons/"
    file_path = os.path.join(directory, "customer_searching.json")

    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save the results to a JSON file
    with open(file_path, "w") as file:
        json.dump(all_results, file, indent=4)

    print(f"Results saved to {file_path}")
    pprint.pprint(all_results)


if __name__ == "__main__":
    main()



