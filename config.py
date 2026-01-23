import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
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
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Demo ortamı logları
        import logging
        app.logger.setLevel(logging.INFO)
        app.logger.info('Demo ortamı başlatıldı')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'demo': DemoConfig,
    'default': DevelopmentConfig
}

def get_database_url():
    """ENV değişkenine göre doğru veritabanı URL'ini döndürür"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Railway/Heroku postgres:// formatını postgresql:// olarak düzelt
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
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
