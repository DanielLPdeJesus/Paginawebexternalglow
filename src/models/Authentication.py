import pyrebase
from flask import Blueprint, abort, app, redirect, request, flash, session, url_for, jsonify
from functools import wraps
import secrets
from dotenv import load_dotenv
import os
import logging
import requests
from validate_email import validate_email
from datetime import datetime, time, timedelta
from werkzeug.utils import secure_filename
import uuid


project_folder = os.path.expanduser('~/Paginawebexternalglow')
logging.warning(project_folder)
load_dotenv(os.path.join(project_folder, '.env'))

load_dotenv()


main = Blueprint('Authentication', __name__, url_prefix='/Authentication')

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


@main.route('/register', methods=['POST'])
def registrarme():
    if request.method == 'POST':
        business_name = request.form['business_name']
        owner_name = request.form['owner_name']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        business_address = request.form['business_address']
        plus_code = request.form['plus_code']
        services_offered = request.form['services_offered']
        
        # Nuevo manejo de horarios
        opening_time_1 = request.form['opening_time_1']
        closing_time_1 = request.form['closing_time_1']
        opening_time_2 = request.form.get('opening_time_2', '')
        closing_time_2 = request.form.get('closing_time_2', '')
        
        opening_hours = {
            "turno_1": f"{opening_time_1} - {closing_time_1}",
            "turno_2": f"{opening_time_2} - {closing_time_2}" if opening_time_2 and closing_time_2 else None
        }
        
        accept_terms = request.form.get('accept-terms')  

        business_images = request.files.getlist('business-image-upload')
        service_images = request.files.getlist('service-image-upload')
        profile_images = request.files.getlist('profile-image-upload')
        
        if not accept_terms:
            flash('Debes aceptar los términos y condiciones para registrarte.', 'danger')
            return redirect('/register')

        if len(business_images) < 3 or len(service_images) < 3 or len(profile_images) != 1:
            flash('Debes subir al menos 3 imágenes para el negocio, 3 para los servicios y exactamente 1 para la foto de perfil.', 'danger')
            return redirect('/register')

        try:
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])
            
            fecha_registro = datetime.now().isoformat()

            datos = {
                "nombre_negocio": business_name,
                "nombre_propietario": owner_name,
                "correo": email,
                "numero_telefono": phone_number,
                "direccion_negocio": business_address,
                "plus_code": plus_code,
                "servicios_ofrecidos": services_offered,
                "horas_trabajo": opening_hours,
                "rol": "cliente",
                "terminos_aceptados": True,
                "pagado": False,
                "negocio_aceptado": False,
                "negocio_activo": False,
                "fecha_registro": fecha_registro,
                "calificacion_promedio": 0,
                "numero_resenas": 0,
                "numero_gustas": 0,
                "no_me_gustas": 0,
                "numero_gustas": 0,
                "postal_code": 29950,
                "reservaCancel": 0,
                "reservaAcep": 0,
                "reserva_activo":False,
            }

            business_image_urls = []
            service_image_urls = []
            profile_image_url = ""

            for image in business_images:
                if image and image.filename:
                    storage = firebase.storage()
                    image_name = f"{user['localId']}_negocios_{image.filename}"
                    storage.child(f"negocios_imagenes/{image_name}").put(image)
                    image_url = storage.child(f"negocios_imagenes/{image_name}").get_url(None)
                    business_image_urls.append(image_url)

            for image in service_images:
                if image and image.filename:
                    storage = firebase.storage()
                    image_name = f"{user['localId']}_servicios_{image.filename}"
                    storage.child(f"servicios_imagenes/{image_name}").put(image)
                    image_url = storage.child(f"servicios_imagenes/{image_name}").get_url(None)
                    service_image_urls.append(image_url)
            
            if profile_images and profile_images[0].filename:
                storage = firebase.storage()
                image_name = f"{user['localId']}_perfiles_{profile_images[0].filename}"
                storage.child(f"perfiles_imagenes/{image_name}").put(profile_images[0])
                profile_image_url = storage.child(f"perfiles_imagenes/{image_name}").get_url(None)

            if len(business_image_urls) < 3 or len(service_image_urls) < 3 or not profile_image_url:
                raise Exception("No se pudieron subir todas las imágenes requeridas.")

            datos["negocios_imagenes"] = business_image_urls
            datos["servicios_imagenes"] = service_image_urls
            datos["perfiles_imagenes"] = profile_image_url

            db.child('Negousers').child(user['localId']).set(datos)

            flash('¡Registro exitoso! Se ha enviado un correo de verificación a tu dirección de correo electrónico.', 'success')
            return redirect('/login')
        except Exception as e:
            print(str(e))
            flash('Error durante el registro. Por favor, inténtalo de nuevo.', 'danger')
            return redirect('/register')

    return redirect('/register')
     
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if not email or not password:
            flash('Por favor, proporciona tanto el correo electrónico como la contraseña.', 'danger')
            return redirect('/login')

        if not validate_email(email):
            flash('Por favor, proporciona un correo electrónico válido.', 'danger')
            return redirect('/login')

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return redirect('/login')
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_info = auth.get_account_info(user['idToken'])

            if user_info['users'][0]['emailVerified']:
                user_data = db.child('Negousers').child(user['localId']).get().val()
                if not user_data.get('terminos_aceptados', False):
                    flash('No has aceptado los términos y condiciones. Por favor, regístrate nuevamente.', 'warning')
                    return redirect('/register')
                
                session['user_id'] = user['localId']
                session['token'] = secrets.token_hex(16) 
                
                if user_data.get('negocio_aceptado', False):
                    if user_data.get('pagado', False):  
                        return redirect(url_for('index_blueprint.dashboard_premium', token=session['token']))
                    else:  
                        return redirect(url_for('index_blueprint.dashboard_regular', token=session['token']))
                else:
                    return redirect(url_for('index_blueprint.cover', token=session['token']))
            else:
                flash('¡Verifica tu correo electrónico antes de iniciar sesión!', 'warning')
                return redirect('/login')

        except Exception as e:
            error_message = str(e)
            print(f"Error durante el inicio de sesión: {error_message}")
            
            if 'INVALID_PASSWORD' in error_message:
                flash('Contraseña incorrecta. Por favor, verifica tus credenciales y vuelve a intentarlo.', 'danger')
            elif 'TOO_MANY_ATTEMPTS_TRY_LATER' in error_message:
                flash('Tu cuenta ha sido bloqueada temporalmente debido a demasiados intentos fallidos. Intenta nuevamente más tarde o restablece tu contraseña.', 'danger')
            else:
                flash('Error durante el inicio de sesión. Por favor, verifica tus credenciales y vuelve a intentarlo.', 'danger')
            return redirect('/login')

    return redirect('/login')

