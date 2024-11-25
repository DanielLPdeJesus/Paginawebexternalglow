import pyrebase
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS, cross_origin
import logging
import uuid
import base64
import requests
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

        # Validación básica
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
            # Consulta específica para verificar duplicados
            reservations_ref = db.child('reservaciones')
            # Utilizamos orderByChild y equalTo para filtrar las reservaciones
            query = reservations_ref.order_by_child('fecha').equal_to(date)
            existing_reservations = query.get()

            if existing_reservations:
                for reservation in existing_reservations:
                    reservation_data = reservation.val()
                    # Verificación más estricta de duplicados
                    is_duplicate = (
                        str(reservation_data.get('id_usuario')) == str(user_id) and
                        str(reservation_data.get('id_negocio')) == str(business_id) and
                        reservation_data.get('hora_seleccionada') == selected_time and
                        reservation_data.get('estado') not in ['cancelada', 'rechazada']
                    )

                    if is_duplicate:
                        return jsonify({
                            "success": False,
                            "message": "Ya tienes una reservación activa para esta fecha y hora en este negocio."
                        }), 409

            # Si no hay duplicados, crear la reservación
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

            # Procesar imagen si existe
            if image:
                image_data = base64.b64decode(image.split(',')[1])
                file_name = f"reservacion_imagenes/{uuid.uuid4()}.jpg"
                storage = firebase.storage()
                storage.child(file_name).put(image_data)
                image_url = storage.child(file_name).get_url(None)
                reservation_data['imagen_url'] = image_url

            # Crear la nueva reservación
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
                if (business_data.get('negocio_aceptado', False) is True and
                    business_data.get('negocio_activo', False) is True):
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
                    'plus_code': business.get('plus_code'),
                    'owner_name': business.get('nombre_propietario'),
                    'email': business.get('correo'),
                    'phone_number': business.get('numero_telefono'),
                    'profile_image': business.get('perfiles_imagenes'),
                    'business_images': business.get('negocios_imagenes', []),
                    'services_offered': business.get('servicios_imagenes'),
                    'opening_hours': business.get('horas_trabajo', {}),
                    'calificacion_promedio': business.get('calificacion_promedio', 0),
                    'numero_gustas': business.get('numero_gustas', 0),
                    'no_me_gustas': business.get('no_me_gustas', 0),
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



@main.route('/api/user-reservations/<string:user_id>', methods=['GET'])
@cross_origin()
def get_user_reservations(user_id):
    try:
        # Usar shallow=True para obtener solo las claves primero
        all_reservations_ref = db.child('reservaciones')
        all_reservations = all_reservations_ref.get()

        user_reservations = []

        if all_reservations.each():
            for reservation_snapshot in all_reservations.each():
                # Obtener cada reservación individualmente para evitar caché
                reservation_data = db.child('reservaciones').child(reservation_snapshot.key()).get().val()

                # En get_user_reservations, modifica el formatted_reservation para incluir el ID
                if reservation_data and reservation_data.get('id_usuario') == user_id:
                    formatted_reservation = {
                        "id": reservation_snapshot.key(),  # Añade esta línea para incluir el ID
                        "comentarios": reservation_data.get('comentarios', ''),
                        "comentariosnego": reservation_data.get('comentariosnego', ''),
                        "estado": reservation_data.get('estado', ''),
                        "fecha": reservation_data.get('fecha', ''),
                        "fecha_actualizacion": reservation_data.get('fecha_actualizacion', ''),
                        "fecha_creacion": reservation_data.get('fecha_creacion', ''),
                        "hora_seleccionada": reservation_data.get('hora_seleccionada', ''),
                        "id_negocio": reservation_data.get('id_negocio', ''),
                        "id_usuario": reservation_data.get('id_usuario', ''),
                        "imagen_url": reservation_data.get('imagen_url', ''),
                        "peticion": reservation_data.get('peticion', ''),
                        "tipo_de_servicio": reservation_data.get('tipo_de_servicio', '')
                    }
                    user_reservations.append(formatted_reservation)

        # Agregar headers para evitar caché
        response = jsonify({
            "success": True,
            "reservations": user_reservations
        })
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response, 200

    except Exception as e:
        print(f"Error al obtener las reservaciones del usuario: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al obtener las reservaciones del usuario.",
            "error": str(e)
        }), 500

