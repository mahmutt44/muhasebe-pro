from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from models import db, Transaction, Customer, CustomerTransaction, Product, Receipt, ReceiptItem
from config import config, get_database_url, is_production, is_demo
from translations import get_all_translations, get_translation
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import os

# Türkiye saat dilimi (UTC+3)
TURKEY_TZ = timezone(timedelta(hours=3))

def to_turkey_time(dt):
    """UTC datetime'ı Türkiye saatine dönüştürür"""
    if dt is None:
        return None
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
    
    # Tabloları oluşturma (hata varsa fallback)
    try:
        with app.app_context():
            db.create_all()
            app.logger.info('Database tables created successfully')
    except Exception as e:
        app.logger.error(f'Database connection failed: {e}')
        # SQLite fallback
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///muhasebe_fallback.db'
        with app.app_context():
            db.create_all()
        app.logger.info('Fallback to SQLite database')
    
    # Route'ları kaydetme
    from routes.main import main_bp
    from routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Demo verisi ekleme (sadece demo ortamında)
    if is_demo():
        with app.app_context():
            if Customer.query.count() == 0:
                create_demo_data()
    
    return app

def create_demo_data():
    """Demo ortamı için sahte veriler oluşturur"""
    # Demo ürünler
    products = [
        Product(name='Çay', unit='adet', unit_price=Decimal('5.00')),
        Product(name='Kahve', unit='fincan', unit_price=Decimal('15.00')),
        Product(name='Sandviç', unit='adet', unit_price=Decimal('25.00')),
        Product(name='Su', unit='pet', unit_price=Decimal('3.00')),
        Product(name='Meyve Suyu', unit='litre', unit_price=Decimal('20.00'))
    ]
    
    for product in products:
        db.session.add(product)
    
    # Demo müşteriler
    customers = [
        Customer(name='Ahmet Yılmaz', phone='0532 111 22 33', notes='Düzenli müşteri'),
        Customer(name='Ayşe Demir', phone='0543 444 55 66', notes='Toptancı'),
        Customer(name='Mehmet Kaya', phone='0555 777 88 99', notes='Komşu'),
        Customer(name='Fatma Öztürk', phone='0538 222 33 44', notes='Öğrenci'),
        Customer(name='Ali Vural', phone='0546 666 77 88', notes='İş yeri')
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
        Transaction(type='income', amount=Decimal('2500.00'), description='Günlük ciro'),
        Transaction(type='expense', amount=Decimal('500.00'), description='Kiraya ödeme'),
        Transaction(type='expense', amount=Decimal('200.00'), description='Elektrik faturası'),
        Transaction(type='expense', amount=Decimal('150.00'), description='Su faturası'),
        Transaction(type='expense', amount=Decimal('300.00'), description='Malzeme alışverişi'),
        Transaction(type='income', amount=Decimal('1800.00'), description='Günlük ciro'),
        Transaction(type='expense', amount=Decimal('100.00'), description='İnternet faturası')
    ]
    
    for transaction in transactions:
        db.session.add(transaction)
    
    db.session.commit()
    
    # Demo fişler
    receipts = [
        Receipt(customer_id=1, receipt_no='F001', total_amount=Decimal('150.00'), notes='Kahve ve çay'),
        Receipt(customer_id=2, receipt_no='F002', total_amount=Decimal('500.00'), notes='Toptan satış'),
        Receipt(customer_id=3, receipt_no='F003', total_amount=Decimal('75.00'), notes='Günlük')
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

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
