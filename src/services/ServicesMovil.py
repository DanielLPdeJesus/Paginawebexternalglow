import pyrebase
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS, cross_origin
import logging
import uuid
import base64
from werkzeug.utils import secure_filename
from datetime import datetime

project_folder = os.path.expanduser('~/external')
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
            file_name = f"perfil_usuarios/{user['localId']}.jpg"
            storage = firebase.storage()
            storage.child(file_name).put(image_data)
            profile_image_url = storage.child(file_name).get_url(None)
            
            user_data = {
                "nombre_usuario": full_name,
                "apellidos": last_name,
                "correo": email,
                "numero_telefono": phone_number,
                "genero": gender,
                "fecha_cumpleanos": birth_date,
                "rol": "usuario",
                "terminos_aceptados": True,
                "perfil_usuarios": profile_image_url,
                "activo": True
            }
            
            db.child('Usuarios').child(user['localId']).set(user_data)
            
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
            
            user_data = db.child('Usuarios').child(user['localId']).get().val()
            
            if not user_data.get('activo', False):
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
                    "full_name": user_data.get('nombre_usuario'),
                    "last_name": user_data.get('apellidos'),
                    "phone_number": user_data.get('numero_telefono'),
                    "gender": user_data.get('genero'),
                    "birth_date": user_data.get('fecha_cumpleanos'),
                    "role": user_data.get('rol'),
                    "profile_image": user_data.get('perfil_usuarios'),
                    "active": user_data.get('activo')
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
                "id_negocio": business_id,
                "hora_seleccionada": selected_time,
                "fecha": date,
                "tipo_de_servicio": service_type,
                "peticion": request_details,
                "comentarios": comments,
                "id_usuario": user_id,
                "estado": "pendiente",
                "comentariosnego": "En proceso",
                "fecha_creacion": datetime.now().isoformat(),
                "fecha_actualizacion": datetime.now().isoformat()
            }

            if image:
                image_data = base64.b64decode(image.split(',')[1])
                file_name = f"reservacion_imagenes/{uuid.uuid4()}.jpg"
                storage = firebase.storage()
                storage.child(file_name).put(image_data)
                image_url = storage.child(file_name).get_url(None)
                reservation_data['imagen_url'] = image_url

            new_reservation = db.child('reservaciones').push(reservation_data)

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

@main.route('/api/update-profile', methods=['PUT'])
@cross_origin()
def update_profile():
    if request.method == 'PUT':
        data = request.json
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Usuario no autenticado."
            }), 401

        try:
            current_user_data = db.child('Usuarios').child(user_id).get().val()
            
            if not current_user_data:
                return jsonify({
                    "success": False,
                    "message": "Usuario no encontrado."
                }), 404

            update_fields = ['nombre_usuario', 'apellidos', 'numero_telefono', 'genero', 'fecha_cumpleanos']
            user_data = {}
            for field in update_fields:
                if data.get(field) is not None:
                    user_data[field] = data.get(field)
                elif field in current_user_data:
                    user_data[field] = current_user_data[field]
            db.child('Usuarios').child(user_id).update(user_data)
            
            return jsonify({
                "success": True,
                "message": "Perfil actualizado exitosamente."
            }), 200
        
        except Exception as e:
            print(f"Error al actualizar el perfil: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error al actualizar el perfil. Por favor, inténtalo de nuevo.",
                "error": str(e)
            }), 400

    return jsonify({"success": False, "message": "Método no permitido"}), 405

@main.route('/api/update-profile-image', methods=['PUT'])
@cross_origin()
def update_profile_image():
    if 'profileImage' not in request.files:
        return jsonify({
            "success": False,
            "message": "No se encontró la imagen en la solicitud."
        }), 400

    user_id = request.form.get('userId')
    if not user_id:
        return jsonify({
            "success": False,
            "message": "Usuario no autenticado."
        }), 401

    file = request.files['profileImage']
    if file.filename == '':
        return jsonify({
            "success": False,
            "message": "No se seleccionó ningún archivo."
        }), 400

    if file:
        try:
            filename = secure_filename(f"{user_id}_perfil_{uuid.uuid4()}.jpg")
            
            temp_path = os.path.join('/tmp', filename)
            file.save(temp_path)
            
            storage = firebase.storage()
            storage.child(f"perfil_usuarios/{filename}").put(temp_path)
            profile_image_url = storage.child(f"perfil_usuarios/{filename}").get_url(None)
            
            db.child('Usuarios').child(user_id).update({"perfil_usuarios": profile_image_url})
            
            os.remove(temp_path)
            
            return jsonify({
                "success": True,
                "message": "Imagen de perfil actualizada exitosamente.",
                "profile_image_url": profile_image_url
            }), 200
        
        except Exception as e:
            print(f"Error al actualizar la imagen de perfil: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error al actualizar la imagen de perfil. Por favor, inténtalo de nuevo.",
                "error": str(e)
            }), 500

    return jsonify({
        "success": False,
        "message": "Ocurrió un error inesperado."
    }), 500

