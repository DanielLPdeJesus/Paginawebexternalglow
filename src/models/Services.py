import logging
import pyrebase
from flask import Blueprint, jsonify, redirect, request
from dotenv import load_dotenv
import os
from flask_cors import CORS, cross_origin
from cryptography.fernet import Fernet

project_folder = os.path.expanduser('~/externalglow')
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

@main.route('/test', methods=['POST'])
def test():
    business_id = request.form.get('business_id')
    selected_time = request.form.get('selected-time')
    date = request.form.get('date')
    service_type = request.form.get('service-type')
    request_details = request.form.get('request')
    comments = request.form.get('comments')
    terms_accepted = request.form.get('accept-terms')
    image = request.files.get('image-upload')
        
    
    if not terms_accepted:
        return "Debes aceptar los términos y condiciones", 400
    
    datos = {
        "business_id": business_id,
        "hora_seleccionada": selected_time,
        "fecha": date,
        "tipo_de_servicio": service_type,
        "peticion": request_details,
        "comentarios": comments
    }

    if image:
        storage = firebase.storage()
        image_path = f"images/{image.filename}"
        storage.child(image_path).put(image)
        image_url = storage.child(image_path).get_url(None)
        datos['imagen_url'] = image_url
        
    db.child('reservaciones').push(datos)
    return redirect('/')


@main.route('/api/businesses', methods=['GET'])
@cross_origin()
def get_all_businesses():
    try:
        businesses = db.child('Negousers').get()
        business_list = []
        if businesses.each():
            for business in businesses.each():
                business_data = business.val()
                # Filtrar negocios con estatus `false`
                if business_data.get('status', False) is True:
                    # Incluir el ID del negocio en los datos
                    business_data['id'] = business.key()
                    business_list.append(business_data)
        return jsonify({"success": True, "businesses": business_list}), 200
    except Exception as e:
        print(f"Error al obtener los negocios: {str(e)}")
        return jsonify({"success": False, "message": "Error al obtener los negocios.", "error": str(e)}), 500

    

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()



            