@main.route('/recurpass', methods=['GET', 'POST'])
def recurpass():
    if request.method == 'POST':
        email = request.form['email']
        
        if not email:
            flash('Por favor, ingresa una dirección de correo electrónico.', 'danger')
            return redirect('/recurpass')

        if not validate_email(email):
            flash('Por favor, ingresa una dirección de correo electrónico válida.', 'danger')
            return redirect('/login')
        try:
            auth.send_password_reset_email(email)
            flash('Se ha enviado un enlace de restablecimiento de contraseña a tu correo electrónico.', 'success')
        except Exception as e:
            flash('Verifica que has ingresado un correo electrónico válido.', 'danger')
        return redirect('/login')
    else:
        return redirect('/login')
 

def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        user_data = db.child('Negousers').child(user_id).get().val()
        if not user_data or user_data.get('pagado') != True:
            flash('Esta función requiere una membresía premium.', 'warning')
            return redirect('/dashboard_regular')
        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@main.route('/update_reservation_status/<string:reservation_id>', methods=['POST'])
@login_required
def update_reservation_status(reservation_id):
    data = request.json
    new_status = data.get('status')
    
    db.child('reservaciones').child(reservation_id).update({'estado': new_status})
    
    return jsonify({'success': True})


@main.route('/update_reservation_status_and_comment/<string:reservation_id>', methods=['POST'])
@login_required
def update_reservation_status_and_comment(reservation_id):
    data = request.json
    new_status = data.get('status')
    business_comment = data.get('reason', '')
    current_time = datetime.now().isoformat()
    
    updates = {
        'estado': new_status,
        'comentariosnego': business_comment,
        'fecha_actualizacion': current_time
    }
    
    db.child('reservaciones').child(reservation_id).update(updates)
    
    return jsonify({'success': True})


@main.before_request
def check_session_expiration():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)  
    session.modified = True

