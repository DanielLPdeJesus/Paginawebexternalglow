import pyrebase
from flask import Blueprint, redirect, request, flash

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
            return redirect('/')
        except Exception as e:
            print(str(e))
            flash('Error durante el registro. Por favor, inténtalo de nuevo.', 'danger')
            print('Error durante el registro intentelo de nuevo')
            return redirect('/register')