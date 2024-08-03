from flask import Flask, render_template

# Routes
from .routes import IndexRoutes
from .models import Authentication, Services
from .services import ServicesMovil
from flask_cors import CORS


app = Flask(__name__)
CORS(app) 


def init_app(config):
    app.config.from_object(config)

    app.register_blueprint(IndexRoutes.main, url_prefix='/')
    app.register_blueprint(Authentication.main, url_prefix='/Authentication')
    app.register_blueprint(Services.main, url_prefix='/Services')
    app.register_blueprint(ServicesMovil.main, url_prefix='/ServicesMovil')

    return app

@app.errorhandler(404)
def page_not_found(error):
    return render_template('Auth/Admin/pagenofount.html', error_message="La página que buscas no se encuentra"), 404
    
