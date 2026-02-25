from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, current_app
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from models import db, Transaction, Customer, CustomerTransaction, Product, Receipt, ReceiptItem, User, Company
from config import config, get_database_url, is_production, is_demo, is_development
from translations import get_all_translations, get_translation
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import os
import sys
from sqlalchemy import inspect, text

# Flask-Login başlatma
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bu sayfayı görüntülemek için giriş yapmalısınız.'
login_manager.login_message_category = 'warning'

# Flask-Migrate başlatma
migrate = Migrate()

# Türkiye saat dilimi (UTC+3)
TURKEY_TZ = timezone(timedelta(hours=3))

def to_turkey_time(dt):
    """UTC datetime'ı Türkiye saatine dönüştürür"""
    if dt is None:
        return None
    # Eğer date objesi ise (datetime.date), direkt döndür
    if hasattr(dt, 'tzinfo') is False:
        # datetime.date objesi - tzinfo yok
        return dt
    # Eğer naive datetime ise UTC olarak kabul et
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TURKEY_TZ)

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Konfigürasyon
    if config_name is None:
        config_name = os.environ.get('ENV', 'default')
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Veritabanı URL'i
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 30,
        'max_overflow': 0
    }
    
    # Veritabanı başlatma
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Flask-Login başlatma
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Jinja2 filter - Türkiye saati (dil desteği ile)
    @app.template_filter('turkey_time')
    def turkey_time_filter(dt, format='%d.%m.%Y %H:%M'):
        """Template'de Türkiye saatini göster"""
        turkey_dt = to_turkey_time(dt)
        if turkey_dt:
            lang = session.get('lang', 'tr')
            formatted = turkey_dt.strftime(format)
            if lang == 'ar':
                # Arapça rakamlarına çevir
                arabic_numerals = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')
                formatted = formatted.translate(arabic_numerals)
            return formatted
        return ''
    
    # Jinja2 filter - Sadece tarih (dil desteği ile)
    @app.template_filter('format_date')
    def format_date_filter(dt, format='%d.%m.%Y'):
        """Template'de tarihi formatla"""
        if dt is None:
            return ''
        lang = session.get('lang', 'tr')
        if hasattr(dt, 'strftime'):
            formatted = dt.strftime(format)
        else:
            formatted = str(dt)
        if lang == 'ar':
            # Arapça rakamlarına çevir
            arabic_numerals = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')
            formatted = formatted.translate(arabic_numerals)
        return formatted
    
    # Dil context processor - tüm template'lerde kullanılabilir
    @app.context_processor
    def inject_translations():
        lang = session.get('lang', 'tr')
        return {
            't': get_all_translations(lang),
            'current_lang': lang,
            'is_rtl': lang == 'ar'
        }
    
    # Dil değiştirme route'u
    @app.route('/set-language/<lang>')
    def set_language(lang):
        if lang in ['tr', 'ar']:
            session['lang'] = lang
        return redirect(request.referrer or url_for('main.index'))
    
    # Production ortamında veritabanı bağlantısını kontrol et
    if is_production():
        try:
            with app.app_context():
                # Sadece bağlantı testi - tablo oluşturma yok!
                db.session.execute(text('SELECT 1'))
                app.logger.info('Production database connection successful')
        except Exception as e:
            app.logger.error(f'CRITICAL: Production database connection failed: {e}')
            sys.exit(1)  # Uygulamayı durdur
    
    # Development ortamında sadece tablo oluştur (migration yoksa)
    elif is_development():
        try:
            with app.app_context():
                db.create_all()
                app.logger.info('Development database initialized')
        except Exception as e:
            app.logger.error(f'Development database initialization failed: {e}')
            # Development'ta bile fallback yok - kullanıcı bilgilendirilsin
            raise
    
    # Route'ları kaydetme
    from routes.main import main_bp
    from routes.api import api_bp
    from auth import auth
    from reports import reports
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(reports)

    # Context processor to inject global variables into all templates
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from models import CompanyRequest
        
        context = {}
        if current_user.is_authenticated and current_user.is_platform_admin:
            # Platform admin için bekleyen talep sayısı
            context['pending_requests_count'] = CompanyRequest.query.filter_by(status='pending').count()
        else:
            context['pending_requests_count'] = 0
        return context
    
    # SaaS şema bootstrap (eski DB'ler için güvenli)
    with app.app_context():
        ensure_saas_schema()
    
    # Demo verisi ekleme (sadece demo ortamında)
    if is_demo():
        with app.app_context():
            if Customer.query.count() == 0:
                create_demo_data()
    
    # Production için admin kullanıcısı oluştur
    elif is_production():
        with app.app_context():
            if User.query.count() == 0:
                create_production_admin()
    
    return app


