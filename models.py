from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import event
from sqlalchemy.orm import Query
from flask import g

db = SQLAlchemy()

# Tenant izolasyonu için modeller listesi
TENANT_MODELS = {'customers', 'products', 'suppliers', 'receipts', 'transactions'}

@event.listens_for(Query, "before_compile", retval=True)
def auto_filter_by_company(query):
    """
    Otomatik tenant izolasyonu - company_id filtresi ekler.
    Platform admin kullanıcılar için filtre uygulanmaz.
    """
    # Kullanıcı giriş yapmamış veya platform admin ise filtreleme
    if not hasattr(g, 'is_platform_admin'):
        return query
    
    if g.is_platform_admin:
        return query
    
    # company_id yoksa filtreleme yapma
    if not hasattr(g, 'company_id') or g.company_id is None:
        return query
    
    # Tenant modelleri için company_id filtresi ekle
    if query.column_descriptions:
        entity = query.column_descriptions[0]['entity']
        if entity is not None:
            table_name = getattr(entity, '__tablename__', None)
            if table_name in TENANT_MODELS:
                # Company column'u var mı kontrol et
                if hasattr(entity, 'company_id'):
                    query = query.filter(entity.company_id == g.company_id)
    
    return query

# Türkiye saat dilimi (UTC+3)
TURKEY_TZ = timezone(timedelta(hours=3))

def get_turkey_time():
    """Türkiye saatini döndürür"""
    return datetime.now(TURKEY_TZ)

def get_turkey_date():
    """Türkiye tarihini döndürür"""
    return datetime.now(TURKEY_TZ).date()

