#!/bin/bash
# 🚀 TEK KOMUT DEPLOY - DigitalOcean'da çalıştır

echo "🚀 Tek komutla deploy başlıyor..."

cd ~/telegrambot
git pull origin main
pkill -f "python3 main.py" 2>/dev/null
sleep 2
source venv/bin/activate
pip install -r requirements.txt >/dev/null 2>&1
nohup python3 main.py > bot.log 2>&1 &

echo "✅ Bot güncellendi ve başlatıldı!"
echo "📊 Log: tail -f ~/telegrambot/bot.log"