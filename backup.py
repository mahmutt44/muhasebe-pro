"""
Google Drive Yedekleme Scripti
Bu script veritabanını günlük olarak Google Drive'a yedekler.

Kurulum:
1. Google Cloud Console'dan bir proje oluşturun
2. Google Drive API'yi etkinleştirin
3. OAuth 2.0 credentials oluşturun (Desktop app)
4. credentials.json dosyasını bu klasöre indirin
5. pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

İlk çalıştırmada tarayıcı açılacak ve Google hesabınıza giriş yapmanız istenecek.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# Google Drive API için gerekli kütüphaneler
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("Google API kütüphaneleri yüklü değil.")
    print("Yüklemek için: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# Ayarlar
SCOPES = ['https://www.googleapis.com/auth/drive.file']
DATABASE_PATH = Path(__file__).parent / 'instance' / 'muhasebe_demo.db'
BACKUP_FOLDER = Path(__file__).parent / 'backups'
CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'
TOKEN_FILE = Path(__file__).parent / 'token.json'
DRIVE_FOLDER_NAME = 'Muhasebe_Yedekleri'

def get_drive_service():
    """Google Drive API servisini başlat"""
    creds = None
    
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"HATA: {CREDENTIALS_FILE} dosyası bulunamadı!")
                print("Google Cloud Console'dan credentials.json dosyasını indirin.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name):
    """Google Drive'da klasör bul veya oluştur"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    
    # Klasör yoksa oluştur
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"'{folder_name}' klasörü oluşturuldu.")
    return folder.get('id')

def create_local_backup():
    """Yerel yedek oluştur"""
    if not DATABASE_PATH.exists():
        print(f"HATA: Veritabanı bulunamadı: {DATABASE_PATH}")
        return None
    
    BACKUP_FOLDER.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"muhasebe_backup_{timestamp}.db"
    backup_path = BACKUP_FOLDER / backup_name
    
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"Yerel yedek oluşturuldu: {backup_path}")
    
    return backup_path

def upload_to_drive(service, file_path, folder_id):
    """Dosyayı Google Drive'a yükle"""
    file_metadata = {
        'name': file_path.name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(str(file_path), resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
    
    print(f"Google Drive'a yüklendi: {file.get('name')}")
    return file.get('id')

def cleanup_old_backups(service, folder_id, keep_count=7):
    """Eski yedekleri temizle (son 7 yedek hariç)"""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query, 
        spaces='drive', 
        fields='files(id, name, createdTime)',
        orderBy='createdTime desc'
    ).execute()
    
    files = results.get('files', [])
    
    if len(files) > keep_count:
        for file in files[keep_count:]:
            service.files().delete(fileId=file['id']).execute()
            print(f"Eski yedek silindi: {file['name']}")

def cleanup_local_backups(keep_count=7):
    """Yerel eski yedekleri temizle"""
    if not BACKUP_FOLDER.exists():
        return
    
    backups = sorted(BACKUP_FOLDER.glob('*.db'), key=os.path.getmtime, reverse=True)
    
    for backup in backups[keep_count:]:
        backup.unlink()
        print(f"Yerel eski yedek silindi: {backup.name}")

def backup():
    """Ana yedekleme fonksiyonu"""
    print("=" * 50)
    print(f"Yedekleme başlatıldı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Yerel yedek oluştur
    backup_path = create_local_backup()
    if not backup_path:
        return False
    
    # Google Drive'a yükle
    if GOOGLE_API_AVAILABLE:
        try:
            service = get_drive_service()
            if service:
                folder_id = get_or_create_folder(service, DRIVE_FOLDER_NAME)
                upload_to_drive(service, backup_path, folder_id)
                cleanup_old_backups(service, folder_id)
                print("Google Drive yedeklemesi tamamlandı!")
            else:
                print("Google Drive servisi başlatılamadı.")
        except Exception as e:
            print(f"Google Drive hatası: {e}")
    else:
        print("Google Drive yedeklemesi atlandı (kütüphaneler yüklü değil).")
    
    # Yerel eski yedekleri temizle
    cleanup_local_backups()
    
    print("=" * 50)
    print("Yedekleme tamamlandı!")
    print("=" * 50)
    return True

if __name__ == '__main__':
    backup()
