import logging
import pyrebase
from flask import Blueprint, jsonify, redirect, request
from dotenv import load_dotenv
import os
from flask_cors import CORS, cross_origin
from cryptography.fernet import Fernet
import requests

project_folder = os.path.expanduser('~/external')
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

GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

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


    
@main.route('/get_address_suggestions', methods=['GET'])
def get_address_suggestions():
    input_text = request.args.get('input')
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={input_text}&types=address&components=country:mx&key={GOOGLE_MAPS_API_KEY}"
    
    response = requests.get(url)
    suggestions = response.json().get('predictions', [])
    
    return jsonify(suggestions)

@main.route('/get_place_details', methods=['GET'])
def get_place_details():
    place_id = request.args.get('place_id')
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_address,geometry&key={GOOGLE_MAPS_API_KEY}"
    
    response = requests.get(url)
    details = response.json().get('result', {})
    
    return jsonify(details)