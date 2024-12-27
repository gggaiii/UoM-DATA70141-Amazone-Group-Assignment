from pymongo import MongoClient
import pprint
import matplotlib.pyplot as plt

# Connect to MongoDB
def connect_to_db():
    connection_str = "mongodb+srv://admin:admin@amazone.dodun.mongodb.net/"
    client = MongoClient(connection_str, serverSelectionTimeoutMS=5000)
    print("Connected to the server")
    return client['Amazone']

def get_lowest_inventory_products(db, limit=10):
    """Retrieve products with the lowest daily inventory."""
    pipeline = [
    {
        '$unwind': {
            'path': '$inventoryDetails'
        }
    }, {
        '$sort': {
            'inventoryDetails.QuantityInInventory': 1
        }
    }, {
        '$lookup': {
            'from': 'products', 
            'localField': 'inventoryDetails.productID', 
            'foreignField': '_id', 
            'as': 'product_details'
        }
    }, {
        '$match': {
            'product_details.productType': 'Fresh'
        }
    }, {
        '$limit': 10
    }, {
        '$lookup': {
            'from': 'freshProducts', 
            'localField': 'product_details._id', 
            'foreignField': '_id', 
            'as': 'fresh'
        }
    }, {
        '$unwind': {
            'path': '$fresh'
        }
    }, {
        '$project': {
            'productName': '$fresh.productName', 
            'inventoryQuantity': '$inventoryDetails.QuantityInInventory', 
            'date': '$inventoryDetails.date'
        }
    }
    ]
    return list(db.dailyInventory.aggregate(pipeline))

# visualize the data in graph by matplotlib
def save_graph(data, file_path):
    """Save a bar graph of the lowest inventory products."""
    # Extract product names and inventory quantity
    product_names = [product["productName"] for product in data]
    inventory_quantity = [product["inventoryQuantity"] for product in data]

    # Create the graph
    plt.figure(figsize=(10, 6))
    plt.barh(product_names, inventory_quantity, color='skyblue')
    plt.xlabel("Inventory Quantity")
    plt.ylabel("Product Name")
    plt.title("Products with the Lowest Daily Inventory")
    plt.gca().invert_yaxis()  # Highest inventory at the top
    plt.tight_layout()

    # Save the graph as an image file
    plt.savefig(file_path)

def main():
    db = connect_to_db()

    # Get products with the lowest daily inventory
    lowest_inventory_products = get_lowest_inventory_products(db, limit=10)
    if not lowest_inventory_products:
        print("No inventory data found.")
        return

    # Print results
    print("Products with the lowest daily inventory:")
    print(lowest_inventory_products)

    save_graph(lowest_inventory_products, "Data_Science/Database/Assignment2/outputs/lowest_inventory.png")

if __name__ == "__main__":
    main()
