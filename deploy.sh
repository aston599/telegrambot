#!/bin/bash

# 🤖 KirveHub Bot - DigitalOcean Ubuntu Deployment Script
# Python 3.12+ uyumlu, Ubuntu 24.04 production-ready kurulum

set -e  # Hata durumunda script'i durdur

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOT_USER="kirvehub"
BOT_DIR="/home/$BOT_USER/telegrambot"
SERVICE_NAME="kirvehub-bot"
PYTHON_VERSION="3.12"

echo -e "${BLUE}🚀 KirveHub Bot Deployment Başlatılıyor...${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ Bu script root olarak çalıştırılmamalı!${NC}"
   exit 1
fi

# Update system
echo -e "${YELLOW}📦 Sistem güncelleniyor...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${YELLOW}📦 Gerekli paketler kuruluyor...${NC}"
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    postgresql-client \
    nginx \
    curl \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev

# Create user if not exists
if ! id "$BOT_USER" &>/dev/null; then
    echo -e "${YELLOW}👤 Bot kullanıcısı oluşturuluyor...${NC}"
    sudo useradd -m -s /bin/bash $BOT_USER
    sudo usermod -aG sudo $BOT_USER
fi

# Create bot directory
echo -e "${YELLOW}📁 Bot dizini oluşturuluyor...${NC}"
sudo mkdir -p $BOT_DIR
sudo chown $BOT_USER:$BOT_USER $BOT_DIR

# Clone or update repository
if [ -d "$BOT_DIR/.git" ]; then
    echo -e "${YELLOW}🔄 Repository güncelleniyor...${NC}"
    cd $BOT_DIR
    git pull origin main
else
    echo -e "${YELLOW}📥 Repository klonlanıyor...${NC}"
    cd /tmp
    git clone https://github.com/your-repo/kirvehub-bot.git
    sudo cp -r kirvehub-bot/* $BOT_DIR/
    sudo chown -R $BOT_USER:$BOT_USER $BOT_DIR
fi

# Create virtual environment
echo -e "${YELLOW}🐍 Python virtual environment oluşturuluyor...${NC}"
cd $BOT_DIR
python3.12 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}📦 Python paketleri kuruluyor...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo -e "${YELLOW}📁 Gerekli dizinler oluşturuluyor...${NC}"
mkdir -p logs data

# Set proper permissions
echo -e "${YELLOW}🔐 İzinler ayarlanıyor...${NC}"
chmod +x deploy.sh
chmod 755 logs data

# Create .env file if not exists
if [ ! -f "$BOT_DIR/.env" ]; then
    echo -e "${YELLOW}⚙️ .env dosyası oluşturuluyor...${NC}"
    cat > $BOT_DIR/.env << EOF
# Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_admin_id_here
DATABASE_URL=postgresql://username:password@localhost:5432/kirvehub_db

# Environment
PRODUCTION_MODE=true
DEBUG_MODE=false
MAINTENANCE_MODE=false

# Server Settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
WORKER_PROCESSES=2

# Database Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Performance
MAX_CONCURRENT_UPDATES=50
UPDATE_TIMEOUT=30
RATE_LIMIT_DELAY=0.1

# Security
ENABLE_RATE_LIMITING=true
MAX_MESSAGES_PER_MINUTE=60
ENABLE_IP_WHITELIST=false
EOF
    echo -e "${RED}⚠️  Lütfen .env dosyasını düzenleyin!${NC}"
fi

# Setup systemd service
echo -e "${YELLOW}🔧 Systemd service kuruluyor...${NC}"
sudo cp systemd/kirvehub-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Setup Nginx (optional)
echo -e "${YELLOW}🌐 Nginx konfigürasyonu...${NC}"
sudo tee /etc/nginx/sites-available/kirvehub-bot > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/kirvehub-bot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Setup firewall
echo -e "${YELLOW}🔥 Firewall ayarlanıyor...${NC}"
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Setup log rotation
echo -e "${YELLOW}📋 Log rotation ayarlanıyor...${NC}"
sudo tee /etc/logrotate.d/kirvehub-bot > /dev/null << EOF
$BOT_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $BOT_USER $BOT_USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

# Final setup
echo -e "${YELLOW}🎯 Son ayarlar yapılıyor...${NC}"
sudo chown -R $BOT_USER:$BOT_USER $BOT_DIR

echo -e "${GREEN}✅ Deployment tamamlandı!${NC}"
echo -e "${BLUE}📋 Sonraki adımlar:${NC}"
echo -e "1. ${YELLOW}cd $BOT_DIR${NC}"
echo -e "2. ${YELLOW}nano .env${NC} (Bot token ve database bilgilerini girin)"
echo -e "3. ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
echo -e "4. ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "5. ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC} (logları izlemek için)"

echo -e "${GREEN}🎉 KirveHub Bot başarıyla kuruldu!${NC}" 