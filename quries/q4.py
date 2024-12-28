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

def calculate_sales_and_inventory(collection_past_order_items):
    pipeline = [
        {
            '$unwind': {
                'path': '$items'  
            }
        }, {
            "$lookup": {
                "from": "products",
                "localField": "items.productID",
                "foreignField": "_id",
                "as": "product_info"
            }
        }, {
            "$unwind": {
                "path": "$product_info"
            }
        }, {
            "$match": {
                "product_info.productType": "Fresh"  # choose productType is Fresh
            }
        }, {
            "$group": {
                "_id": "$items.productID",  # group by productID
                "totalsaleQuantity": {"$sum": "$items.itemQuantity"},  
                "productName": {"$first": "$items.productName"},  
                "productType": {"$first": "$product_info.productType"} 
            }
        }, {
            "$lookup": {
                "from": "stores",
                "let": {"productID": "$_id"},
                "pipeline": [
                    {"$unwind": "$groceryItems"},
                    {"$match": {"$expr": {"$eq": ["$groceryItems.productID", "$$productID"]}}},
                    {"$group": {
                        "_id": "$groceryItems.productID",
                        "totalstoreQuantity": {"$sum": "$groceryItems.quantityInStore"}
                    }}
                ],
                "as": "inventory"
            }
        }, {
            "$unwind": {
                "path": "$inventory",
                "preserveNullAndEmptyArrays": True
            }
        }, {
            "$project": {
                "_id": 0,
                "productID": "$_id",
                "productName": 1,
                "productType": 1,
                "totalsaleQuantity": 1,
                "totalstoreQuantity": {"$ifNull": ["$inventory.totalstoreQuantity", 0]}
            }
        }
    ]

    result = collection_past_order_items.aggregate(pipeline)
    return list(result)

def visualize_data(data):
    product_names = [item['productName'] for item in data]
    totalsale_quantities = [item['totalsaleQuantity'] for item in data]
    totalstore_quantities = [item['totalstoreQuantity'] for item in data]

    x = range(len(product_names))

    # both sales and inventory
    plt.figure(figsize=(14, 7))
    plt.bar(x, totalsale_quantities, width=0.4, label='Total Sale Quantity', align='center')
    plt.bar(x, totalstore_quantities, width=0.4, label='Total Store Quantity', align='edge')
    plt.xlabel('Product Name')
    plt.ylabel('Quantity')
    plt.title('Product Sales and Inventory')
    plt.xticks(x, product_names, rotation='vertical')
    plt.legend()
    plt.tight_layout()
    plt.savefig('combined_sales_inventory.png')
    plt.show()

    # sales:
    plt.figure(figsize=(14, 7))
    plt.bar(x, totalsale_quantities, width=0.4, label='Total Sale Quantity', align='center')
    plt.xlabel('Product Name')
    plt.ylabel('Quantity')
    plt.title('Product Sales')
    plt.xticks(x, product_names, rotation='vertical')
    plt.legend()
    plt.tight_layout()
    plt.savefig('sales.png')
    plt.show()

    # inventory:
    plt.figure(figsize=(14, 7))
    plt.bar(x, totalstore_quantities, width=0.4, label='Total Store Quantity', align='center')
    plt.xlabel('Product Name')
    plt.ylabel('Quantity')
    plt.title('Product Inventory')
    plt.xticks(x, product_names, rotation='vertical')
    plt.legend()
    plt.tight_layout()
    plt.savefig('inventory.png')
    plt.show()

def main():
    client = connect_to_mongo()
    db = client['Amazone']
    collection_past_order_items = db['pastOrderItems']
    collection_store = db['stores']

    # Calculate the sales volume and inventory of each product
    sales_and_inventory = calculate_sales_and_inventory(collection_past_order_items)
    print("Sales and Inventory:", sales_and_inventory)

    # store the data in a json file
    save_to_json(sales_and_inventory, 'sales_and_inventory.json')

    # visualize the data
    visualize_data(sales_and_inventory)

if __name__ == "__main__":
    main()
