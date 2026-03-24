import os
import flask.json

# Monkeypatch for flask-mongoengine compatibility with Flask 3.0+
if not hasattr(flask.json, 'override_json_encoder'):
    flask.json.override_json_encoder = lambda app, cls: None

# Flask 3.0 removed JSONEncoder from flask.json
try:
    from flask.json import JSONEncoder
except ImportError:
    import json
    class JSONEncoder(json.JSONEncoder):
        pass
    flask.json.JSONEncoder = JSONEncoder

if not hasattr(flask, 'json_encoder'):
    flask.json_encoder = JSONEncoder

from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_cors import CORS # Added import
from extensions import socketio, jwt
from models.database import User, init_db
from config import config
from services.ngrok_service import ngrok_service
import requests

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='src/templates')
    
    # Flask 3.0+ compatibility for flask-mongoengine
    if not hasattr(app, 'json_encoder'):
        app.json_encoder = flask.json.JSONEncoder
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Enable CORS for the Flask app
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    jwt.init_app(app)
    # Use threading mode for better stability on Windows dev environments
    # Initialize SocketIO with CORS
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(id=user_id).first()
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    from src.blueprints.auth import auth_bp
    from src.blueprints.main import main_bp
    from src.blueprints.fir import fir_bp
    from src.blueprints.analysis import analysis_bp
    from src.blueprints.coordination import coordination_bp
    from src.blueprints.sos import sos_bp
    from src.blueprints.user import user_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(fir_bp, url_prefix='/fir')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(coordination_bp, url_prefix='/api')
    app.register_blueprint(sos_bp, url_prefix='/sos')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # Unified Mobile Proxy: Intercept non-API requests and forward to Vite
    if os.getenv('SENTINEL_MOBILE_MODE') == 'true':
        @app.before_request
        def proxy_to_frontend():
            # SMART ROUTING: 
            # 1. Localhost (127.0.0.1) -> Serves regular Web CMS (Police/Admin)
            # 2. Ngrok Host (Mobile Device) -> Serves Citizen Mobile App
            if 'ngrok-free.dev' not in request.host:
                return None # Regular Web CMS for Local Access
            
            # If accessing via Ngrok, we want the Mobile App
            # But we still let API/Auth requests pass to blueprints
            if request.path.startswith(('/api', '/auth', '/sos', '/fir', '/analysis', '/static')):
                return None # Continue to regular routing for Mobile API calls
            
            # For everything else, proxy to Vite
            # We use request.path instead of full_path to avoid trailing '?' issues
            query_string = f"?{request.query_string.decode()}" if request.query_string else ""
            target_url = f"http://localhost:5173{request.path}{query_string}"
            try:
                # Optimized proxy logic
                resp = requests.request(
                    method=request.method,
                    url=target_url,
                    headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
                    data=request.get_data(),
                    cookies=request.cookies,
                    allow_redirects=False
                )
                
                # Filter response headers
                excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
                headers = [(name, value) for (name, value) in resp.headers.items()
                           if name.lower() not in excluded_headers]
                
                return resp.content, resp.status_code, headers
            except Exception as e:
                return f"<b>Mobile Engine Offline</b><br>Make sure 'npm run dev' is running in citizen-mobile folder! Error: {str(e)}", 502
    
    # Socket.IO Room Management (Supporting both default and /police namespaces)
    from flask_socketio import join_room, leave_room
    
    @socketio.on('join', namespace='/police')
    @socketio.on('join')
    def on_join(data):
        room = data.get('room')
        if room:
            join_room(room)
            import logging
            logging.getLogger(__name__).info(f"Client joined room: {room} (Namespace: {getattr(request, 'namespace', 'default')})")

    @socketio.on('leave', namespace='/police')
    @socketio.on('leave')
    def on_leave(data):
        room = data.get('room')
        if room:
            leave_room(room)
            import logging
            logging.getLogger(__name__).info(f"Client left room: {room} (Namespace: {getattr(request, 'namespace', 'default')})")

    return app

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Note: Mobile access is now handled exclusively via: python start_mobile.py
    # This prevents 'socket 305' errors and double-tunneling on Windows.
        
    # Use allow_unsafe_werkzeug=True for development with threading
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True, allow_unsafe_werkzeug=True)