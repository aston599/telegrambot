# 🚀 DigitalOcean'a Bot Yükleme Rehberi

## 📋 Ön Gereksinimler

1. **DigitalOcean Hesabı** - Ücretsiz hesap oluştur
2. **SSH Key** - Windows'ta oluştur
3. **Bot Token** - @BotFather'dan al
4. **Admin ID** - @userinfobot'dan al

---

## 🔑 1. SSH Key Oluşturma (Windows)

```powershell
# PowerShell aç
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# Enter tuşuna bas (varsayılan konum)
# Passphrase boş bırak
# Public key'i kopyala:
cat ~/.ssh/id_rsa.pub
```

---

## 🌐 2. DigitalOcean Droplet Oluşturma

1. **DigitalOcean Dashboard**'a git
2. **"Create" > "Droplets"** seç
3. **Ubuntu 24.04 LTS** seç
4. **Plan**: Basic > $12/month (2GB RAM, 1 vCPU)
5. **Datacenter**: Frankfurt (EU) veya Amsterdam
6. **Authentication**: SSH Key ekle (yukarıda oluşturduğun)
7. **Hostname**: kirvehub-bot
8. **"Create Droplet"** tıkla

---

## 🔧 3. Sunucuya İlk Bağlantı

```bash
# Sunucuya bağlan
ssh root@YOUR_DROPLET_IP

# Sistem güncelle
apt update && apt upgrade -y

# Gerekli paketleri kur
apt install -y git python3.12 python3.12-venv python3.12-dev python3-pip postgresql postgresql-contrib nginx curl wget unzip

# Bot kullanıcısı oluştur
useradd -m -s /bin/bash kirvehub
usermod -aG sudo kirvehub
passwd kirvehub  # Şifre: kirvehub123

# Sudo yetkisi ver
echo "kirvehub ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
```

---

## 📥 4. Proje İndirme ve Kurulum

```bash
# Bot kullanıcısına geç
su - kirvehub

# Projeyi indir
git clone https://github.com/aston599/telegrambot.git
cd telegrambot

# Python environment kur
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Gerekli dizinleri oluştur
mkdir -p logs data
chmod 755 logs data
```

---

## 🗄️ 5. Database Kurulumu

```bash
# PostgreSQL servisini başlat
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Database kullanıcısı oluştur
sudo -u postgres psql

# PostgreSQL komutları:
CREATE USER kirvehub WITH PASSWORD 'kirvehub123';
CREATE DATABASE kirvehub_db OWNER kirvehub;
GRANT ALL PRIVILEGES ON DATABASE kirvehub_db TO kirvehub;
\q

# Database bağlantısını test et
psql -h localhost -U kirvehub -d kirvehub_db
# Şifre: kirvehub123
# Çıkış: \q
```

---

## ⚙️ 6. Bot Konfigürasyonu

```bash
# Environment dosyası oluştur
cp env.example .env
nano .env
```

### .env Dosyası İçeriği:

```env
# Bot Token (Telegram BotFather'dan al)
BOT_TOKEN=your_actual_bot_token_here

# Admin User ID (Telegram user ID)
ADMIN_USER_ID=your_actual_admin_id_here

# Database URL
DATABASE_URL=postgresql://kirvehub:kirvehub123@localhost:5432/kirvehub_db

# Environment Settings
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

# Logging Settings
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Performance Settings
MAX_CONCURRENT_UPDATES=50
UPDATE_TIMEOUT=30
RATE_LIMIT_DELAY=0.1

# Security Settings
ENABLE_RATE_LIMITING=true
MAX_MESSAGES_PER_MINUTE=60
ENABLE_IP_WHITELIST=false

# Point System Settings
POINT_PER_MESSAGE=0.02
DAILY_POINT_LIMIT=5.00
FLOOD_PROTECTION_SECONDS=10
MIN_MESSAGE_LENGTH=5

# Notification Settings
ENABLE_STARTUP_NOTIFICATIONS=true
ENABLE_SHUTDOWN_NOTIFICATIONS=true
NOTIFICATION_DELAY=0.1
```

---

## 🔧 7. Service Kurulumu

```bash
# Systemd service dosyası oluştur
sudo nano /etc/systemd/system/kirvehub-bot.service
```

### Service Dosyası İçeriği:

```ini
[Unit]
Description=KirveHub Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=kirvehub
Group=kirvehub
WorkingDirectory=/home/kirvehub/telegrambot
Environment=PATH=/home/kirvehub/telegrambot/venv/bin
Environment=PYTHONPATH=/home/kirvehub/telegrambot
ExecStart=/home/kirvehub/telegrambot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/home/kirvehub/telegrambot

[Install]
WantedBy=multi-user.target
```

