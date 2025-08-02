# 🚀 KirveHub Bot - Otomatik Deployment Kurulumu

## 📋 Kurulum Adımları

### 1. GitHub Actions Kurulumu

#### A. GitHub Repository Secrets Ekle:
1. GitHub'da repository'ne git
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** ekle:

```
DROPLET_IP: [DigitalOcean IP adresi]
SSH_USERNAME: kirvehub
SSH_PRIVATE_KEY: [SSH private key]
```

#### B. SSH Key Oluşturma:
```bash
# Yerel bilgisayarında
ssh-keygen -t rsa -b 4096 -C "kirvehub@digitalocean"
# Public key'i DigitalOcean'a ekle
cat ~/.ssh/id_rsa.pub
# Private key'i GitHub secrets'a ekle
cat ~/.ssh/id_rsa
```

### 2. Hızlı Deployment Script

#### A. Script'i Çalıştırılabilir Yap:
```bash
chmod +x deploy.sh
```

#### B. IP Adresini Güncelle:
`deploy.sh` dosyasında `YOUR_DROPLET_IP` yerine gerçek IP'yi yaz.

#### C. Kullanım:
```bash
./deploy.sh
```

### 3. Manuel Deployment

#### A. Git Push:
```bash
git add .
git commit -m "Update: [açıklama]"
git push origin main
```

#### B. Sunucuda Güncelleme:
```bash
ssh kirvehub@[IP_ADRESI]
cd /home/kirvehub/telegrambot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart kirvehub-bot
```

## 🔄 Deployment Yöntemleri

### 1. GitHub Actions (Otomatik)
- ✅ Her push'ta otomatik deploy
- ✅ GitHub'da log görüntüleme
- ✅ Hata durumunda bildirim

### 2. Script (Yarı Otomatik)
- ✅ Hızlı deployment
- ✅ Manuel kontrol
- ✅ Renkli çıktı

### 3. Manuel (Tam Kontrol)
- ✅ Tam kontrol
- ✅ Debug imkanı
- ✅ Adım adım izleme

## 🎯 Kullanım

### GitHub Actions:
```bash
# Sadece push yap
git push origin main
# GitHub Actions otomatik deploy eder
```

### Script:
```bash
# Script'i çalıştır
./deploy.sh
# Otomatik commit, push ve deploy
```

### Manuel:
```bash
# Git push
git push origin main

# SSH ile sunucuya bağlan
ssh kirvehub@[IP]

# Manuel güncelle
cd /home/kirvehub/telegrambot
git pull origin main
sudo systemctl restart kirvehub-bot
```

## 🔍 Kontrol Komutları

### Bot Durumu:
```bash
sudo systemctl status kirvehub-bot
```

### Logları Gör:
```bash
sudo journalctl -u kirvehub-bot -f
```

### Son Loglar:
```bash
sudo journalctl -u kirvehub-bot -n 50
```

## ⚠️ Önemli Notlar

1. **SSH Key**: Private key'i GitHub secrets'a ekle
2. **IP Adresi**: Doğru IP'yi kullan
3. **Permissions**: Script'i çalıştırılabilir yap
4. **Backup**: Önemli değişikliklerden önce backup al

## 🚀 Hızlı Başlangıç

1. GitHub secrets'ları ekle
2. `deploy.sh` dosyasındaki IP'yi güncelle
3. `chmod +x deploy.sh` çalıştır
4. `./deploy.sh` ile test et

Artık her değişiklik otomatik olarak DigitalOcean'a deploy edilecek! 🎉 