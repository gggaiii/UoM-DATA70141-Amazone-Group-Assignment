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


# Helper Functions
def haversine_distance(coord1, coord2):
    """Calculates Haversine distance (in meters) between two geographical points."""
    R = 6371000  # Radius of Earth in meters
    lon1, lat1 = radians(coord1[0]), radians(coord1[1])
    lon2, lat2 = radians(coord2[0]), radians(coord2[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 4 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def calculate_delivery_distance(driver_location, store_location, customer_location):
    """Calculates total delivery distance (driver → store → customer)."""
    driver_to_store = haversine_distance(
        (driver_location["longitude"], driver_location["latitude"]),
        (store_location["longitude"], store_location["latitude"])
    )
    store_to_customer = haversine_distance(
        (store_location["longitude"], store_location["latitude"]),
        (customer_location["longitude"], customer_location["latitude"])
    )
    return driver_to_store + store_to_customer


# MongoDB Queries
def find_customers_buying_fresh(db):
    """Find customers who buy fresh products."""
    pipeline = [
        {"$unwind": {"path": "$currentOrders", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$currentOrders.products", "preserveNullAndEmptyArrays": True}},
        {"$match": {"currentOrders.products.productType": {"$regex": "^fresh$", "$options": "i"}}},
        {"$project": {"ID": {"$toString": "$_id"}, "Name": "$name", "Products": "$currentOrders.products"}}
    ]
    return list(db.customers.aggregate(pipeline))


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


def check_product_availability(db, stores, product_name):
    """Check if a product is available in the given stores."""
    for store in stores:
        for item in store.get("groceryItems", []):
            if item.get("productName", "").lower() == product_name.lower():
                return store
    return None


def get_driver_address_and_assign(db, customer_id, store_location):
    """Find and assign the nearest driver to the delivery."""
    pipeline = [
        {"$geoNear": {
            "near": {"type": "Point", "coordinates": [store_location["longitude"], store_location["latitude"]]},
            "distanceField": "distance",
            "spherical": True,
            "query": {"driverStatus.isActive": True, "driverStatus.onRoute": False}
        }},
        {"$limit": 1}
    ]
    nearest_driver_result = list(db.partners.aggregate(pipeline))
    if not nearest_driver_result:
        return None, None

    driver = nearest_driver_result[0]
    db.partners.update_one({"_id": driver["_id"]}, {"$set": {"driverStatus.onRoute": True}})
    db.customers.update_one({"_id": ObjectId(customer_id)}, {"$set": {"currentOrders.0.deliveryPartnerID": driver["_id"]}})
    return driver, driver.get("driverAddress")


def create_new_order(db, customer_id, product_name, quantity, store, driver):
    """Create a new current order for the customer."""
    new_order = {
        "orderID": ObjectId(),
        "deliveryPartnerID": driver["_id"],
        "products": [{"productName": product_name, "quantityBought": quantity}],
        "storeID": store["_id"],
        "orderDate": datetime.now().isoformat()
    }
    db.customers.update_one({"_id": ObjectId(customer_id)}, {"$push": {"currentOrders": new_order}})
    return new_order


def generate_order_output(order_time, customer, product_name, quantity, store, driver, delivery_distance, total_time):
    """Generate a formatted dictionary for the order."""
    return {
        "Order Details": {
            "Time": order_time,
            "Customer": customer["name"],
            "Product": product_name,
            "Quantity": quantity,
            "Store": {
                "Store ID": str(store["_id"]),
                "Location": store["storeAddress"]["streetName"],
                "City": store["storeAddress"]["city"],
                "Postcode": store["storeAddress"]["postCode"]
            },
            "Assigned Driver": {
                "Name": driver["driverName"],
                "Rating": driver["statistics"]["averageRating"],
                "TotalDeliveries": driver["statistics"]["totalDeliveries"]
            },
            "Delivery Details": {
                "Total Distance (miles)": round(delivery_distance / 750, 2),
                "Estimated Delivery Time (minutes)": int(total_time)
            }
        }
    }


# Order Processing
def process_order(db, customer, product_name, quantity):
    """Processes a new order for the customer."""
    customer_location = {"longitude": customer["shipping_address"]["longitude"], "latitude": customer["shipping_address"]["latitude"]}
    nearest_stores = find_nearest_stores(db, customer_location)
    store = check_product_availability(db, nearest_stores, product_name)
    if not store:
        print(f"{product_name} not available for customer {customer['name']}.")
        return None

    driver, _ = get_driver_address_and_assign(db, customer["_id"], store["location"])
    if not driver:
        print(f"No driver available for {customer['name']}.")
        return None

    new_order = create_new_order(db, customer["_id"], product_name, quantity, store, driver)
    delivery_distance = calculate_delivery_distance(driver["location"], store["location"], customer_location)
    total_time = delivery_distance / 750 / 30 * 60 * 0.5
    return generate_order_output(new_order["orderDate"], customer, product_name, quantity, store, driver, delivery_distance, total_time)


# Main Function
def main():
    db = connect_to_db()
    db.partners.create_index([("location", "2dsphere")])
    db.stores.create_index([("location", "2dsphere")])

    customers_and_products = [
        {"name": "Olivia Wilde", "desired_product": "Almond Danish", "quantity": 2},
        {"name": "Nathan Drake", "desired_product": "Almond Danish", "quantity": 3}
    ]

    all_orders = []
    for customer_data in customers_and_products:
        customer = db.customers.find_one({"name": customer_data["name"]})
        if not customer:
            print(f"Customer {customer_data['name']} not found.")
            continue

        customer["shipping_address"] = get_customer_address(db, customer["_id"])
        if not customer["shipping_address"]:
            print(f"Shipping address not found for {customer['name']}.")
            continue

        order_output = process_order(db, customer, customer_data["desired_product"], customer_data["quantity"])
        if order_output:
            all_orders.append(order_output)

    pprint.pprint(all_orders)
    save_orders_to_file(all_orders, './Data_Science/Database/Assignment2/jsons/new_order_details.json')


def save_orders_to_file(orders, filepath):
    """Save orders to a JSON file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(orders, f, indent=4)
        print(f"Orders saved to {filepath}")
    except Exception as e:
        print(f"Error saving orders: {e}")


if __name__ == "__main__":
    main()
