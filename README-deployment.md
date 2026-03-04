# DigitalOcean Droplet Production Deployment Guide

Bu rehber, Flask SaaS Muhasebe uygulamasının DigitalOcean Droplet üzerinde Docker ile production ortamına kurulumunu açıklar.

## 📋 Gereksinimler

- DigitalOcean hesabı
- DigitalOcean Droplet (Ubuntu 22.04)
- Minimum 2 GB RAM, 20 GB SSD (Basic Droplet yeterli)
- Domain (SSL için isteğe bağlı)

## 🚀 Hızlı Kurulum

### 1. DigitalOcean Droplet Oluşturma

1. **DigitalOcean Console**'a giriş yapın
2. **Create** → **Droplets** seçin
3. **Region**: En yakın lokasyon ( Frankfurt, Amsterdam, vs.)
4. **Image**: Ubuntu 22.04 (LTS) x64
5. **Plan**: Basic
   - **CPU Options**: Regular Intel with SSD
   - **Size**: $6/month (1 GB RAM / 1 CPU / 25 GB SSD) - Minimal
   - Veya $12/month (2 GB RAM / 1 CPU / 50 GB SSD) - Önerilen
6. **Authentication**: SSH Key (önerilir) veya Password
7. **Hostname**: muhasebe-app (veya istediğiniz isim)
8. **Create Droplet**

### 2. Sunucuya Bağlanma

Droplet IP adresini DigitalOcean panelinden alın:

```bash
ssh root@DROPLET_IP_ADRESI

# Örnek:
ssh root@167.172.123.45
```

### 3. Docker Kurulumu

```bash
# Sistem güncelleme
apt update && apt upgrade -y

# Docker kurulumu
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose kurulumu
apt install -y docker-compose-plugin

# Docker'ı test kullanıcısına ekle (opsiyonel)
usermod -aG docker root
```

### 4. Proje Kurulumu

```bash
# Proje dizini
cd /opt

# GitHub'dan klonla
git clone https://github.com/mahmutt44/muhasebe-pro.git muhasebe
cd muhasebe

# Environment dosyası oluştur
cp .env.example .env
nano .env
```

`.env` dosyasını düzenleyin:

```env
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key-here-change-this-min-32-chars
POSTGRES_DB=muhasebe
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-postgres-password-here
DEMO_ADMIN_PASSWORD=your-demo-admin-password
```

**SECRET_KEY** için güçlü bir key oluşturun:
```bash
openssl rand -hex 32
```

### 5. Container'ları Başlatma

```bash
# Container'ları arka planda başlat
docker-compose up -d

# Logları kontrol et
docker-compose logs -f
```

### 6. Database Migration

```bash
# Migration'ları çalıştır
docker-compose exec web flask db upgrade
```

### 7. Erişim Testi

Tarayıcınızda şu adresi açın:
```
http://DROPLET_IP
```

Örnek: `http://167.172.123.45`

## 🔒 Güvenlik Yapılandırması

### Firewall (UFW)

```bash
# UFW kurulumu
apt install -y ufw

# Varsayılan kurallar
ufw default deny incoming
ufw default allow outgoing

# Portlar
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# Firewall'u aktif et
ufw enable
```

### Fail2Ban

```bash
# Kurulum
apt install -y fail2ban

# Otomatik başlatma
systemctl enable fail2ban
systemctl start fail2ban
```

## 🔐 SSL Sertifikası (HTTPS)

Domain'iniz varsa Let's Encrypt ile ücretsiz SSL:

### 1. Domain DNS Ayarları

Domain sağlayıcınızdan:
- **A Record**: `@` → `DROPLET_IP`
- **A Record**: `www` → `DROPLET_IP`

DNS yayılımı 24 saat sürebilir.

### 2. Certbot Kurulumu

```bash
# Certbot kurulumu
apt install -y certbot

# Nginx container'ını durdur
docker-compose stop nginx

# Sertifika al
# Örnek: certbot certonly --standalone -d muhasebeniz.com
certbot certonly --standalone -d your-domain.com

# Nginx config'i domain için güncelle
nano nginx/conf.d/default.conf
```

`server_name` satırını domain'inizle güncelleyin:
```nginx
server_name your-domain.com;
```

### 3. SSL için Nginx Güncelleme

