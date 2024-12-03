import pytest
from flask import Flask, session, url_for
from unittest.mock import Mock, patch
import os
from src.models.Authentication import main as auth_blueprint
from werkzeug.datastructures import FileStorage
import io

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-key'
    
    # Registrar el blueprint de Authentication
    app.register_blueprint(auth_blueprint)
    
    # Registrar el blueprint index para las redirecciones
    from flask import Blueprint
    index_bp = Blueprint('index_blueprint', __name__)
    
    @index_bp.route('/dashboard_premium')
    def dashboard_premium():
        return 'Premium Dashboard'
    
    app.register_blueprint(index_bp)
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_firebase():
    with patch('src.models.Authentication.auth') as mock_auth, \
         patch('src.models.Authentication.db') as mock_db, \
         patch('src.models.Authentication.firebase.storage') as mock_storage:
        yield {
            'auth': mock_auth,
            'db': mock_db,
            'storage': mock_storage
        }

def test_login_valid_credentials(client, app, mock_firebase):
    with app.test_request_context():
        mock_firebase['auth'].sign_in_with_email_and_password.return_value = {
            'localId': 'test-user-id',
            'idToken': 'test-token'
        }
        mock_firebase['auth'].get_account_info.return_value = {
            'users': [{'emailVerified': True}]
        }
        mock_firebase['db'].child().child().get().val.return_value = {
            'terminos_aceptados': True,
            'negocio_aceptado': True,
            'pagado': True
        }

        response = client.post('/Authentication/login', data={
            'email': 'test@example.com',
            'password': 'test123456'
        }, follow_redirects=True)

        assert response.status_code == 200

def test_register_valid_data(client, app, mock_firebase):
    with app.test_request_context():
        def create_test_file(filename):
            return FileStorage(
                stream=io.BytesIO(b"test file content"),
                filename=filename,
                content_type='image/jpeg',
            )

        data = {
            'business_name': 'Test Business',
            'owner_name': 'Test Owner',
            'email': 'test@example.com',
            'password': 'test123456',
            'phone_number': '1234567890',
            'business_address': 'Test Address',
            'plus_code': 'TEST123',
            'services_offered': 'Test Services',
            'opening_time_1': '09:00',
            'closing_time_1': '18:00',
            'accept-terms': 'on'
        }

        data['business-image-upload'] = [
            create_test_file('business1.jpg'),
            create_test_file('business2.jpg'),
            create_test_file('business3.jpg')
        ]
        data['service-image-upload'] = [
            create_test_file('service1.jpg'),
            create_test_file('service2.jpg'),
            create_test_file('service3.jpg')
        ]
        data['profile-image-upload'] = [create_test_file('profile.jpg')]

        mock_storage = mock_firebase['storage'].return_value
        mock_storage.child().put.return_value = None
        mock_storage.child().get_url.return_value = "http://test-url.com/image.jpg"


        mock_firebase['auth'].create_user_with_email_and_password.return_value = {
            'localId': 'test-user-id',
            'idToken': 'test-token'
        }

        response = client.post(
            '/Authentication/register',
            data=data,
            follow_redirects=False,
            content_type='multipart/form-data'
        )

        assert response.status_code == 302
        assert '/login' in response.location
def test_login_invalid_credentials(client, mock_firebase):
    mock_firebase['auth'].sign_in_with_email_and_password.side_effect = Exception('INVALID_PASSWORD')

    response = client.post('/Authentication/login', data={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })

    assert response.status_code == 302
    assert 'login' in response.location