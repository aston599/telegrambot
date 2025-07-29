#!/bin/bash

# 🚀 Hızlı Bot Güncelleme Script'i
# PuTTY'de çalıştırılacak

echo "🔄 Bot güncelleniyor..."

# 1. Mevcut botu durdur
echo "⏹️ Bot durduruluyor..."
pkill -f "python3 main.py" || true
sleep 2

# 2. Virtual environment'ı aktifleştir
echo "🐍 Virtual environment aktifleştiriliyor..."
cd ~/telegrambot
source venv/bin/activate

# 3. Gereksinimleri kontrol et (eğer requirements.txt değiştiyse)
if [ -f "requirements.txt" ]; then
    echo "📦 Gereksinimler kontrol ediliyor..."
    pip install -r requirements.txt
fi

# 4. Botu başlat
echo "🤖 Bot başlatılıyor..."
nohup python3 main.py > bot.log 2>&1 &

# 5. Durumu kontrol et
sleep 3
if pgrep -f "python3 main.py" > /dev/null; then
    echo "✅ Bot başarıyla başlatıldı!"
    echo "📊 Log: tail -f ~/telegrambot/bot.log"
else
    echo "❌ Bot başlatılamadı!"
    echo "🔍 Hata logu: tail -f ~/telegrambot/bot.log"
fi

echo "🎉 Güncelleme tamamlandı!"