class Company(db.Model):
    """Şirketler"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    business_type = db.Column(db.String(50))  # kafe, market, restoran, genel
    authorized_person = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    updated_at = db.Column(db.DateTime, default=get_turkey_time, onupdate=get_turkey_time)
    
    # İlişkiler
    users = db.relationship('User', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'business_type': self.business_type,
            'authorized_person': self.authorized_person,
            'phone': self.phone,
            'email': self.email,
            'city': self.city,
            'notes': self.notes,
            'status': self.status,
            'rejection_reason': self.rejection_reason or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CompanyRequest(db.Model):
    """Şirket talepleri"""
    __tablename__ = 'company_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    business_type = db.Column(db.String(50), nullable=False)
    authorized_person = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    rejection_reason = db.Column(db.Text)
    approved_username = db.Column(db.String(100))
    temporary_password = db.Column(db.String(100))  # Geçici şifre - onay anında gösterilir
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    updated_at = db.Column(db.DateTime, default=get_turkey_time, onupdate=get_turkey_time)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'business_type': self.business_type,
            'authorized_person': self.authorized_person,
            'phone': self.phone,
            'email': self.email,
            'city': self.city,
            'notes': self.notes,
            'status': self.status,
            'rejection_reason': self.rejection_reason or '',
            'approved_username': self.approved_username or '',
            'temporary_password': self.temporary_password or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class User(db.Model, UserMixin):
    """Kullanıcılar (platform_admin, admin ve observer rolleri)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)  # SaaS için
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')
    is_active = db.Column(db.Boolean, default=True)
    force_password_change = db.Column(db.Boolean, default=False)  # İlk girişte şifre değiştirme zorunluluğu
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    last_login = db.Column(db.DateTime)
    
    @property
    def is_admin(self):
        """Admin yetkisi olan rolleri kontrol eder"""
        return self.role in ('admin', 'platform_admin')

    @property
    def is_platform_admin(self):
        """Platform admin kontrolü"""
        return self.role == 'platform_admin'
    
    @property
    def is_observer(self):
        """Kullanıcının gözlemci olup olmadığını kontrol eder"""
        return self.role == 'observer'
    
    def set_password(self, password):
        """Şifre hashleme"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Şifre kontrolü"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Transaction(db.Model):
    """Gelir/Gider işlemleri"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)  # SaaS için
    type = db.Column(db.String(10), nullable=False)  # 'income' veya 'expense'
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=get_turkey_date)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'amount': str(self.amount) if self.amount else '0.00',
            'description': self.description or '',
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Customer(db.Model):
    """Müşteriler"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)  # SaaS için
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    updated_at = db.Column(db.DateTime, default=get_turkey_time, onupdate=get_turkey_time)
    
    # İlişkiler
    transactions = db.relationship('CustomerTransaction', backref='customer', lazy=True, cascade='all, delete-orphan')
    receipts = db.relationship('Receipt', backref='customer', lazy=True)
    
    def get_balance(self):
        """Müşterinin güncel bakiyesini hesaplar"""
        total_debt = sum(t.amount for t in self.transactions if t.type == 'debt')
        total_payment = sum(t.amount for t in self.transactions if t.type == 'payment')
        return total_debt - total_payment
    
    @property
    def balance(self):
        """Müşterinin güncel bakiyesini property olarak döndürür"""
        return self.get_balance()
    
    def to_json(self):
        """Modeli JSON formatına çevirir"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'notes': self.notes,
            'balance': str(self.balance) if self.balance else '0.00',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone or '',
            'notes': self.notes or '',
            'balance': str(self.get_balance()) if self.get_balance() else '0.00',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CustomerTransaction(db.Model):
    """Müşteri borç/alacak işlemleri"""
    __tablename__ = 'customer_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'debt' veya 'payment'
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=get_turkey_date)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'type': self.type,
            'amount': str(self.amount) if self.amount else '0.00',
            'description': self.description or '',
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Supplier(db.Model):
    """Tedarikçiler"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)  # SaaS için
    
    # Firma bilgileri
    name = db.Column(db.String(100), nullable=False)  # Firma adı
    contact_person = db.Column(db.String(100))  # Yetkili kişi
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    tax_number = db.Column(db.String(50))  # Vergi numarası (opsiyonel)
    notes = db.Column(db.Text)
    
    # Durum
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    updated_at = db.Column(db.DateTime, default=get_turkey_time, onupdate=get_turkey_time)
    
    # İlişkiler
    transactions = db.relationship('SupplierTransaction', backref='supplier', lazy=True, cascade='all, delete-orphan')
    
    def get_balance(self):
        """Tedarikçinin güncel bakiyesini hesaplar (borç - ödeme)"""
        total_debt = sum(t.amount for t in self.transactions if t.type == 'debt')
        total_payment = sum(t.amount for t in self.transactions if t.type == 'payment')
        return total_debt - total_payment
    
    @property
    def balance(self):
        """Tedarikçinin güncel bakiyesini property olarak döndürür"""
        return self.get_balance()
    
    def to_json(self):
        """Modeli JSON formatına çevirir"""
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'tax_number': self.tax_number,
            'notes': self.notes,
            'is_active': self.is_active,
            'balance': str(self.balance) if self.balance else '0.00',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person or '',
            'phone': self.phone or '',
            'email': self.email or '',
            'address': self.address or '',
            'tax_number': self.tax_number or '',
            'notes': self.notes or '',
            'is_active': self.is_active,
            'balance': str(self.get_balance()) if self.get_balance() else '0.00',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SupplierTransaction(db.Model):
    """Tedarikçi borç/ödeme işlemleri"""
    __tablename__ = 'supplier_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'debt' (borç) veya 'payment' (ödeme)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=get_turkey_date)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    
    def to_dict(self):
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'type': self.type,
            'amount': str(self.amount) if self.amount else '0.00',
            'description': self.description or '',
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Product(db.Model):
    """Ürünler (stoklu)"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)  # SaaS için
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # adet, kg, gram, paket vb.
    unit_price = db.Column(db.Numeric(15, 2), nullable=False)
    purchase_price = db.Column(db.Numeric(15, 2), default=0)  # Alış fiyatı (stok değeri için)
    stock_quantity = db.Column(db.Numeric(10, 2), default=0)  # Mevcut stok
    stock_threshold = db.Column(db.Numeric(10, 2), default=10)  # Düşük stok uyarı eşiği
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    updated_at = db.Column(db.DateTime, default=get_turkey_time, onupdate=get_turkey_time)
    
    @property
    def is_low_stock(self):
        """Stok düşük mü?"""
        return float(self.stock_quantity or 0) < float(self.stock_threshold or 10)
    
    @property
    def stock_value(self):
        """Stok değeri (stok * alış fiyatı)"""
        return Decimal(str(self.stock_quantity or 0)) * Decimal(str(self.purchase_price or 0))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'unit_price': str(self.unit_price) if self.unit_price else '0.00',
            'purchase_price': str(self.purchase_price) if self.purchase_price else '0.00',
            'stock_quantity': str(self.stock_quantity) if self.stock_quantity else '0.00',
            'stock_threshold': str(self.stock_threshold) if self.stock_threshold else '10.00',
            'is_low_stock': self.is_low_stock,
            'stock_value': str(self.stock_value),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_json(self):
        """Modeli JSON formatına çevirir"""
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'unit_price': str(self.unit_price) if self.unit_price else '0.00',
            'purchase_price': str(self.purchase_price) if self.purchase_price else '0.00',
            'stock_quantity': str(self.stock_quantity) if self.stock_quantity else '0.00',
            'stock_threshold': str(self.stock_threshold) if self.stock_threshold else '10.00',
            'is_low_stock': self.is_low_stock,
            'stock_value': str(self.stock_value),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Receipt(db.Model):
    """Satış fişleri"""
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)  # SaaS için
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    receipt_no = db.Column(db.String(20), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0)
    grand_total = db.Column(db.Numeric(15, 2), nullable=False)
    notes = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=get_turkey_date)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    
    # İlişkiler
    items = db.relationship('ReceiptItem', backref='receipt', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'receipt_no': self.receipt_no,
            'total_amount': str(self.total_amount),
            'tax_rate': str(self.tax_rate) if self.tax_rate else '0',
            'tax_amount': str(self.tax_amount) if self.tax_amount else '0',
            'grand_total': str(self.grand_total) if self.grand_total else str(self.total_amount),
            'notes': self.notes,
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }

class ReceiptItem(db.Model):
    """Fiş kalemleri"""
    __tablename__ = 'receipt_items'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(15, 2), nullable=False)
    total_price = db.Column(db.Numeric(15, 2), nullable=False)
    
    # İlişkiler
    product = db.relationship('Product', backref='receipt_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_unit': self.product.unit if self.product else None,
            'quantity': str(self.quantity),
            'unit_price': str(self.unit_price),
            'total_price': str(self.total_price)
        }
