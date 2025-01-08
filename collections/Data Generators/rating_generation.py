import json
import random


with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/customers.json', 'r') as f:
    customers = json.load(f)

with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/others.json', 'r') as f:
    others_products = json.load(f)

with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/freshProducts.json', 'r') as f:
    fresh_products = json.load(f)

all_products = others_products + fresh_products

customer_ratings = []

for customer in customers:
    ratings = []
    sampled_products = random.sample(all_products, 3)
    for product in sampled_products:
        rating = 8 if product in others_products else 9
        ratings.append({
            "productid": product["_id"],
            "rating": rating
        })
    customer_ratings.append({
        "customerID": customer["_id"],
        "customerRatings": ratings
    })

with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/customerRatings.json', 'w') as f:
    json.dump(customer_ratings, f, indent=4)


#Update the last two customers to rate all products
others_product_ids = {product['_id'] for product in others_products}
fresh_products_ids = {product['_id'] for product in fresh_products}

all_ratings = []
for product_id in others_product_ids:
    all_ratings.append({"productid": product_id, "rating": 8})
for product_id in fresh_products_ids:
    all_ratings.append({"productid": product_id, "rating": 9})

customer_ratings[-2]['customerRatings'] = all_ratings
customer_ratings[-1]['customerRatings'] = all_ratings

with open('/Users/mikepham/Desktop/Databases/Coursework 2/collections/customerRatings.json', 'w') as f:
    json.dump(customer_ratings, f, indent=4)