@main.route('/api/cancel-reservation/<string:reservation_id>', methods=['PUT'])
@cross_origin()
def cancel_reservation(reservation_id):
    try:
        data = request.json
        user_id = data.get('userId')
        token = data.get('token')  # Obtener el token del body

        if not user_id:
            return jsonify({
                "success": False,
                "message": "Usuario no autenticado."
            }), 401

        try:
            # Actualizar el estado sin verificación adicional
            db.child('reservaciones').child(reservation_id).update({
                'estado': 'cancelada',
                'fecha_actualizacion': datetime.now().isoformat()
            })

            return jsonify({
                "success": True,
                "message": "Reservación cancelada exitosamente."
            }), 200

        except Exception as e:
            print(f"Error al actualizar la reservación: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error al cancelar la reservación.",
                "error": str(e)
            }), 500

    except Exception as e:
        print(f"Error general: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al procesar la solicitud.",
            "error": str(e)
        }), 500



@main.route('/api/process-hairstyle', methods=['POST'])
@cross_origin()
def process_hairstyle():
    try:
        data = request.json
        base64_image = data.get('image')
        hair_style = data.get('hair_style')
        user_id = data.get('userId')

        if not all([base64_image, hair_style, user_id]):
            return jsonify({
                "success": False,
                "message": "Faltan datos requeridos"
            }), 400

        # Guardar la imagen base64 como archivo temporal
        image_data = base64.b64decode(base64_image.split(',')[1])
        temp_path = f"/tmp/{user_id}_temp.jpg"
        with open(temp_path, 'wb') as f:
            f.write(image_data)

        url = "https://www.ailabapi.com/api/portrait/effects/hairstyle-editor-pro"
        api_key = os.getenv('AILAB_API_KEY') 
        
        if not api_key:
            raise Exception("API key no configurada")
            
        payload = {'task_type': 'async', 'auto': '1', 'hair_style': hair_style}
        files = [('image', ('file', open(temp_path, 'rb'), 'application/octet-stream'))]
        headers = {'ailabapi-api-key': api_key}

        response = requests.post(url, headers=headers, data=payload, files=files)
        os.remove(temp_path)  # Limpiar archivo temporal

        if response.status_code == 200:
            task_data = response.json()
            return jsonify({
                "success": True,
                "task_id": task_data.get('task_id')
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Error al procesar la imagen"
            }), 400

    except Exception as e:
        print(f"Error en process_hairstyle: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@main.route('/api/check-hairstyle-status/<task_id>', methods=['GET'])
@cross_origin()
def check_hairstyle_status(task_id):
    try:
        url = "https://www.ailabapi.com/api/common/query-async-task-result"
        api_key = os.getenv('AILAB_API_KEY') 
        
        if not api_key:
            raise Exception("API key no configurada")
            
        headers = {'ailabapi-api-key': api_key}
        params = {'task_id': task_id}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            result = response.json()

            if result.get('task_status') == 2 and result.get('data', {}).get('images'):
                image_url = result['data']['images'][0]
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    storage = firebase.storage()
                    file_name = f"hairstyles/{task_id}.jpg"
                    storage.child(file_name).put(image_response.content)
                    firebase_url = storage.child(file_name).get_url(None)
                    result['firebase_url'] = firebase_url

            return jsonify(result), 200

        return jsonify({
            "success": False,
            "message": "Error al verificar el estado"
        }), 400

    except Exception as e:
        print(f"Error en check_hairstyle_status: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500










# Versión corregida de la API de comentarios

@main.route('/api/comments/<string:business_id>', methods=['GET'])
@cross_origin()
def get_business_comments(business_id):
    try:
        # Obtener todos los comentarios del negocio
        comments_ref = db.child('ComentariosUser').order_by_child('business_id').equal_to(business_id).get()

        comments_list = []
        if comments_ref.each():
            for comment in comments_ref.each():
                comment_data = comment.val()
                # Obtener información del usuario que comentó
                user_data = db.child('Usuarios').child(comment_data['user_id']).get().val()

                formatted_comment = {
                    'id': comment.key(),
                    'comment_text': comment_data.get('comment_text', ''),
                    'created_at': comment_data.get('created_at', ''),
                    'user_id': comment_data.get('user_id', ''),
                    'user_name': f"{user_data.get('nombre_usuario', '')} {user_data.get('apellidos', '')}",
                    'user_image': user_data.get('perfil_usuarios', ''),
                    'business_id': comment_data.get('business_id', '')
                }
                comments_list.append(formatted_comment)

        # Ordenar comentarios por fecha de creación (más recientes primero)
        comments_list.sort(key=lambda x: x['created_at'], reverse=True)

        return jsonify({
            "success": True,
            "comments": comments_list
        }), 200

    except Exception as e:
        print(f"Error al obtener los comentarios: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al obtener los comentarios.",
            "error": str(e)
        }), 500

@main.route('/api/comments', methods=['POST'])
@cross_origin()
def add_comment():
    if request.method == 'POST':
        try:
            data = request.json
            business_id = data.get('business_id')
            user_id = data.get('user_id')
            comment_text = data.get('comment_text')

            if not all([business_id, user_id, comment_text]):
                return jsonify({
                    "success": False,
                    "message": "Faltan datos requeridos."
                }), 400

            # Verificar y obtener datos del negocio primero
            business_ref = db.child('Negousers').child(business_id)
            business_data = business_ref.get().val()

            if not business_data:
                return jsonify({
                    "success": False,
                    "message": "Negocio no encontrado."
                }), 404

            # Crear el comentario
            comment_data = {
                'business_id': business_id,
                'user_id': user_id,
                'comment_text': comment_text,
                'created_at': datetime.now().isoformat(),
                'active': True
            }

            # Guardar el comentario
            new_comment = db.child('ComentariosUser').push(comment_data)

            if not new_comment:
                raise Exception("Error al crear el comentario")

            # Actualizar el contador de reseñas directamente
            current_reviews = int(business_data.get('numero_resenas', 0))

            # Usar transaction para actualizar el contador
            try:
                db.child('Negousers').child(business_id).update({
                    'numero_resenas': current_reviews + 1
                })
            except Exception as update_error:
                print(f"Error al actualizar contador: {str(update_error)}")
                # Aunque falle la actualización del contador, continuamos

            # Obtener datos del usuario para la respuesta
            try:
                user_data = db.child('Usuarios').child(user_id).get().val()
                formatted_comment = {
                    'id': new_comment['name'],
                    'comment_text': comment_text,
                    'created_at': comment_data['created_at'],
                    'user_id': user_id,
                    'user_name': f"{user_data.get('nombre_usuario', '')} {user_data.get('apellidos', '')}",
                    'user_image': user_data.get('perfil_usuarios', ''),
                    'business_id': business_id
                }
            except Exception as user_error:
                print(f"Error al obtener datos del usuario: {str(user_error)}")
                formatted_comment = {
                    'id': new_comment['name'],
                    'comment_text': comment_text,
                    'created_at': comment_data['created_at'],
                    'user_id': user_id,
                    'business_id': business_id
                }

            # Verificar el contador actualizado
            updated_business = db.child('Negousers').child(business_id).get().val()
            print(f"Contador actualizado: {updated_business.get('numero_resenas')}")

            return jsonify({
                "success": True,
                "message": "Comentario agregado exitosamente.",
                "comment": formatted_comment,
                "updated_review_count": updated_business.get('numero_resenas')
            }), 200

        except Exception as e:
            print(f"Error general: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error al procesar la solicitud.",
                "error_details": str(e)
            }), 500

    return jsonify({"success": False, "message": "Método no permitido"}), 405


