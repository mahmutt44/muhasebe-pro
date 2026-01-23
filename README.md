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

### 4. Uygulamayı Başlatın
```bash
python app.py
```

Tarayıcıda açın: `http://localhost:5000`

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
