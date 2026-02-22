from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models import db, Transaction, Customer, CustomerTransaction, Product, Receipt, ReceiptItem
from datetime import datetime, date
from decimal import Decimal
from config import is_production, is_demo
from functools import wraps
from translations import get_translation

main_bp = Blueprint('main', __name__)


def get_current_company_id():
    """Platform admin için None (işlem yapamaz), diğerleri için kendi şirketi."""
    if current_user.is_platform_admin:
        return None
    return current_user.company_id or 1


def scoped_transactions_query():
    """Platform admin veri görüntüleyebilir ama işlem yapamaz (company_id=None)."""
    if current_user.is_platform_admin:
        # Platform admin tüm transactionları görebilir ama kendi company_id'si yoktur
        return Transaction.query
    return Transaction.query.filter_by(company_id=current_user.company_id)


def scoped_customers_query():
    """Platform admin tüm müşterileri görebilir."""
    if current_user.is_platform_admin:
        return Customer.query
    return Customer.query.filter_by(company_id=current_user.company_id)


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


def admin_required(f):
    """Sadece admin kullanıcıları için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash(get_translation('admin_required', session.get('lang', 'tr')), 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def observer_read_only():
    """Gözlemci kullanıcıları için uyarı"""
    if current_user.is_authenticated and current_user.is_observer:
        flash('Gözlemci rolü ile sadece görüntüleme yapabilirsiniz.', 'warning')
        return True
    return False

@main_bp.route('/')
@login_required
def index():
    """Ana sayfa - Kasa durumu"""
    company_id = get_current_company_id()

    # Gelir/Gider toplamları
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.type == 'income'
    ).scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.type == 'expense'
    ).scalar() or 0
    cash_balance = total_income - total_expense
    
    # Müşteri borç toplamı
    total_customer_debt = sum(customer.get_balance() for customer in scoped_customers_query().all())
    
    # Bugünkü işlemler
    today = date.today()
    today_transactions = scoped_transactions_query().filter(
        Transaction.date == today
    ).order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Son fişler
    recent_receipts = scoped_receipts_query().order_by(Receipt.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         cash_balance=cash_balance,
                         total_income=total_income,
                         total_expense=total_expense,
                         total_debt=total_customer_debt,
                         today_transactions=today_transactions,
                         recent_receipts=recent_receipts,
                         today_date=today)

@main_bp.route('/transactions')
@login_required
def transactions():
    """Gelir/Gider işlemleri sayfası"""
    company_id = get_current_company_id()
    page = request.args.get('page', 1, type=int)
    transactions = scoped_transactions_query().order_by(Transaction.date.desc(), Transaction.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    # Gelir/Gider toplamları
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.type == 'income'
    ).scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.company_id == company_id,
        Transaction.type == 'expense'
    ).scalar() or 0
    
    return render_template('transactions.html', 
                         transactions=transactions,
                         total_income=total_income,
                         total_expense=total_expense)

@main_bp.route('/customers')
@login_required
def customers():
    """Müşteri defteri sayfası"""
    customers = scoped_customers_query().order_by(Customer.name).all()
    
    # Toplam borç hesapla
    total_debt = sum(customer.get_balance() for customer in customers if customer.get_balance() > 0)
    
    return render_template('customers.html', customers=customers, total_debt=total_debt)

@main_bp.route('/customer/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    """Müşteri detay sayfası"""
    customer = scoped_customers_query().filter_by(id=customer_id).first_or_404()
    transactions = CustomerTransaction.query.filter_by(customer_id=customer_id).order_by(CustomerTransaction.date.desc()).all()
    receipts = scoped_receipts_query().filter_by(customer_id=customer_id).order_by(Receipt.date.desc()).all()
    
    return render_template('customer_detail.html', customer=customer, transactions=transactions, receipts=receipts)

@main_bp.route('/products')
@login_required
def products():
    """Ürün yönetimi sayfası"""
    products = scoped_products_query().order_by(Product.name).all()
    return render_template('products.html', products=products)

@main_bp.route('/receipt')
@login_required
@admin_required
def receipt():
    """Fiş kesme sayfası - sadece admin"""
    customers = scoped_customers_query().order_by(Customer.name).all()
    products = scoped_products_query().order_by(Product.name).all()
    
    # Fiş numarası oluştur
    last_receipt = scoped_receipts_query().order_by(Receipt.id.desc()).first()
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
@login_required
def receipt_detail(receipt_id):
    """Fiş detay sayfası"""
    receipt = scoped_receipts_query().filter_by(id=receipt_id).first_or_404()
    return render_template('receipt_detail.html', receipt=receipt)
