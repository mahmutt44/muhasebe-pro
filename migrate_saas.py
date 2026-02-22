"""
SaaS Migration Script
Mevcut veritabanını SaaS yapısına dönüştürür
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime

# Veritabanı bağlantısı
db = SQLAlchemy()

def migrate_database():
    """Veritabanını SaaS yapısına dönüştürür"""
    app = Flask(__name__)
    
    # Veritabanı konfigürasyonu
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///muhasebe_fallback.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            print("Migration başlatılıyor...")
            
            # 1. Tüm tabloları oluştur
            db.create_all()
            print("✅ Tüm tablolar oluşturuldu")
            
            # 2. Varsayılan şirket kontrolü ve oluştur
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT id FROM companies WHERE id = 1")).fetchone()
                
            if not result:
                # Varsayılan şirket oluştur (ID=1)
                conn.execute(text("""
                    INSERT INTO companies (id, name, business_type, authorized_person, phone, email, city, notes, status, created_at, updated_at)
                    VALUES (1, 'Varsayılan Şirket', 'genel', 'Sistem', '', 'admin@localhost', '', 'Varsayılan şirket mevcut kullanıcılar için', 'approved', :now, :now)
                """))
                print("✅ Varsayılan şirket oluşturuldu (ID: 1)")
            
            print("🎉 Migration başarıyla tamamlandı!")
            
        except Exception as e:
            print(f"❌ Migration hatası: {e}")
            raise e

if __name__ == "__main__":
    migrate_database()
