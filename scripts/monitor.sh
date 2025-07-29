#!/bin/bash

# 📊 KirveHub Bot - Monitoring Script
# DigitalOcean Ubuntu için optimize edilmiş

BOT_DIR="/home/kirvehub/telegrambot"
LOG_FILE="$BOT_DIR/logs/monitor.log"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if bot is running
check_bot_status() {
    if pgrep -f "python.*main.py" > /dev/null; then
        log "✅ Bot çalışıyor"
        return 0
    else
        log "❌ Bot çalışmıyor!"
        return 1
    fi
}

# Check database connection
check_database() {
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        log "✅ Database bağlantısı aktif"
        return 0
    else
        log "❌ Database bağlantısı yok!"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local usage=$(df /home | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $usage -gt 90 ]; then
        log "⚠️ Disk alanı kritik: ${usage}%"
        return 1
    elif [ $usage -gt 80 ]; then
        log "⚠️ Disk alanı uyarı: ${usage}%"
        return 0
    else
        log "✅ Disk alanı normal: ${usage}%"
        return 0
    fi
}

# Check memory usage
check_memory() {
    local usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ $usage -gt 90 ]; then
        log "⚠️ Bellek kullanımı kritik: ${usage}%"
        return 1
    elif [ $usage -gt 80 ]; then
        log "⚠️ Bellek kullanımı uyarı: ${usage}%"
        return 0
    else
        log "✅ Bellek kullanımı normal: ${usage}%"
        return 0
    fi
}

# Check log file size
check_log_size() {
    local log_size=$(du -m "$LOG_FILE" 2>/dev/null | cut -f1 || echo "0")
    if [ $log_size -gt 100 ]; then
        log "⚠️ Log dosyası büyük: ${log_size}MB"
        # Rotate log
        mv "$LOG_FILE" "${LOG_FILE}.old"
        touch "$LOG_FILE"
        log "📝 Log dosyası rotate edildi"
    fi
}

# Restart bot if needed
restart_bot_if_needed() {
    if ! check_bot_status; then
        log "🔄 Bot yeniden başlatılıyor..."
        systemctl restart kirvehub-bot
        sleep 5
        
        if check_bot_status; then
            log "✅ Bot başarıyla yeniden başlatıldı"
        else
            log "❌ Bot başlatılamadı!"
        fi
    fi
}

# Send alert to admin
send_alert() {
    local message="$1"
    # Burada Telegram API ile admin'e mesaj gönderebilirsiniz
    log "🚨 ALERT: $message"
}

# Main monitoring function
main() {
    log "📊 Monitoring başlatıldı"
    
    local issues=0
    
    # Check bot status
    if ! check_bot_status; then
        issues=$((issues + 1))
        restart_bot_if_needed
    fi
    
    # Check database
    if ! check_database; then
        issues=$((issues + 1))
        send_alert "Database bağlantısı yok!"
    fi
    
    # Check disk space
    if ! check_disk_space; then
        issues=$((issues + 1))
        send_alert "Disk alanı kritik!"
    fi
    
    # Check memory
    if ! check_memory; then
        issues=$((issues + 1))
        send_alert "Bellek kullanımı kritik!"
    fi
    
    # Check log size
    check_log_size
    
    if [ $issues -eq 0 ]; then
        log "✅ Tüm sistemler normal"
    else
        log "⚠️ $issues sorun tespit edildi"
    fi
    
    log "📊 Monitoring tamamlandı"
}

# Run main function
main "$@" 