@main.route('/check_session', methods=['POST'])
def check_session():
    if 'last_activity' in session:
        last_activity = session['last_activity']
        if time.time() - last_activity > 1800: 
            session.clear()
            return jsonify({"status": "expired"}), 401
    session['last_activity'] = time.time()
    return jsonify({"status": "active"}), 200



@main.route('/crear_promocion', methods=['POST'])
def crear_promocion():
    user_id = session.get('user_id')
    start_date = request.form['start_date']
    start_time = request.form['start_time']
    end_date = request.form['end_date']
    end_time = request.form['end_time']
    discount = request.form['discount']
    promotion = request.form['promotion']
    terms_accepted = request.form.get('terms') == 'on'
    promo_accepted = request.form.get('aceptar_promo') == 'on'

    # Validaciones
    if not all([start_date, start_time, end_date, end_time, discount, promotion, terms_accepted, promo_accepted]):
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('index_blueprint.promotions'))

    try:
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
        current_datetime = datetime.now()
        
        if start_datetime < current_datetime:
            flash('La fecha de inicio no puede ser anterior a la fecha actual.', 'danger')
            return redirect(url_for('index_blueprint.promotions'))

        if end_datetime <= start_datetime:
            flash('La fecha de finalización debe ser posterior a la fecha de inicio.', 'danger')
            return redirect(url_for('index_blueprint.promotions'))

        if (end_datetime - start_datetime) > timedelta(days=3):
            flash('La promoción no puede durar más de 3 días.', 'danger')
            return redirect(url_for('index_blueprint.promotions'))

        discount = int(discount)
        if not (1 <= discount <= 100):
            flash('El porcentaje de descuento debe estar entre 1 y 100.', 'danger')
            return redirect(url_for('index_blueprint.promotions'))

        promociones_usuario = db.child('promociones').child(user_id).get().val()
        if promociones_usuario:
            promociones_activas = [promo for promo in promociones_usuario.values() 
                                   if datetime.fromisoformat(promo['fecha_fin']) > current_datetime]
            if promociones_activas:
                flash('Ya tienes una promoción activa. No puedes crear otra hasta que finalice la actual.', 'warning')
                return redirect(url_for('index_blueprint.promotions'))

            ultima_promocion = max(promociones_usuario.values(), key=lambda x: x['fecha_creacion'])
            fecha_ultima_promocion = datetime.fromisoformat(ultima_promocion['fecha_creacion'])
            if (current_datetime - fecha_ultima_promocion) < timedelta(days=3):
                flash('Debes esperar 3 días hábiles desde tu última promoción para crear una nueva.', 'warning')
                return redirect(url_for('index_blueprint.promotions'))

        negocio = db.child('Negousers').child(user_id).get().val()
        
        if not negocio:
            flash('No se encontró información del negocio.', 'danger')
            return redirect(url_for('index_blueprint.promotions'))

        nueva_promocion = {
            'fecha_inicio': start_datetime.isoformat(),
            'fecha_fin': end_datetime.isoformat(),
            'porcentaje_descuento': discount,
            'descripcion': promotion,
            'estado': 'activa',
            'fecha_creacion': current_datetime.isoformat(),
            'nombre_negocio': negocio.get('nombre_negocio', ''),
            'servicios_ofrecidos': negocio.get('servicios_ofrecidos', ''),
            'aceptada_movil': promo_accepted,
            'activa_movil':'false'
        }

        db.child('promociones').child(user_id).push(nueva_promocion)

        flash('Promoción creada exitosamente.', 'success')
    except ValueError as e:
        flash(f'Error en el formato de los datos: {str(e)}', 'danger')
    except Exception as e:
        print(str(e))
        flash('Error al crear la promoción. Por favor, inténtalo de nuevo.', 'danger')

    return redirect(url_for('index_blueprint.promotions'))


@main.route('/paypal_ipn', methods=['POST'])
def handle_paypal_ipn():
    payload = request.form.to_dict()
    payload['cmd'] = '_notify-validate'
    response = requests.post('https://ipnpb.paypal.com/cgi-bin/webscr', data=payload)
    
    if response.text != 'VERIFIED':
        abort(400)
    if payload.get('payment_status') != 'Completed':
        return 'OK'

    business_id = payload.get('custom')
    if not business_id:
        abort(400)

    ipn_data = {
        'timestamp': datetime.now().isoformat(),
        'payload': payload
    }
    db.child('ipn_logs').push(ipn_data)

    db.child('Negousers').child(business_id).update({'pagado': True})

    return 'OK'