@main.route('/api/comments/<string:comment_id>', methods=['DELETE'])
@cross_origin()
def delete_comment(comment_id):
    try:
        # Obtener datos del comentario
        comment_ref = db.child('ComentariosUser').child(comment_id)
        comment_data = comment_ref.get().val()

        if not comment_data:
            return jsonify({
                "success": False,
                "message": "Comentario no encontrado."
            }), 404

        business_id = comment_data.get('business_id')

        # Eliminar el comentario
        comment_ref.remove()

        if business_id:
            # Actualizar el contador de reseñas
            business_ref = db.child('Negousers').child(business_id)
            business_data = business_ref.get().val()
            current_reviews = business_data.get('numero_resenas', 1)
            # Asegurar que no sea menor que 0
            business_ref.update({'numero_resenas': max(0, current_reviews - 1)})

        return jsonify({
            "success": True,
            "message": "Comentario eliminado exitosamente."
        }), 200

    except Exception as e:
        print(f"Error al eliminar el comentario: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al eliminar el comentario.",
            "error": str(e)
        }), 500

# Endpoint para inicializar/corregir los contadores de reseñas
@main.route('/api/fix-review-counts', methods=['POST'])
@cross_origin()
def fix_review_counts():
    try:
        # Obtener todos los negocios
        businesses = db.child('Negousers').get()

        for business in businesses.each():
            business_id = business.key()

            # Contar comentarios existentes
            comments = db.child('ComentariosUser').order_by_child('business_id').equal_to(business_id).get()
            comment_count = len([c for c in comments.each()]) if comments.each() else 0

            # Actualizar el contador
            db.child('Negousers').child(business_id).update({
                'numero_resenas': comment_count
            })

        return jsonify({
            "success": True,
            "message": "Contadores actualizados correctamente"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500














@main.route('/api/business-interactions', methods=['POST'])
@cross_origin()
def update_business_interaction():
    try:
        data = request.json
        business_id = data.get('business_id')
        user_id = data.get('user_id')
        interaction_type = data.get('type')

        if not all([business_id, user_id, interaction_type]):
            return jsonify({
                "success": False,
                "message": "Faltan datos requeridos"
            }), 400

        business_ref = db.child('Negousers').child(business_id)
        business_data = business_ref.get().val()

        if not business_data:
            return jsonify({
                "success": False,
                "message": "Negocio no encontrado"
            }), 404

        current_likes = int(business_data.get('numero_gustas', 0))
        current_dislikes = int(business_data.get('no_me_gustas', 0))

        existing_interaction = None
        interactions = db.child('BusinessInteractions').get()

        if interactions.each():
            for interaction in interactions.each():
                interaction_data = interaction.val()
                if (interaction_data.get('business_id') == business_id and
                    interaction_data.get('user_id') == user_id):
                    existing_interaction = {
                        'id': interaction.key(),
                        'data': interaction_data
                    }
                    break

        try:
            if interaction_type == 'remove':
                if existing_interaction:
                    db.child('BusinessInteractions').child(existing_interaction['id']).remove()

                    if existing_interaction['data']['type'] == 'like':
                        db.child('Negousers').child(business_id).update({
                            'numero_gustas': max(0, current_likes - 1)
                        })
                    else:
                        db.child('Negousers').child(business_id).update({
                            'no_me_gustas': max(0, current_dislikes - 1)
                        })
            else:
                new_interaction_data = {
                    'business_id': business_id,
                    'user_id': user_id,
                    'type': interaction_type,
                    'created_at': datetime.now().isoformat()
                }

                if existing_interaction:
                    old_type = existing_interaction['data']['type']
                    db.child('BusinessInteractions').child(existing_interaction['id']).update(new_interaction_data)

                    if old_type != interaction_type:
                        if old_type == 'like':
                            db.child('Negousers').child(business_id).update({
                                'numero_gustas': max(0, current_likes - 1),
                                'no_me_gustas': current_dislikes + 1
                            })
                        else:
                            db.child('Negousers').child(business_id).update({
                                'no_me_gustas': max(0, current_dislikes - 1),
                                'numero_gustas': current_likes + 1
                            })
                else:
                    db.child('BusinessInteractions').push(new_interaction_data)

                    if interaction_type == 'like':
                        db.child('Negousers').child(business_id).update({
                            'numero_gustas': current_likes + 1
                        })
                    else:
                        db.child('Negousers').child(business_id).update({
                            'no_me_gustas': current_dislikes + 1
                        })

            updated_business = business_ref.get().val()

            return jsonify({
                "success": True,
                "message": "Interacción actualizada exitosamente",
                "data": {
                    "numero_gustas": int(updated_business.get('numero_gustas', 0)),
                    "no_me_gustas": int(updated_business.get('no_me_gustas', 0))
                }
            }), 200

        except Exception as update_error:
            print(f"Error en la actualización: {str(update_error)}")
            return jsonify({
                "success": False,
                "message": f"Error al actualizar los contadores: {str(update_error)}"
            }), 500

    except Exception as e:
        print(f"Error general: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error al procesar la interacción: {str(e)}"
        }), 500

# Endpoint para corregir/inicializar contadores
@main.route('/api/fix-interaction-counts', methods=['POST'])
@cross_origin()
def fix_interaction_counts():
    try:
        # Obtener todos los negocios
        businesses = db.child('Negousers').get()

        for business in businesses.each():
            business_id = business.key()

            # Contar likes y dislikes
            likes = 0
            dislikes = 0

            interactions = db.child('BusinessInteractions').get()
            if interactions.each():
                for interaction in interactions.each():
                    interaction_data = interaction.val()
                    if interaction_data.get('business_id') == business_id:
                        if interaction_data.get('type') == 'like':
                            likes += 1
                        elif interaction_data.get('type') == 'dislike':
                            dislikes += 1

            # Actualizar contadores
            db.child('Negousers').child(business_id).update({
                'numero_gustas': likes,
                'no_me_gustas': dislikes
            })

        return jsonify({
            "success": True,
            "message": "Contadores actualizados correctamente"
        }), 200

    except Exception as e:
        print(f"Error fixing counters: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error al actualizar contadores: {str(e)}"
        }), 500



