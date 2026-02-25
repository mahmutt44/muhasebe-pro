from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from models import db, Transaction, Customer, CustomerTransaction, Product, Receipt, ReceiptItem, Supplier, SupplierTransaction
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from functools import wraps
from translations import get_translation

api_bp = Blueprint('api', __name__)


def get_current_company_id():
    """Platform admin için None (işlem yapamaz), diğerleri için kendi şirketi."""
    if current_user.is_platform_admin:
        return None
    return current_user.company_id or 1


def scoped_transactions_query():
    """Platform admin tüm transactionları görebilir (salt-okunur)."""
    if current_user.is_platform_admin:
        return Transaction.query
    return Transaction.query.filter_by(company_id=current_user.company_id)


def scoped_customers_query():
    """Platform admin tüm müşterileri görebilir."""
    if current_user.is_platform_admin:
        return Customer.query
    return Customer.query.filter_by(company_id=current_user.company_id)


def scoped_suppliers_query():
    """Platform admin tüm tedarikçileri görebilir."""
    if current_user.is_platform_admin:
        return Supplier.query
    return Supplier.query.filter_by(company_id=current_user.company_id)


def scoped_products_query():
    """Platform admin tüm ürünleri görebilir."""
    if current_user.is_platform_admin:
        return Product.query
    return Product.query.filter_by(company_id=current_user.company_id)


def scoped_receipts_query():
    """Platform admin tüm fişleri görebilir."""
    if current_user.is_platform_admin:
        return Receipt.query
    return Receipt.query.filter_by(company_id=current_user.company_id)