@main.route('/mi_perfil')
@login_required
def mi_perfil():
    business_id = session.get('user_id')
    user_data = db.child('Negousers').child(business_id).get().val()

    if not business_id:
        flash('No se ha encontrado el ID del negocio.', 'danger')
        return redirect('/dashboard_regular')

    session['nombre_negocio']= user_data.get('nombre_negocio')
    session['negocio_activo']= user_data.get('negocio_activo')
    session['nombre_propietario']= user_data.get('nombre_propietario')
    session['direccion_negocio']= user_data.get('direccion_negocio')
    session['horas_trabajo']= user_data.get('horas_trabajo')
    session['correo']= user_data.get('correo')
    session['servicios_ofrecidos']= user_data.get('servicios_ofrecidos')
    session['pagado']= user_data.get('pagado')

    session['calificacion_promedio']= f'{ user_data.get("calificacion_promedio")}'
    session['numero_gustas']= f'{ user_data.get("numero_gustas")}'
    session['numero_resenas']= f'{ user_data.get("numero_resenas")}'

    session['reservaAcep']= f'{ user_data.get("reservaAcep")}'
    session['reservaCancel']= f'{ user_data.get("reservaCancel")}'

    session['numero_telefono']= f'{ user_data.get("numero_telefono")}'
    session['postal_code']= f'{ user_data.get("postal_code")}'

    session['perfiles_imagenes']= user_data.get('perfiles_imagenes')
    session['negocios_imagenes']= user_data.get('negocios_imagenes')
    session['servicios_imagenes']= user_data.get('servicios_imagenes')
    
    return redirect('/perfil')




@main.route('/update_business_profile', methods=['POST'])
@login_required
def update_business_profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    current_user_data = db.child('Negousers').child(user_id).get().val()

    data = {
        'nombre_negocio': request.form.get('business_name') or current_user_data.get('nombre_negocio'),
        'negocio_activo': request.form.get('business_state') == 'activado' if request.form.get('business_state') else current_user_data.get('negocio_activo'),
        'nombre_propietario': request.form.get('owner_name') or current_user_data.get('nombre_propietario'),
        'direccion_negocio': request.form.get('business_address') or current_user_data.get('direccion_negocio'),
        'servicios_ofrecidos': request.form.get('services_offered') or current_user_data.get('servicios_ofrecidos'),
        'horas_trabajo': current_user_data.get('horas_trabajo', {})
    }

    if request.form.get('opening_time_1') and request.form.get('closing_time_1'):
        data['horas_trabajo']['turno_1'] = f"{request.form.get('opening_time_1')} - {request.form.get('closing_time_1')}"
    if request.form.get('opening_time_2') and request.form.get('closing_time_2'):
        data['horas_trabajo']['turno_2'] = f"{request.form.get('opening_time_2')} - {request.form.get('closing_time_2')}"

    try:
        def upload_image_to_firebase(file, folder):
            if file and file.filename != '':
                filename = secure_filename(f"{user_id}_{uuid.uuid4()}.jpg")
                file_path = os.path.join(folder, filename)
                storage = firebase.storage()
                storage.child(file_path).put(file)
                url = storage.child(file_path).get_url(None)
                return url
            return None
        
        profile_image = request.files.get('profile-image-upload')
        profile_image_url = upload_image_to_firebase(profile_image, 'perfiles_imagenes') if profile_image else None

        update_data = {
            'nombre_negocio': data['nombre_negocio'],
            'negocio_activo': data['negocio_activo'],
            'nombre_propietario': data['nombre_propietario'],
            'direccion_negocio': data['direccion_negocio'],
            'servicios_ofrecidos': data['servicios_ofrecidos'],
            'horas_trabajo': data['horas_trabajo']
        }

        if profile_image_url:
            update_data['perfiles_imagenes'] = profile_image_url

        db.child('Negousers').child(user_id).update(update_data)

        flash('Perfil del negocio actualizado con éxito', 'success')
        return redirect('/Authentication/mi_perfil')
    
    except Exception as e:
        print(f"Error al actualizar el perfil del negocio: {e}")
        flash('Error al actualizar el perfil del negocio', 'error')
        return redirect('/profile')