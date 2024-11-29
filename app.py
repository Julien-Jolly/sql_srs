# Base de données : Remplacer le fichier JSON par une base de données (SQLite, PostgreSQL, etc.).
# Rôles et permissions : Ajouter des niveaux d'accès pour les utilisateurs.
# Email de récupération : Implémenter une récupération de mot de passe via email.
# Design : Améliorer l'interface utilisateur avec des widgets Streamlit avancés.


# pylint: disable = missing-module-docstring
import duckdb
import streamlit as st
from streamlit_scroll_navigation import scroll_navbar
from datetime import date, timedelta
import logging
import os
import pandas as pd
from auth import (
    create_account,
    verify_password,
    send_reset_email,
    load_users,
    verify_reset_code,
    hash_password,
    save_users,
)


def login_page():
    st.title("Page de connexion")

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if verify_password(username, password):
            st.success("Bienvenue, vous êtes connecté !")
            st.session_state["username"] = username
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")


def create_account_page():
    st.title("Créer un compte")

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    email = st.text_input("Email")

    if st.button("Créer le compte"):
        if create_account(username, password, email):
            st.success(
                "Compte créé avec succès ! Vous pouvez maintenant vous connecter."
            )
        else:
            st.error("Un compte avec ce nom d'utilisateur existe déjà.")


def forgot_password_page():
    st.title("Mot de passe oublié")

    email = st.text_input("Entrez votre email")
    reset_code = st.text_input("Entrez le code de réinitialisation envoyé par email")

    if st.button("Envoyer un code de réinitialisation"):
        users = load_users()
        user_found = False

        for username, user_data in users.items():
            if user_data["email"] == email:
                send_reset_email(email, username)
                user_found = True
                st.success(f"Un code de réinitialisation a été envoyé à {email}.")
                break

        if not user_found:
            st.error("Aucun utilisateur trouvé avec cet email.")

    if reset_code:
        new_password = st.text_input("Nouveau mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")

        if st.button("Réinitialiser le mot de passe"):
            if new_password == confirm_password:
                if verify_reset_code(reset_code, email):
                    if reset_user_password(email, new_password):
                        st.success("Mot de passe réinitialisé avec succès.")
                    else:
                        st.error("Erreur lors de la réinitialisation du mot de passe.")
                else:
                    st.error("Code de réinitialisation invalide.")
            else:
                st.error("Les mots de passe ne correspondent pas.")


def reset_user_password(email, new_password):
    """Réinitialise le mot de passe de l'utilisateur."""
    users = load_users()
    for username, user_data in users.items():
        if user_data["email"] == email:
            hashed_password = hash_password(new_password)
            users[username]["password"] = hashed_password
            save_users(users)
            return True
    return False


def initialize_environment():
    """Crée le dossier et initialise la base de données si nécessaire."""
    if "data" not in os.listdir():
        logging.error(os.listdir())
        logging.error("Creating folder: data")
        os.mkdir("data")

    if "exercises_sql_tables.duckdb" not in os.listdir("data"):
        exec(open("init_db.py").read())

    return duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)


def get_theme(con):
    themes = con.execute("SELECT DISTINCT theme FROM memory_state").fetchdf()
    theme = st.sidebar.selectbox(
        "Quel thème souhaitez-vous réviser ?",
        themes["theme"].unique(),
        index=None,
        placeholder="Sélectionnez un thème...",
    )
    return theme


def get_exercise(con):
    theme = get_theme(con)

    query = (
        f"SELECT * FROM memory_state WHERE theme = '{theme}'"
        if theme
        else "SELECT * FROM memory_state"
    )
    exercises = con.execute(query).df().sort_values("last_reviewed")

    exercises["last_reviewed"] = pd.to_datetime(exercises["last_reviewed"])

    today = pd.Timestamp(date.today())
    if (exercises["last_reviewed"] > today).all():
        return None, None, None, None, None

    exercise_name = exercises.iloc[0]["exercise_name"]

    query_answer = (
        f"SELECT answers FROM exercises WHERE exercise_name = '{exercise_name}'"
    )
    answer_df = con.execute(query_answer).fetchdf()

    if not answer_df.empty:
        answer = answer_df.iloc[0]["answers"]
        answer = answer.strip('"')
    else:
        answer = "No answer found for this exercise"

    try:
        solution_df = con.execute(answer).df()
    except Exception as e:
        solution_df = None
        st.error(f"Erreur dans l'exécution de la requête SQL : {e}")

    return exercises, exercises.iloc[0], exercise_name, answer, solution_df


