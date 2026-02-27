# Hetzner VPS Production Deployment Guide

Bu rehber, Flask SaaS Muhasebe uygulamasının Hetzner VPS üzerinde Docker ile production ortamına kurulumunu açıklar.

## 📋 Gereksinimler

- Hetzner VPS (Ubuntu 22.04+ önerilir)
- Minimum 2 GB RAM, 20 GB SSD
- Public IP adresi
- Domain (SSL için isteğe bağlı)

## 🚀 Hızlı Kurulum (Tek Komut)

```bash
# Sunucunuza SSH ile bağlandıktan sonra:
curl -fsSL https://raw.githubusercontent.com/mahmutt44/muhasebe-pro/main/deploy-hetzner.sh | sudo bash
```

## 🛠️ Manuel Kurulum Adımları

### 1. Sunucu Güncelleme

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Docker Kurulumu

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Docker Compose Kurulumu

```bash
sudo apt install -y docker-compose-plugin
```

### 4. Projeyi Klonlama

```bash
cd /opt
sudo git clone https://github.com/mahmutt44/muhasebe-pro.git muhasebe
cd muhasebe
```

### 5. Environment Dosyası

```bash
sudo cp .env.example .env
sudo nano .env
```

Aşağıdaki değerleri güncelleyin:

```env
SECRET_KEY=your-super-secure-secret-key-here
POSTGRES_PASSWORD=your-secure-postgres-password
DEMO_ADMIN_PASSWORD=your-demo-admin-password
```

### 6. Container'ları Başlatma

```bash
sudo docker-compose up -d
```

### 7. Database Migration

```bash
sudo docker-compose exec app flask db upgrade
```

## 🔒 Güvenlik Yapılandırması

### Firewall (UFW)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Fail2Ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### SSL Sertifikası (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d muhasebeniz.com
```

## 📁 Dosya Yapısı

```
muhasebe/
├── app.py                 # Ana Flask uygulaması
├── Dockerfile             # Flask container image
├── docker-compose.yml     # Multi-container yapılandırma
├── .env.example           # Environment şablonu
├── nginx/
│   ├── nginx.conf         # Ana Nginx yapılandırması
│   └── conf.d/
│       └── default.conf   # Server blok yapılandırması
├── deploy-hetzner.sh      # Otomatik deployment scripti
└── ...
```

## 🔧 Yararlı Komutlar

### Container Yönetimi

```bash
# Container'ları başlat
sudo docker-compose up -d

# Container'ları durdur
sudo docker-compose down

# Container'ları yeniden başlat
sudo docker-compose restart

# Container durumlarını görüntüle
sudo docker-compose ps

# Logları görüntüle
sudo docker-compose logs -f

# Belirli servisin loglarını görüntüle
sudo docker-compose logs -f app
```

### Database İşlemleri

```bash
# Database backup al
sudo docker-compose exec db pg_dump -U muhasebe_user muhasebe > backup.sql

# Database restore et
cat backup.sql | sudo docker-compose exec -T db psql -U muhasebe_user muhasebe

# Database shell'e gir
sudo docker-compose exec db psql -U muhasebe_user -d muhasebe
```

### Güncelleme

```bash
# Son kodları çek
cd /opt/muhasebe
git pull origin main

# Container'ları yeniden oluştur
sudo docker-compose down
sudo docker-compose up -d --build

# Migration'ları çalıştır
sudo docker-compose exec app flask db upgrade
```

## 🌐 Servisler ve Portlar

| Servis | Port | Açıklama |
|--------|------|----------|
| Nginx | 80/443 | Reverse Proxy |
| Flask App | 8000 | Gunicorn (internal) |
| PostgreSQL | 5432 | Database (internal) |

## 🐛 Sorun Giderme

### Container'lar başlamıyor

```bash
# Logları kontrol et
sudo docker-compose logs

# Container'ların durumunu kontrol et
sudo docker-compose ps
```

### Database bağlantı hatası

```bash
# Database container'ının sağlıklı olduğundan emin ol
sudo docker-compose exec db pg_isready

# Migration'ları tekrar çalıştır
sudo docker-compose exec app flask db upgrade
```

### 502 Bad Gateway

```bash
# App container'ının çalıştığından emin ol
sudo docker-compose ps

# App loglarını kontrol et
sudo docker-compose logs app
```

## 📊 Monitoring

### System Resources

```bash
# CPU ve Memory kullanımı
sudo docker stats

# Disk kullanımı
sudo df -h
```

### Health Check

```bash
curl http://localhost/health
```

## 🔐 Güvenlik Notları

1. **SECRET_KEY**: Production için güçlü ve benzersiz bir key kullanın
2. **POSTGRES_PASSWORD**: Güçlü bir database şifresi kullanın
3. **Firewall**: Sadece gerekli portları açın (22, 80, 443)
4. **SSL**: Production için mutlaka SSL kullanın
5. **Backup**: Düzenli database backup'ları alın

## 📞 Destek

Sorun yaşarsanız:

1. Logları kontrol edin: `sudo docker-compose logs`
2. Container durumlarını kontrol edin: `sudo docker-compose ps`
3. GitHub Issues üzerinden destek alın

## 📝 Changelog

- **v1.0**: İlk production deployment yapılandırması
- Docker + Gunicorn + Nginx + PostgreSQL stack
- Let's Encrypt SSL desteği
- Otomatik deployment scripti
