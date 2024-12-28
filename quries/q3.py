import json
from pymongo import MongoClient

#connect to mongodb:
def connect_to_mongo():
    con = "mongodb+srv://admin:admin@amazone.dodun.mongodb.net/"
    client = MongoClient(con, serverSelectionTimeoutMS=5000)
    try:
        print("Connected to the Server")
    except Exception:
        print("Unable to connect to the server.")
    return client

'''
    Optional conditional field: orderCount: customer's order count 
'''
def sucess_current_order(database, condition=None):
    collection = database['customers']
    pipeline = [
        {
            '$unwind': {
                'path': '$currentOrders'  # expand currentOrders
            }
        }, {
            "$group": {
                "_id": "$_id",  # group by _id
                "name": {"$first": "$name"},  # name
                "balance": {"$first": {"$toInt": "$balance"}},  # transfrom balance to int
                "totalCostSum": {"$sum": "$currentOrders.totalcost"},  # sum totalcost 
                "orders": {"$push": "$currentOrders"},  # products
                "orderCount": {"$sum": 1}  # calculate order count
            }
        }, {
            "$match": {  #Filter items where totalCostSum is less than balance
                "$expr": {"$lt": ["$totalCostSum", "$balance"]}
            }
        }, {
            "$project": {  
                "_id": 1,
                "name": 1,
                "balance": 1,
                "totalCostSum": 1,
                "orders": 1,
                "orderCount": 1  
            }
        }
    ]

    if condition:
        pipeline.append({
            "$match": condition
        })
    

    # Run an aggregated query
    current_order = collection.aggregate(pipeline)
    # format the output
    formatted_orders = []
    for result in current_order:
        formatted_order = {
            "Customer": result["name"],
            "Balance": result["balance"],
            "Total Order Cost": result["totalCostSum"],
            "Order Count": result["orderCount"],
            "Orders": []
        }
        for order in result["orders"]:
            formatted_order_order = {
                "Order ID": str(order.get("orderID", "N/A")),
                "OrderCost": order.get("totalcost", "N/A"),
                "Products": []
            }
            for product in order["products"]:
                formatted_order_order["Products"].append({
                    "Product": product.get("productName", "N/A"),
                    "Quantity": product.get("quantityBought", "N/A"),
                    "productID": str(product.get("productID", "N/A")),
                    "productType": product.get("productType", "N/A")
                })
            formatted_order["Orders"].append(formatted_order_order)
        formatted_orders.append(formatted_order)
    return formatted_orders

def multi_query(*queries):
    combined_results = {}
    for i, query in enumerate(queries, start=1):
        combined_results[f"Query{i}"] = query
    return combined_results

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    client = connect_to_mongo()
    db = client['Amazone']

    q1 = sucess_current_order(db)

    condition1 = {"orderCount": {"$gt": 5}} 
    q2 = sucess_current_order(db, condition1)

    condition2 = {"orders.products.productType": "Fresh"} 
    q3 = sucess_current_order(db, condition2)

    combined_results = multi_query(q1, q2, q3)


    # output to json file
    save_to_json(combined_results, 'Q3.json')


if __name__ == "__main__":
    main()




