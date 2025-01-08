import json
import random

def write_to_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def read_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

customers = read_json_file(
    '/Users/mikepham/Desktop/Databases/Coursework 2/collections/customers.json')

others = read_json_file(
    '/Users/mikepham/Desktop/Databases/Coursework 2/collections/others.json')

fresh_products = read_json_file(
    '/Users/mikepham/Desktop/Databases/Coursework 2/collections/freshProducts.json')

products = read_json_file(
    '/Users/mikepham/Desktop/Databases/Coursework 2/collections/products.json')


temp_others = []

for product in others:
    product_id = product['_id']
    product_name = product['productName']
    product_category = product['categoryName']
    average_rating = next((p['averageRating'] for p in products if p['_id'] == product_id), None)
    
    temp_others.append({
        '_id': product_id,
        'productName': product_name,
        'product_category': product_category,
        'averageRating': average_rating
    })


write_to_json_file(
    '/Users/mikepham/Desktop/Databases/Coursework 2/collections/tempOthers.json', temp_others)

temp_freshProducts = []

for product in fresh_products:
    product_id = product['_id']
    product_name = product['productName']
    product_category = product['productSpecifics']['productCategory']
    average_rating = next((p['averageRating'] for p in products if p['_id'] == product_id), None)
    
    temp_freshProducts.append({
        '_id': product_id,
        'productName': product_name,
        'product_category': product_category,
        'averageRating': average_rating
    })

write_to_json_file(
    '/Users/mikepham/Desktop/Databases/Coursework 2/collections/tempfreshProducts.json', temp_freshProducts)

temp_products = temp_others + temp_freshProducts

write_to_json_file(
    '/Users/mikepham/Desktop/Databases/Coursework 2/collections/tempProducts.json', temp_products)

def get_product_info(product_id):
    return next((product for product in temp_products if product['_id'] == product_id), None)

def generate_recommended_products(customers):
    for customer in customers:
        customer["recommendedProducts"] = []
        for order in customer['currentOrders']:
            for item in order["products"]:
                current_product = get_product_info(item["productID"])
                rec_products = [
                    {key: product[key] for key in product if key != 'product_category'}
                    for product in temp_products
                    if product['product_category'] == current_product['product_category'] and product['averageRating'] >= current_product['averageRating']
                ]
                for rec_product in rec_products:
                    rec_product['productID'] = rec_product.pop('_id')
                customer["recommendedProducts"].extend(rec_products[:1])  # Limit to 1 item per 1 item ordered

    return customers

generate_recommended_products(customers)

write_to_json_file(
    '/Users/mikepham/Desktop/Databases/Coursework 2/collections/customers.json', customers)



                



            