@main.route('/api/business-interactions/<string:business_id>/<string:user_id>', methods=['GET'])
@cross_origin()
def get_business_interaction(business_id, user_id):
    try:
        # Buscar la interacción de manera más simple
        interactions = db.child('BusinessInteractions').get()

        user_interaction = None
        if interactions.each():
            for interaction in interactions.each():
                interaction_data = interaction.val()
                if (interaction_data.get('business_id') == business_id and
                    interaction_data.get('user_id') == user_id):
                    user_interaction = {
                        'id': interaction.key(),
                        'type': interaction_data.get('type')
                    }
                    break

        return jsonify({
            "success": True,
            "interaction": user_interaction
        }), 200

    except Exception as e:
        print(f"Error getting interaction: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al obtener la interacción",
            "error": str(e)
        }), 500












@main.route('/api/reservation-details/<string:reservation_id>', methods=['GET'])
@cross_origin()
def get_reservation_details(reservation_id):
    try:
        # 1. Obtener los detalles de la reservación
        reservation_data = db.child('reservaciones').child(reservation_id).get().val()

        if not reservation_data:
            return jsonify({
                "success": False,
                "message": "Reservación no encontrada"
            }), 404

        # 2. Obtener los detalles del negocio asociado
        business_id = reservation_data.get('id_negocio')
        business_data = db.child('Negousers').child(business_id).get().val()

        if not business_data:
            return jsonify({
                "success": False,
                "message": "Negocio no encontrado"
            }), 404

        # 3. Formatear la respuesta combinando ambos datos
        formatted_response = {
            "reservation": {
                "id": reservation_id,
                "estado": reservation_data.get('estado', ''),
                "fecha": reservation_data.get('fecha', ''),
                "hora_seleccionada": reservation_data.get('hora_seleccionada', ''),
                "tipo_de_servicio": reservation_data.get('tipo_de_servicio', ''),
                "peticion": reservation_data.get('peticion', ''),
                "comentarios": reservation_data.get('comentarios', ''),
                "comentariosnego": reservation_data.get('comentariosnego', ''),
                "fecha_creacion": reservation_data.get('fecha_creacion', ''),
                "fecha_actualizacion": reservation_data.get('fecha_actualizacion', ''),
                "imagen_url": reservation_data.get('imagen_url', '')
            },
            "business": {
                "id": business_id,
                "nombre": business_data.get('nombre_negocio', ''),
                "direccion": business_data.get('direccion_negocio', ''),
                "telefono": business_data.get('numero_telefono', ''),
                "correo": business_data.get('correo', ''),
                "logo_url": business_data.get('perfiles_imagenes', ''),
                "calificacion_promedio": business_data.get('calificacion_promedio', 0),
                "numero_gustas": business_data.get('numero_gustas', 0),
                "numero_resenas": business_data.get('numero_resenas', 0),
                "horas_trabajo": business_data.get('horas_trabajo', {}),
                "plus_code": business_data.get('plus_code', ''),
                "nombre_propietario": business_data.get('nombre_propietario', '')
            }
        }

        return jsonify({
            "success": True,
            "data": formatted_response
        }), 200

    except Exception as e:
        print(f"Error al obtener los detalles: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al obtener los detalles de la reservación",
            "error": str(e)
        }), 500



