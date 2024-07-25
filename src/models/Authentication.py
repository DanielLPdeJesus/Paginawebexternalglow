import pyrebase
from flask import Blueprint, redirect, request, flash, session, url_for, jsonify
from functools import wraps
import secrets
from dotenv import load_dotenv
import os
from flask_cors import CORS, cross_origin
import logging
from validate_email import validate_email

project_folder = os.path.expanduser('~/externalglow')
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


#############################################################################
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
        opening_hours = request.form['opening_hours']
        accept_terms = request.form.get('accept-terms')  

        business_images = request.files.getlist('business-image-upload')
        service_images = request.files.getlist('service-image-upload')

        # Verificar la aceptación de los términos
        if not accept_terms:
            flash('Debes aceptar los términos y condiciones para registrarte.', 'danger')
            return redirect('/register')

        # Verificar que se hayan enviado las imágenes y que haya al menos 3 en cada categoría
        if len(business_images) < 3 or len(service_images) < 3:
            flash('Debes subir al menos 3 imágenes para el negocio y 3 para los servicios.', 'danger')
            return redirect('/register')

        try:
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])

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
                "statusnego": False
            }

            business_image_urls = []
            service_image_urls = []

            # Subir imágenes del negocio
            for image in business_images:
                if image and image.filename:
                    storage = firebase.storage()
                    image_name = f"{user['localId']}_business_{image.filename}"
                    storage.child(f"business_images/{image_name}").put(image)
                    image_url = storage.child(f"business_images/{image_name}").get_url(None)
                    business_image_urls.append(image_url)

            # Subir imágenes de servicios
            for image in service_images:
                if image and image.filename:
                    storage = firebase.storage()
                    image_name = f"{user['localId']}_service_{image.filename}"
                    storage.child(f"service_images/{image_name}").put(image)
                    image_url = storage.child(f"service_images/{image_name}").get_url(None)
                    service_image_urls.append(image_url)

            # Verificar que se hayan subido todas las imágenes
            if len(business_image_urls) < 3 or len(service_image_urls) < 3:
                raise Exception("No se pudieron subir todas las imágenes requeridas.")

            datos["business_images"] = business_image_urls
            datos["service_images"] = service_image_urls

            db.child('Negousers').child(user['localId']).set(datos)

            flash('¡Registro exitoso! Se ha enviado un correo de verificación a tu dirección de correo electrónico.', 'success')
            return redirect('/login')
        except Exception as e:
            print(str(e))
            flash('Error durante el registro. Por favor, inténtalo de nuevo.', 'danger')
            return redirect('/register')

    return redirect('/register')
######################################################################################################################################################        
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
                session['user_id'] = user['localId']
                session['token'] = secrets.token_hex(16) 
                
                flash('Inicio de sesión exitoso. Correo electrónico verificado.', 'success')
                dashboard_url = url_for('index_blueprint.dashboard', token=session['token'])
                return redirect(dashboard_url)
            else:
                flash('¡Verifica tu correo electrónico antes de iniciar sesión!', 'warning')
                return redirect('/login')

        except Exception as e:
            print(f"Error de login: {str(e)}")
            flash('Error durante el inicio de sesión. Por favor, verifica tus credenciales y vuelve a intentarlo.', 'danger')
            return redirect('/login')  

    return redirect('/login')


####################################################################################################################################
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

        try:
            user = auth.create_user_with_email_and_password(email, password)
            
            auth.send_email_verification(user['idToken'])
            
            user_data = {
                "full_name": full_name,
                "last_name": last_name,
                "email": email,
                "phone_number": phone_number,
                "gender": gender,
                "birth_date": birth_date,
                "role": "usuario"
                
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

    return jsonify({"success": False, "message": "Método no permitidoo"}), 405




            