SSL sertifikalarını Nginx container'ına bağlamak için `docker-compose.yml` güncelleme:

```yaml
  nginx:
    image: nginx:alpine
    container_name: muhasebe_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro  # SSL sertifikaları
      - /etc/ssl/certs:/etc/ssl/certs:ro
    depends_on:
      - web
    networks:
      - muhasebe_network
```

### 4. Container'ları Yeniden Başlat

```bash
docker-compose up -d
```

## 📊 Yararlı Komutlar

### Container Yönetimi

```bash
# Container'ları başlat
docker-compose up -d

# Container'ları durdur
docker-compose down

# Container'ları yeniden başlat
docker-compose restart

# Container durumlarını görüntüle
docker-compose ps

# Logları görüntüle
docker-compose logs -f

# Belirli servisin loglarını görüntüle
docker-compose logs -f web
```

### Database İşlemleri

```bash
# Database backup al
docker-compose exec db pg_dump -U postgres muhasebe > backup_$(date +%Y%m%d_%H%M%S).sql

# Database restore et
cat backup.sql | docker-compose exec -T db psql -U postgres -d muhasebe

# Database shell'e gir
docker-compose exec db psql -U postgres -d muhasebe
```

### Güncelleme

```bash
# Son kodları çek
cd /opt/muhasebe
git pull origin main

# Container'ları yeniden oluştur
docker-compose down
docker-compose up -d --build

# Migration'ları çalıştır
docker-compose exec web flask db upgrade
```

## 💾 Backup Otomasyonu

### Backup Script

`/opt/backup.sh` dosyası oluşturun:

```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

mkdir -p $BACKUP_DIR

cd /opt/muhasebe

# Database backup
docker-compose exec -T db pg_dump -U postgres muhasebe > $BACKUP_DIR/muhasebe_$DATE.sql

# Eski backup'ları sil (7 günden eski)
find $BACKUP_DIR -name "muhasebe_*.sql" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR/muhasebe_$DATE.sql"
```

### Cron Job

Her gün 02:00'de otomatik backup:

```bash
chmod +x /opt/backup.sh

# Crontab düzenle
crontab -e

# Şu satırı ekle:
0 2 * * * /opt/backup.sh >> /var/log/backup.log 2>&1
```

## 🌐 Servisler ve Portlar

| Servis | Port | Açıklama |
|--------|------|----------|
| Nginx | 80/443 | Reverse Proxy |
| Flask (Gunicorn) | 8000 | Internal only |
| PostgreSQL | 5432 | Internal only |

## 🐛 Sorun Giderme

### Container'lar başlamıyor

```bash
# Logları kontrol et
docker-compose logs

# Container'ların durumunu kontrol et
docker-compose ps
```

### Database bağlantı hatası

```bash
# Database container'ının sağlıklı olduğundan emin ol
docker-compose exec db pg_isready

# Migration'ları tekrar çalıştır
docker-compose exec web flask db upgrade
```

### 502 Bad Gateway

```bash
# Web container'ının çalıştığından emin ol
docker-compose ps

# Web loglarını kontrol et
docker-compose logs web
```

## 📈 Monitoring

### System Resources

```bash
# CPU ve Memory kullanımı
docker stats

# Disk kullanımı
df -h
```

## 🔐 Güvenlik Notları

1. **SECRET_KEY**: Production için güçlü ve benzersiz bir key kullanın (min 32 karakter)
2. **POSTGRES_PASSWORD**: Güçlü bir database şifresi kullanın
3. **Firewall**: Sadece gerekli portları açın (22, 80, 443)
4. **SSL**: Production için mutlaka SSL kullanın
5. **Backup**: Düzenli database backup'ları alın
6. **Updates**: Düzenli olarak sistem ve Docker image güncellemeleri yapın

## 📞 Destek

Sorun yaşarsanız:

1. Logları kontrol edin: `docker-compose logs`
2. Container durumlarını kontrol edin: `docker-compose ps`
3. GitHub Issues üzerinden destek alın

## 📝 Changelog

- **v1.0**: DigitalOcean Droplet deployment yapılandırması
- Docker + Gunicorn + Nginx + PostgreSQL stack
- Let's Encrypt SSL desteği
- Otomatik backup scripti