```bash
# Service'i etkinleştir
sudo systemctl daemon-reload
sudo systemctl enable kirvehub-bot
sudo systemctl start kirvehub-bot

# Service durumunu kontrol et
sudo systemctl status kirvehub-bot
```

---

## 🧪 8. Test ve Kontrol

```bash
# Manuel test
cd /home/kirvehub/telegrambot
source venv/bin/activate
python main.py

# Logları kontrol et
sudo journalctl -u kirvehub-bot -f

# Bot durumunu kontrol et
sudo systemctl status kirvehub-bot

# Database bağlantısını test et
cd /home/kirvehub/telegrambot
source venv/bin/activate
python -c "
import asyncio
from database import init_database
async def test():
    result = await init_database()
    print(f'Database connection: {result}')
asyncio.run(test())
"
```

---

## 🔄 9. Güncelleme ve Deployment

### Yerel Bilgisayardan Güncelleme:

```bash
# Windows'ta deploy.sh çalıştır
./deploy.sh

# IP adresi ve kullanıcı adını gir
# Script otomatik olarak güncelleyecek
```

### Sunucuda Manuel Güncelleme:

```bash
# Sunucuya bağlan
ssh kirvehub@YOUR_DROPLET_IP

# Botu güncelle
cd /home/kirvehub/telegrambot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart kirvehub-bot

# Durumu kontrol et
sudo systemctl status kirvehub-bot
```

---

## 🔍 10. Sorun Giderme

### Bot Çalışmıyorsa:

```bash
# Logları kontrol et
sudo journalctl -u kirvehub-bot -f

# Manuel test et
cd /home/kirvehub/telegrambot
source venv/bin/activate
python main.py

# Environment dosyasını kontrol et
cat .env
```

### Database Bağlantı Sorunu:

```bash
# PostgreSQL durumunu kontrol et
sudo systemctl status postgresql

# Database bağlantısını test et
psql -h localhost -U kirvehub -d kirvehub_db

# Database kullanıcısını yeniden oluştur
sudo -u postgres psql
DROP USER IF EXISTS kirvehub;
CREATE USER kirvehub WITH PASSWORD 'kirvehub123';
CREATE DATABASE kirvehub_db OWNER kirvehub;
GRANT ALL PRIVILEGES ON DATABASE kirvehub_db TO kirvehub;
\q
```

### Permission Sorunları:

```bash
# Dizin izinlerini düzelt
sudo chown -R kirvehub:kirvehub /home/kirvehub/telegrambot
sudo chmod -R 755 /home/kirvehub/telegrambot

# Log dizini izinlerini düzelt
sudo mkdir -p /home/kirvehub/telegrambot/logs
sudo chown -R kirvehub:kirvehub /home/kirvehub/telegrambot/logs
sudo chmod -R 755 /home/kirvehub/telegrambot/logs
```

---

## 📊 11. Monitoring Komutları

```bash
# Bot durumu
sudo systemctl status kirvehub-bot

# Canlı loglar
sudo journalctl -u kirvehub-bot -f

# Son 100 log
sudo journalctl -u kirvehub-bot -n 100

# Bot yeniden başlat
sudo systemctl restart kirvehub-bot

# Bot durdur
sudo systemctl stop kirvehub-bot

# Bot başlat
sudo systemctl start kirvehub-bot
```

---

## 🎯 Önemli Notlar

### ✅ Yapılması Gerekenler:
- .env dosyasında BOT_TOKEN ve ADMIN_USER_ID'yi doğru ayarla
- Database şifresini güvenli yap
- Firewall ayarlarını kontrol et
- Düzenli backup al

### ❌ Yapılmaması Gerekenler:
- Root kullanıcısıyla bot çalıştırma
- Güvenlik güncellemelerini atlama
- Log dosyalarını sınırsız büyütme
- Database şifresini açık bırakma

---

## 🚀 Başarı!

Bot artık DigitalOcean'da çalışıyor! 

**Test etmek için:**
1. Telegram'da botunuza mesaj gönderin
2. `/start` komutunu kullanın
3. `/menu` ile menüyü açın

**Sorun yaşarsan:**
1. Logları kontrol edin: `sudo journalctl -u kirvehub-bot -f`
2. Bot durumunu kontrol edin: `sudo systemctl status kirvehub-bot`
3. Database bağlantısını test edin: `psql -h localhost -U kirvehub -d kirvehub_db` 