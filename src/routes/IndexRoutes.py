from flask import Blueprint, render_template

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

@main.route('/dashboard')
def dasboard():
    return render_template('Admin/dashboard.html')


@main.route('/resetpass')
def resetpass():
    return render_template('Auth/Admin/resetpass.html')


@main.route('/contact')
def contact():
    return render_template('Users/contact.html')

@main.route('/services')
def services():
    return render_template('Users/services.html')