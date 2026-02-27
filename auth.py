from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Company, CompanyRequest, Customer, Transaction, Product, Receipt, LoginAttempt
from datetime import datetime, timezone, timedelta
from functools import wraps
from translations import get_translation
import secrets
import string
import re
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse, urljoin

auth = Blueprint('auth', __name__)

TURKEY_TZ = timezone(timedelta(hours=3))


def is_safe_url(target):
    """
    Next parametresinin güvenli olup olmadığını kontrol eder.
    Sadece uygulama içindeki URL'lere izin verir, harici domainleri engeller.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    # URL scheme ve netloc kontrolü
    # Scheme http veya https olmalı
    if test_url.scheme not in ('http', 'https'):
        return False
    
    # Netloc (domain) kontrolü - sadece aynı domain'e izin ver
    if ref_url.netloc != test_url.netloc:
        return False
    
    # JavaScript protokolü kontrolü (javascript: alert(1) gibi)
    if test_url.scheme.startswith('javascript'):
        return False
    
    # Data URI kontrolü
    if test_url.scheme.startswith('data'):
        return False
    
    return True


def get_safe_redirect(target, default='main.index'):
    """
    Güvenli redirect URL'i döndürür.
    Eğer hedef güvenli değilse varsayılan sayfaya yönlendirir.
    """
    if target and is_safe_url(target):
        return target
    return url_for(default)


def admin_required(f):
    """Sadece admin kullanıcıları için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def platform_admin_required(f):
    """Sadece platform admin kullanıcıları için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_platform_admin:
            flash('Bu sayfaya sadece platform yöneticisi erişebilir.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_company_id():
    """Platform admin için None, diğerleri için kendi şirketi."""
    if current_user.is_platform_admin:
        return None
    return current_user.company_id or 1


def scoped_users_query():
    """Kullanıcı sorgusunu şirket bazında filtreler."""
    if current_user.is_platform_admin:
        return User.query
    return User.query.filter_by(company_id=current_user.company_id)


def scoped_company_users_query():
    """Şirket kullanıcılarını listele (Platform admin için tüm şirketler)."""
    if current_user.is_platform_admin:
        return User.query.filter(User.company_id.isnot(None))
    return User.query.filter_by(company_id=current_user.company_id)


def company_required(f):
    """Sadece şirket kullanıcıları için decorator - Platform admin hariç"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Platform admin bu decorator ile erişemez (sadece company admin/observer)
        if current_user.is_platform_admin:
            flash('Bu sayfa şirket yöneticileri içindir.', 'warning')
            return redirect(url_for('auth.platform_admin_dashboard'))
        
        # Observer kullanıcılar admin sayfalarına erişemez
        if current_user.is_observer:
            flash('Bu işlem için admin yetkisi gereklidir.', 'danger')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function


def company_read_only(f):
    """Şirket kullanıcıları için sadece okuma yetkisi - Observer için"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Platform admin bu decorator ile erişemez
        if current_user.is_platform_admin:
            flash('Bu sayfa şirket kullanıcıları içindir.', 'warning')
            return redirect(url_for('auth.platform_admin_dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def password_change_required(f):
    """Şifre değiştirme zorunluluğu kontrolü - force_password_change=True ise sadece change_password'e izin ver"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Şifre değiştirme zorunluluğu varsa ve şu an change_password sayfasında değilse
        if current_user.force_password_change and request.endpoint != 'auth.change_password':
            flash('Lütfen önce şifrenizi değiştirin.', 'warning')
            return redirect(url_for('auth.change_password'))
        
        return f(*args, **kwargs)
    return decorated_function


