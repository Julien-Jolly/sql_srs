import duckdb
import pandas as pd
import os
import gdown
import importlib
import sys
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

google_drive_secrets = st.secrets["google_drive"]
users_file_id = google_drive_secrets["users_file_id"]
google_credentials = st.secrets["google_credentials"]
credentials = service_account.Credentials.from_service_account_info(google_credentials)
service = build("drive", "v3", credentials=credentials)

# Connexion à la base de données DuckDB
con = duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)


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

EXERCISES_FILE_ID = "1NM1Q5iF7UsEtR1I2V3r6MgXqQpgG9T9f"
EXERCISES_FILE = "data/exercises.csv"

if not os.path.exists(EXERCISES_FILE):
    gdown.download(
        f"https://drive.google.com/uc?id={EXERCISES_FILE_ID}",
        EXERCISES_FILE,
        quiet=False,
    )

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

FOLDER_ID = "1_hbAjm0oACHL4Qo73KBhgTEQrMXOhKMK"  # ID du dossier Google Drive
directory = "data/tables"

os.makedirs(directory, exist_ok=True)

sys.path.append(directory)


# Fonction pour télécharger un fichier Google Drive
def download_file(file_id, file_name, local_directory):
    local_path = os.path.join(local_directory, file_name)
    if not os.path.exists(local_path):  # Vérifier si le fichier existe déjà
        url = f"https://drive.google.com/uc?id={file_id}&export=download"
        gdown.download(url, local_path, quiet=False)
        print(f"Téléchargement du fichier : {file_name} terminé.")
    else:
        print(f"Le fichier {file_name} existe déjà, il n'a pas été téléchargé.")


# Lister et télécharger les fichiers
def list_files_in_folder(folder_id):
    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents",
            pageSize=10,  # Limiter le nombre de résultats
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )
    return results


# Lister et télécharger les fichiers
try:
    results = list_files_in_folder(FOLDER_ID)
    files = results.get("files", [])
    if not files:
        print("Aucun fichier trouvé dans le dossier Google Drive.")
    else:
        for file in files:
            print(f"Téléchargement du fichier : {file['name']}...")
            download_file(file["id"], file["name"], directory)
        print("Tous les fichiers ont été téléchargés.")
except Exception as e:
    print(f"Une erreur est survenue : {e}")


# -----------------------------------------------------------------------------------
# EXECUTION DES MODULES
# -----------------------------------------------------------------------------------

results = {}
python_files = [f for f in os.listdir(directory) if f.endswith(".py")]

for filename in os.listdir(directory):
    if filename.endswith(".py"):
        module_name = filename[:-3]  # Retirer l'extension .py
        module_path = f"{module_name}"  # Utiliser le nom du fichier sans l'extension

        try:
            module = importlib.import_module(module_path)  # Importer le module
            module.make_df(con)
        except ModuleNotFoundError as e:
            print(f"Module {module_path} introuvable: {e}")

con.close()
