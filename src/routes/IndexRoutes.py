from flask import Blueprint, render_template, session, abort, flash, redirect
from src.models.Authentication import login_required, db

main = Blueprint('index_blueprint', __name__)

@main.route('/')
def index():
    return render_template('Users/index.html')

@main.route('/login')
def login():
    return render_template('Auth/Admin/login.html')


@main.route('/register')
def register():
    return render_template('Auth/Admin/Register.html')

@main.route('/<path:token>/dashboard')
@login_required
def dashboard(token=None):
    if token and token != session.get('token'):
        abort(404)
    citas = db.child('reservaciones').get().val()
    
    if citas is None:
        citas = {}
    
    citas_list = [{"id": id, **data} for id, data in citas.items()]
    
    return render_template('Admin/dashboard.html', citas=citas_list)

@main.route('/resetpass')
def resetpass():
    return render_template('Auth/Admin/resetpass.html')


@main.route('/contact')
def contact():
    return render_template('Users/contact.html')

@main.route('/services')
def services():
    return render_template('Users/services.html')

@main.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect('/login')

@main.route('/test')
def test():
    return render_template('Users/test.html')