def ensure_saas_schema():
    """Eski veritabanlarını company_id alanlarıyla uyumlu hale getirir."""
    inspector = inspect(db.engine)

    table_columns = {
        table: {c['name'] for c in inspector.get_columns(table)}
        for table in inspector.get_table_names()
    }

    alter_statements = []

    if 'users' in table_columns and 'company_id' not in table_columns['users']:
        alter_statements.append("ALTER TABLE users ADD COLUMN company_id INTEGER")

    if 'customers' in table_columns and 'company_id' not in table_columns['customers']:
        alter_statements.append("ALTER TABLE customers ADD COLUMN company_id INTEGER DEFAULT 1")

    if 'transactions' in table_columns and 'company_id' not in table_columns['transactions']:
        alter_statements.append("ALTER TABLE transactions ADD COLUMN company_id INTEGER DEFAULT 1")

    if 'products' in table_columns and 'company_id' not in table_columns['products']:
        alter_statements.append("ALTER TABLE products ADD COLUMN company_id INTEGER DEFAULT 1")

    if 'receipts' in table_columns and 'company_id' not in table_columns['receipts']:
        alter_statements.append("ALTER TABLE receipts ADD COLUMN company_id INTEGER DEFAULT 1")

    if 'company_requests' in table_columns and 'approved_username' not in table_columns['company_requests']:
        alter_statements.append("ALTER TABLE company_requests ADD COLUMN approved_username VARCHAR(100)")

    if 'company_requests' in table_columns and 'temporary_password' not in table_columns['company_requests']:
        alter_statements.append("ALTER TABLE company_requests ADD COLUMN temporary_password VARCHAR(100)")

    with db.engine.begin() as conn:
        for stmt in alter_statements:
            conn.execute(text(stmt))

    # Varsayılan şirket
    default_company = Company.query.get(1)
    if default_company is None:
        default_company = Company(
            id=1,
            name='Varsayılan İşletme',
            business_type='genel',
            authorized_person='Sistem',
            email='system@local',
            status='approved'
        )
        db.session.add(default_company)
        db.session.commit()

    # Eksik company_id verilerini varsayılan şirkete ata
    with db.engine.begin() as conn:
        conn.execute(text("UPDATE customers SET company_id = 1 WHERE company_id IS NULL"))
        conn.execute(text("UPDATE transactions SET company_id = 1 WHERE company_id IS NULL"))
        conn.execute(text("UPDATE products SET company_id = 1 WHERE company_id IS NULL"))
        conn.execute(text("UPDATE receipts SET company_id = 1 WHERE company_id IS NULL"))
        conn.execute(text("UPDATE users SET role = 'platform_admin' WHERE company_id IS NULL AND role = 'admin'"))
        conn.execute(text("UPDATE users SET company_id = 1 WHERE company_id IS NULL AND role = 'observer'"))

def create_production_admin():
    """Production ortamı için admin kullanıcısı oluşturur"""
    # Production admin kullanıcısı
    admin_user = User(
        company_id=1,
        username='admin',
        email='admin@railway.com',
        role='platform_admin',
        is_active=True
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)
    
    # Production gözlemci kullanıcısı
    observer_user = User(
        company_id=1,
        username='gozlemci',
        email='gozlemci@railway.com',
        role='observer',
        is_active=True
    )
    observer_user.set_password('gozlemci123')
    db.session.add(observer_user)
    
    db.session.commit()
    current_app.logger.info('Production admin kullanıcısı oluşturuldu!')

