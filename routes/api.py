from flask import Blueprint, jsonify, request
from models import db, Transaction, Customer, CustomerTransaction, Product, Receipt, ReceiptItem
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

api_bp = Blueprint('api', __name__)

# Gelir/Gider API'leri
@api_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Tüm gelir/gider işlemlerini getir"""
    transactions = Transaction.query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()
    return jsonify([t.to_dict() for t in transactions])

@api_bp.route('/transactions', methods=['POST'])
def create_transaction():
    """Yeni gelir/gider işlemi ekle"""
    data = request.get_json()
    
    try:
        transaction = Transaction(
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
def get_transaction(transaction_id):
    """Tekil gelir/gider işlemi getir"""
    transaction = Transaction.query.get_or_404(transaction_id)
    return jsonify(transaction.to_dict())

@api_bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Gelir/gider işlemi sil"""
    transaction = Transaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'İşlem silindi'})

@api_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """Gelir/gider işlemini güncelle"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
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
def get_customers():
    """Tüm müşterileri getir"""
    try:
        customers = Customer.query.order_by(Customer.name).all()
        result = [c.to_dict() for c in customers]
        print(f"DEBUG: Müşteri sayısı: {len(customers)}")
        print(f"DEBUG: İlk müşteri: {result[0] if result else 'Yok'}")
        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: Müşteri API hatası: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/customers', methods=['POST'])
def create_customer():
    """Yeni müşteri ekle"""
    data = request.get_json()
    
    try:
        customer = Customer(
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
def get_customer(customer_id):
    """Tekil müşteri getir"""
    customer = Customer.query.get_or_404(customer_id)
    return jsonify(customer.to_dict())

@api_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Müşteri bilgilerini güncelle"""
    customer = Customer.query.get_or_404(customer_id)
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
def delete_customer(customer_id):
    """Müşteri sil"""
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Müşteri silindi'})

@api_bp.route('/customers/<int:customer_id>/balance')
def get_customer_balance(customer_id):
    """Müşteri bakiyesini getir"""
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({'balance': float(customer.get_balance())})

# Müşteri İşlem API'leri
@api_bp.route('/customers/<int:customer_id>/transactions', methods=['GET'])
def get_customer_transactions(customer_id):
    """Müşteri işlemlerini getir"""
    transactions = CustomerTransaction.query.filter_by(customer_id=customer_id).order_by(CustomerTransaction.date.desc()).all()
    return jsonify([t.to_dict() for t in transactions])

@api_bp.route('/customers/<int:customer_id>/transactions', methods=['POST'])
def create_customer_transaction(customer_id):
    """Müşteri borç/ödeme işlemi ekle"""
    customer = Customer.query.get_or_404(customer_id)
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
def update_customer_transaction(transaction_id):
    """Müşteri işlemini güncelle"""
    transaction = CustomerTransaction.query.get_or_404(transaction_id)
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
def delete_customer_transaction(transaction_id):
    """Müşteri işlemini sil"""
    transaction = CustomerTransaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'İşlem silindi'})

# Ürün API'leri
@api_bp.route('/products', methods=['GET'])
def get_products():
    """Tüm ürünleri getir"""
    products = Product.query.order_by(Product.name).all()
    return jsonify([p.to_dict() for p in products])

@api_bp.route('/products', methods=['POST'])
def create_product():
    """Yeni ürün ekle"""
    data = request.get_json()
    
    try:
        product = Product(
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
def get_product(product_id):
    """Tekil ürün getir"""
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@api_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Ürün bilgilerini güncelle"""
    product = Product.query.get_or_404(product_id)
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
def delete_product(product_id):
    """Ürün sil"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Ürün silindi'})

# Fiş API'leri
@api_bp.route('/receipts', methods=['GET'])
def get_receipts():
    """Tüm fişleri getir"""
    receipts = Receipt.query.order_by(Receipt.date.desc(), Receipt.created_at.desc()).all()
    return jsonify([r.to_dict() for r in receipts])

@api_bp.route('/receipts', methods=['POST'])
def create_receipt():
    """Yeni fiş oluştur"""
    data = request.get_json()
    
    try:
        # Fiş numarası oluştur
        last_receipt = Receipt.query.order_by(Receipt.id.desc()).first()
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
        customer = Customer.query.get(data['customer_id'])
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
def get_receipt(receipt_id):
    """Fiş detaylarını getir"""
    receipt = Receipt.query.get_or_404(receipt_id)
    return jsonify(receipt.to_dict())

@api_bp.route('/receipts/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    """Fiş sil"""
    receipt = Receipt.query.get_or_404(receipt_id)
    db.session.delete(receipt)
    db.session.commit()
    return jsonify({'message': 'Fiş silindi'})

# İstatistik API'leri
@api_bp.route('/stats/dashboard')
def get_dashboard_stats():
    """Dashboard istatistikleri"""
    # Gelir/Gider
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'income').scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'expense').scalar() or 0
    cash_balance = total_income - total_expense
    
    # Müşteri borçları
    total_customer_debt = sum(customer.get_balance() for customer in Customer.query.all())
    
    # Bugünkü işlemler
    today = date.today()
    today_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'income', Transaction.date == today).scalar() or 0
    today_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'expense', Transaction.date == today).scalar() or 0
    
    return jsonify({
        'cash_balance': float(cash_balance),
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'total_customer_debt': float(total_customer_debt),
        'today_income': float(today_income),
        'today_expense': float(today_expense)
    })
