import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-not-for-production'
    
class ProductionConfig(Config):
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production'da SECRET_KEY zorunlu kontrolü
        secret_key = os.environ.get('FLASK_SECRET_KEY')
        if not secret_key or secret_key.strip() == '':
            raise RuntimeError(
                "ERROR: FLASK_SECRET_KEY environment variable is not set!\n"
                "Production ortamında güvenlik için FLASK_SECRET_KEY tanımlanması zorunludur.\n"
                "Örnek: export FLASK_SECRET_KEY=$(openssl rand -hex 32)"
            )
        app.config['SECRET_KEY'] = secret_key
        
        # Production için loglama ayarları
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler('logs/muhasebe.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Muhasebe Uygulaması başlatıldı')

class DemoConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'demo-secret-key-not-for-production'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Demo ortamı logları
        import logging
        app.logger.setLevel(logging.INFO)
        app.logger.info('Demo ortamı başlatıldı')

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'test-secret-key'
    # Allow override via environment variable for migration compatibility
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'demo': DemoConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_database_url():
    """ENV değişkenine göre doğru veritabanı URL'ini döndürür"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Railway/Heroku postgres:// formatını postgresql+pg8000:// olarak düzelt
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        return database_url
    else:
        # Lokal geliştirme için SQLite
        return 'sqlite:///muhasebe_demo.db'

def is_production():
    """Production ortamında mı çalıştığını kontrol eder"""
    return os.environ.get('ENV') == 'production'

def is_demo():
    """Demo ortamında mı çalıştığını kontrol eder"""
    return os.environ.get('ENV') == 'demo'

def is_testing():
    """Test ortamında mı çalıştığını kontrol eder"""
    return os.environ.get('ENV') == 'testing'

def is_development():
    """Development ortamında mı çalıştığını kontrol eder"""
    env = os.environ.get('ENV', 'default')
    return env in ['development', 'default', 'dev']
