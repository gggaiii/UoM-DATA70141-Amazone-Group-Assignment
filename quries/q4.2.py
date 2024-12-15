import json
import matplotlib.pyplot as plt
from pymongo import MongoClient
from bson import ObjectId

#connect to mongodb:
def connect_to_mongo():
    con = "mongodb+srv://admin:admin@amazone.dodun.mongodb.net/"
    client = MongoClient(con, serverSelectionTimeoutMS=5000)
    try:
        print("Connected to the Server")
    except Exception:
        print("Unable to connect to the server.")
    return client

def save_to_json(data, filename):
    def convert_objectid(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, list):
            return [convert_objectid(item) for item in obj]
        if isinstance(obj, dict):
            return {key: convert_objectid(value) for key, value in obj.items()}
        return obj

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(convert_objectid(data), f, ensure_ascii=False, indent=4)

def calculate_product_sales(collection):
    pipeline = [
        {
            '$unwind': {
                'path': '$items'
            }
        }, {
            "$group": {
                "_id": "$items.productID",  
                "totalsaleQuantity": {"$sum": "$items.itemQuantity"},  
                "productName": {"$first": "$items.productName"}  
            }
        }, {
            "$project": { 
                "_id": 0,
                "productID": "$_id",
                "productName": 1,
                "totalsaleQuantity": 1
            }
        }
    ]


    result = collection.aggregate(pipeline)
    return list(result)

def calculate_product_inventory(collection):
    pipeline = [
        {
            '$unwind': {
                'path': '$groceryItems'  
            }
        }, {
            "$group": {
                "_id": "$groceryItems.productID",  
                "totalstoreQuantity": {"$sum": "$groceryItems.quantityInStore"},  
                "productName": {"$first": "$groceryItems.productName"}  
            }
        }, {
            "$project": {  
                "_id": 0,
                "productID": "$_id",
                "productName": 1,
                "totalstoreQuantity": 1
            }
        }
    ]

    result = collection.aggregate(pipeline)
    return list(result)

def visualize_data(data, title, filename):
    product_names = [item['productName'] for item in data]
    quantities = [item['totalsaleQuantity'] if 'totalsaleQuantity' in item else item['totalstoreQuantity'] for item in data]

    x = range(len(product_names))

    plt.figure(figsize=(14, 7))
    plt.bar(x, quantities, width=0.4, align='center')
    plt.xlabel('Product Name')
    plt.ylabel('Quantity')
    plt.title(title)
    plt.xticks(x, product_names, rotation='vertical')
    plt.tight_layout()
    plt.savefig(filename)
    plt.show()

def main():
    client = connect_to_mongo()
    db = client['Amazone']
    collection_past_order_items = db['pastOrderItems']
    collection_store = db['stores']

 
    product_sales = calculate_product_sales(collection_past_order_items)
    print("Product Sales:", product_sales)

  
    product_inventory = calculate_product_inventory(collection_store)
    print("Product Inventory:", product_inventory)

  
    save_to_json(product_sales, 'product_sales.json')
    save_to_json(product_inventory, 'product_inventory.json')

  
    visualize_data(product_sales, 'Product Sales', 'sales.png')
    visualize_data(product_inventory, 'Product Inventory', 'inventory.png')

if __name__ == "__main__":
    main()