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

from flask import Flask, render_template
from flask_login import LoginManager
from extensions import socketio, jwt
from models.database import User, init_db
from config import config

def create_app(config_name='default'):
    app = Flask(__name__, template_folder='src/templates')
    
    # Flask 3.0+ compatibility for flask-mongoengine
    if not hasattr(app, 'json_encoder'):
        app.json_encoder = flask.json.JSONEncoder
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
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
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(fir_bp, url_prefix='/fir')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(coordination_bp, url_prefix='/api')
    
    return app

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))