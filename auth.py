from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime, timezone, timedelta
from functools import wraps
from translations import get_translation

auth = Blueprint('auth', __name__)

TURKEY_TZ = timezone(timedelta(hours=3))


def admin_required(f):
    """Sadece admin kullanıcıları için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı girişi"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Hesabınız devre dışı bırakılmış.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.now(TURKEY_TZ)
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.', 'danger')
    
    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    """Kullanıcı çıkışı"""
    logout_user()
    flash(get_translation('logout_success', session.get('lang', 'tr')), 'success')
    return redirect(url_for('auth.login'))


@auth.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Kullanıcı yönetimi paneli"""
    users = User.query.all()
    return render_template('auth/admin_users.html', users=users)


@auth.route('/admin/users/add', methods=['POST'])
@login_required
@admin_required
def admin_add_user():
    """Yeni kullanıcı ekle"""
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
    
    # Benzersizlik kontrolü
    if User.query.filter_by(username=username).first():
        flash('Bu kullanıcı adı zaten kullanılıyor.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    if User.query.filter_by(email=email).first():
        flash('Bu e-posta adresi zaten kullanılıyor.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    # Kullanıcı oluştur
    user = User(
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
@admin_required
def admin_toggle_user(user_id):
    """Kullanıcı durumunu değiştir (aktif/pasif)"""
    user = User.query.get_or_404(user_id)
    
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
@admin_required
def admin_reset_password(user_id):
    """Kullanıcı şifresini sıfırla"""
    user = User.query.get_or_404(user_id)
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
@admin_required
def admin_delete_user(user_id):
    """Kullanıcı sil"""
    user = User.query.get_or_404(user_id)
    
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
@admin_required
def admin_change_role(user_id):
    """Kullanıcı rolünü değiştir"""
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('new_role', 'admin')
    
    # Kendi rolünü değiştiremez
    if user.id == current_user.id:
        flash('Kendi rolünüzü değiştiremezsiniz.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    if new_role not in ['admin', 'observer']:
        flash('Geçersiz rol.', 'danger')
        return redirect(url_for('auth.admin_users'))
    
    user.role = new_role
    db.session.commit()
    
    flash(f'Kullanıcı {user.username} rolü {new_role} olarak değiştirildi.', 'success')
    return redirect(url_for('auth.admin_users'))
