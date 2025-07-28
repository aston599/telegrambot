#!/bin/bash

# 🤖 KirveHub Bot - Monitoring Script
# DigitalOcean Ubuntu Production Environment için optimize edilmiş

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BOT_USER="kirvehub"
BOT_DIR="/home/$BOT_USER/telegrambot"
SERVICE_NAME="kirvehub-bot"
LOG_FILE="$BOT_DIR/logs/monitor.log"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if bot is running
check_bot_status() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✅ Bot çalışıyor${NC}"
        return 0
    else
        echo -e "${RED}❌ Bot çalışmıyor${NC}"
        return 1
    fi
}

# Check system resources
check_system_resources() {
    echo -e "${BLUE}📊 Sistem Kaynakları:${NC}"
    
    # CPU Usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "CPU Kullanımı: ${YELLOW}${CPU_USAGE}%${NC}"
    
    # Memory Usage
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo -e "RAM Kullanımı: ${YELLOW}${MEMORY_USAGE}%${NC}"
    
    # Disk Usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    echo -e "Disk Kullanımı: ${YELLOW}${DISK_USAGE}%${NC}"
    
    # Check thresholds
    if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
        echo -e "${RED}⚠️  CPU kullanımı yüksek!${NC}"
    fi
    
    if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
        echo -e "${RED}⚠️  RAM kullanımı yüksek!${NC}"
    fi
    
    if [ "$DISK_USAGE" -gt 80 ]; then
        echo -e "${RED}⚠️  Disk kullanımı yüksek!${NC}"
    fi
}

# Check database connection
check_database() {
    echo -e "${BLUE}🗄️  Database Durumu:${NC}"
    
    if command -v psql &> /dev/null; then
        if psql -h localhost -U kirvehub -d kirvehub_db -c "SELECT 1;" &> /dev/null; then
            echo -e "${GREEN}✅ Database bağlantısı OK${NC}"
        else
            echo -e "${RED}❌ Database bağlantı hatası${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  PostgreSQL client kurulu değil${NC}"
    fi
}

# Check log files
check_logs() {
    echo -e "${BLUE}📋 Log Dosyaları:${NC}"
    
    # Bot log
    if [ -f "$BOT_DIR/logs/bot.log" ]; then
        LOG_SIZE=$(du -h "$BOT_DIR/logs/bot.log" | cut -f1)
        echo -e "Bot Log: ${YELLOW}${LOG_SIZE}${NC}"
        
        # Check for errors in last 100 lines
        ERROR_COUNT=$(tail -100 "$BOT_DIR/logs/bot.log" | grep -i "error\|exception" | wc -l)
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo -e "${RED}⚠️  Son 100 satırda $ERROR_COUNT hata bulundu${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Bot log dosyası bulunamadı${NC}"
    fi
    
    # Systemd log
    SYSTEMD_ERRORS=$(journalctl -u $SERVICE_NAME --since "1 hour ago" | grep -i "error\|failed" | wc -l)
    if [ "$SYSTEMD_ERRORS" -gt 0 ]; then
        echo -e "${RED}⚠️  Son 1 saatte $SYSTEMD_ERRORS systemd hatası${NC}"
    fi
}

# Check network connectivity
check_network() {
    echo -e "${BLUE}🌐 Ağ Bağlantısı:${NC}"
    
    # Check internet
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo -e "${GREEN}✅ İnternet bağlantısı OK${NC}"
    else
        echo -e "${RED}❌ İnternet bağlantısı yok${NC}"
    fi
    
    # Check Telegram API
    if curl -s https://api.telegram.org &> /dev/null; then
        echo -e "${GREEN}✅ Telegram API erişimi OK${NC}"
    else
        echo -e "${RED}❌ Telegram API erişimi yok${NC}"
    fi
}

# Check ports
check_ports() {
    echo -e "${BLUE}🔌 Port Durumu:${NC}"
    
    # Check if port 8000 is listening
    if netstat -tuln | grep ":8000 " &> /dev/null; then
        echo -e "${GREEN}✅ Port 8000 dinleniyor${NC}"
    else
        echo -e "${RED}❌ Port 8000 dinlenmiyor${NC}"
    fi
    
    # Check if port 80 is listening (nginx)
    if netstat -tuln | grep ":80 " &> /dev/null; then
        echo -e "${GREEN}✅ Port 80 dinleniyor (Nginx)${NC}"
    else
        echo -e "${YELLOW}⚠️  Port 80 dinlenmiyor${NC}"
    fi
}

# Check process details
check_process() {
    echo -e "${BLUE}🔍 Process Detayları:${NC}"
    
    BOT_PID=$(systemctl show -p MainPID $SERVICE_NAME | cut -d= -f2)
    if [ "$BOT_PID" != "0" ]; then
        echo -e "Bot PID: ${YELLOW}$BOT_PID${NC}"
        
        # Memory usage
        if [ -f "/proc/$BOT_PID/status" ]; then
            MEMORY_KB=$(grep VmRSS "/proc/$BOT_PID/status" | awk '{print $2}')
            MEMORY_MB=$((MEMORY_KB / 1024))
            echo -e "Bot Memory: ${YELLOW}${MEMORY_MB}MB${NC}"
        fi
        
        # CPU usage
        CPU_PERCENT=$(ps -p $BOT_PID -o %cpu --no-headers)
        echo -e "Bot CPU: ${YELLOW}${CPU_PERCENT}%${NC}"
    else
        echo -e "${RED}❌ Bot process bulunamadı${NC}"
    fi
}

# Generate report
generate_report() {
    echo -e "${BLUE}📊 Monitoring Raporu - $(date)${NC}"
    echo "=================================="
    
    check_bot_status
    echo ""
    
    check_system_resources
    echo ""
    
    check_database
    echo ""
    
    check_logs
    echo ""
    
    check_network
    echo ""
    
    check_ports
    echo ""
    
    check_process
    echo ""
    
    echo "=================================="
}

# Main function
main() {
    log "Monitoring script başlatıldı"
    
    if [ "$1" = "--report" ]; then
        generate_report
    elif [ "$1" = "--status" ]; then
        check_bot_status
    elif [ "$1" = "--resources" ]; then
        check_system_resources
    elif [ "$1" = "--logs" ]; then
        check_logs
    else
        generate_report
    fi
    
    log "Monitoring script tamamlandı"
}

# Run main function
main "$@" 