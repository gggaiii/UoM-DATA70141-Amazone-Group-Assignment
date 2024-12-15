import json
from datetime import datetime, timedelta
from pymongo import MongoClient

def connect_to_mongo():
    con = "mongodb+srv://admin:admin@amazone.dodun.mongodb.net/"
    client = MongoClient(con, serverSelectionTimeoutMS=5000)
    try:
        print("Connected to the Server")
    except Exception:
        print("Unable to connect to the server.")
    return client


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def calculate_monthly_sales(collection, condition=None):
    pipeline = [
        {
            "$group": {
                "_id": {"year": {"$year": "$orderDate"}, "month": {"$month": "$orderDate"}},  # Breakdown by year and month
                "totalSales": {"$sum": "$totalCost"}  # calculate totalCost total
            }
        }, {
            "$sort": {
                "_id.year": 1,
                "_id.month": 1  # sort by year and month
            }
        }, {
            "$project": {
                "_id": 0,
                "month": {
                    "$concat": [
                        {"$toString": "$_id.year"}, "-",
                        {"$cond": {
                            "if": {"$lt": ["$_id.month", 10]},
                            "then": {"$concat": ["0", {"$toString": "$_id.month"}]},
                            "else": {"$toString": "$_id.month"}
                        }},
                        "-01"
                    ]
                },
                "totalSales": 1
            }
        }
    ]

    if condition:
        pipeline.insert(0, {
            "$match": condition  # add date range condition at the beginning
        })

    # Run an aggregated query
    result = collection.aggregate(pipeline)
    sales_by_month = {r["month"]: r["totalSales"] for r in result}

    # Ensure that all months show that even if sales are 0
    start_date = datetime.strptime(min(sales_by_month.keys()), "%Y-%m-%d")
    end_date = datetime.strptime(max(sales_by_month.keys()), "%Y-%m-%d")
    current_date = start_date

    all_months = []
    while current_date <= end_date:
        month_str = current_date.strftime("%Y-%m-01")
        total_sales = sales_by_month.get(month_str, 0)
        all_months.append({"month": month_str, "totalSales": total_sales})
        current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    return all_months

def calculate_daily_sales(collection, condition=None):
    pipeline = [
        {
            "$group": {
                "_id": {"year": {"$year": "$orderDate"}, "month": {"$month": "$orderDate"}, "day": {"$dayOfMonth": "$orderDate"}},  # 按年份、月份和日期分組
                "totalSales": {"$sum": "$totalCost"}  # 計算 totalCost 總和
            }
        }, {
            "$sort": {
                "_id.year": 1,
                "_id.month": 1,
                "_id.day": 1  
            }
        }, {
            "$project": {
                "_id": 0,
                "date": {
                    "$concat": [
                        {"$toString": "$_id.year"}, "-",
                        {"$cond": {
                            "if": {"$lt": ["$_id.month", 10]},
                            "then": {"$concat": ["0", {"$toString": "$_id.month"}]},
                            "else": {"$toString": "$_id.month"}
                        }},
                        "-",
                        {"$cond": {
                            "if": {"$lt": ["$_id.day", 10]},
                            "then": {"$concat": ["0", {"$toString": "$_id.day"}]},
                            "else": {"$toString": "$_id.day"}
                        }}
                    ]
                },
                "totalSales": 1
            }
        }
    ]

    if condition:
        pipeline.insert(0, {
            "$match": condition  # add date range condition at the beginning
        })

    # Run an aggregated query
    result = collection.aggregate(pipeline)
    return [{"date": r["date"], "totalSales": r["totalSales"]} for r in result]

def calculate_total_sales(collection, condition=None):
    pipeline = [
        {
            "$group": {
                "_id": None,  #only one group
                "totalSales": {"$sum": "$totalCost"}  # sum totalCost
            }
        }
    ]

    if condition:
        pipeline.insert(0, {
            "$match": condition  # add date range condition at the beginning
        })

    
    result = collection.aggregate(pipeline)
    return list(result)

def calculate_yearly_sales(collection, condition=None):
    pipeline = [
        {
            "$group": {
                "_id": {"year": {"$year": "$orderDate"}},  
                "totalSales": {"$sum": "$totalCost"}  
            }
        }, {
            "$sort": {
                "_id.year": 1  
            }
        }, {
            "$project": {
                "_id": 0,
                "year": {"$toString": "$_id.year"},
                "totalSales": 1
            }
        }
    ]

    if condition:
        pipeline.insert(0, {
            "$match": condition  
        })

    
    result = collection.aggregate(pipeline)
    return [{"year": r["year"], "totalSales": r["totalSales"]} for r in result]


def main():
    client = connect_to_mongo()
    db = client['Amazone']
    collection_past_order = db['pastOrders']

    # Calculate Monthly Sales Volume
    monthly_sales = calculate_monthly_sales(collection_past_order)
    print("Monthly Sales:", monthly_sales)

    # Enquiry on monthly sales between 2020-06-20 and 2022-01-15
    condition_example = {"orderDate": {"$gte": datetime(2020, 6, 20), "$lt": datetime(2022, 1, 15)}}
    monthly_sales_con = calculate_monthly_sales(collection_past_order, condition_example)

    yearly_sales = calculate_yearly_sales(collection_past_order)

    #save_to_json(monthly_sales_con, 'monthly_sales.json')

if __name__ == "__main__":
    main()
