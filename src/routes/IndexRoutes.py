from flask import Blueprint, render_template, session, abort, flash, redirect
from src.models.Authentication import login_required, db, premium_required

main = Blueprint('index_blueprint', __name__, url_prefix='/')

@main.route('/')
def index():
    return render_template('/Users/index.html')

@main.route('/login')
def login():
    return render_template('/Auth/Admin/login.html')


@main.route('/register')
def register():
    return render_template('/Auth/Admin/Register.html')

@main.route('/dashboard_premium')
@login_required
@premium_required
def dashboard_premium(token=None):
    if token and token != session.get('token'):
        abort(404)
    
    business_id = session.get('user_id')
    print(f"Business ID: {business_id}")
    
    todas_reservaciones = db.child('reservaciones').get().val()
    print(f"Todas las reservaciones: {todas_reservaciones}")
    
    if todas_reservaciones is None:
        todas_reservaciones = {}
    
    reservaciones_negocio = {id: data for id, data in todas_reservaciones.items() 
                         if str(data.get('id_negocio')) == str(business_id) 
                         and data.get('estado') == 'pendiente'}
    print(f"Reservaciones pendientes del negocio: {reservaciones_negocio}")
    
    reservaciones_list = []
    for id, data in reservaciones_negocio.items():
        user_data = db.child('Usuarios').child(data.get('id_usuario')).get().val()
        reservacion = {
            "id": id,
            **data,
            "user_name": user_data.get('nombre_usuario', 'N/A'),
            "last_name": user_data.get('apellidos', 'N/A'),
            "user_email": user_data.get('correo', 'N/A'),
            "user_phone": user_data.get('numero_telefono', 'N/A'),
            "user_profile_image": user_data.get('perfil_usuarios', 'N/A')
        }
        reservaciones_list.append(reservacion)
        print(f"Reservación agregada: {reservacion}")
        
    print("Reservaciones pasadas a la plantilla:", reservaciones_list)
    return render_template('/Admin/dashboard_premium.html', reservaciones=reservaciones_list)

@main.route('/resetpass')
def resetpass():
    return render_template('/Auth/Admin/resetpass.html')


@main.route('/contact')
def contact():
    return render_template('/Users/contact.html')

@main.route('/services')
def services():
    return render_template('/Users/services.html')

@main.route('/princing')
@login_required
def pricing(token=None):
    return render_template('/Admin/princing.html')

@main.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect('/login')

    
@main.route('/cover')
@login_required
def cover(token=None):
    return render_template('/Admin/cover.html')

    
@main.route('/promotions')
@login_required
@premium_required
def promotions():
    return render_template('/Admin/promotions.html')

@main.route('/dashboard_regular')
@login_required
def dashboard_regular():
    user_id = session.get('user_id')
    user_data = db.child('Negousers').child(user_id).get().val()
    if user_data and user_data.get('pagado', False):
        return redirect('/dashboard_premium')
    return render_template('/Admin/dashboard_regular.html', business_id=user_id)


@main.route('/accepted_reservations')
@login_required
@premium_required
def accepted_reservations(token=None):
    if token and token != session.get('token'):
        abort(404)
    
    business_id = session.get('user_id')
    print(f"ID del negocio: {business_id}")
    
    todas_reservaciones = db.child('reservaciones').get().val()
    
    if todas_reservaciones is None:
        print("No se encontraron reservaciones en la base de datos")
        todas_reservaciones = {}
    else:
        print(f"Total de reservaciones encontradas: {len(todas_reservaciones)}")
    
    reservaciones_negocio = {id: data for id, data in todas_reservaciones.items() 
                         if str(data.get('id_negocio')) == str(business_id) 
                         and data.get('estado') == 'aceptada'}
    
    print(f"Reservaciones aceptadas para este negocio: {len(reservaciones_negocio)}")
    
    reservaciones_list = []
    for id, data in reservaciones_negocio.items():
        user_id = data.get('id_usuario')  # Asumiendo que el campo se llama 'id_usuario'
        print(f"Procesando reservación {id} para usuario {user_id}")
        
        user_data = db.child('Usuarios').child(user_id).get().val()
        if user_data is None:
            print(f"No se encontraron datos para el usuario {user_id}")
            user_data = {} 
        
        reservacion = {
            "id": id,
            **data,
            "user_name": user_data.get('nombre_usuario', 'N/A'),
            "last_name": user_data.get('apellidos', 'N/A'),
            "user_email": user_data.get('correo', 'N/A'),
            "user_phone": user_data.get('numero_telefono', 'N/A'),
            "user_profile_image": user_data.get('perfil_usuarios', 'N/A')
        }
        reservaciones_list.append(reservacion)
        print(f"Reservación agregada: {reservacion}")
    
    print(f"Total de reservaciones procesadas: {len(reservaciones_list)}")
    return render_template('/Admin/accepted_reservations.html', reservaciones=reservaciones_list)

