import io
import duckdb
import pandas as pd

con = duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)


# -----------------------------------------------------------------------------------
# EXERCICES LIST
# -----------------------------------------------------------------------------------

data = {
    "theme": ["Cross_Joins", "Cross_Joins", "Inner_Joins"],
    "exercise_name": ["beverages_and_food", "sizes_and_trademarks", "customers_and_orders"],
    "tables": [["beverages", "food_items"], ["sizes", "trademarks"], ["orders_data", "customers_data", "products_data", "order_details_data"]],
    "last_reviewed": ["1980-01-01", "1970-01-01", "1970-01-01"],
    "question": ["faire un cross-join sur les 2 tables", "faire un cross-join sur les 2 tables", "inner join pour rassembler les commandes avec les détails"]
}
memory_state_df = pd.DataFrame(data)
con.execute("CREATE OR REPLACE TABLE memory_state AS SELECT * FROM memory_state_df")


# -----------------------------------------------------------------------------------
# CROSS JOIN EXERCICES
# -----------------------------------------------------------------------------------

CSV = """
beverage, price
orange_juice, 2.5
Expresso, 2
Tea, 3
"""
beverages = pd.read_csv(io.StringIO(CSV))
con.execute("CREATE OR REPLACE TABLE beverages AS SELECT * FROM beverages")


CSV2 = """
food_item, food_price
cookie, 2.5
chocolatine, 2
muffin, 3
"""
food_items = pd.read_csv(io.StringIO(CSV2))
con.execute("CREATE OR REPLACE TABLE food_items AS SELECT * FROM food_items")


sizes = """
size
XS
M
L
XL
"""
sizes = pd.read_csv(io.StringIO(sizes))
con.execute("CREATE OR REPLACE TABLE sizes AS SELECT * FROM sizes")


trademarks = """
trademark
Nike
Asphalte
Abercrombie
Levis
"""
trademarks = pd.read_csv(io.StringIO(trademarks))
con.execute("CREATE OR REPLACE TABLE trademarks AS SELECT * FROM trademarks")


orders_data_temp = {
    'order_id': [1, 2, 3, 4, 5],
    'customer_id': [101, 102, 103, 104, 105]
}
orders_str = "order_id, customer_id\n"  # Entête
orders_str += "\n".join([f"{oid}, {cid}" for oid, cid in zip(orders_data_temp['order_id'], orders_data_temp['customer_id'])])
orders_data = pd.read_csv(io.StringIO(orders_str))
con.execute("CREATE OR REPLACE TABLE orders_data AS SELECT * FROM orders_data")


customers_data_temp = {
    'customer_id': [101, 102, 103, 104, 105, 106],
    'customer_name': ["Toufik", "Daniel", "Tancrède", "Kaouter", "Jean-Nicolas", "David"]
}
customers_str = "customer_id, customer_name\n"  # Entête
customers_str += "\n".join([f"{cid}, {cun}" for cid, cun in zip(customers_data_temp['customer_id'], customers_data_temp['customer_name'])])
customers_data = pd.read_csv(io.StringIO(customers_str))
con.execute("CREATE OR REPLACE TABLE customers_data AS SELECT * FROM customers_data")


products_data_temp = {
    'product_id': [101, 103, 104, 105],
    'product_name': ["Laptop", "Ipad", "Livre", "Petitos"],
    'product_price': [800, 400, 30, 2]
}
products_str = "product_id, product_name, product_price\n"  # Entête
products_str += "\n".join([f"{pid}, {prn}, {prp}" for pid, prn, prp in zip(products_data_temp['product_id'], products_data_temp['product_name'],products_data_temp['product_price'])])
products_data = pd.read_csv(io.StringIO(products_str))
con.execute("CREATE OR REPLACE TABLE products_data AS SELECT * FROM products_data")


order_details_data_temp = {
    'order_id': [1, 2, 3, 4, 5],
    'product_id': [102, 104, 101, 103, 105],
    'quantity': [2, 1, 3, 2, 1]
}
order_details_str = "order_id, product_id, quantity\n"  # Entête
order_details_str += "\n".join([f"{oid}, {pri}, {qua}" for oid, pri, qua in zip(order_details_data_temp['order_id'], order_details_data_temp['product_id'],order_details_data_temp['quantity'])])
order_details_data = pd.read_csv(io.StringIO(order_details_str))
con.execute("CREATE OR REPLACE TABLE order_details_data AS SELECT * FROM order_details_data")









con.close()
