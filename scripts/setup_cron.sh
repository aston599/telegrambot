#!/bin/bash

# ⏰ KirveHub Bot - Cron Jobs Setup
# DigitalOcean Ubuntu için optimize edilmiş

echo "⏰ Cron jobs kuruluyor..."

# Backup cron job (günlük saat 02:00)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/kirvehub/telegrambot/scripts/backup.sh") | crontab -

# Monitoring cron job (her 5 dakikada)
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/kirvehub/telegrambot/scripts/monitor.sh") | crontab -

# Log cleanup cron job (haftalık Pazar 03:00)
(crontab -l 2>/dev/null; echo "0 3 * * 0 find /home/kirvehub/telegrambot/logs -name '*.log.old' -mtime +7 -delete") | crontab -

# System update cron job (haftalık Pazartesi 04:00)
(crontab -l 2>/dev/null; echo "0 4 * * 1 apt update && apt upgrade -y") | crontab -

echo "✅ Cron jobs kuruldu!"
echo "📋 Aktif cron jobs:"
crontab -l