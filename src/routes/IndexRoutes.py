from flask import Blueprint, render_template

main = Blueprint('index_blueprint', __name__)

@main.route('/')
def index():
    return render_template('Users/index.html')

@main.route('/login')
def login():
    return render_template('Auth/Users/login.html')
