from flask import Blueprint, render_template, session, abort, flash, redirect
from src.models.Authentication import login_required, db

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

@main.route('/<path:token>/dashboard_premium')
@login_required
def dashboard_premium(token=None):
    if token and token != session.get('token'):
        abort(404)
    
    business_id = session.get('user_id') 
    print(f"Business ID: {business_id}") 
    
    todas_reservaciones = db.child('reservaciones').get().val()
    print(f"Todas las reservaciones: {todas_reservaciones}") 
    
    if todas_reservaciones is None:
        todas_reservaciones = {}
    
    reservaciones_negocio = {id: data for id, data in todas_reservaciones.items() if str(data.get('business_id')) == str(business_id)}
    print(f"Reservaciones del negocio: {reservaciones_negocio}")
    
    reservaciones_list = [{"id": id, **data} for id, data in reservaciones_negocio.items()]

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

@main.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect('/login')

@main.route('/test')
def test():
        negocios = db.child('Negousers').get().val()
        if negocios is None:
            negocios = {}
        
        negocios_list = [{"id": id, "nombre": data.get('business_name')} for id, data in negocios.items()]
        
        return render_template('/Users/test.html', negocios=negocios_list)
    
@main.route('/<path:token>/cover')
@login_required
def cover(token=None):
    return render_template('/Admin/cover.html')

@main.route('/<path:token>/dashboard_regular')
@login_required
def dashboard_regular(token=None):
    business_id = session.get('user_id')
    return render_template('/Admin/dashboard_regular.html', business_id=business_id)