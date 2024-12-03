from prometheus_client import Counter, Histogram, Gauge
from flask import request
import time

# Métricas básicas
REQUEST_COUNT = Counter(
    'flask_request_count', 
    'Contador de peticiones',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'flask_request_latency_seconds',
    'Latencia de peticiones',
    ['endpoint']
)

ACTIVE_USERS = Gauge(
    'flask_active_users',
    'Usuarios activos actuales'
)

# Métricas de Firebase
FIREBASE_OPERATIONS = Counter(
    'firebase_operations_total',
    'Operaciones de Firebase',
    ['operation', 'status']
)

def init_metrics(app):
    @app.before_request
    def before_request():
        request._prometheus_start_time = time.time()
        ACTIVE_USERS.inc()

    @app.after_request
    def after_request(response):
        # Registrar tiempo de respuesta
        if hasattr(request, '_prometheus_start_time'):
            latency = time.time() - request._prometheus_start_time
            REQUEST_LATENCY.labels(endpoint=request.endpoint).observe(latency)

        # Registrar conteo de requests
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint,
            status=response.status_code
        ).inc()

        ACTIVE_USERS.dec()
        return response

    @app.route('/metrics')
    def metrics():
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}