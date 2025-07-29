#!/bin/bash

# 🚀 KirveHub Bot - Otomatik Deploy Script
# DigitalOcean'da çalıştırılacak

echo "🔧 KirveHub Bot Deploy Başlatılıyor..."

# 1. Mevcut botu durdur
echo "⏹️ Mevcut bot durduruluyor..."
pkill -f "python3 main.py" || true
sleep 2

# 2. Git'ten güncellemeleri çek
echo "📥 Git güncellemeleri çekiliyor..."
cd ~/telegrambot
git fetch origin
git reset --hard origin/main

# 3. Virtual environment'ı aktifleştir
echo "🐍 Virtual environment aktifleştiriliyor..."
source venv/bin/activate

# 4. Gereksinimleri güncelle
echo "📦 Gereksinimler güncelleniyor..."
pip install -r requirements.txt

# 5. Database migration'ları çalıştır
echo "🗄️ Database kontrol ediliyor..."
python3 -c "import asyncio; from database import init_database; asyncio.run(init_database())"

# 6. Botu başlat
echo "🤖 Bot başlatılıyor..."
nohup python3 main.py > bot.log 2>&1 &

# 7. Durumu kontrol et
sleep 5
if pgrep -f "python3 main.py" > /dev/null; then
    echo "✅ Bot başarıyla başlatıldı!"
    echo "📊 Log dosyası: ~/telegrambot/bot.log"
else
    echo "❌ Bot başlatılamadı!"
    echo "🔍 Log kontrolü: tail -f ~/telegrambot/bot.log"
fi

echo "🚀 Deploy tamamlandı!" 