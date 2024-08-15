import pyrebase
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS, cross_origin
import logging
import uuid
import base64
from datetime import datetime

project_folder = os.path.expanduser('~/externalglow')
logging.warning(project_folder)
load_dotenv(os.path.join(project_folder, '.env'))

load_dotenv()


main = Blueprint('ServicesMovil', __name__, url_prefix='/ServicesMovil')

config = {
    "apiKey": os.getenv("API_KEY"),
    "authDomain": os.getenv("AUTH_DOMAIN"),
    "databaseURL": os.getenv("DATABASE_URL"),
    "projectId": os.getenv("PROJECT_ID"),
    "storageBucket": os.getenv("STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
    "appId": os.getenv("APP_ID")
}

logging.warning(config)

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

@main.route('/api/register', methods=['POST'])
@cross_origin()
def api_register():
    if request.method == 'POST':
        data = request.json 
        
        full_name = data.get('fullName')
        last_name = data.get('lastName')
        email = data.get('email')
        phone_number = data.get('phone')
        gender = data.get('gender')
        birth_date = data.get('birthDate')
        password = data.get('password')
        profile_image = data.get('profileImage')  
        
        if not profile_image:
            return jsonify({
                "success": False,
                "message": "La imagen de perfil es obligatoria."
            }), 400

        try:
            user = auth.create_user_with_email_and_password(email, password)
            
            auth.send_email_verification(user['idToken'])
            
            image_data = base64.b64decode(profile_image.split(',')[1])
            file_name = f"profile_images/{user['localId']}.jpg"
            storage = firebase.storage()
            storage.child(file_name).put(image_data)
            profile_image_url = storage.child(file_name).get_url(None)
            
            user_data = {
                "full_name": full_name,
                "last_name": last_name,
                "email": email,
                "phone_number": phone_number,
                "gender": gender,
                "birth_date": birth_date,
                "role": "usuario",
                "terms_accepted": True,
                "profile_image": profile_image_url,
                "active": True
            }
            
            db.child('Users').child(user['localId']).set(user_data)
            
            return jsonify({
                "success": True,
                "message": "Registro exitoso. Se ha enviado un correo de verificación."
            }), 200
        
        except Exception as e:
            print(f"Error durante el registro: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error durante el registro. Por favor, inténtalo de nuevo.",
                "error": str(e)
            }), 400

    return jsonify({"success": False, "message": "Método no permitido"}), 405


@main.route('/api/login', methods=['POST'])
@cross_origin()
def api_login():
    if request.method == 'POST':
        data = request.json
        
        email = data.get('email')
        password = data.get('password')
        
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            
            user_info = auth.get_account_info(user['idToken'])
            
            if not user_info['users'][0]['emailVerified']:
                return jsonify({
                    "success": False,
                    "message": "Por favor, verifica tu correo electrónico antes de iniciar sesión."
                }), 401
            
            user_data = db.child('Users').child(user['localId']).get().val()
            
            if not user_data.get('active', False):
                return jsonify({
                    "success": False,
                    "message": "Tu cuenta está inactiva. Por favor, contacta al administrador."
                }), 403
            
            response_data = {
                "success": True,
                "message": "Inicio de sesión exitoso",
                "user": {
                    "uid": user['localId'],
                    "email": email,
                    "full_name": user_data.get('full_name'),
                    "last_name": user_data.get('last_name'),
                    "phone_number": user_data.get('phone_number'),
                    "gender": user_data.get('gender'),
                    "birth_date": user_data.get('birth_date'),
                    "role": user_data.get('role'),
                    "profile_image": user_data.get('profile_image'),
                    "active": user_data.get('active')
                },
                "id_token": user['idToken']
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            print(f"Error durante el inicio de sesión: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error durante el inicio de sesión. Por favor, verifica tus credenciales e inténtalo de nuevo.",
            }), 401
    
    return jsonify({"success": False, "message": "Método no permitido"}), 405


@main.route('/api/recuperar-password', methods=['POST'])
@cross_origin()
def recuperar_password():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Por favor, ingresa una dirección de correo electrónico.'}), 400

    try:
        auth.send_password_reset_email(email)
        return jsonify({'message': 'Se ha enviado un enlace de restablecimiento de contraseña a tu correo electrónico.'}), 200
    except Exception as e:
        return jsonify({'error': 'Verifica que has ingresado un correo electrónico válido.'}), 400


@main.route('/api/reservation', methods=['POST'])
@cross_origin()
def api_reservation():
    if request.method == 'POST':
        data = request.json

        business_id = data.get('businessId')
        selected_time = data.get('selectedTime')
        date = data.get('date')
        service_type = data.get('serviceType')
        request_details = data.get('requestDetails')
        comments = data.get('comments')
        terms_accepted = data.get('termsAccepted')
        image = data.get('image')  
        user_id = data.get('userId') 

        if not terms_accepted:
            return jsonify({
                "success": False,
                "message": "Debes aceptar los términos y condiciones."
            }), 400

        if not user_id:
            return jsonify({
                "success": False,
                "message": "Usuario no autenticado."
            }), 401

        try:
            reservation_data = {
                "business_id": business_id,
                "hora_seleccionada": selected_time,
                "fecha": date,
                "tipo_de_servicio": service_type,
                "peticion": request_details,
                "comentarios": comments,
                "user_id": user_id,
                "estado": "pendiente",
                "fecha_creacion": datetime.now().isoformat(),
                "fecha_actualizacion": datetime.now().isoformat()
            }

            if image:
                image_data = base64.b64decode(image.split(',')[1])
                file_name = f"reservation_images/{uuid.uuid4()}.jpg"
                storage = firebase.storage()
                storage.child(file_name).put(image_data)
                image_url = storage.child(file_name).get_url(None)
                reservation_data['imagen_url'] = image_url

            new_reservation = db.child('reservaciones').push(reservation_data)

            db.child('estadisticas').child('reservaciones_totales').transaction(lambda current_value: current_value + 1 if current_value else 1)
            current_month = datetime.now().strftime('%Y-%m')
            db.child('estadisticas').child('reservaciones_por_mes').child(current_month).transaction(lambda current_value: current_value + 1 if current_value else 1)

            return jsonify({
                "success": True,
                "message": "Reservación realizada exitosamente.",
                "reservation_id": new_reservation['name']
            }), 200

        except Exception as e:
            print(f"Error durante la reservación: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error durante la reservación. Por favor, inténtalo de nuevo.",
                "error": str(e)
            }), 400

    return jsonify({"success": False, "message": "Método no permitido"}), 405