import hashlib
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import id_mail


USERS_FILE = "users.json"
RESET_CODES_FILE = "reset_codes.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_reset_codes():
    try:
        with open(RESET_CODES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_reset_codes(codes):
    with open(RESET_CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)

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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username, password):
    users = load_users()
    if username in users and users[username]["password"] == hash_password(password):
        return True
    return False

def send_reset_email(email, username):
    """Envoie un code de réinitialisation par email."""
    reset_code = generate_reset_code()
    codes = load_reset_codes()
    codes[username] = reset_code
    save_reset_codes(codes)

    # Configuration de l'email
    sender_email = id_mail.sender_email
    sender_password = id_mail.sender_password
    receiver_email = email
    subject = "Code de réinitialisation de mot de passe"
    body = f"Bonjour {username},\n\nVotre code de réinitialisation est : {reset_code}\n\nCordialement."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Envoi via SMTP Gmail
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Sécurise la connexion
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("E-mail envoyé avec succès.")
    except smtplib.SMTPException as e:
        print(f"Erreur SMTP : {e}")

def generate_reset_code():
    """Génère un code de réinitialisation aléatoire."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def verify_reset_code(reset_code, email):
    """Vérifie le code de réinitialisation."""
    codes = load_reset_codes()
    for username, code in codes.items():
        if code == reset_code and load_users().get(username, {}).get("email") == email:
            return True
    return False