@main.route('/api/get-user-profile', methods=['GET'])
@cross_origin()
def get_user_profile():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({
            "success": False,
            "message": "Usuario no autenticado."
        }), 401

    try:
        user_data = db.child('Usuarios').child(user_id).get().val()
        if user_data:
            return jsonify({
                "success": True,
                "user": user_data
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Usuario no encontrado."
            }), 404
    except Exception as e:
        print(f"Error al obtener el perfil del usuario: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al obtener el perfil del usuario.",
            "error": str(e)
        }), 500 
        
        
@main.route('/api/businesses', methods=['GET'])
@cross_origin()
def get_all_businesses():
    try:
        businesses = db.child('Negousers').get()
        business_list = []
        if businesses.each():
            for business in businesses.each():
                business_data = business.val()
                if business_data.get('negocio_aceptado', False) is True:
                    business_data['id'] = business.key()
                    business_list.append(business_data)
        return jsonify({"success": True, "businesses": business_list}), 200
    except Exception as e:
        print(f"Error al obtener los negocios: {str(e)}")
        return jsonify({"success": False, "message": "Error al obtener los negocios.", "error": str(e)}), 500
    

@main.route('/api/business/<string:business_id>', methods=['GET'])
@cross_origin()
def get_business_details(business_id):
    try:
        business = db.child('Negousers').child(business_id).get().val()
        if business:
            if business.get('negocio_aceptado', False) is True:
                business['id'] = business_id
                
                business_details = {
                    'id': business_id,
                    'business_name': business.get('nombre_negocio'),
                    'business_address': business.get('direccion_negocio'),
                    'owner_name': business.get('nombre_propietario'),
                    'email': business.get('correo'),
                    'phone_number': business.get('numero_telefono'),
                    'profile_image': business.get('perfiles_imagenes'),
                    'business_images': business.get('negocios_imagenes', []),
                    'services_offered': business.get('servicios_imagenes'),
                    'opening_hours': business.get('horas_trabajo', {}),
                    'calificacion_promedio': business.get('calificacion_promedio', 0),
                    'numero_gustas': business.get('numero_gustas', 0),
                    'numero_resenas': business.get('numero_resenas', 0)
                }
                
                # Obtener promociones
                promotions = db.child('promociones').child(business_id).get().val()
                active_promotions = []
                if promotions:
                    for promo_id, promo_data in promotions.items():
                        if promo_data.get('estado') == 'activa' and promo_data.get('activa_movil') == 'true':
                            promo_data['id'] = promo_id
                            active_promotions.append(promo_data)
                
                business_details['promotions'] = active_promotions
                
                # Obtener reseñas
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

@main.route('/api/like', methods=['POST'])
@cross_origin()
def like_business():
    data = request.json
    business_id = data.get('businessId')
    user_id = data.get('userId')

    if not business_id or not user_id:
        return jsonify({"success": False, "message": "Se requieren businessId y userId"}), 400

    try:
        business_ref = db.child('Negousers').child(business_id)
        interaction_ref = db.child('BusinessInteractions').child(business_id).child(user_id)

        business_data = business_ref.get().val()
        interaction_data = interaction_ref.get().val()

        if interaction_data and interaction_data.get('disliked'):
            business_ref.update({'no_me_gustas': business_data.get('no_me_gustas', 0) - 1})

        if not interaction_data or not interaction_data.get('liked'):
            business_ref.update({'numero_gustas': business_data.get('numero_gustas', 0) + 1})
            interaction_ref.set({'liked': True, 'disliked': False})
        else:
            business_ref.update({'numero_gustas': max(0, business_data.get('numero_gustas', 0) - 1)})
            interaction_ref.set({'liked': False, 'disliked': False})

        return jsonify({"success": True, "message": "Interacción actualizada exitosamente"}), 200

    except Exception as e:
        print(f"Error al actualizar el me gusta: {str(e)}")
        return jsonify({"success": False, "message": "Error al actualizar la interacción", "error": str(e)}), 500

