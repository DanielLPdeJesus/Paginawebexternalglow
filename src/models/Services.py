import logging
import pyrebase
from flask import Blueprint, jsonify, redirect, request
from dotenv import load_dotenv
import os
from flask_cors import CORS, cross_origin
from cryptography.fernet import Fernet

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
                if business_data.get('status', False) is True:
                    business_data['id'] = business.key()
                    business_list.append(business_data)
        return jsonify({"success": True, "businesses": business_list}), 200
    except Exception as e:
        print(f"Error al obtener los negocios: {str(e)}")
        return jsonify({"success": False, "message": "Error al obtener los negocios.", "error": str(e)}), 500

    

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()



@main.route('/api/business/<string:business_id>', methods=['GET'])
@cross_origin()
def get_business_details(business_id):
    try:
        business = db.child('Negousers').child(business_id).get().val()
        if business:
            if business.get('status', False) is True:
                # Añadir el ID del negocio a los datos
                business['id'] = business_id
                
                # Crear un diccionario con los campos que necesitamos
                business_details = {
                    'id': business_id,
                    'business_name': business.get('business_name'),
                    'business_address': business.get('business_address'),
                    'owner_name': business.get('owner_name'),
                    'email': business.get('email'),
                    'phone_number': business.get('phone_number'),
                    'profile_image': business.get('profile_image'),
                    'business_images': business.get('business_images', []),
                    'services_offered': business.get('services_offered'),
                    'opening_hours': business.get('opening_hours', {}),
                    'calificacion_promedio': business.get('calificacion_promedio', 0),
                    'numero_gustas': business.get('numero_gustas', 0),
                    'numero_resenas': business.get('numero_resenas', 0)
                }
                
                # Obtener reseñas del negocio
                try:
                    reviews = db.child('Reviews').order_by_child('business_id').equal_to(business_id).get().val()
                    if reviews:
                        business_details['reviews'] = list(reviews.values())
                    else:
                        business_details['reviews'] = []
                        business_details['no_reviews_message'] = "No hay reseñas disponibles para este negocio."
                except Exception as review_error:
                    print(f"Error al obtener reseñas: {str(review_error)}")
                    business_details['reviews'] = []
                    business_details['no_reviews_message'] = "No se pudieron cargar las reseñas en este momento."
                
                return jsonify({"success": True, "business": business_details}), 200
            else:
                return jsonify({"success": False, "message": "El negocio no está activo."}), 404
        else:
            return jsonify({"success": False, "message": "Negocio no encontrado."}), 404
    except Exception as e:
        print(f"Error detallado al obtener los detalles del negocio: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "Error al obtener los detalles del negocio.", "error": str(e)}), 500