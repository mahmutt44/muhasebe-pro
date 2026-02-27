#!/bin/bash
#
# Hetzner VPS Production Deployment Script
# Flask SaaS Muhasebe Uygulaması
#

set -e

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log fonksiyonu
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Root kontrolü
if [[ $EUID -ne 0 ]]; then
   error "Bu script root yetkisi ile çalıştırılmalıdır."
   exit 1
fi

log "Flask SaaS Muhasebe - Hetzner Deployment Başlıyor..."

# 1. Sistem güncelleme
log "Sistem paketleri güncelleniyor..."
apt-get update
apt-get upgrade -y

# 2. Docker kurulumu
log "Docker kuruluyor..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    usermod -aG docker ${SUDO_USER:-$USER}
    success "Docker kuruldu"
else
    log "Docker zaten kurulu"
fi

# 3. Docker Compose kurulumu
log "Docker Compose kuruluyor..."
if ! command -v docker-compose &> /dev/null; then
    apt-get install -y docker-compose-plugin
    # Alternatif: pip ile kurulum
    # apt-get install -y python3-pip
    # pip3 install docker-compose
    success "Docker Compose kuruldu"
else
    log "Docker Compose zaten kurulu"
fi

# 4. Gerekli paketler
log "Gerekli paketler kuruluyor..."
apt-get install -y \
    git \
    curl \
    wget \
    nano \
    htop \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx

# 5. Firewall yapılandırması
log "Firewall yapılandırılıyor..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
success "Firewall yapılandırıldı"

# 6. Fail2ban yapılandırması
log "Fail2ban yapılandırılıyor..."
systemctl enable fail2ban
systemctl start fail2ban

# 7. Proje dizini oluştur
PROJECT_DIR="/opt/muhasebe"
log "Proje dizini oluşturuluyor: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 8. GitHub'dan projeyi klonla
log "GitHub'dan proje klonlanıyor..."
if [ -d "$PROJECT_DIR/.git" ]; then
    log "Proje zaten var, güncelleniyor..."
    git pull origin main
else
    # Repo URL'sini kullanıcıdan al veya varsayılan kullan
    REPO_URL="https://github.com/mahmutt44/muhasebe-pro.git"
    git clone $REPO_URL .
fi
success "Proje klonlandı/güncellendi"

# 9. Environment dosyası oluştur
log "Environment dosyası oluşturuluyor..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    
    # Güçlü secret key oluştur
    SECRET_KEY=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    DEMO_PASSWORD=$(openssl rand -hex 8)
    
    sed -i "s/your-very-strong-secret-key-change-this-in-production/$SECRET_KEY/" .env
    sed -i "s/your-secure-postgres-password/$POSTGRES_PASSWORD/" .env
    sed -i "s/change_this_strong_password/$DEMO_PASSWORD/" .env
    
    warn ".env dosyası oluşturuldu. Lütfen gerekli değişiklikleri yapın:"
    warn "nano $PROJECT_DIR/.env"
    
    success "Environment dosyası oluşturuldu"
else
    log ".env dosyası zaten var"
fi

# 10. Docker containerları başlat
log "Docker containerları başlatılıyor..."
docker-compose down 2>/dev/null || true
docker-compose pull
docker-compose up -d --build

# 11. Database migration
log "Veritabanı migration'ları çalıştırılıyor..."
sleep 10  # PostgreSQL'in başlaması için bekle
docker-compose exec -T app flask db upgrade || warn "Migration hatası - manuel kontrol gerekebilir"

# 12. SSL Sertifikası (isteğe bağlı)
read -p "SSL sertifikası kurulsun mu? (y/N): " ssl_choice
if [[ $ssl_choice == "y" || $ssl_choice == "Y" ]]; then
    read -p "Domain adını girin (örn: muhasebe.example.com): " domain
    if [ ! -z "$domain" ]; then
        log "SSL sertifikası için Nginx yapılandırması güncelleniyor..."
        # Nginx config'i domain için güncelle
        sed -i "s/server_name _;/server_name $domain;/" nginx/conf.d/default.conf
        
        # Let's Encrypt ile sertifika al
        certbot --nginx -d $domain --non-interactive --agree-tos --email admin@$domain || warn "SSL kurulumunda hata"
        
        # Nginx yeniden başlat
        docker-compose restart nginx
    fi
fi

# 13. Durum kontrolü
log "Servis durumları kontrol ediliyor..."
docker-compose ps

# 14. Log görüntüleme
log "Container logları (son 50 satır):"
docker-compose logs --tail=50

success "Deployment tamamlandı!"
echo ""
echo "=========================================="
echo "  Muhasebe Uygulaması Çalışıyor!"
echo "=========================================="
echo ""
echo "Uygulama URL: http://$(curl -s ifconfig.me 2>/dev/null || echo 'SUNUCU_IP')"
echo "Proje dizini: $PROJECT_DIR"
echo ""
echo "Yararlı komutlar:"
echo "  docker-compose logs -f        # Logları takip et"
echo "  docker-compose ps             # Container durumları"
echo "  docker-compose restart        # Tüm servisleri yeniden başlat"
echo "  docker-compose down           # Tüm servisleri durdur"
echo ""
echo "=========================================="