def admin_required_api(f):
    """API için sadece admin kullanıcıları decorator'ü"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': get_translation('admin_required', session.get('lang', 'tr'))}), 403
        return f(*args, **kwargs)
    return decorated_function


# Gelir/Gider API'leri
@api_bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    """Tüm gelir/gider işlemlerini getir"""
    transactions = scoped_transactions_query().order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()
    return jsonify([t.to_dict() for t in transactions])

@api_bp.route('/transactions', methods=['POST'])
@login_required
@admin_required_api
def create_transaction():
    """Yeni gelir/gider işlemi ekle - Sadece admin"""
    data = request.get_json()
    
    try:
        transaction = Transaction(
            company_id=get_current_company_id(),
            type=data['type'],
            amount=Decimal(str(data['amount'])),
            description=data.get('description', ''),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else date.today()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
@login_required
def get_transaction(transaction_id):
    """Tekil gelir/gider işlemi getir"""
    transaction = scoped_transactions_query().filter_by(id=transaction_id).first_or_404()
    return jsonify(transaction.to_dict())

@api_bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_transaction(transaction_id):
    """Gelir/gider işlemi sil - Sadece admin"""
    transaction = scoped_transactions_query().filter_by(id=transaction_id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'İşlem silindi'})

@api_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_transaction(transaction_id):
    """Gelir/gider işlemini güncelle - Sadece admin"""
    transaction = scoped_transactions_query().filter_by(id=transaction_id).first_or_404()
    
    data = request.get_json()
    print(f"DEBUG: Gelen veri: {data}")
    print(f"DEBUG: Eski işlem: {transaction.to_dict()}")
    
    try:
        transaction.type = data['type']
        transaction.amount = float(data['amount'])
        transaction.description = data['description']
        transaction.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        print(f"DEBUG: Yeni işlem: {transaction.to_dict()}")
        
        db.session.commit()
        
        print(f"DEBUG: Veritabanına kaydedildi")
        
        return jsonify(transaction.to_dict())
    except (ValueError, KeyError) as e:
        print(f"DEBUG: Hata: {e}")
        return jsonify({'error': str(e)}), 400

# Müşteri API'leri
@api_bp.route('/customers', methods=['GET'])
@login_required
def get_customers():
    """Tüm müşterileri getir"""
    try:
        customers = scoped_customers_query().order_by(Customer.name).all()
        result = [c.to_dict() for c in customers]
        print(f"DEBUG: Müşteri sayısı: {len(customers)}")
        print(f"DEBUG: İlk müşteri: {result[0] if result else 'Yok'}")
        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: Müşteri API hatası: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/customers', methods=['POST'])
@login_required
@admin_required_api
def create_customer():
    """Yeni müşteri ekle - Sadece admin"""
    data = request.get_json()
    
    try:
        customer = Customer(
            company_id=get_current_company_id(),
            name=data['name'],
            phone=data.get('phone', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify(customer.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    """Tekil müşteri getir"""
    customer = scoped_customers_query().filter_by(id=customer_id).first_or_404()
    return jsonify(customer.to_dict())

@api_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_customer(customer_id):
    """Müşteri bilgilerini güncelle - Sadece admin"""
    customer = scoped_customers_query().filter_by(id=customer_id).first_or_404()
    data = request.get_json()
    
    try:
        customer.name = data.get('name', customer.name)
        customer.phone = data.get('phone', customer.phone)
        customer.notes = data.get('notes', customer.notes)
        
        db.session.commit()
        return jsonify(customer.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_customer(customer_id):
    """Müşteri sil - Sadece admin"""
    customer = scoped_customers_query().filter_by(id=customer_id).first_or_404()
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Müşteri silindi'})

@api_bp.route('/customers/<int:customer_id>/balance')
@login_required
def get_customer_balance(customer_id):
    """Müşteri bakiyesini getir"""
    customer = scoped_customers_query().filter_by(id=customer_id).first_or_404()
    return jsonify({'balance': float(customer.get_balance())})

# Müşteri İşlem API'leri
@api_bp.route('/customers/<int:customer_id>/transactions', methods=['GET'])
@login_required
def get_customer_transactions(customer_id):
    """Müşteri işlemlerini getir"""
    customer = scoped_customers_query().filter_by(id=customer_id).first_or_404()
    transactions = CustomerTransaction.query.filter_by(customer_id=customer_id).order_by(CustomerTransaction.date.desc()).all()
    return jsonify([t.to_dict() for t in transactions])

@api_bp.route('/customers/<int:customer_id>/transactions', methods=['POST'])
@login_required
@admin_required_api
def create_customer_transaction(customer_id):
    """Müşteri borç/ödeme işlemi ekle - Sadece admin"""
    customer = scoped_customers_query().filter_by(id=customer_id).first_or_404()
    data = request.get_json()
    
    try:
        transaction = CustomerTransaction(
            customer_id=customer_id,
            type=data['type'],
            amount=Decimal(str(data['amount'])),
            description=data.get('description', ''),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else date.today()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/customer-transactions/<int:transaction_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_customer_transaction(transaction_id):
    """Müşteri işlemini güncelle - Sadece admin"""
    transaction = CustomerTransaction.query.join(Customer).filter(
        CustomerTransaction.id == transaction_id,
        Customer.id == CustomerTransaction.customer_id,
        Customer.company_id == get_current_company_id()
    ).first_or_404()
    data = request.get_json()
    
    try:
        transaction.type = data['type']
        transaction.amount = Decimal(str(data['amount']))
        transaction.description = data.get('description', '')
        transaction.date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else transaction.date
        
        db.session.commit()
        return jsonify(transaction.to_dict())
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/customer-transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_customer_transaction(transaction_id):
    """Müşteri işlemini sil - Sadece admin"""
    transaction = CustomerTransaction.query.join(Customer).filter(
        CustomerTransaction.id == transaction_id,
        Customer.id == CustomerTransaction.customer_id,
        Customer.company_id == get_current_company_id()
    ).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'İşlem silindi'})

# Tedarikçi API'leri
@api_bp.route('/suppliers', methods=['GET'])
@login_required
def get_suppliers():
    """Tüm tedarikçileri getir"""
    try:
        suppliers = scoped_suppliers_query().order_by(Supplier.name).all()
        result = [s.to_dict() for s in suppliers]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/suppliers', methods=['POST'])
@login_required
@admin_required_api
def create_supplier():
    """Yeni tedarikçi ekle - Sadece admin"""
    data = request.get_json()
    
    try:
        supplier = Supplier(
            company_id=get_current_company_id(),
            name=data['name'],
            contact_person=data.get('contact_person', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            address=data.get('address', ''),
            tax_number=data.get('tax_number', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify(supplier.to_dict()), 201
    except KeyError as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
@login_required
def get_supplier(supplier_id):
    """Tekil tedarikçi getir"""
    supplier = scoped_suppliers_query().filter_by(id=supplier_id).first_or_404()
    return jsonify(supplier.to_dict())

@api_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_supplier(supplier_id):
    """Tedarikçi bilgilerini güncelle - Sadece admin"""
    supplier = scoped_suppliers_query().filter_by(id=supplier_id).first_or_404()
    data = request.get_json()
    
    try:
        supplier.name = data.get('name', supplier.name)
        supplier.contact_person = data.get('contact_person', supplier.contact_person)
        supplier.phone = data.get('phone', supplier.phone)
        supplier.email = data.get('email', supplier.email)
        supplier.address = data.get('address', supplier.address)
        supplier.tax_number = data.get('tax_number', supplier.tax_number)
        supplier.notes = data.get('notes', supplier.notes)
        supplier.is_active = data.get('is_active', supplier.is_active)
        
        db.session.commit()
        return jsonify(supplier.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_supplier(supplier_id):
    """Tedarikçi sil - Sadece admin"""
    supplier = scoped_suppliers_query().filter_by(id=supplier_id).first_or_404()
    db.session.delete(supplier)
    db.session.commit()
    return jsonify({'message': 'Tedarikçi silindi'})

@api_bp.route('/suppliers/<int:supplier_id>/transactions', methods=['GET'])
@login_required
def get_supplier_transactions(supplier_id):
    """Tedarikçinin tüm işlemlerini getir"""
    supplier = scoped_suppliers_query().filter_by(id=supplier_id).first_or_404()
    transactions = SupplierTransaction.query.filter_by(supplier_id=supplier_id).order_by(SupplierTransaction.date.desc()).all()
    return jsonify([t.to_dict() for t in transactions])

@api_bp.route('/suppliers/<int:supplier_id>/transactions', methods=['POST'])
@login_required
@admin_required_api
def create_supplier_transaction(supplier_id):
    """Tedarikçiye yeni işlem ekle - Sadece admin"""
    supplier = scoped_suppliers_query().filter_by(id=supplier_id).first_or_404()
    data = request.get_json()
    
    try:
        transaction = SupplierTransaction(
            supplier_id=supplier_id,
            type=data['type'],  # 'debt' veya 'payment'
            amount=Decimal(str(data['amount'])),
            description=data.get('description', ''),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else date.today()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify(transaction.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/supplier-transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_supplier_transaction(transaction_id):
    """Tedarikçi işlemini sil - Sadece admin"""
    transaction = SupplierTransaction.query.join(Supplier).filter(
        SupplierTransaction.id == transaction_id,
        Supplier.id == SupplierTransaction.supplier_id,
        Supplier.company_id == get_current_company_id()
    ).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'İşlem silindi'})

# Ürün API'leri
@api_bp.route('/products', methods=['GET'])
@login_required
def get_products():
    """Tüm ürünleri getir"""
    products = scoped_products_query().order_by(Product.name).all()
    return jsonify([p.to_dict() for p in products])

@api_bp.route('/products', methods=['POST'])
@login_required
@admin_required_api
def create_product():
    """Yeni ürün ekle - Sadece admin"""
    data = request.get_json()
    
    try:
        product = Product(
            company_id=get_current_company_id(),
            name=data['name'],
            unit=data['unit'],
            unit_price=Decimal(str(data['unit_price']))
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    """Tekil ürün getir"""
    product = scoped_products_query().filter_by(id=product_id).first_or_404()
    return jsonify(product.to_dict())

@api_bp.route('/products/<int:product_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_product(product_id):
    """Ürün bilgilerini güncelle - Sadece admin"""
    product = scoped_products_query().filter_by(id=product_id).first_or_404()
    data = request.get_json()
    
    try:
        product.name = data.get('name', product.name)
        product.unit = data.get('unit', product.unit)
        product.unit_price = Decimal(str(data.get('unit_price', product.unit_price)))
        
        db.session.commit()
        return jsonify(product.to_dict())
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/products/<int:product_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_product(product_id):
    """Ürün sil - Sadece admin"""
    product = scoped_products_query().filter_by(id=product_id).first_or_404()
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Ürün silindi'})

# Fiş API'leri
@api_bp.route('/receipts', methods=['GET'])
@login_required
def get_receipts():
    """Tüm fişleri getir"""
    receipts = scoped_receipts_query().order_by(Receipt.date.desc(), Receipt.created_at.desc()).all()
    return jsonify([r.to_dict() for r in receipts])

@api_bp.route('/receipts', methods=['POST'])
@login_required
@admin_required_api
def create_receipt():
    """Yeni fiş oluştur - Sadece admin"""
    data = request.get_json()
    
    try:
        # Fiş numarası oluştur
        last_receipt = scoped_receipts_query().order_by(Receipt.id.desc()).first()
        if last_receipt:
            receipt_no = f"F{int(last_receipt.receipt_no[1:]) + 1:03d}"
        else:
            receipt_no = "F001"
        
        # KDV hesapla
        total_amount = Decimal(str(data['total_amount']))
        tax_rate = Decimal(str(data.get('tax_rate', 0)))
        tax_amount = total_amount * tax_rate / 100
        grand_total = total_amount + tax_amount
        
        # Fişi oluştur
        receipt = Receipt(
            company_id=get_current_company_id(),
            customer_id=data['customer_id'],
            receipt_no=receipt_no,
            total_amount=total_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            grand_total=grand_total,
            notes=data.get('notes', ''),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else date.today()
        )
        
        db.session.add(receipt)
        db.session.flush()  # ID'yi almak için
        
        # Fiş kalemlerini ekle
        for item_data in data['items']:
            item = ReceiptItem(
                receipt_id=receipt.id,
                product_id=item_data['product_id'],
                quantity=Decimal(str(item_data['quantity'])),
                unit_price=Decimal(str(item_data['unit_price'])),
                total_price=Decimal(str(item_data['total_price']))
            )
            db.session.add(item)
        
        # Müşteri borcunu güncelle (KDV dahil toplam)
        customer = scoped_customers_query().filter_by(id=data['customer_id']).first_or_404()
        debt_transaction = CustomerTransaction(
            customer_id=data['customer_id'],
            type='debt',
            amount=grand_total,
            description=f"Fiş #{receipt_no} - {data.get('notes', 'Satış')}",
            date=receipt.date
        )
        db.session.add(debt_transaction)
        
        db.session.commit()
        
        return jsonify(receipt.to_dict()), 201
    except (ValueError, KeyError, IntegrityError) as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/receipts/<int:receipt_id>')
@login_required
def get_receipt(receipt_id):
    """Fiş detaylarını getir"""
    receipt = scoped_receipts_query().filter_by(id=receipt_id).first_or_404()
    return jsonify(receipt.to_dict())

@api_bp.route('/receipts/<int:receipt_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_receipt(receipt_id):
    """Fiş sil - Sadece admin"""
    receipt = scoped_receipts_query().filter_by(id=receipt_id).first_or_404()
    db.session.delete(receipt)
    db.session.commit()
    return jsonify({'message': 'Fiş silindi'})

# İstatistik API'leri
@api_bp.route('/stats/dashboard')
@login_required
def get_dashboard_stats():
    """Dashboard istatistikleri"""
    company_id = get_current_company_id()
    # Gelir/Gider
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.type == 'income'
    ).scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.type == 'expense'
    ).scalar() or 0
    cash_balance = total_income - total_expense
    
    # Müşteri borçları
    total_customer_debt = sum(customer.get_balance() for customer in scoped_customers_query().all())
    
    # Bugünkü işlemler
    today = date.today()
    today_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.type == 'income',
        Transaction.date == today
    ).scalar() or 0
    today_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.type == 'expense',
        Transaction.date == today
    ).scalar() or 0
    
    return jsonify({
        'cash_balance': float(cash_balance),
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'total_customer_debt': float(total_customer_debt),
        'today_income': float(today_income),
        'today_expense': float(today_expense)
    })
