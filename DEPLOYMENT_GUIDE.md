# 🚀 KirveHub Bot - DigitalOcean Ubuntu Deployment Guide

## 📋 Ön Gereksinimler

### 1. DigitalOcean Droplet Oluşturma
```bash
# Ubuntu 24.04 LTS seçin
# Minimum: 1GB RAM, 1 vCPU, 25GB SSD
# SSH key ekleyin
```

### 2. Sunucu Hazırlığı

```bash
# Root olarak giriş yapın
ssh root@your-server-ip

# Sistem güncellemeleri
apt update && apt upgrade -y

# Temel paketler
apt install -y curl wget git htop nano

# Firewall ayarları
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 3. Kullanıcı Oluşturma

```bash
# Bot kullanıcısı oluştur
adduser kirvehub
usermod -aG sudo kirvehub

# SSH key kopyala
mkdir -p /home/kirvehub/.ssh
cp ~/.ssh/authorized_keys /home/kirvehub/.ssh/
chown -R kirvehub:kirvehub /home/kirvehub/.ssh
chmod 700 /home/kirvehub/.ssh
chmod 600 /home/kirvehub/.ssh/authorized_keys

# Kullanıcıya geç
su - kirvehub
```

## 🐍 Python Kurulumu

```bash
# Python 3.12 kurulumu
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Virtual environment oluştur
cd ~
python3.12 -m venv venv
source venv/bin/activate
```

## 🗄️ PostgreSQL Kurulumu

```bash
# PostgreSQL kurulumu
sudo apt install -y postgresql postgresql-contrib

# PostgreSQL servisini başlat
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Database kullanıcısı oluştur
sudo -u postgres psql
CREATE DATABASE kirvehub_db;
CREATE USER kirvehub WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE kirvehub_db TO kirvehub;
\q
```

## 🤖 Bot Kurulumu

```bash
# Bot dizini oluştur
mkdir -p ~/telegrambot
cd ~/telegrambot

# Git'ten projeyi çek
git clone https://github.com/your-repo/telegrambot.git .

# Virtual environment aktifleştir
source ~/venv/bin/activate

# Gereksinimleri kur
pip install -r requirements.txt
```

## ⚙️ Konfigürasyon

```bash
# Environment dosyası oluştur
cp env.example .env
nano .env

# Gerekli değerleri doldurun:
# BOT_TOKEN=your_bot_token
# ADMIN_USER_ID=your_admin_id
# DATABASE_URL=postgresql://kirvehub:your_password@localhost:5432/kirvehub_db
# PRODUCTION_MODE=true
```

## 🔧 Systemd Service Kurulumu

```bash
# Service dosyasını kopyala
sudo cp systemd/kirvehub-bot.service /etc/systemd/system/

# Service'i etkinleştir
sudo systemctl daemon-reload
sudo systemctl enable kirvehub-bot
sudo systemctl start kirvehub-bot

# Durumu kontrol et
sudo systemctl status kirvehub-bot
```

## 📊 Monitoring ve Backup

```bash
# Script'leri çalıştırılabilir yap
chmod +x scripts/*.sh

# Cron jobs kur
./scripts/setup_cron.sh

# İlk backup al
./scripts/backup.sh
```

## 🌐 Nginx Kurulumu (Opsiyonel)

```bash
# Nginx kurulumu
sudo apt install -y nginx

# Konfigürasyonu kopyala
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf

# Nginx'i başlat
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 🔒 SSL Sertifikası (Opsiyonel)

```bash
# Certbot kurulumu
sudo apt install -y certbot python3-certbot-nginx

# SSL sertifikası al
sudo certbot --nginx -d yourdomain.com

# Otomatik yenileme
sudo crontab -e
# Şu satırı ekleyin:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🧪 Test Etme

```bash
# Bot durumunu kontrol et
sudo systemctl status kirvehub-bot

# Log'ları kontrol et
tail -f ~/telegrambot/logs/bot.log

# Database bağlantısını test et
psql -h localhost -U kirvehub -d kirvehub_db -c "SELECT 1;"
```

## 🔧 Sorun Giderme

### Bot Başlamıyor
```bash
# Log'ları kontrol et
sudo journalctl -u kirvehub-bot -f

# Manuel test
cd ~/telegrambot
source ~/venv/bin/activate
python main.py
```

### Database Bağlantı Hatası
```bash
# PostgreSQL durumunu kontrol et
sudo systemctl status postgresql

# Bağlantıyı test et
psql -h localhost -U kirvehub -d kirvehub_db
```

### Disk Alanı Sorunu
```bash
# Disk kullanımını kontrol et
df -h

# Log dosyalarını temizle
find ~/telegrambot/logs -name "*.log" -mtime +7 -delete
```

## 📈 Monitoring

```bash
# Sistem durumunu kontrol et
htop

# Bot process'ini kontrol et
ps aux | grep python

# Log boyutlarını kontrol et
du -sh ~/telegrambot/logs/*
```

## 🔄 Güncelleme

```bash
# Bot'u durdur
sudo systemctl stop kirvehub-bot

# Git'ten güncellemeleri çek
cd ~/telegrambot
git pull origin main

# Gereksinimleri güncelle
source ~/venv/bin/activate
pip install -r requirements.txt

# Bot'u yeniden başlat
sudo systemctl start kirvehub-bot
```

## 📞 Destek

Sorun yaşarsanız:
1. Log dosyalarını kontrol edin: `tail -f ~/telegrambot/logs/bot.log`
2. Systemd log'larını kontrol edin: `sudo journalctl -u kirvehub-bot -f`
3. Database bağlantısını test edin
4. Disk alanını kontrol edin

## ✅ Deployment Checklist

- [ ] DigitalOcean droplet oluşturuldu
- [ ] Sistem güncellemeleri yapıldı
- [ ] Firewall ayarlandı
- [ ] Bot kullanıcısı oluşturuldu
- [ ] Python 3.12 kuruldu
- [ ] PostgreSQL kuruldu ve yapılandırıldı
- [ ] Bot kodu indirildi
- [ ] Virtual environment oluşturuldu
- [ ] Gereksinimler kuruldu
- [ ] Environment dosyası yapılandırıldı
- [ ] Systemd service kuruldu
- [ ] Bot başlatıldı ve test edildi
- [ ] Monitoring script'leri kuruldu
- [ ] Cron jobs ayarlandı
- [ ] Backup sistemi test edildi
- [ ] SSL sertifikası alındı (opsiyonel)
- [ ] Nginx kuruldu (opsiyonel)