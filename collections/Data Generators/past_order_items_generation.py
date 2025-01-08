import json
import random

# Load past orders, others, and fresh products data
with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/pastOrders.json') as f:
    past_orders = json.load(f)

with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/others.json') as f:
    others = json.load(f)

with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/freshProducts.json') as f:
    fresh_products = json.load(f)

# Combine others and fresh products into a single list
all_products = others + fresh_products

# Generate order items
order_items = []
for order in past_orders:
    order_id = order["_id"]
    num_items = random.randint(1, 4)
    items = []
    for item_id in range(1, num_items + 1):
        product = random.choice(all_products)
        items.append({
            "itemID": item_id,
            "productID": product["_id"],
            "productName": product["productName"],
            "itemQuantity": random.randint(1, 4)
        })
    order_items.append({
        "orderID": order_id,
        "items": items
    })

# Save the generated order items to a new JSON file
with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/pastOrderItems.json', 'w') as f:
    json.dump(order_items, f, indent=4)

    # Update total cost in past orders
    for order in order_items:
        order_id = order["orderID"]
        total_cost = 0
        for item in order["items"]:
            product_id = item["productID"]
            item_quantity = item["itemQuantity"]
            product = next((p for p in all_products if p["_id"] == product_id), None)
            if product:
                if "costInMorrizon" in product["productSpecifics"]:
                    total_cost += product["productSpecifics"]["costInMorrizon"] * item_quantity
                else:
                    total_cost += product["productSpecifics"]["averagePrice"] * item_quantity
        for past_order in past_orders:
            if past_order["_id"] == order_id:
                past_order["totalCost"] = total_cost

    # Save the updated past orders to the JSON file
    with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/pastOrders.json', 'w') as f:
        json.dump(past_orders, f, indent=4)