import hashlib
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


GOOGLE_DRIVE_FILE_ID = st.secrets["google_drive"]["users_file_id"]
SERVICE_ACCOUNT_INFO = st.secrets["google_credentials"]
API_NAME = 'drive'
API_VERSION = 'v3'

def download_json():
    service = authenticate_google_drive()
    try:
        file_content = service.files().get_media(fileId=GOOGLE_DRIVE_FILE_ID).execute()

        with open("json/users.json", "wb") as f:
            f.write(file_content)
        print("Fichier 'users.json' téléchargé avec succès.")
    except Exception as e:
        st.error(f"Erreur lors du téléchargement des utilisateurs : {e}")


def authenticate_google_drive():
    try:
        credentials = service_account.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build(API_NAME, API_VERSION, credentials=credentials)
        return service
    except HttpError as error:
        st.error(f"Une erreur s'est produite lors de l'authentification : {error}")
        st.stop()



def load_users():
    service = authenticate_google_drive()
    try:
        file_content = service.files().get_media(fileId=GOOGLE_DRIVE_FILE_ID).execute()

        with open("json/users.json", "wb") as f:
            f.write(file_content)  # Sauvegarde du fichier téléchargé

        with open("json/users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        st.error(f"Erreur lors du chargement des utilisateurs : {e}")
        return {}


def save_users(users):
    try:
        with open("json/users.json", "w") as f:
            json.dump(users, f, indent=4)

        service = authenticate_google_drive()
        file_metadata = {"name": "users.json"}
        media = MediaFileUpload("json/users.json", mimetype="application/json")

        # Vérifie si le fichier existe déjà et met à jour le fichier Google Drive
        file = service.files().get(fileId=GOOGLE_DRIVE_FILE_ID).execute()
        updated_file = service.files().update(fileId=GOOGLE_DRIVE_FILE_ID, media_body=media).execute()

        st.success("Fichier 'users.json' mis à jour sur Google Drive.")
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde des utilisateurs : {e}")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_account(username, password, email):
    users = load_users()
    if username not in users:
        users[username] = {
            "password": hash_password(password),
            "email": email
        }
        save_users(users)
        return True
    return False


def verify_password(username, password):
    users = load_users()
    if username in users and users[username]["password"] == hash_password(password):
        return True
    return False


def generate_reset_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def send_reset_email(email, username):
    reset_code = generate_reset_code()
    users = load_users()
    if username in users:
        users[username]["reset_code"] = reset_code
        save_users(users)
    else:
        raise ValueError("Utilisateur introuvable.")

    receiver_email = email
    subject = "Code de réinitialisation de mot de passe"
    body = f"Bonjour {username},\n\nVotre code de réinitialisation est : {reset_code}\n\nCordialement."

    msg = MIMEMultipart()
    msg['From'] = st.secrets["gmail"]["sender_email"]
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(st.secrets["gmail"]["sender_email"], st.secrets["gmail"]["sender_password"])
            server.sendmail(st.secrets["gmail"]["sender_email"], receiver_email, msg.as_string())
            print("E-mail envoyé avec succès.")
    except smtplib.SMTPException as e:
        print(f"Erreur SMTP : {e}")


def verify_reset_code(username, reset_code):
    """Vérifie le code de réinitialisation."""
    users = load_users()
    if username in users and users[username].get("reset_code") == reset_code:
        return True
    return False


def update_password(username, new_password):
    """Met à jour le mot de passe d'un utilisateur."""
    users = load_users()
    if username in users:
        users[username]["password"] = hash_password(new_password)
        users[username].pop("reset_code", None)
        save_users(users)
        return True
    return False
