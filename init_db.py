import duckdb
import pandas as pd
import os
import gdown

con = duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)

EXERCISES_FILE_ID = "1NM1Q5iF7UsEtR1I2V3r6MgXqQpgG9T9f"
TABLES_FILE_ID = "1PsMtuAVsX0b-0TtNaDC1MvirkPKrQNr0"


EXERCISES_FILE = "data/exercises.csv"
TABLES_FILE = "data/tables.csv"

if not os.path.exists(EXERCISES_FILE):
    gdown.download(f"https://drive.google.com/uc?id={EXERCISES_FILE_ID}", EXERCISES_FILE, quiet=False)

if not os.path.exists(TABLES_FILE):
    gdown.download(f"https://drive.google.com/uc?id={TABLES_FILE_ID}", TABLES_FILE, quiet=False)

# -----------------------------------------------------------------------------------
# FONCTION DE CONVERSION
# -----------------------------------------------------------------------------------
def convert_value(value, dtype):
    if dtype == "int":
        return int(value)
    elif dtype == "float":
        return float(value)
    elif dtype == "str":
        return value
    else:
        raise ValueError(f"Type non supporté : {dtype}")


# -----------------------------------------------------------------------------------
# CHARGEMENT DES EXERCICES
# -----------------------------------------------------------------------------------

exercises_csv = "data/exercises.csv"
exercises_df = pd.read_csv(exercises_csv, delimiter=";", encoding="latin-1")

con.execute(
    """
    CREATE OR REPLACE TABLE memory_state AS 
    SELECT exercise_name, theme, tables_used, last_reviewed, question, difficulty, tables, answers, author
    FROM exercises_df
"""
)

print("Table memory_state créée avec succès.")
exercises_df = con.execute("SELECT * FROM memory_state").fetchdf()
print(exercises_df)

# -----------------------------------------------------------------------------------
# CHARGEMENT DES TABLES
# -----------------------------------------------------------------------------------

tables_csv = "data/tables.csv"
tables_df = pd.read_csv(tables_csv, delimiter=";", encoding="latin-1")


for index, row in tables_df.iterrows():
    table_name = row["tables"]
    columns = row["columns"]
    data = row["data"]
    types = row["types"].split(",")

    data_list = [
        dict(
            zip(
                columns.split(","),
                [
                    convert_value(value, dtype)
                    for value, dtype in zip(item.split(":"), types)
                ],
            )
        )
        for item in data.split(",")
    ]

    table_df = pd.DataFrame(data_list)

    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM table_df")
    print(f"Table {table_name} créée ou mise à jour avec succès.")


con.close()


# directory = "/home/julien/sql_srs/exercises"
# results = {}
# python_files = [f for f in os.listdir(directory) if f.endswith(".py")]
#
# for filename in os.listdir(directory):
#     if filename.endswith(".py"):
#         module_name = filename[:-3]
#         module_path = f"exercises.{module_name}"
#
#         module = importlib.import_module(module_path)
#
#         module.make_df(con)
