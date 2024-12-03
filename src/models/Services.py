import logging
import pyrebase
from flask import Blueprint, jsonify, redirect, request
from dotenv import load_dotenv
import os
from flask_cors import CORS
from cryptography.fernet import Fernet

project_folder = os.path.expanduser('~/Paginawebexternalglow')
logging.warning(project_folder)
load_dotenv(os.path.join(project_folder, '.env'))

load_dotenv()

key = Fernet.generate_key()
cipher_suite = Fernet(key)

main = Blueprint('Services', __name__, url_prefix='/Services')

config = {
    "apiKey": os.getenv("API_KEY"),
    "authDomain": os.getenv("AUTH_DOMAIN"),
    "databaseURL": os.getenv("DATABASE_URL"),
    "projectId": os.getenv("PROJECT_ID"),
    "storageBucket": os.getenv("STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
    "appId": os.getenv("APP_ID")
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

@main.route('/contactinfo', methods=['POST'])
def contactinfo():
    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']
    asunto = request.form['asunto']
    mensaje_original = request.form['mensaje']
    
    telefono_encriptado = encrypt_data(telefono)
    mensaje_encriptado = encrypt_data(mensaje_original)

    datos = {
        "nombre": nombre,
        "correo": correo,
        "telefono": telefono_encriptado,
        "asunto": asunto,
        "mensaje": mensaje_encriptado
    }


    db.child('contact').push(datos)  

    return redirect('/contact')


def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()

