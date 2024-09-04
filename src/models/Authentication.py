import pyrebase
from flask import Blueprint, redirect, request, flash, session, url_for, jsonify
from functools import wraps
import secrets
from dotenv import load_dotenv
import os
import logging
from validate_email import validate_email
from datetime import datetime


project_folder = os.path.expanduser('~/external')
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
                "business_name": business_name,
                "owner_name": owner_name,
                "email": email,
                "phone_number": phone_number,
                "business_address": business_address,
                "services_offered": services_offered,
                "opening_hours": opening_hours,
                "role": "cliente",
                "terms_accepted": True,
                "status": False,
                "statusnego": False,
                "fecha_registro": fecha_registro,
                "calificacion_promedio": 0,
                "numero_resenas": 0,
                "numero_gustas": 0,
                "postal_code": 29950,
            }

            business_image_urls = []
            service_image_urls = []
            profile_image_url = ""

            for image in business_images:
                if image and image.filename:
                    storage = firebase.storage()
                    image_name = f"{user['localId']}_business_{image.filename}"
                    storage.child(f"business_images/{image_name}").put(image)
                    image_url = storage.child(f"business_images/{image_name}").get_url(None)
                    business_image_urls.append(image_url)

            for image in service_images:
                if image and image.filename:
                    storage = firebase.storage()
                    image_name = f"{user['localId']}_service_{image.filename}"
                    storage.child(f"service_images/{image_name}").put(image)
                    image_url = storage.child(f"service_images/{image_name}").get_url(None)
                    service_image_urls.append(image_url)
            
            if profile_images and profile_images[0].filename:
                storage = firebase.storage()
                image_name = f"{user['localId']}_profile_{profile_images[0].filename}"
                storage.child(f"profile_images/{image_name}").put(profile_images[0])
                profile_image_url = storage.child(f"profile_images/{image_name}").get_url(None)

            if len(business_image_urls) < 3 or len(service_image_urls) < 3 or not profile_image_url:
                raise Exception("No se pudieron subir todas las imágenes requeridas.")

            datos["business_images"] = business_image_urls
            datos["service_images"] = service_image_urls
            datos["profile_image"] = profile_image_url

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
                if not user_data.get('terms_accepted', False):
                    flash('No has aceptado los términos y condiciones. Por favor, regístrate nuevamente.', 'warning')
                    return redirect('/register')
                
                session['user_id'] = user['localId']
                session['token'] = secrets.token_hex(16) 
                
                if user_data.get('statusnego', False):
                    if user_data.get('status', False):  
                        return redirect(url_for('index_blueprint.dashboard_premium', token=session['token']))
                    else:  
                        return redirect(url_for('index_blueprint.dashboard_regular', token=session['token']))
                else:
                    return redirect(url_for('index_blueprint.cover',  token=session['token']))
            else:
                flash('¡Verifica tu correo electrónico antes de iniciar sesión!', 'warning')
                return redirect('/login')

        except Exception as e:
            print(f"Error de login: {str(e)}")
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
 


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