@main.route('/api/business-reservations/<string:business_id>/<string:date>', methods=['GET'])
@cross_origin()
def get_business_reservations(business_id, date):
    try:
        reservations_ref = db.child('reservaciones')
        query = reservations_ref.order_by_child('fecha').equal_to(date)
        reservations = query.get()

        business_reservations = []
        if reservations.each():
            for reservation in reservations.each():
                reservation_data = reservation.val()
                if reservation_data.get('id_negocio') == business_id:
                    business_reservations.append({
                        'id': reservation.key(),
                        'hora_seleccionada': reservation_data.get('hora_seleccionada'),
                        'estado': reservation_data.get('estado')
                    })

        return jsonify({
            "success": True,
            "reservations": business_reservations
        }), 200

    except Exception as e:
        print(f"Error al obtener las reservaciones: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error al obtener las reservaciones.",
            "error": str(e)
        }), 500
        
@main.route('/api/businnes-acept-admin-jaydey-external', methods=['GET'])
@cross_origin()
def get_all_businnes_acept_jaydey():
    try:
        business_acept = db.child('Negousers').get()
        business_list_acept = []
        
        if business_acept.each():
            for business in business_acept.each():
                business_data = business.val()
                if (business_data.get('negocio_aceptado', True) is False and 
                    business_data.get('terminos_aceptados', False) is True):
                    business_data['id'] = business.key()
                    business_list_acept.append(business_data)

        return jsonify({
            "success": True, 
            "pending_businesses": business_list_acept,
            "total_pending": len(business_list_acept),
            "message": "Negocios pendientes de aceptación con términos aceptados"
        }), 200
        
    except Exception as e:
        print(f"Error al obtener los negocios pendientes: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "Error al obtener los negocios pendientes de aceptación.", 
            "error": str(e)
        }), 500