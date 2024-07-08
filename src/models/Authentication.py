import pyrebase
from flask import Blueprint, redirect, request, flash, session, url_for
from functools import wraps
import secrets
from dotenv import load_dotenv
import os

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

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

@main.route('/register', methods=['POST','GET'])
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
                "password": password,
                "role": "cliente"  
            }
            db.child('Negousers').child(user['localId']).set(datos)
            flash('¡Registro exitoso! Se ha enviado un correo de verificación a tu dirección de correo electrónico.', 'success')
            print('Registro exitoso. Correo de verificación enviado.')
            return redirect('/login')
        except Exception as e:
            print(str(e))
            flash('Error durante el registro. Por favor, inténtalo de nuevo.', 'danger')
            print('Error durante el registro intentelo de nuevo')
            return redirect('/register')
        
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

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

@main.route('/recurpass', methods=['GET', 'POST'])
def recurpass():
    if request.method == 'POST':
        email = request.form['email']
        try:
            auth.send_password_reset_email(email)
            flash('Se ha enviado un enlace de restablecimiento de contraseña a tu correo electrónico.', 'success')
        except Exception as e:
            flash('Verifica que has ingresado un correo electrónico válido.', 'danger')
        return redirect('/login')
    else:
        return redirect('/login')

@main.route('/contactinfo', methods=['POST'])
def contactinfo():
    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']
    asunto = request.form['asunto']
    mensaje_original = request.form['mensaje']

    datos = {
        "nombre": nombre,
        "correo": correo,
        "telefono": telefono,
        "asunto": asunto,
        "mensaje": mensaje_original
    }

    db.child('contact').push(datos)  

    return redirect('/contact')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@main.route('/test', methods=['POST'])
def test():
    # Obtener datos del formulario
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
    
    # Guardar los datos en Firebase Realtime Database
    db.child('reservaciones').push(datos)

    return redirect('/')



            