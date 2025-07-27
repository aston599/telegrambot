#!/bin/bash
# 🚀 Production Bot Başlatma Script'i

echo "🚀 KirveHub Bot Production Modu Başlatılıyor..."

# Environment variables
export PRODUCTION_MODE=true
export PYTHONPATH=.

# Bot'u başlat
python main.py
