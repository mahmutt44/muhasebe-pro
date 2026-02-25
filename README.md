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

**Geliştirme ortamında:**
```bash
# İlk migration oluştur (models.py değişikliklerinden)
flask db migrate -m "initial migration"

# Migration'ları uygula
flask db upgrade
```

**Production ortamında:**
```bash
# Uygulamayı başlatmadan önce migration'ları çalıştır
flask db upgrade
```

### 5. Uygulamayı Başlatın
```bash
python app.py
```

Tarayıcıda açın: `http://localhost:5000`

## 🗄️ Veritabanı Yönetimi

### Güvenlik Önlemleri

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

## 📱 Telefonda Kullanım

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

## 📁 Proje Yapısı

```
├── app.py              # Ana uygulama
├── config.py           # Ayarlar
├── models.py           # Veritabanı modelleri
├── backup.py           # Yedekleme scripti
├── requirements.txt    # Bağımlılıklar
├── Procfile           # Hosting için
├── routes/
│   ├── main.py        # Sayfa route'ları
│   └── api.py         # API endpoint'leri
└── templates/         # HTML şablonları
```

## 📄 Lisans

MIT License
