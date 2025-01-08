import json
import random
from bson import ObjectId
from datetime import datetime, timedelta

# Load customer data
with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/customer.json', 'r') as file:
    customers = json.load(file)

# Function to generate random date before 25/12/2024
def random_date():
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 24)
    return start_date + (end_date - start_date) * random.random()

# Generate past orders
past_orders = []
for customer in customers:
    for _ in range(5):
        past_order = {
            "_id": str(ObjectId()),
            "customerID": customer["_id"],
            "totalCost": 0,
            "orderDate": random_date().isoformat()
        }
        past_orders.append(past_order)

# Save past orders to file
with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/pastOrders.json', 'w') as file:
    json.dump(past_orders, file, indent=4)

