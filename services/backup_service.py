import os
import subprocess
import logging
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import is_production

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self):
        self.is_production = is_production()
        
    def create_database_backup(self):
        """PostgreSQL veritabanı yedeği oluşturur"""
        if not self.is_production:
            logger.info("Demo ortamında yedekleme yapılmıyor")
            return None
            
        try:
            # Yedek dosyası adı oluştur
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"muhasebe_backup_{timestamp}.sql"
            backup_path = os.path.join('backup', backup_filename)
            
            # Backup klasörünü kontrol et
            os.makedirs('backup', exist_ok=True)
            
            # Database URL'den bilgileri al
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL environment variable not found")
                return None
                
            # URL'den bağlantı bilgilerini çıkar
            # Format: postgresql://username:password@host:port/database
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
            if not match:
                logger.error("Invalid DATABASE_URL format")
                return None
                
            username, password, host, port, database = match.groups()
            
            # pg_dump komutu oluştur
            pg_dump_command = [
                'pg_dump',
                f'--host={host}',
                f'--port={port}',
                f'--username={username}',
                f'--dbname={database}',
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                '--format=custom',
                f'--file={backup_path}'
            ]
            
            # Environment variables for pg_dump
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            # Yedekleme işlemini çalıştır
            logger.info(f"Creating database backup: {backup_filename}")
            result = subprocess.run(pg_dump_command, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                return None
                
            logger.info(f"Database backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}")
            return None
    
    def upload_to_google_drive(self, file_path):
        """Google Drive'a dosya yükler"""
        if not self.is_production:
            logger.info("Demo ortamında Google Drive yükleme yapılmıyor")
            return False
            
        try:
            # Google Drive credentials
            credentials_file = os.environ.get('GOOGLE_DRIVE_CREDENTIALS_FILE')
            if not credentials_file or not os.path.exists(credentials_file):
                logger.error("Google Drive credentials file not found")
                return False
                
            folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
            if not folder_id:
                logger.error("Google Drive folder ID not found")
                return False
                
            # Google Drive API client oluştur
            credentials = service_account.Credentials.from_service_account_file(
                credentials_file,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Dosya metadata
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [folder_id]
            }
            
            # Media upload
            media = MediaFileUpload(file_path, resumable=True)
            
            # Dosyayı yükle
            logger.info(f"Uploading {file_path} to Google Drive")
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"File uploaded successfully to Google Drive. File ID: {file.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {str(e)}")
            return False
    
    def cleanup_old_backups(self, keep_days=7):
        """Eski yedek dosyalarını temizler"""
        if not self.is_production:
            logger.info("Demo ortamında temizlik yapılmıyor")
            return
            
        try:
            backup_dir = 'backup'
            if not os.path.exists(backup_dir):
                return
                
            current_time = datetime.now()
            
            for filename in os.listdir(backup_dir):
                if filename.startswith('muhasebe_backup_') and filename.endswith('.sql'):
                    file_path = os.path.join(backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Dosya yaşı
                    age_days = (current_time - file_time).days
                    
                    if age_days > keep_days:
                        os.remove(file_path)
                        logger.info(f"Deleted old backup: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
    
    def perform_backup(self):
        """Tam yedekleme işlemi yapar"""
        if not self.is_production:
            logger.info("Demo ortamında yedekleme yapılmıyor")
            return False
            
        try:
            logger.info("Starting backup process")
            
            # 1. Veritabanı yedeği oluştur
            backup_path = self.create_database_backup()
            if not backup_path:
                logger.error("Failed to create database backup")
                return False
                
            # 2. Google Drive'a yükle
            upload_success = self.upload_to_google_drive(backup_path)
            if not upload_success:
                logger.error("Failed to upload to Google Drive")
                return False
                
            # 3. Eski yedekleri temizle
            self.cleanup_old_backups()
            
            logger.info("Backup process completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in backup process: {str(e)}")
            return False

# Backup task scheduler
def schedule_daily_backup():
    """Günlük yedekleme zamanlayıcısı"""
    import schedule
    import time
    
    backup_service = BackupService()
    
    # Her gün saat 02:00'de yedekle
    schedule.every().day.at("02:00").do(backup_service.perform_backup)
    
    logger.info("Daily backup scheduler started")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Her dakika kontrol et

if __name__ == "__main__":
    # Manual backup for testing
    backup_service = BackupService()
    backup_service.perform_backup()