@main.route('/api/dislike', methods=['POST'])
@cross_origin()
def dislike_business():
    data = request.json
    business_id = data.get('businessId')
    user_id = data.get('userId')

    if not business_id or not user_id:
        return jsonify({"success": False, "message": "Se requieren businessId y userId"}), 400

    try:
        business_ref = db.child('Negousers').child(business_id)
        interaction_ref = db.child('BusinessInteractions').child(business_id).child(user_id)

        business_data = business_ref.get().val()
        interaction_data = interaction_ref.get().val()

        if interaction_data and interaction_data.get('liked'):
            business_ref.update({'numero_gustas': max(0, business_data.get('numero_gustas', 0) - 1)})

        if not interaction_data or not interaction_data.get('disliked'):
            business_ref.update({'no_me_gustas': business_data.get('no_me_gustas', 0) + 1})
            interaction_ref.set({'liked': False, 'disliked': True})
        else:
            business_ref.update({'no_me_gustas': max(0, business_data.get('no_me_gustas', 0) - 1)})
            interaction_ref.set({'liked': False, 'disliked': False})

        return jsonify({"success": True, "message": "Interacción actualizada exitosamente"}), 200

    except Exception as e:
        print(f"Error al actualizar el no me gusta: {str(e)}")
        return jsonify({"success": False, "message": "Error al actualizar la interacción", "error": str(e)}), 500

@main.route('/api/comment', methods=['POST'])
@cross_origin()
def add_comment():
    data = request.json
    business_id = data.get('businessId')
    user_id = data.get('userId')
    comment = data.get('comment')

    if not business_id or not user_id or not comment:
        return jsonify({"success": False, "message": "Se requieren businessId, userId y comment"}), 400

    try:
        business_ref = db.child('Negousers').child(business_id)
        comments_ref = db.child('BusinessComments').child(business_id)
        user_ref = db.child('Usuarios').child(user_id)

        user_data = user_ref.get().val()
        if not user_data:
            return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

        new_comment = {
            'userId': user_id,
            'userName': user_data.get('nombre_usuario', 'Usuario Anónimo'),
            'comment': comment,
            'timestamp': datetime.now().isoformat()
        }

        new_comment_ref = comments_ref.push(new_comment)

        business_data = business_ref.get().val()
        current_reviews = business_data.get('numero_resenas', 0)
        business_ref.update({'numero_resenas': current_reviews + 1})

        return jsonify({
            "success": True,
            "message": "Comentario agregado exitosamente",
            "commentId": new_comment_ref['name']
        }), 200

    except Exception as e:
        print(f"Error al agregar el comentario: {str(e)}")
        return jsonify({"success": False, "message": "Error al agregar el comentario", "error": str(e)}), 500

@main.route('/api/get-interactions', methods=['GET'])
@cross_origin()
def get_interactions():
    business_id = request.args.get('businessId')
    user_id = request.args.get('userId')

    if not business_id or not user_id:
        return jsonify({"success": False, "message": "Se requieren businessId y userId"}), 400

    try:
        interaction_ref = db.child('BusinessInteractions').child(business_id).child(user_id)
        interaction_data = interaction_ref.get().val()

        if interaction_data is None:
            interaction_data = {'liked': False, 'disliked': False}

        return jsonify({
            "success": True,
            "interactions": interaction_data
        }), 200

    except Exception as e:
        print(f"Error al obtener las interacciones: {str(e)}")
        return jsonify({"success": False, "message": "Error al obtener las interacciones", "error": str(e)}), 500
    
    
    
    
    
@main.route('/api/promotions/<string:business_id>', methods=['GET'])
@cross_origin()
def get_business_promotions(business_id):
    try:
        promotions = db.child('promociones').child(business_id).get().val()
        
        if promotions:
            active_promotions = []
            for promo_id, promo_data in promotions.items():
                if promo_data.get('estado') == 'activa' and promo_data.get('activa_movil') == 'true':
                    promo_data['id'] = promo_id
                    active_promotions.append(promo_data)
            
            return jsonify({
                "success": True,
                "promotions": active_promotions
            }), 200
        else:
            return jsonify({
                "success": True,
                "promotions": []
            }), 200
    except Exception as e:
        print(f"Error al obtener las promociones: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al obtener las promociones",
            "error": str(e)
        }), 500