def create_demo_data():
    """Demo ortamı için sahte veriler oluşturur"""
    company = Company.query.get(1)
    if company is None:
        company = Company(
            id=1,
            name='Demo İşletme',
            business_type='genel',
            authorized_person='Demo Admin',
            email='demo@local',
            status='approved'
        )
        db.session.add(company)
        db.session.commit()

    # Demo ürünler
    products = [
        Product(company_id=company.id, name='Çay', unit='adet', unit_price=Decimal('5.00')),
        Product(company_id=company.id, name='Kahve', unit='fincan', unit_price=Decimal('15.00')),
        Product(company_id=company.id, name='Sandviç', unit='adet', unit_price=Decimal('25.00')),
        Product(company_id=company.id, name='Su', unit='pet', unit_price=Decimal('3.00')),
        Product(company_id=company.id, name='Meyve Suyu', unit='litre', unit_price=Decimal('20.00'))
    ]
    
    for product in products:
        db.session.add(product)
    
    # Demo müşteriler
    customers = [
        Customer(company_id=company.id, name='Ahmet Yılmaz', phone='0532 111 22 33', notes='Düzenli müşteri'),
        Customer(company_id=company.id, name='Ayşe Demir', phone='0543 444 55 66', notes='Toptancı'),
        Customer(company_id=company.id, name='Mehmet Kaya', phone='0555 777 88 99', notes='Komşu'),
        Customer(company_id=company.id, name='Fatma Öztürk', phone='0538 222 33 44', notes='Öğrenci'),
        Customer(company_id=company.id, name='Ali Vural', phone='0546 666 77 88', notes='İş yeri')
    ]
    
    for customer in customers:
        db.session.add(customer)
    
    db.session.commit()
    
    # Demo müşteri işlemleri
    customer_transactions = [
        CustomerTransaction(customer_id=1, type='debt', amount=Decimal('150.00'), description='Kahve ve çay alışverişi'),
        CustomerTransaction(customer_id=1, type='payment', amount=Decimal('50.00'), description='Ödeme'),
        CustomerTransaction(customer_id=2, type='debt', amount=Decimal('500.00'), description='Toptan alışveriş'),
        CustomerTransaction(customer_id=3, type='debt', amount=Decimal('75.00'), description='Günlük alışveriş'),
        CustomerTransaction(customer_id=4, type='debt', amount=Decimal('30.00'), description='Meyve suyu'),
        CustomerTransaction(customer_id=5, type='debt', amount=Decimal('200.00'), description='İş yeri için'),
        CustomerTransaction(customer_id=5, type='payment', amount=Decimal('100.00'), description='Kısmi ödeme')
    ]
    
    for transaction in customer_transactions:
        db.session.add(transaction)
    
    # Demo gelir/gider işlemleri
    transactions = [
        Transaction(company_id=company.id, type='income', amount=Decimal('2500.00'), description='Günlük ciro'),
        Transaction(company_id=company.id, type='expense', amount=Decimal('500.00'), description='Kiraya ödeme'),
        Transaction(company_id=company.id, type='expense', amount=Decimal('200.00'), description='Elektrik faturası'),
        Transaction(company_id=company.id, type='expense', amount=Decimal('150.00'), description='Su faturası'),
        Transaction(company_id=company.id, type='expense', amount=Decimal('300.00'), description='Malzeme alışverişi'),
        Transaction(company_id=company.id, type='income', amount=Decimal('1800.00'), description='Günlük ciro'),
        Transaction(company_id=company.id, type='expense', amount=Decimal('100.00'), description='İnternet faturası')
    ]
    
    for transaction in transactions:
        db.session.add(transaction)
    
    db.session.commit()
    
    # Demo fişler
    receipts = [
        Receipt(company_id=company.id, customer_id=1, receipt_no='F001', total_amount=Decimal('150.00'), grand_total=Decimal('150.00'), notes='Kahve ve çay'),
        Receipt(company_id=company.id, customer_id=2, receipt_no='F002', total_amount=Decimal('500.00'), grand_total=Decimal('500.00'), notes='Toptan satış'),
        Receipt(company_id=company.id, customer_id=3, receipt_no='F003', total_amount=Decimal('75.00'), grand_total=Decimal('75.00'), notes='Günlük')
    ]
    
    for receipt in receipts:
        db.session.add(receipt)
    
    db.session.commit()
    
    # Demo fiş kalemleri
    receipt_items = [
        ReceiptItem(receipt_id=1, product_id=1, quantity=Decimal('10'), unit_price=Decimal('5.00'), total_price=Decimal('50.00')),
        ReceiptItem(receipt_id=1, product_id=2, quantity=Decimal('5'), unit_price=Decimal('15.00'), total_price=Decimal('75.00')),
        ReceiptItem(receipt_id=1, product_id=3, quantity=Decimal('1'), unit_price=Decimal('25.00'), total_price=Decimal('25.00')),
        ReceiptItem(receipt_id=2, product_id=1, quantity=Decimal('50'), unit_price=Decimal('5.00'), total_price=Decimal('250.00')),
        ReceiptItem(receipt_id=2, product_id=2, quantity=Decimal('10'), unit_price=Decimal('15.00'), total_price=Decimal('150.00')),
        ReceiptItem(receipt_id=2, product_id=3, quantity=Decimal('4'), unit_price=Decimal('25.00'), total_price=Decimal('100.00')),
        ReceiptItem(receipt_id=3, product_id=1, quantity=Decimal('5'), unit_price=Decimal('5.00'), total_price=Decimal('25.00')),
        ReceiptItem(receipt_id=3, product_id=2, quantity=Decimal('2'), unit_price=Decimal('15.00'), total_price=Decimal('30.00')),
        ReceiptItem(receipt_id=3, product_id=4, quantity=Decimal('5'), unit_price=Decimal('3.00'), total_price=Decimal('15.00'))
    ]
    
    for item in receipt_items:
        db.session.add(item)
    
    db.session.commit()
    
    # Default admin kullanıcı
    admin_user = User(
        company_id=company.id,
        username='admin',
        email='admin@example.com',
        role='platform_admin',
        is_active=True
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)
    
    # Demo gözlemci kullanıcı
    observer_user = User(
        company_id=company.id,
        username='gozlemci',
        email='gozlemci@example.com',
        role='observer',
        is_active=True
    )
    observer_user.set_password('gozlemci123')
    db.session.add(observer_user)
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
