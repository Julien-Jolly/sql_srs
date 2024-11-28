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
from auth import create_account, verify_password, send_reset_email, load_users, verify_reset_code, hash_password, save_users

logging.basicConfig(level=logging.INFO)

def login_page():
    st.title("Page de connexion")

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if verify_password(username, password):
            st.success("Bienvenue, vous êtes connecté !")
            st.session_state['username'] = username
            st.session_state['authenticated'] = True
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
            st.success("Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
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
                send_reset_email(email, username)  # Envoi du code de réinitialisation
                user_found = True
                st.success(f"Un code de réinitialisation a été envoyé à {email}.")
                break

        if not user_found:
            st.error("Aucun utilisateur trouvé avec cet email.")

    # Vérification du code et réinitialisation du mot de passe
    if reset_code:
        new_password = st.text_input("Nouveau mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")

        if st.button("Réinitialiser le mot de passe"):
            if new_password == confirm_password:
                if verify_reset_code(reset_code, email):  # Vérifie le code de réinitialisation
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

    if "json" not in os.listdir():
        logging.error(os.listdir())
        logging.error("Creating folder: json")
        os.mkdir("json")

    if "exercises_sql_tables.duckdb" not in os.listdir("data"):
        exec(open("init_db.py").read())

    return duckdb.connect(database="data/exercises_sql_tables.duckdb", read_only=False)


def reset_password_page(token, username):
    """
    Page de réinitialisation de mot de passe.
    Vérifie le token, puis permet à l'utilisateur de saisir un nouveau mot de passe.
    """
    st.title("Réinitialisation de mot de passe")

    # Chargement des données utilisateur
    users_data = load_users()

    # Vérification de la validité du token
    if username not in users_data or users_data[username].get("reset_token") != token:
        st.error("Lien invalide ou expiré.")
        return

    # Formulaire pour saisir un nouveau mot de passe
    new_password = st.text_input("Nouveau mot de passe", type="password")
    confirm_password = st.text_input("Confirmez le nouveau mot de passe", type="password")

    if st.button("Réinitialiser le mot de passe"):
        if not new_password or not confirm_password:
            st.error("Veuillez remplir tous les champs.")
        elif new_password != confirm_password:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            # Mise à jour du mot de passe et suppression du token
            users_data[username]["password"] = hash_password(new_password)
            users_data[username]["reset_token"] = None  # Supprimer le token après utilisation
            save_users(users_data)

            st.success("Votre mot de passe a été réinitialisé avec succès.")
            st.info("Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.")



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

    # Convertir `last_reviewed` en datetime
    exercises["last_reviewed"] = pd.to_datetime(exercises["last_reviewed"])

    # Vérifier si toutes les dates de révision sont au-delà d'aujourd'hui
    today = pd.Timestamp(date.today())  # Convertir `date.today()` en format compatible
    if (exercises["last_reviewed"] > today).all():
        return None, None, None, None, None

    # Charger la réponse associée à l'exercice
    exercise_name = exercises.iloc[0]["exercise_name"]
    with open(f"answers/{exercise_name}.sql", "r") as file:
        answer = file.read()

    solution_df = con.execute(answer).df()
    return exercises, exercises.iloc[0], exercise_name, answer, solution_df



def reset_input(key):
    if key in st.session_state:
        st.session_state[key] = ""

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
            reset_input(user_query)  # Réinitialise après validation
        else:
            st.error("Des différences existent avec la solution.")
            st.dataframe(differences)
    except KeyError:
        st.error("Certaines colonnes sont manquantes ou incorrectes.")

# Gestion des révisions
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
    with st.sidebar:
        if st.session_state["authenticated"]:
            # Si l'utilisateur est authentifié, afficher un bouton de déconnexion
            if st.button("Quitter"):
                st.session_state["authenticated"] = False
                st.session_state["username"] = None
                st.rerun()  # Forcer un rechargement pour afficher la page de connexion

# Application principale
def main_app():
    """Fonction principale de l'application."""
    # Initialisation de l'état d'authentification
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None

    # Récupération des paramètres d'URL (utile pour les fonctionnalités comme les tokens)
    query_params = st.query_params

    # Gestion des tokens pour la réinitialisation de mot de passe
    if "token" in query_params and "username" in query_params:
        token = query_params["token"]
        username = query_params["username"]
        reset_password_page(token=token, username=username)
        return  # On quitte la fonction après avoir affiché la page de réinitialisation

    # Si l'utilisateur est connecté, afficher l'application principale
    if st.session_state["authenticated"]:
        st.title("Système de révision SQL")

        # Chargement de l'environnement
        con = initialize_environment()
        exercises, exercise, exercise_name, answer, solution_df = get_exercise(con)

        # Si aucun exercice n'est disponible
        if exercise is None:
            st.info("Aucune révision prévue aujourd'hui.")
            schedule_review(con, "all")  # Permet de réinitialiser les dates de révision
        else:
            display_sidebar()  # Barre latérale pour la navigation

            # Contenu principal : Affichage des exercices
            with st.container():
                st.subheader(exercise["question"])
                user_query = st.text_area("Entrez votre requête SQL", key="user_input")
                schedule_review(con, exercise_name)

                if st.button("Valider la solution"):
                    check_users_solution(con, user_query, solution_df)

            # Navigation entre les sections : Exercices, Tables, Solutions
            with st.container():
                st.markdown('<div id="exercises_list"></div>', unsafe_allow_html=True)
                st.subheader("Liste des exercices")
                st.dataframe(exercises)

                st.markdown('<div id="tables"></div>', unsafe_allow_html=True)
                display_tables(con, exercise)

                st.markdown('<div id="solution"></div>', unsafe_allow_html=True)
                display_solution(answer)
    else:
        # Si l'utilisateur n'est pas connecté, afficher les options de connexion
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Accès à l'application",
            ["Connexion", "Créer un compte", "Mot de passe oublié"]
        )
        if page == "Connexion":
            login_page()
        elif page == "Créer un compte":
            create_account_page()
        elif page == "Mot de passe oublié":
            forgot_password_page()


# Exécution de l'application
if __name__ == "__main__":
    main_app()
