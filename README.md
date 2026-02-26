# 💰 Muhasebe Pro

Modern, mobil uyumlu muhasebe ve fiş yönetim uygulaması.

## ✨ Özellikler

- 📊 **Dashboard** - Anlık finansal durum özeti
- 💵 **Gelir/Gider Takibi** - Tüm işlemlerinizi kaydedin
- 👥 **Müşteri Yönetimi** - Müşteri borç/alacak takibi
- 📦 **Ürün Yönetimi** - Ürün ve fiyat listesi
- 🧾 **Fiş Kesme** - Satış fişi oluşturma ve yazdırma
- 📱 **Mobil Uyumlu** - Telefondan rahat kullanım
- 🌙 **Koyu Tema** - Göz yormayan modern tasarım
- 💾 **Google Drive Yedekleme** - Otomatik günlük yedek

## 🚀 Kurulum

### 1. Projeyi İndirin
```bash
git clone https://github.com/KULLANICI_ADINIZ/muhasebe-pro.git
cd muhasebe-pro
```

### 2. Sanal Ortam Oluşturun
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# veya
source venv/bin/activate  # Linux/Mac
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Veritabanı Migration'ları Çalıştırın

**⚠️ Önemli:** Geliştirme ve production ortamlarında tüm schema değişiklikleri Flask-Migrate migration sistemi üzerinden yapılmalıdır. `db.create_all()` kullanımı tamamen kaldırılmıştır.

**İlk kurulum (Development ve Production):**
```bash
# Migration sistemini başlat (ilk kurulumda bir kez çalıştırın)
flask db init

# İlk migration oluştur
flask db migrate -m "initial migration"

# Migration'ları veritabanına uygula
flask db upgrade
```

**Sonraki güncellemeler:**
```bash
# Model değişikliklerinden yeni migration oluştur
flask db migrate -m "add new feature"

# Migration'ları uygula
flask db upgrade
```

### 5. Uygulamayı Başlatın
```bash
python app.py
```

Tarayıcıda açın: `http://localhost:5000`

## 🗄️ Veritabanı Yönetimi

### Güvenlik Önlemleri

✅ **Migration-First Yaklaşım:**
- Geliştirme ve production ortamları aynı migration sistemini kullanır
- `db.create_all()` otomatik çalıştırılmaz - migration zorunludur
- Tüm schema değişiklikleri Flask-Migrate ile yönetilir

✅ **Production'da veri kaybı yok:**
- Uygulama başlarken hiçbir durumda veritabanı DROP edilmez
- Sadece migration sistemi kullanılır
- Bağlantı hatası varsa uygulama başlamaz (veri koruma için)

### Migration Komutları

| Komut | Açıklama |
|-------|----------|
| `flask db init` | Migration sistemi başlat |
| `flask db migrate` | Model değişikliklerinden migration oluştur |
| `flask db upgrade` | Migration'ları uygula |
| `flask db downgrade` | Son migration'ı geri al |
| `flask db current` | Mevcut versiyonu göster |
| `flask db history` | Tüm geçmişi göster |

### Ortam Değişkenleri

```bash
# .env dosyasında
ENV=development  # veya production
DATABASE_URL=postgresql+pg8000://user:pass@host/dbname
FLASK_SECRET_KEY=your-secret-key
```

## � Production Deployment

### Railway/Render/Heroku Deployment

Uygulama başlatılırken otomatik olarak veritabanı migration'ları çalıştırılır:

```
1. flask db upgrade (migration'ları uygula)
2. gunicorn --workers 1 --timeout 120 --bind 0.0.0.0:8080 "app:create_app()"
```

**Önemli:**
- Eğer migration başarısız olursa uygulama **başlatılmaz**
- Bu sayede veritabanı şeması her zaman güncel tutulur
- Veri kaybı riski önlenir

### Manual Production Deployment

```bash
# 1. Ortam değişkenlerini ayarla
export ENV=production
export DATABASE_URL=postgresql+pg8000://user:pass@host/dbname
export FLASK_SECRET_KEY=$(openssl rand -hex 32)

# 2. Migration'ları uygula
flask db upgrade

# 3. Uygulamayı başlat
gunicorn --workers 1 --timeout 120 --bind 0.0.0.0:8080 "app:create_app()"
```

## �📱 Telefonda Kullanım

1. Uygulamayı bir hosting servisine yükleyin (Railway, Render, vb.)
2. Verilen URL'yi telefonun tarayıcısında açın
3. **Ana ekrana ekleyin:**
   - **iPhone:** Safari → Paylaş → "Ana Ekrana Ekle"
   - **Android:** Chrome → ⋮ → "Ana ekrana ekle"

## 💾 Google Drive Yedekleme

1. [Google Cloud Console](https://console.cloud.google.com)'dan proje oluşturun
2. Google Drive API'yi etkinleştirin
3. OAuth credentials oluşturup `credentials.json` olarak kaydedin
4. `python backup.py` çalıştırın

## 🛠️ Teknolojiler

- **Backend:** Flask, SQLAlchemy
- **Frontend:** Bootstrap 5, Bootstrap Icons
- **Veritabanı:** SQLite
- **Font:** Inter (Google Fonts)

## 🧪 Testing

### Test Ortamı (Migration-First)

Test ortamı, geliştirme ve production ortamlarıyla aynı **migration-first** yaklaşımını kullanır:

- Test veritabanı SQLite dosya tabanlıdır (`test.db`)
- Migration'lar `flask db upgrade` ile uygulanır
- `db.create_all()` kullanılmaz - migration sistemi zorunludur
- Bu sayede testler gerçek migration yapısını doğrular

### Running Tests Locally

```bash
# Install dependencies (including test dependencies)
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run with coverage report
pytest --cov=app --cov-report=html
```

### Test Structure

- `tests/conftest.py` - Test fixtures and configuration (migration-first setup)
- `tests/test_auth.py` - Authentication tests (login, user creation)
- `tests/test_company.py` - Company and customer management tests
- `tests/test_reports.py` - Report and API endpoint tests

### CI/CD

Tests run automatically on GitHub Actions for every push and pull request. CI pipeline'da migration'lar otomatik olarak uygulanır ve testler migration yapısını doğrular.

## 📁 Proje Yapısı

```
├── app.py              # Ana uygulama
├── config.py           # Ayarlar
├── models.py           # Veritabanı modelleri
├── backup.py           # Yedekleme scripti
├── requirements.txt    # Bağımlılıklar
├── Procfile           # Hosting için
├── tests/             # Test dosyaları
│   ├── conftest.py    # Test yapılandırması
│   ├── test_auth.py   # Auth testleri
│   ├── test_company.py # Şirket testleri
│   └── test_reports.py # Rapor testleri
├── routes/
│   ├── main.py        # Sayfa route'ları
│   └── api.py         # API endpoint'leri
└── templates/         # HTML şablonları
```

## 📄 Lisans

MIT License
