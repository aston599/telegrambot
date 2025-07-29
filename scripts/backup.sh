#!/bin/bash

# 🔄 KirveHub Bot - Backup Script
# DigitalOcean Ubuntu için optimize edilmiş

BACKUP_DIR="/home/kirvehub/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="kirvehub_backup_$DATE"

echo "🔄 Backup başlatılıyor: $BACKUP_NAME"

# Backup dizini oluştur
mkdir -p $BACKUP_DIR

# Database backup
echo "🗄️ Database backup alınıyor..."
pg_dump kirvehub_db > $BACKUP_DIR/${BACKUP_NAME}_db.sql

# Bot dosyaları backup
echo "🤖 Bot dosyaları backup alınıyor..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}_files.tar.gz \
    --exclude='venv' \
    --exclude='logs/*' \
    --exclude='data/*' \
    --exclude='.git' \
    /home/kirvehub/telegrambot

# Log dosyaları backup (son 7 gün)
echo "📝 Log dosyaları backup alınıyor..."
find /home/kirvehub/telegrambot/logs -name "*.log" -mtime -7 -exec tar -czf $BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz {} \;

# Eski backup'ları temizle (30 günden eski)
echo "🧹 Eski backup'lar temizleniyor..."
find $BACKUP_DIR -name "kirvehub_backup_*" -mtime +30 -delete

echo "✅ Backup tamamlandı: $BACKUP_DIR"
echo "📊 Backup boyutu:"
du -h $BACKUP_DIR/${BACKUP_NAME}_* 