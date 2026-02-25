#!/usr/bin/env python3
"""
İlk admin kullanıcı oluşturma scripti

Kullanım:
    python create_admin.py --username admin --email admin@example.com --password <şifre> --role platform_admin
    
    veya environment variable ile:
    
    ADMIN_USERNAME=admin ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=şifre python create_admin.py

 roller:
    - platform_admin: Platform yöneticisi (tüm şirketlere erişim)
    - admin: Şirket yöneticisi
    - observer: Gözlemci (sadece görüntüleme)
"""

import os
import sys
import argparse
import getpass
from app import create_app
from models import db, User, Company

def create_admin_user(username, email, password, role='platform_admin', company_id=1):
    """Admin kullanıcı oluştur"""
    app = create_app()
    
    with app.app_context():
        # Şirket kontrolü
        company = Company.query.get(company_id)
        if not company:
            print(f"❌ Hata: ID {company_id} olan şirket bulunamadı!")
            print("💡 Önce şirket oluşturun veya migrations'ları çalıştırın:")
            print("   flask db upgrade")
            return False
        
        # Kullanıcı adı veya e-posta zaten var mı kontrol et
        if User.query.filter_by(username=username).first():
            print(f"❌ Hata: '{username}' kullanıcı adı zaten kullanılıyor!")
            return False
            
        if User.query.filter_by(email=email).first():
            print(f"❌ Hata: '{email}' e-posta adresi zaten kullanılıyor!")
            return False
        
        # Yeni kullanıcı oluştur
        user = User(
            company_id=company_id,
            username=username,
            email=email,
            role=role,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ Admin kullanıcı başarıyla oluşturuldu!")
        print(f"   Kullanıcı adı: {username}")
        print(f"   E-posta: {email}")
        print(f"   Rol: {role}")
        print(f"   Şirket ID: {company_id}")
        return True

def main():
    parser = argparse.ArgumentParser(
        description='İlk admin kullanıcı oluşturma scripti',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python create_admin.py -u admin -e admin@example.com -p mypassword -r platform_admin
  python create_admin.py --username admin --email admin@site.com --password secret123
  
Environment Variables:
  ADMIN_USERNAME    Kullanıcı adı
  ADMIN_EMAIL       E-posta adresi
  ADMIN_PASSWORD    Şifre
  ADMIN_ROLE        Rol (varsayılan: platform_admin)
  ADMIN_COMPANY_ID  Şirket ID (varsayılan: 1)
        """
    )
    
    parser.add_argument('-u', '--username', 
                        default=os.environ.get('ADMIN_USERNAME'),
                        help='Kullanıcı adı (veya ADMIN_USERNAME env)')
    parser.add_argument('-e', '--email',
                        default=os.environ.get('ADMIN_EMAIL'),
                        help='E-posta adresi (veya ADMIN_EMAIL env)')
    parser.add_argument('-p', '--password',
                        default=os.environ.get('ADMIN_PASSWORD'),
                        help='Şifre (veya ADMIN_PASSWORD env)')
    parser.add_argument('-r', '--role',
                        default=os.environ.get('ADMIN_ROLE', 'platform_admin'),
                        choices=['platform_admin', 'admin', 'observer'],
                        help='Kullanıcı rolü (varsayılan: platform_admin)')
    parser.add_argument('-c', '--company-id',
                        type=int,
                        default=int(os.environ.get('ADMIN_COMPANY_ID', 1)),
                        help='Şirket ID (varsayılan: 1)')
    parser.add_argument('--interactive', '-i',
                        action='store_true',
                        help='Etkileşimli mod (şifre gizli girilir)')
    
    args = parser.parse_args()
    
    # Etkileşimli mod
    if args.interactive or not (args.username and args.email and args.password):
        print("🔐 İlk Admin Kullanıcı Oluşturma")
        print("=" * 40)
        
        if not args.username:
            args.username = input("Kullanıcı adı: ").strip()
        if not args.email:
            args.email = input("E-posta: ").strip()
        if not args.password:
            args.password = getpass.getpass("Şifre: ")
            confirm = getpass.getpass("Şifre (tekrar): ")
            if args.password != confirm:
                print("❌ Hata: Şifreler eşleşmiyor!")
                sys.exit(1)
        
        if not args.role:
            print("\nRoller:")
            print("  1. platform_admin (Platform yöneticisi)")
            print("  2. admin (Şirket yöneticisi)")
            print("  3. observer (Gözlemci)")
            role_choice = input("Rol [1-3] (varsayılan: 1): ").strip() or "1"
            roles = {"1": "platform_admin", "2": "admin", "3": "observer"}
            args.role = roles.get(role_choice, "platform_admin")
    
    # Validasyon
    if not args.username or len(args.username) < 3:
        print("❌ Hata: Kullanıcı adı en az 3 karakter olmalı!")
        sys.exit(1)
    
    if not args.email or '@' not in args.email:
        print("❌ Hata: Geçerli bir e-posta adresi girin!")
        sys.exit(1)
    
    if not args.password or len(args.password) < 6:
        print("❌ Hata: Şifre en az 6 karakter olmalı!")
        sys.exit(1)
    
    # Kullanıcı oluştur
    success = create_admin_user(
        username=args.username,
        email=args.email,
        password=args.password,
        role=args.role,
        company_id=args.company_id
    )
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
