import io
import duckdb
import pandas as pd

con = duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)


# -----------------------------------------------------------------------------------
# EXERCICES LIST
# -----------------------------------------------------------------------------------

data = {
    "theme": ["Cross_Joins", "Cross_Joins"],
    "exercise_name": ["beverages_and_food", "sizes_and_trademarks"],
    "tables": [["beverages", "food_items"], ["sizes", "trademarks"]],
    "last_reviewed": ["1980-01-01", "1970-01-01"],
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

con.close()
