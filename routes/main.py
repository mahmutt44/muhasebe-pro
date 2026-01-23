from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Transaction, Customer, CustomerTransaction, Product, Receipt, ReceiptItem
from datetime import datetime, date
from decimal import Decimal
from config import is_production, is_demo

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Ana sayfa - Kasa durumu"""
    # Gelir/Gider toplamları
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'income').scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'expense').scalar() or 0
    cash_balance = total_income - total_expense
    
    # Müşteri borç toplamı
    total_customer_debt = sum(customer.get_balance() for customer in Customer.query.all())
    
    # Bugünkü işlemler
    today = date.today()
    today_transactions = Transaction.query.filter(Transaction.date == today).order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Son fişler
    recent_receipts = Receipt.query.order_by(Receipt.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         cash_balance=cash_balance,
                         total_income=total_income,
                         total_expense=total_expense,
                         total_debt=total_customer_debt,
                         today_transactions=today_transactions,
                         recent_receipts=recent_receipts,
                         today_date=today)

@main_bp.route('/transactions')
def transactions():
    """Gelir/Gider işlemleri sayfası"""
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    # Gelir/Gider toplamları
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'income').scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'expense').scalar() or 0
    
    return render_template('transactions.html', 
                         transactions=transactions,
                         total_income=total_income,
                         total_expense=total_expense)

@main_bp.route('/customers')
def customers():
    """Müşteri defteri sayfası"""
    customers = Customer.query.order_by(Customer.name).all()
    
    # Toplam borç hesapla
    total_debt = sum(customer.get_balance() for customer in customers if customer.get_balance() > 0)
    
    return render_template('customers.html', customers=customers, total_debt=total_debt)

@main_bp.route('/customer/<int:customer_id>')
def customer_detail(customer_id):
    """Müşteri detay sayfası"""
    customer = Customer.query.get_or_404(customer_id)
    transactions = CustomerTransaction.query.filter_by(customer_id=customer_id).order_by(CustomerTransaction.date.desc()).all()
    receipts = Receipt.query.filter_by(customer_id=customer_id).order_by(Receipt.date.desc()).all()
    
    return render_template('customer_detail.html', customer=customer, transactions=transactions, receipts=receipts)

@main_bp.route('/products')
def products():
    """Ürün yönetimi sayfası"""
    products = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=products)

@main_bp.route('/receipt')
def receipt():
    """Fiş kesme sayfası"""
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.order_by(Product.name).all()
    
    # Fiş numarası oluştur
    last_receipt = Receipt.query.order_by(Receipt.id.desc()).first()
    if last_receipt:
        receipt_no = f"F{int(last_receipt.receipt_no[1:]) + 1:03d}"
    else:
        receipt_no = "F001"
    
    # Customer_id parametresi varsa seçili müşteri olarak ayarla
    selected_customer_id = request.args.get('customer_id', type=int)
    
    return render_template('receipt.html', 
                         customers=customers, 
                         products=products, 
                         receipt_no=receipt_no,
                         selected_customer_id=selected_customer_id,
                         today_date=date.today())

@main_bp.route('/receipt/<int:receipt_id>')
def receipt_detail(receipt_id):
    """Fiş detay sayfası"""
    receipt = Receipt.query.get_or_404(receipt_id)
    return render_template('receipt_detail.html', receipt=receipt)
