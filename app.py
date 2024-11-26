# Base de données : Remplacer le fichier JSON par une base de données (SQLite, PostgreSQL, etc.).
# Rôles et permissions : Ajouter des niveaux d'accès pour les utilisateurs.
# Email de récupération : Implémenter une récupération de mot de passe via email.
# Design : Améliorer l'interface utilisateur avec des widgets Streamlit avancés.


# pylint: disable = missing-module-docstring
import duckdb
import streamlit as st
from streamlit_scroll_navigation import scroll_navbar
import os
import logging
import bcrypt
import json
from pathlib import Path
from datetime import date, timedelta

# Initialisation et configuration
USER_FILE = Path("users.json")

# Charger les utilisateurs existants depuis un fichier JSON
def load_users():
    if USER_FILE.exists():
        with open(USER_FILE, "r") as file:
            return json.load(file)
    return {}

# Sauvegarder les utilisateurs dans un fichier JSON
def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

# Hacher un mot de passe
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Vérifier un mot de passe
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# Page de connexion
def login_page():
    st.title("Connexion")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        users = load_users()
        if username in users and verify_password(password, users[username]["password"]):
            st.success(f"Bienvenue, {username}!")
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")

# Page de création d'utilisateur
def create_user_page():
    st.title("Créer un utilisateur")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    confirm_password = st.text_input("Confirmez le mot de passe", type="password")

    if st.button("Créer un compte"):
        users = load_users()
        if username in users:
            st.error("Ce nom d'utilisateur existe déjà.")
        elif password != confirm_password:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            hashed_password = hash_password(password)
            users[username] = {"password": hashed_password}
            save_users(users)
            st.success("Utilisateur créé avec succès ! Vous pouvez maintenant vous connecter.")
            st.rerun()


def initialize_environment():
    """Crée le dossier et initialise la base de données si nécessaire."""
    if "data" not in os.listdir():
        logging.error(os.listdir())
        logging.error("Creating folder: data")
        os.mkdir("data")

    if "exercises_sql_tables.duckdb" not in os.listdir("data"):
        exec(open("init_db.py").read())

    return duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)


# Chargement d'un exercice
def get_exercise(con):
    """Charge un exercice basé sur le thème sélectionné."""
    themes = con.execute("SELECT DISTINCT theme FROM memory_state").df()
    theme = st.sidebar.selectbox(
        "Quel thème souhaitez-vous réviser ?",
        themes["theme"].unique(),
        index=None,
        placeholder="Sélectionnez un thème...",
    )

    # Construire la requête pour charger les exercices
    query = f"SELECT * FROM memory_state WHERE theme = '{theme}'" if theme else "SELECT * FROM memory_state"
    exercises = con.execute(query).df().sort_values("last_reviewed")

    # Charger la réponse associée à l'exercice
    exercise_name = exercises.iloc[0]["exercise_name"]
    with open(f"answers/{exercise_name}.sql", "r") as file:
        answer = file.read()

    solution_df = con.execute(answer).df()
    return exercises, exercises.iloc[0], exercise_name, answer, solution_df

# Vérification de la solution utilisateur
def check_users_solution(con, user_query, solution_df):
    """
    Vérifie que la requête de l'utilisateur correspond à la solution attendue.
    """
    try:
        result = con.execute(user_query).df()
        st.dataframe(result)

        # Vérification des colonnes et comparaison des résultats
        result = result[solution_df.columns]
        differences = result.compare(solution_df)

        if differences.shape == (0, 0):
            st.success("Correct !")
            st.balloons()
        else:
            st.error("Des différences existent avec la solution.")
            st.dataframe(differences)
    except KeyError:
        st.error("Certaines colonnes sont manquantes ou incorrectes.")

# Gestion des révisions
def schedule_review(con, exercise_name):
    """Planifie une prochaine révision."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Revoir dans 2 jours"):
            next_review = date.today() + timedelta(days=2)
            con.execute(
                f"UPDATE memory_state SET last_reviewed = '{next_review}' WHERE exercise_name = '{exercise_name}'"
            )
            st.rerun()
    with col2:
        if st.button("Revoir dans 7 jours"):
            next_review = date.today() + timedelta(days=7)
            con.execute(
                f"UPDATE memory_state SET last_reviewed = '{next_review}' WHERE exercise_name = '{exercise_name}'"
            )
            st.rerun()
    with col3:
        if st.button("Revoir dans 21 jours"):
            next_review = date.today() + timedelta(days=21)
            con.execute(
                f"UPDATE memory_state SET last_reviewed = '{next_review}' WHERE exercise_name = '{exercise_name}'"
            )
            st.rerun()
    with col4:
        if st.button("Réinitialiser toutes les dates"):
            con.execute("UPDATE memory_state SET last_reviewed = '1970-01-01'")
            st.rerun()

# Affichage des tables
def display_tables(con, exercise):
    """Affiche les tables liées à l'exercice, avec deux tables par ligne et sans indice."""
    st.subheader("Tables")
    tables = exercise["tables"]

    # Répartir les tables en lignes de deux colonnes
    for i in range(0, len(tables), 2):
        cols = st.columns(2)  # Crée deux colonnes
        for j, table in enumerate(tables[i:i+2]):  # Parcourt jusqu'à deux tables
            with cols[j]:  # Place chaque table dans une colonne
                st.write(f"**Table : {table}**")
                table_df = con.execute(f"SELECT * FROM {table}").df()
                st.dataframe(table_df)

# Affichage de la solution
def display_solution(solution_query):
    """Affiche la solution SQL."""
    st.subheader("Solution")
    st.text(solution_query)

# Ajout de la sidebar
def display_sidebar():
    """Affiche une sidebar avec navigation ancrée."""
    anchor_ids = ["exercises_list", "tables", "solution"]
    anchor_icons = ["list", "table", "code"]

    with st.sidebar:
        st.subheader("Navigation")
        scroll_navbar(
            anchor_ids,
            anchor_labels=["Liste des exercices", "Tables", "Solution"],
            anchor_icons=anchor_icons
        )

# Application principale
def main_app():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None

    if not st.session_state["authenticated"]:
        page = st.sidebar.radio("Navigation", ["Connexion", "Créer un utilisateur"])
        if page == "Connexion":
            login_page()
        elif page == "Créer un utilisateur":
            create_user_page()

    else:
        st.title("Système de révision SQL")
        con = initialize_environment()

        # Charger les exercices et la solution
        exercises, exercise, exercise_name, answer, solution_df = get_exercise(con)

        # Sidebar
        display_sidebar()

        # Partie supérieure : Titre de la question et boutons
        with st.container():
            st.subheader(exercise["question"])  # Affiche la question sélectionnée
            user_query = st.text_area("Entrez votre requête SQL ici", key="user_input")
            schedule_review(con, exercise_name)

            if st.button("Valider votre solution"):
                check_users_solution(con, user_query, solution_df)

        # Partie inférieure : Navigation entre les sections
        with st.container():
            st.markdown('<div id="exercises_list"></div>', unsafe_allow_html=True)
            st.subheader("Liste des exercices")
            st.dataframe(exercises)

            st.markdown('<div id="tables"></div>', unsafe_allow_html=True)
            display_tables(con, exercise)

            st.markdown('<div id="solution"></div>', unsafe_allow_html=True)
            display_solution(answer)

# Exécution de l'application
if __name__ == "__main__":
    main_app()