def check_users_solution(con, user_query, solution_df):
    """Vérification de la solution de l'utilisateur."""
    try:
        result = con.execute(user_query).df()
        text = ("Votre réponse :", "Solution :")

        cols = st.columns(2)
        with cols[0]:
            st.write(f"**{text[0]}**")
            st.dataframe(result, hide_index=True)

        with cols[1]:
            st.write(f"**{text[1]}**")
            st.dataframe(solution_df, hide_index=True)

        if result.shape[0] != solution_df.shape[0]:
            st.write("Le nombre de lignes est incorrect")

        elif result.shape[1] != solution_df.shape[1]:
            st.write("Le nombre de colonnes est incorrect")

        elif not result.compare(solution_df).empty:
            st.write("Le contenu est incorrect")

        else:
            st.write("Bravo, réponse correcte !")
            st.balloons()

    except (AttributeError, duckdb.ParserException) as e:
        st.write(
            "Il y a une erreur dans la syntaxe de votre requête. Veuillez réessayer."
        )
        result = None


def schedule_review(con, exercise_name):
    """Planifie une prochaine révision."""
    col1, col2, col3, col4 = st.columns(4)
    if exercise_name != "all":
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


def display_tables(con, exercise):
    st.subheader("Tables")

    if isinstance(exercise["tables_used"], str):
        tables = exercise["tables_used"].split(",")

    else:
        tables = exercise["tables_used"]

    for i in range(0, len(tables), 2):
        cols = st.columns(2)
        for j, table in enumerate(tables[i : i + 2]):
            with cols[j]:
                if not table.strip():
                    st.warning(f"Nom de table vide ou incorrect : {table}")
                    continue

                st.write(f"**Table : {table}**")

                try:
                    table_df = con.execute(f"SELECT * FROM {table}").df()
                    st.dataframe(table_df, hide_index=True)
                except Exception as e:
                    st.error(f"Erreur lors de la récupération de la table {table}: {e}")


def display_solution(solution_query):
    st.subheader("Solution")
    with st.expander("voir"):
        st.text(solution_query)


def display_sidebar():
    anchor_ids = ["exercises_list", "response", "tables", "solution"]
    anchor_icons = ["list", "code", "table", "check-circle"]

    with st.sidebar:
        st.subheader("Navigation")
        scroll_navbar(
            anchor_ids,
            anchor_labels=[
                "Liste des exercices",
                "Votre réponse",
                "Tables",
                "Solution",
            ],
            anchor_icons=anchor_icons,
        )
    with st.sidebar:
        if st.session_state["authenticated"]:
            if st.button("Quitter"):
                st.session_state["authenticated"] = False
                st.session_state["username"] = None
                st.rerun()


def launch_questions(exercises, exercise, con, exercise_name, solution_df, answer):
    st.divider()

    with st.container():
        st.markdown('<div id="exercises_list"></div>', unsafe_allow_html=True)
        st.subheader("Liste des exercices")
        exercises_display = exercises.drop(columns=["tables"], errors="ignore")
        exercises_display["last_reviewed"] = exercises_display[
            "last_reviewed"
        ].dt.strftime("%Y-%m-%d")
        st.dataframe(exercises_display, hide_index=True)

    st.divider()

    with st.container():
        st.subheader(exercise["question"])
        st.markdown('<div id="response"></div>', unsafe_allow_html=True)
        user_query = st.text_area("titre", key="user_input", label_visibility="hidden")
        schedule_review(con, exercise_name)

        if st.button("Valider la solution"):
            check_users_solution(con, user_query, solution_df)

    st.divider()

    with st.container():
        st.markdown(
            '<div id="tables"></div>,<style>:target::before {content: "";display: block;height: 80px;margin-top: -80px;}</style>',
            unsafe_allow_html=True,
        )
        display_tables(con, exercise)

        st.divider()

        st.markdown('<div id="solution"></div>', unsafe_allow_html=True)
        display_solution(answer)


def main_app():

    con = initialize_environment()
    exercises, exercise, exercise_name, answer, solution_df = get_exercise(con)
    display_sidebar()
    if exercise is None:
        st.info("Aucune révision prévue aujourd'hui.")
        schedule_review(con, "all")  # Permet de réinitialiser les dates de révision
    else:
        launch_questions(exercises, exercise, con, exercise_name, solution_df, answer)


if __name__ == "__main__":
    if "json" not in os.listdir():
        logging.error(os.listdir())
        logging.error("Creating folder: json")
        os.mkdir("json")

    if "users.json" not in os.listdir("json"):
        exec(open("json/json_init.py").read())

    st.title("Système de révision SQL")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None

    if st.session_state["authenticated"]:
        main_app()

    else:
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Accès à l'application",
            ["Connexion", "Créer un compte", "Mot de passe oublié"],
        )
        if page == "Connexion":
            login_page()
        elif page == "Créer un compte":
            create_account_page()
        elif page == "Mot de passe oublié":
            forgot_password_page()
