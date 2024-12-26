import json
from pymongo import MongoClient
from bson import ObjectId
import csv
import matplotlib.pyplot as plt

# Connect to MongoDB
def connect_to_db():
    connection_str = "mongodb+srv://admin:admin@amazone.dodun.mongodb.net/"
    client = MongoClient(connection_str, serverSelectionTimeoutMS=5000)
    print("Connected to the server")
    return client['Amazone']

def get_highest_rated_products(db, limit=10):
    """Retrieve the highest-rated products."""
    pipeline = [
        {"$match": {"productType": 'Fresh'}},  # Ensure the field exists
        {"$sort": {"averageRating": -1}},  # Sort by averageRating in descending order
        {"$limit": limit},  # Limit the number of results
        {"$lookup": {
            "from": "freshProducts",
            "localField": "_id",
            "foreignField": "_id",
            "as": "product_details"
        }},
        {"$unwind": "$product_details"},
        {"$project": {
            "productName": "$product_details.productName",
            "averageRating": 1,
            "description": "$product_details.description"
        }}
    ]
    return list(db.products.aggregate(pipeline))

def save_to_json(data, file_path):
    """Save data to a JSON file, converting ObjectId to strings."""
    def convert_objectid(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4, default=convert_objectid)
    print(f"Results saved to {file_path}")

def save_graph(data, file_path):
    """Save a bar graph of the highest-rated products."""
    # Extract product names and ratings
    product_names = [product["productName"] for product in data]
    ratings = [product["averageRating"] for product in data]

    # Create the graph
    plt.figure(figsize=(10, 6))
    plt.barh(product_names, ratings, color='skyblue')
    plt.xlabel("Average Rating")
    plt.ylabel("Product Name")
    plt.title("Top Rated Products")
    plt.gca().invert_yaxis()  # Highest rating at the top
    plt.tight_layout()

    # Save the graph as an image file
    plt.savefig(file_path)
    print(f"Graph saved to {file_path}")
    plt.close()


def main():
    db = connect_to_db()

    # Get the highest-rated products
    highest_rated_products = get_highest_rated_products(db, limit=10)
    if not highest_rated_products:
        print("No products with ratings found.")
        return

    # Print results
    print("Highest-rated products:")
    for product in highest_rated_products:
        print(f"Product: {product['productName']}, Rating: {product['averageRating']}")

    # Save results to JSON file
    save_to_json(highest_rated_products, "Data_Science/Database/Assignment2/jsons/highest_rated_products.json")

    # Save the graph
    save_graph(highest_rated_products, "Data_Science/Database/Assignment2/outputs/highest_rated_products_graph.png")

if __name__ == "__main__":
    main()
