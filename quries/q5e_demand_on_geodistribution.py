from pymongo import MongoClient
import pprint
import matplotlib.pyplot as plt
import pandas as pd

# Connect to MongoDB
def connect_to_db():
    connection_str = "mongodb+srv://admin:admin@amazone.dodun.mongodb.net/"
    client = MongoClient(connection_str, serverSelectionTimeoutMS=5000)
    print("Connected to the server")
    return client['Amazone']

# get all the geo distribution of the demand

def get_demand_on_geodistribution(db):
    """Retrieve the demand on geo distribution."""
    pipeline = [
    {
        '$project': {
            'lat': '$latitude', 
            'lon': '$longitude'
        }
    }
    ]
    return list(db.customerAddresses.aggregate(pipeline))

# visualize the data in graph by matplotlib
def save_graph(data, geodata, file_path):
    """Save a bar graph of the demand on geo distribution."""
    # Extract product names and inventory quantity
    lats = [product["lat"] for product in data]
    lons = [product["lon"] for product in data]

    # add lats to column in geodata
    geodata['lats'] = lats
    geodata['lons'] = lons


    # Create the graph
    plt.figure(figsize=(10, 6))
    plt.scatter(lons, lats, color='skyblue')
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Demand on Geo Distribution")
    plt.tight_layout()

    # Save the graph
    plt.savefig(file_path)

def main():
    db = connect_to_db()
    data = get_demand_on_geodistribution(db)
    print(data)
    geodata = pd.DataFrame(data)
    save_graph(data, geodata, "Data_Science/Database/Assignment2/outputs/demand_on_geodistribution.png")
    print(geodata)
    geodata.to_csv("Data_Science/Database/Assignment2/outputs/demand_on_geodistribution.csv")

if __name__ == "__main__":
    main()