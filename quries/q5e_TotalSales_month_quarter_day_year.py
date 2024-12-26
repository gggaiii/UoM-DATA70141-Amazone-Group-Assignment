import json
import matplotlib.pyplot as plt
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

def calculate_quarterly_sales(collection, condition=None):
    pipeline = [
        {
            "$group": {
                "_id": {"year": {"$year": "$orderDate"}, "quarter": {"$ceil": {"$divide": [{"$month": "$orderDate"}, 3]}}},  # 按年份和季度分組
                "totalSales": {"$sum": "$totalCost"} 
            }
        }, {
            "$sort": {
                "_id.year": 1,
                "_id.quarter": 1 
            }
        }, {
            "$project": {
                "_id": 0,
                "quarter": {
                    "$concat": [
                        {"$toString": "$_id.year"}, "-Q",
                        {"$toString": "$_id.quarter"}
                    ]
                },
                "totalSales": 1
            }
        }
    ]

    if condition:
        pipeline.insert(0, {
            "$match": condition 
        })

    result = collection.aggregate(pipeline)
    return list(result)

def calculate_growth_rate(data):
    growth_rates = []
    for i in range(1, len(data)):
        previous = data[i - 1]['totalSales']
        current = data[i]['totalSales']
        growth_rate = ((current - previous) / previous) * 100 if previous != 0 else 0
        growth_rates.append(growth_rate)
    return growth_rates

def visualize_quarterly_sales(data):
    quarters = [item['quarter'] for item in data]
    total_sales = [item['totalSales'] for item in data]
    growth_rates = calculate_growth_rate(data)

    x = range(len(quarters))

    fig, ax1 = plt.subplots(figsize=(14, 7))

    ax1.bar(x, total_sales, width=0.4, align='center', label='Total Sales')
    ax1.set_xlabel('Quarter')
    ax1.set_ylabel('Total Sales')
    ax1.set_title('Quarterly Sales')
    ax1.set_xticks(x)
    ax1.set_xticklabels(quarters, rotation='vertical')

    ax2 = ax1.twinx()
    ax2.plot(x[1:], growth_rates, marker='o', color='r', label='Growth Rate')
    ax2.set_ylabel('Growth Rate (%)')

    for i, rate in enumerate(growth_rates):
        ax2.text(i + 1, rate, f'{rate:.2f}%', color='r', ha='center', va='bottom')

    fig.tight_layout()
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    plt.savefig('quarterly_sales.png')
    plt.show()

def visualize_monthly_sales(data):
    months = [item['month'] for item in data]
    total_sales = [item['totalSales'] for item in data]
    growth_rates = calculate_growth_rate(data)

    x = range(len(months))

    fig, ax1 = plt.subplots(figsize=(14, 7))

    ax1.bar(x, total_sales, width=0.4, align='center', label='Total Sales')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Total Sales')
    ax1.set_title('Monthly Sales')
    ax1.set_xticks(x)
    ax1.set_xticklabels(months, rotation='vertical')

    ax2 = ax1.twinx()
    ax2.plot(x[1:], growth_rates, marker='o', color='r', label='Growth Rate')
    ax2.set_ylabel('Growth Rate (%)')

    for i, rate in enumerate(growth_rates):
        ax2.text(i + 1, rate, f'{rate:.2f}%', color='r', ha='center', va='bottom', rotation=90)

    fig.tight_layout()
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    plt.savefig('monthly_sales.png')
    plt.show()

def visualize_yearly_sales(data):
    years = [item['year'] for item in data]
    total_sales = [item['totalSales'] for item in data]
    growth_rates = calculate_growth_rate(data)

    x = range(len(years))

    fig, ax1 = plt.subplots(figsize=(14, 7))

    ax1.bar(x, total_sales, width=0.4, align='center', label='Total Sales')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Total Sales')
    ax1.set_title('Yearly Sales')
    ax1.set_xticks(x)
    ax1.set_xticklabels(years, rotation='vertical')

    ax2 = ax1.twinx()
    ax2.plot(x[1:], growth_rates, marker='o', color='r', label='Growth Rate')
    ax2.set_ylabel('Growth Rate (%)')

    for i, rate in enumerate(growth_rates):
        ax2.text(i + 1, rate, f'{rate:.2f}%', color='r', ha='center', va='bottom')

    fig.tight_layout()
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    plt.savefig('yearly_sales.png')
    plt.show()

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
    print("Monthly Sales (2020-06-20 to 2022-01-15):", monthly_sales_con)

    yearly_sales = calculate_yearly_sales(collection_past_order)
    print("Yearly Sales:", yearly_sales)


    quarterly_sales = calculate_quarterly_sales(collection_past_order)
    print("Quarterly Sales:", quarterly_sales)


    save_to_json(monthly_sales, 'monthly_sales.json')
    save_to_json(monthly_sales_con, 'monthly_sales_con.json')
    save_to_json(yearly_sales, 'yearly_sales.json')
    save_to_json(quarterly_sales, 'quarterly_sales.json')


    visualize_quarterly_sales(quarterly_sales)

    visualize_monthly_sales(monthly_sales)
 
    visualize_yearly_sales(yearly_sales)

if __name__ == "__main__":
    main()




