import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/crime_management_v2'
    }

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    MONGODB_SETTINGS = {
        'host': 'mongodb://localhost:27017/crime_management_test'
    }

class ProductionConfig(Config):
    DEBUG = False
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGODB_URI')
    }

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