@auth.route('/request-account', methods=['GET', 'POST'])
def request_account():
    """İşletme hesabı talep formu"""
    if request.method == 'POST':
        # Form verilerini al
        company_name = request.form.get('company_name', '').strip()
        business_type = request.form.get('business_type', '').strip()
        authorized_person = request.form.get('authorized_person', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        city = request.form.get('city', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Validasyon
        if not all([company_name, business_type, authorized_person, phone, email]):
            flash(get_translation('fill_required_fields', session.get('lang', 'tr')), 'danger')
            return render_template('auth/request_account.html')

        # E-posta sistemde kullanıcı olarak varsa yeni talep alma
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Bu e-posta adresi zaten kullanılıyor.', 'danger')
            return render_template('auth/request_account.html')

        # Aynı e-posta için bekleyen talep varsa tekrar alma
        pending_request = CompanyRequest.query.filter_by(email=email, status='pending').first()
        if pending_request:
            flash('Bu e-posta için zaten bekleyen bir talep var.', 'warning')
            return render_template('auth/request_account.html')
        
        # Talebi oluştur
        company_request = CompanyRequest(
            company_name=company_name,
            business_type=business_type,
            authorized_person=authorized_person,
            phone=phone,
            email=email,
            city=city,
            notes=notes
        )
        
        db.session.add(company_request)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Bu e-posta adresi zaten kullanılıyor.', 'danger')
            return render_template('auth/request_account.html')
        
        flash(get_translation('request_submitted', session.get('lang', 'tr')), 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/request_account.html')


@auth.route('/platform-admin')
@login_required
@platform_admin_required
def platform_admin_dashboard():
    """Platform Admin ana paneli - işletmelerden bağımsız global yönetim"""
    # İstatistikler
    total_companies = Company.query.count()
    total_users = User.query.filter(User.company_id.isnot(None)).count()
    pending_requests = CompanyRequest.query.filter_by(status='pending').count()
    
    # Son işletmeler
    recent_companies = Company.query.order_by(Company.created_at.desc()).limit(5).all()
    
    return render_template('auth/platform_admin_dashboard.html',
                         total_companies=total_companies,
                         total_users=total_users,
                         pending_requests=pending_requests,
                         recent_companies=recent_companies)


@auth.route('/platform-admin/companies')
@login_required
@platform_admin_required
def platform_admin_companies():
    """Tüm işletmeleri listele ve yönet"""
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template('auth/platform_admin_companies.html', companies=companies)


@auth.route('/platform-admin/companies/<int:company_id>')
@login_required
@platform_admin_required
def platform_admin_company_detail(company_id):
    """İşletme detay görünümü"""
    company = Company.query.get_or_404(company_id)
    # İşletmenin kullanıcıları
    users = User.query.filter_by(company_id=company_id).all()
    # İşletmenin istatistikleri
    stats = {
        'customers_count': Customer.query.filter_by(company_id=company_id).count(),
        'transactions_count': Transaction.query.filter_by(company_id=company_id).count(),
        'products_count': Product.query.filter_by(company_id=company_id).count(),
        'receipts_count': Receipt.query.filter_by(company_id=company_id).count()
    }
    return render_template('auth/platform_admin_company_detail.html', 
                         company=company, users=users, stats=stats)


@auth.route('/platform-admin/companies/<int:company_id>/edit', methods=['POST'])
@login_required
@platform_admin_required
def platform_admin_company_edit(company_id):
    """İşletme bilgilerini düzenle"""
    company = Company.query.get_or_404(company_id)
    
    company.name = request.form.get('name', company.name).strip()
    company.business_type = request.form.get('business_type', company.business_type).strip()
    company.authorized_person = request.form.get('authorized_person', company.authorized_person).strip()
    company.phone = request.form.get('phone', company.phone).strip()
    company.email = request.form.get('email', company.email).strip()
    company.city = request.form.get('city', company.city).strip()
    company.notes = request.form.get('notes', company.notes).strip()
    
    try:
        db.session.commit()
        flash(f'İşletme {company.name} başarıyla güncellendi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('İşletme güncellenirken bir hata oluştu.', 'danger')
    
    return redirect(url_for('auth.platform_admin_company_detail', company_id=company_id))


@auth.route('/platform-admin/companies/<int:company_id>/toggle', methods=['POST'])
@login_required
@platform_admin_required
def platform_admin_company_toggle(company_id):
    """İşletme durumunu aktif/pasif değiştir"""
    company = Company.query.get_or_404(company_id)
    
    if company.status == 'approved':
        company.status = 'suspended'
        flash(f'İşletme {company.name} askıya alındı.', 'warning')
    else:
        company.status = 'approved'
        flash(f'İşletme {company.name} aktif duruma getirildi.', 'success')
    
    db.session.commit()
    return redirect(url_for('auth.platform_admin_companies'))


@auth.route('/platform-admin/companies/<int:company_id>/delete', methods=['POST'])
@login_required
@platform_admin_required
def platform_admin_company_delete(company_id):
    """İşletme ve tüm verilerini sil"""
    company = Company.query.get_or_404(company_id)
    
    company_name = company.name
    
    # Cascade delete ile ilişkili tüm veriler silinecek
    try:
        db.session.delete(company)
        db.session.commit()
        flash(f'İşletme {company_name} ve tüm verileri silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('İşletme silinirken bir hata oluştu.', 'danger')
    
    return redirect(url_for('auth.platform_admin_companies'))


@auth.route('/platform-admin/company-requests')
@login_required
@platform_admin_required
def admin_company_requests():
    """Hesap talepleri yönetimi"""
    requests = CompanyRequest.query.order_by(CompanyRequest.created_at.desc()).all()
    return render_template('auth/company_requests.html', requests=requests)


@auth.route('/platform-admin/approve-request/<int:request_id>', methods=['POST'])
@login_required
@platform_admin_required
def approve_request(request_id):
    """Talebi onayla ve şirket oluştur"""
    company_request = CompanyRequest.query.get_or_404(request_id)

    if company_request.status != 'pending':
        flash(get_translation('request_already_processed', session.get('lang', 'tr')), 'warning')
        return redirect(url_for('auth.admin_company_requests'))

    # User.email unique olduğu için onay öncesi kontrol
    if User.query.filter_by(email=company_request.email).first():
        flash('Bu e-posta adresi zaten bir kullanıcıya ait. Talep onaylanamadı.', 'danger')
        return redirect(url_for('auth.admin_company_requests'))
    
    # Yeni şirket oluştur
    company = Company(
        name=company_request.company_name,
        business_type=company_request.business_type,
        authorized_person=company_request.authorized_person,
        phone=company_request.phone,
        email=company_request.email,
        city=company_request.city,
        notes=company_request.notes,
        status='approved'
    )
    
    db.session.add(company)
    db.session.flush()  # Company ID'yi almak için
    
    # Company admin kullanıcı adı: isletmeadi_admin
    slug_company = re.sub(r'[^a-z0-9]', '', company_request.company_name.lower())
    if not slug_company:
        slug_company = 'company'

    base_username = f"{slug_company}_admin"
    username = base_username
    suffix = 1
    while User.query.filter_by(username=username).first() is not None:
        suffix += 1
        username = f"{base_username}{suffix}"

    admin_user = User(
        company_id=company.id,
        username=username,
        email=company_request.email,
        role='admin',
        is_active=True,
        force_password_change=True  # İlk girişte şifre değiştirme zorunluluğu
    )
    
    # Rastgele şifre oluştur - sadece bu seferlik gösterilecek
    alphabet = string.ascii_letters + string.digits + '!@#$%&*'
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
    admin_user.set_password(temp_password)
    
    db.session.add(admin_user)
    
    # Talebi güncelle
    company_request.status = 'approved'
    company_request.approved_username = username
    company_request.set_temporary_password(temp_password)  # Şifreyi hash'le ve sakla
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Talep onaylanamadı. Kullanıcı bilgileri çakışıyor.', 'danger')
        return redirect(url_for('auth.admin_company_requests'))
    
    # Başarı mesajı - şifre sadece bu seferlik gösterilir
    flash(f'İşletme başarıyla onaylandı!', 'success')
    flash(f'Giriş bilgileri: Kullanıcı adı: {username} | Geçici şifre: {temp_password}', 'info')
    flash(f'Not: Bu şifre sadece bir kez gösterilir. Lütfen not alın veya kullanıcıya iletin. İlk girişte şifre değiştirme zorunludur.', 'warning')
    
    return redirect(url_for('auth.admin_company_requests'))


@auth.route('/platform-admin/reject-request/<int:request_id>', methods=['POST'])
@login_required
@platform_admin_required
def reject_request(request_id):
    """Talebi reddet"""
    company_request = CompanyRequest.query.get_or_404(request_id)

    if company_request.status != 'pending':
        flash(get_translation('request_already_processed', session.get('lang', 'tr')), 'warning')
        return redirect(url_for('auth.admin_company_requests'))
    
    rejection_reason = request.form.get('rejection_reason', '').strip()
    
    company_request.status = 'rejected'
    company_request.rejection_reason = rejection_reason
    
    db.session.commit()
    
    flash(get_translation('request_rejected', session.get('lang', 'tr')), 'success')
    return redirect(url_for('auth.admin_company_requests'))


@auth.route('/platform-admin/delete-request/<int:request_id>', methods=['POST'])
@login_required
@platform_admin_required
def delete_request(request_id):
    """Hesap talebini tamamen sil (onaylanmışsa kullanıcıyı da sil)"""
    company_request = CompanyRequest.query.get_or_404(request_id)
    
    company_name = company_request.company_name
    
    # Eğer talep onaylanmışsa, oluşturulan kullanıcıyı da sil
    if company_request.approved_username:
        user = User.query.filter_by(username=company_request.approved_username).first()
        if user:
            db.session.delete(user)
    
    db.session.delete(company_request)
    db.session.commit()
    
    flash(f'{company_name} talebi ve ilişkili kullanıcı silindi.', 'success')
    return redirect(url_for('auth.admin_company_requests'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı girişi - Brute force koruması ile"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Brute force koruması - IP bazlı kontrol
    ip_address = request.remote_addr or 'unknown'
    MAX_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15
    
    # IP bazlı giriş denemesini kontrol et
    ip_attempt = LoginAttempt.query.filter_by(ip_address=ip_address, username=None).first()
    if ip_attempt and ip_attempt.is_locked():
        remaining = ip_attempt.get_remaining_lockout_seconds()
        minutes = remaining // 60
        flash(f'Çok fazla başarısız giriş denemesi. Lütfen {minutes} dakika sonra tekrar deneyin.', 'danger')
        return render_template('auth/login.html')
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # Kullanıcı bazlı kilitleme kontrolü
        if username:
            user_attempt = LoginAttempt.query.filter_by(ip_address=ip_address, username=username).first()
            if user_attempt and user_attempt.is_locked():
                remaining = user_attempt.get_remaining_lockout_seconds()
                minutes = remaining // 60
                flash(f'Bu hesap kilitlendi. Lütfen {minutes} dakika sonra tekrar deneyin.', 'danger')
                return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Başarılı giriş - deneme sayılarını sıfırla
            if ip_attempt:
                ip_attempt.reset_attempts()
            if user_attempt:
                user_attempt.reset_attempts()
            db.session.commit()
            
            if not user.is_active:
                flash('Hesabınız devre dışı bırakılmış.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            session['company_id'] = user.company_id
            session['role'] = user.role
            user.last_login = datetime.now(TURKEY_TZ)
            db.session.commit()
            
            # İlk girişte şifre değiştirme zorunluluğu kontrolü
            if user.force_password_change:
                flash('Lütfen geçici şifrenizi değiştirin.', 'warning')
                return redirect(url_for('auth.change_password'))
            
            # Platform admin kendi paneline, diğerleri ana sayfaya
            if user.is_platform_admin:
                return redirect(url_for('auth.platform_admin_dashboard'))
            
            # Güvenli redirect - open redirect açığını önle
            next_page = request.args.get('next')
            return redirect(get_safe_redirect(next_page, 'main.index'))
        else:
            # Başarısız giriş - deneme sayısını artır
            if not ip_attempt:
                ip_attempt = LoginAttempt(ip_address=ip_address)
                db.session.add(ip_attempt)
            
            ip_attempt.increment_attempt(MAX_ATTEMPTS, LOCKOUT_MINUTES)
            
            # Kullanıcı bazlı takip de yap
            if username:
                user_attempt = LoginAttempt.query.filter_by(ip_address=ip_address, username=username).first()
                if not user_attempt:
                    user_attempt = LoginAttempt(ip_address=ip_address, username=username)
                    db.session.add(user_attempt)
                user_attempt.increment_attempt(MAX_ATTEMPTS, LOCKOUT_MINUTES)
            
            db.session.commit()
            
            remaining_attempts = MAX_ATTEMPTS - ip_attempt.attempt_count
            if remaining_attempts > 0:
                flash(f'Kullanıcı adı veya şifre hatalı. Kalan deneme: {remaining_attempts}', 'danger')
            else:
                flash(f'Çok fazla başarısız giriş denemesi. Hesap {LOCKOUT_MINUTES} dakika kilitlendi.', 'danger')
    
    return render_template('auth/login.html')


@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    """Kullanıcı çıkışı - CSRF korumalı POST endpoint"""
    logout_user()
    session.pop('company_id', None)
    session.pop('role', None)
    flash(get_translation('logout_success', session.get('lang', 'tr')), 'success')
    return redirect(url_for('auth.login'))


@auth.route('/admin/users')
@login_required
@password_change_required
@company_read_only
def admin_users():
    """Şirket kullanıcı yönetimi paneli - admin ve observer görüntüleyebilir"""
    users = scoped_company_users_query().all()
    return render_template('auth/admin_users.html', users=users)


@auth.route('/admin/users/add', methods=['POST'])
@login_required
@password_change_required
@company_required
def admin_add_user():
    """Yeni kullanıcı ekle - Sadece admin"""
    # Observer kullanıcılar yeni kullanıcı ekleyemez
    if current_user.is_observer:
        flash('Bu işlem için admin yetkisi gereklidir.', 'danger')
        return redirect(url_for('auth.admin_users'))
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'admin')
    
    # Validasyon
    if not username or len(username) < 3:
        flash('Kullanıcı adı en az 3 karakter olmalı.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    if not email or '@' not in email:
        flash('Geçerli bir e-posta adresi girin.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    if len(password) < 6:
        flash('Şifre en az 6 karakter olmalı.', 'danger')
        return redirect(url_for('auth.admin_users'))

    allowed_roles = ['admin', 'observer']
    if role not in allowed_roles:
        flash('Geçersiz rol.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    # Benzersizlik kontrolü
    if scoped_users_query().filter_by(username=username).first():
        flash('Bu kullanıcı adı zaten kullanılıyor.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    if User.query.filter_by(email=email).first():
        flash('Bu e-posta adresi zaten kullanılıyor.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    # Kullanıcı oluştur - şirket admin panelinde sadece şirket kullanıcıları
    target_company_id = current_user.company_id or 1

    user = User(
        company_id=target_company_id,
        username=username,
        email=email,
        role=role
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    flash(get_translation('user_created', session.get('lang', 'tr')).format(username=username), 'success')
    return redirect(url_for('auth.admin_users'))


@auth.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@password_change_required
@company_required
def admin_toggle_user(user_id):
    """Kullanıcı durumunu değiştir (aktif/pasif) - Sadece admin"""
    # Observer kullanıcılar bu işlemi yapamaz
    if current_user.is_observer:
        flash('Bu işlem için admin yetkisi gereklidir.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    user = scoped_company_users_query().filter_by(id=user_id).first_or_404()
    
    # Kendi hesabını pasif yapamaz
    if user.id == current_user.id:
        flash('Kendi hesabınızı devre dışı bırakamazsınız.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'aktif' if user.is_active else 'pasif'
    flash(f'Kullanıcı {user.username} {status} duruma getirildi.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@password_change_required
@company_required
def admin_reset_password(user_id):
    """Kullanıcı şifresini sıfırla - Sadece admin"""
    # Observer kullanıcılar şifre sıfırlayamaz
    if current_user.is_observer:
        flash('Bu işlem için admin yetkisi gereklidir.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    user = scoped_company_users_query().filter_by(id=user_id).first_or_404()
    new_password = request.form.get('new_password', '')
    
    if len(new_password) < 6:
        flash('Yeni şifre en az 6 karakter olmalı.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    user.set_password(new_password)
    db.session.commit()
    
    flash(get_translation('password_reset', session.get('lang', 'tr')).format(username=user.username), 'success')
    return redirect(url_for('auth.admin_users'))


@auth.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@password_change_required
@company_required
def admin_delete_user(user_id):
    """Kullanıcı sil - Sadece admin"""
    # Observer kullanıcılar kullanıcı silemez
    if current_user.is_observer:
        flash('Bu işlem için admin yetkisi gereklidir.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    user = scoped_company_users_query().filter_by(id=user_id).first_or_404()
    
    # Kendini silemez
    if user.id == current_user.id:
        flash(get_translation('cannot_delete_self', session.get('lang', 'tr')), 'danger')
        return redirect(url_for('auth.admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(get_translation('user_deleted', session.get('lang', 'tr')).format(username=user.username), 'success')
    return redirect(url_for('auth.admin_users'))


@auth.route('/admin/users/<int:user_id>/change-role', methods=['POST'])
@login_required
@password_change_required
@company_required
def admin_change_role(user_id):
    """Kullanıcı rolünü değiştir - Sadece admin"""
    # Observer kullanıcılar rol değiştiremez
    if current_user.is_observer:
        flash('Bu işlem için admin yetkisi gereklidir.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    user = scoped_company_users_query().filter_by(id=user_id).first_or_404()
    new_role = request.form.get('new_role', 'admin')
    
    # Kendi rolünü değiştiremez
    if user.id == current_user.id:
        flash('Kendi rolünüzü değiştiremezsiniz.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    allowed_roles = ['admin', 'observer']
    if new_role not in allowed_roles:
        flash('Geçersiz rol.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    user.role = new_role
    db.session.commit()
    
    flash(f'Kullanıcı {user.username} rolü {new_role} olarak değiştirildi.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Kullanıcı kendi şifresini değiştirir (ilk girişte zorunlu)"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validasyon
        if not current_password:
            flash('Mevcut şifrenizi girin.', 'danger')
            return render_template('auth/change_password.html')
        
        if not current_user.check_password(current_password):
            flash('Mevcut şifreniz hatalı.', 'danger')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('Yeni şifre en az 6 karakter olmalı.', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('Yeni şifreler eşleşmiyor.', 'danger')
            return render_template('auth/change_password.html')
        
        # Şifreyi güncelle
        current_user.set_password(new_password)
        current_user.force_password_change = False  # İlk giriş kontrolünü kapat
        db.session.commit()
        
        flash('Şifreniz başarıyla değiştirildi!', 'success')
        
        # Platform admin kendi paneline, diğerleri ana sayfaya
        if current_user.is_platform_admin:
            return redirect(url_for('auth.platform_admin_dashboard'))
        return redirect(url_for('main.index'))
    
    return render_template('auth/change_password.html')
