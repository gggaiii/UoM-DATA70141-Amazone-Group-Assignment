from pymongo import MongoClient, GEOSPHERE
from datetime import datetime
import requests
from bson.objectid import ObjectId

class EcommerceSystem:
    def __init__(self, connection_string):
        self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        try:
            print("Connected to the Server")
        except Exception:
            print("Unable to connect to the server.")
        self.db = self.client['Amazone']
        
        # Create necessary indexes including warehouse geolocation
        self.db.Partners.create_index([("location", GEOSPHERE)])
        self.db.Store.create_index([("location", GEOSPHERE)])
        self.db.Warehouse.create_index([("location", GEOSPHERE)])  # New index for warehouse

    def calculate_route_distance(self, start_lat, start_lon, end_lat, end_lon):
        """Calculate actual route distance using OpenStreetMap."""
        url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=false"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if data.get('routes') and data['routes'][0]:
                return {
                    'distance': data['routes'][0]['distance'],  # meters
                    'duration': data['routes'][0]['duration']   # seconds
                }
            return None
        except Exception as e:
            print(f"Error calculating route: {e}")
            return None

    def find_nearest_warehouse_with_product(self, product_id, customer_location):
        """Find nearest warehouse with available product stock."""
        pipeline = [
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [
                            customer_location["longitude"],
                            customer_location["latitude"]
                        ]
                    },
                    "distanceField": "distance",
                    "spherical": True
                }
            },
            {
                "$lookup": {
                    "from": "DailyInventory",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "inventory"
                }
            },
            {
                "$match": {
                    "inventory.inventoryDetails": {
                        "$elemMatch": {
                            "productID": ObjectId(product_id),
                            "QuantityInInventory": {"$gt": 0},
                            "date": {"$eq": datetime.utcnow().date()}
                        }
                    }
                }
            },
            {
                "$project": {
                    "warehouseName": 1,
                    "warehouseLocation": 1,
                    "distance": 1,
                    "inventory.inventoryDetails.$": 1
                }
            },
            {"$limit": 1}
        ]
        
        return self.db.Warehouse.aggregate(pipeline)

    def find_fresh_products_near_warehouse(self, warehouse_id):
        """Find fresh products available in a specific warehouse."""
        pipeline = [
            {
                "$match": {
                    "storageDetails.storageID": ObjectId(warehouse_id)
                }
            },
            {
                "$lookup": {
                    "from": "DailyInventory",
                    "let": {"prod_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "_id": ObjectId(warehouse_id),
                                "inventoryDetails": {
                                    "$elemMatch": {
                                        "productID": "$$prod_id",
                                        "QuantityInInventory": {"$gt": 0}
                                    }
                                }
                            }
                        }
                    ],
                    "as": "inventory"
                }
            },
            {
                "$match": {
                    "productSpecifics.expiryDate": {"$gt": datetime.utcnow()},
                    "inventory": {"$ne": []}
                }
            },
            {
                "$project": {
                    "productName": 1,
                    "description": 1,
                    "productSpecifics": 1,
                    "inventory.inventoryDetails.QuantityInInventory": 1
                }
            }
        ]
        
        return self.db.FreshProducts.aggregate(pipeline)

    def create_order_from_warehouse(self, customer_id, product_id, warehouse_id, quantity, customer_location):
        """Create a new order sourcing from specific warehouse and assign nearest delivery partner."""
        # First find the warehouse location
        warehouse = self.db.Warehouse.find_one({"_id": ObjectId(warehouse_id)})
        
        # Find nearest available delivery partner to warehouse
        delivery_partner = next(self.find_available_delivery_partner({
            "latitude": warehouse["latitude"],
            "longitude": warehouse["longitude"]
        }))
        
        # Calculate route distances
        warehouse_to_customer = self.calculate_route_distance(
            warehouse["latitude"], 
            warehouse["longitude"],
            customer_location["latitude"], 
            customer_location["longitude"]
        )
        
        # Create the order
        order = {
            "orderid": ObjectId(),
            "totalcost": 0,  # Calculate based on product price
            "deliveryPartnerID": delivery_partner["_id"],
            "products": [{
                "productID": ObjectId(product_id),
                "quantityBought": quantity,
                "warehouseSource": ObjectId(warehouse_id)
            }],
            "orderDate": datetime.utcnow(),
            "estimatedDeliveryTime": warehouse_to_customer["duration"] if warehouse_to_customer else None
        }
        
        # Update customer's currentOrders
        result = self.db.Customers.update_one(
            {"_id": ObjectId(customer_id)},
            {"$push": {"currentOrders": order}}
        )
        
        # Update delivery partner status
        if result.modified_count > 0:
            self.db.Partners.update_one(
                {"_id": delivery_partner["_id"]},
                {
                    "$set": {
                        "driverStatus.onRoute": True,
                        "driverStatus.pickedOrderID": order["orderid"],
                        "driverStatus.ETA": warehouse_to_customer["duration"] if warehouse_to_customer else None
                    }
                }
            )
            
            # Update warehouse inventory
            self.db.DailyInventory.update_one(
                {
                    "_id": ObjectId(warehouse_id),
                    "inventoryDetails.productID": ObjectId(product_id)
                },
                {
                    "$inc": {
                        "inventoryDetails.$.QuantityInInventory": -quantity
                    }
                }
            )
        
        return order["orderid"]

    def search_fresh_products_by_location(self, user_location, max_distance=10000):
        """Search for available fresh products in warehouses near user location."""
        pipeline = [
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [
                            user_location["longitude"],
                            user_location["latitude"]
                        ]
                    },
                    "distanceField": "distance",
                    "spherical": True,
                    "maxDistance": max_distance
                }
            },
            {
                "$lookup": {
                    "from": "DailyInventory",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "inventory"
                }
            },
            {
                "$unwind": "$inventory.inventoryDetails"
            },
            {
                "$match": {
                    "inventory.inventoryDetails.QuantityInInventory": {"$gt": 0}
                }
            },
            {
                "$lookup": {
                    "from": "FreshProducts",
                    "localField": "inventory.inventoryDetails.productID",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {
                "$unwind": "$product"
            },
            {
                "$match": {
                    "product.productSpecifics.expiryDate": {"$gt": datetime.utcnow()}
                }
            },
            {
                "$project": {
                    "warehouseName": 1,
                    "warehouseLocation": 1,
                    "distance": 1,
                    "product.productName": 1,
                    "product.productSpecifics": 1,
                    "inventory.inventoryDetails.QuantityInInventory": 1
                }
            },
            {
                "$sort": {"distance": 1}
            }
        ]
        
        return self.db.Warehouse.aggregate(pipeline)

# Example usage:
def main():
    # Initialize the system
    ecommerce = EcommerceSystem('mongodb+srv://admin:admin@amazone.dodun.mongodb.net/')
    
    # Example: Search for fresh products near user
    user_location = {
        "latitude": 53.4698,
        "longitude": -2.2332
    }
    
    # Search for products in nearby warehouses
    fresh_products = ecommerce.search_fresh_products_by_location(user_location)
    
    # Process and display results
    for product in fresh_products:
        print(f"Found product in warehouse: {product}")
        
        # Calculate delivery time from warehouse
        if product.get('distance'):
            route = ecommerce.calculate_route_distance(
                user_location["latitude"],
                user_location["longitude"],
                float(product["latitude"]),
                float(product["longitude"])
            )
            if route:
                print(f"Estimated delivery time: {route['duration']/60:.2f} minutes")

if __name__ == "__main__":
    main()