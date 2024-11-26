# Base de données : Remplacer le fichier JSON par une base de données (SQLite, PostgreSQL, etc.).
# Rôles et permissions : Ajouter des niveaux d'accès pour les utilisateurs.
# Email de récupération : Implémenter une récupération de mot de passe via email.
# Design : Améliorer l'interface utilisateur avec des widgets Streamlit avancés.


# pylint: disable = missing-module-docstring
import duckdb
import streamlit as st
import os
import logging
import bcrypt
import json
from pathlib import Path
from datetime import date, timedelta

# Chemin pour le fichier JSON des utilisateurs
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

# Initialisation
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
    # Code principal de l'application
    if "data" not in os.listdir():
        logging.error(os.listdir())
        logging.error("creating folder data")
        os.mkdir("data")

    if "exercises_sql_tables.duckdb" not in os.listdir("data"):
        exec(open("init_db.py").read())

    con = duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)

    def check_users_solution(user_query: str) -> None:
        """
        check that user query is correct by
        1. checking the columns
        2. checking the values
        :param user_query: a string containing the query inserted by user
        """
        result = con.execute(user_query).df()
        st.dataframe(result)
        try:
            result = result[solution_df.columns]
            st.dataframe(result.compare(solution_df))
            if result.compare(solution_df).shape == (0, 0):
                st.write("Correct !")
                st.balloons()
        except KeyError as e:
            st.write("some columns are missing")
        n_lines_difference = result.shape[0] - solution_df.shape[0]
        if n_lines_difference != 0:
            st.write(
                f"result has a {n_lines_difference} lines different with the solution_df"
            )

    def get_exercise():
        global exercise, answer, solution_df
        with st.sidebar:
            available_themes_df = con.execute(
                "SELECT DISTINCT theme FROM memory_state"
            ).df()
            theme = st.selectbox(
                "What would you like to review ?",
                available_themes_df["theme"].unique(),
                index=None,
                placeholder="Select a theme...",
            )

            if theme:
                st.write(f"You selected: {theme}")
                select_exercise_query = (
                    f"SELECT * FROM memory_state WHERE theme = '{theme}'"
                )
            else:
                select_exercise_query = f"SELECT * FROM memory_state"

            exercise = (
                con.execute(select_exercise_query).df().sort_values("last_reviewed")
            )

            st.write(exercise)
            exercise_name = exercise.iloc[0]["exercise_name"]
            with open(f"answers/{exercise_name}.sql", "r") as f:
                answer = f.read()

            solution_df = con.execute(answer).df()
            return exercise_name

    exercise_name = get_exercise()

    question = exercise.iloc[0]["question"]
    st.header(question)

    form = st.form("my_form")
    query = form.text_area(label="votre code SQL ici", key="user_input")
    form.form_submit_button("Submit")

    if query:
        check_users_solution(query)

    for n_days in [2, 7, 21]:
        if st.button(f"revoir dans {n_days} jours"):
            next_review = date.today() + timedelta(days=n_days)
            con.execute(
                f"UPDATE memory_state SET last_reviewed = '{next_review}' WHERE exercise_name = '{exercise_name}'"
            )
            st.rerun()

    if st.button("Reset"):
        con.execute(f"UPDATE memory_state SET last_reviewed = '1970-01-01'")
        st.rerun()

    tab2, tab3 = st.tabs(["Tables", "Solution"])

    with tab2:
        exercise_tables = exercise.iloc[0]["tables"]
        for table in exercise_tables:
            st.write(f"table: {table}")
            df_table = con.execute(f"SELECT * FROM {table}").df()
            st.dataframe(df_table)

    with tab3:
        st.text(answer)