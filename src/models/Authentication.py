import pyrebase
from flask import Blueprint, redirect, request, flash, abort, session, url_for
from functools import wraps
import secrets

config = {
    "apiKey": "AIzaSyAVFYsPs07a3GEar4dJz2G3BOfRmQO5ZPo",
    "authDomain": "externalglow-a514c.firebaseapp.com",
    "databaseURL": "https://externalglow-a514c-default-rtdb.firebaseio.com",
    "projectId": "externalglow-a514c",
    "storageBucket": "externalglow-a514c.appspot.com",
    "messagingSenderId": "1096331594020",
    "appId": "1:1096331594020:web:1f791ec166462fea544bb1"
}

main = Blueprint('Authentication', __name__, url_prefix='/Authentication')

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
                "password": password 
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



            