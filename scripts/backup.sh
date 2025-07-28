#!/bin/bash

# 🤖 KirveHub Bot - Backup Script
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
BACKUP_DIR="/home/$BOT_USER/backups"
DATABASE_NAME="kirvehub_db"
DATABASE_USER="kirvehub"
RETENTION_DAYS=7
LOG_FILE="$BOT_DIR/logs/backup.log"

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if backup is needed
check_backup_needed() {
    local last_backup_file="$BACKUP_DIR/last_backup.txt"
    
    if [ -f "$last_backup_file" ]; then
        local last_backup=$(cat "$last_backup_file")
        local current_time=$(date +%s)
        local time_diff=$((current_time - last_backup))
        local hours_diff=$((time_diff / 3600))
        
        if [ $hours_diff -lt 24 ]; then
            log "Backup gerekli değil. Son backup: $hours_diff saat önce"
            return 1
        fi
    fi
    
    return 0
}

# Database backup
backup_database() {
    log "Database backup başlatılıyor..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/database_backup_$timestamp.sql"
    
    if pg_dump -h localhost -U $DATABASE_USER -d $DATABASE_NAME > "$backup_file" 2>/dev/null; then
        log "Database backup başarılı: $backup_file"
        
        # Compress backup
        gzip "$backup_file"
        log "Database backup sıkıştırıldı: ${backup_file}.gz"
        
        echo "$(date +%s)" > "$BACKUP_DIR/last_backup.txt"
        return 0
    else
        log "Database backup hatası!"
        return 1
    fi
}

# Files backup
backup_files() {
    log "Dosya backup başlatılıyor..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/files_backup_$timestamp.tar.gz"
    
    # Files to backup
    local files_to_backup=(
        "$BOT_DIR/.env"
        "$BOT_DIR/config.py"
        "$BOT_DIR/requirements.txt"
        "$BOT_DIR/logs"
        "$BOT_DIR/data"
    )
    
    # Create backup
    if tar -czf "$backup_file" -C "$BOT_DIR" "${files_to_backup[@]}" 2>/dev/null; then
        log "Dosya backup başarılı: $backup_file"
        return 0
    else
        log "Dosya backup hatası!"
        return 1
    fi
}

# Full backup
backup_full() {
    log "Tam backup başlatılıyor..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/full_backup_$timestamp.tar.gz"
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    
    # Database backup
    local db_backup="$temp_dir/database_backup.sql"
    if pg_dump -h localhost -U $DATABASE_USER -d $DATABASE_NAME > "$db_backup" 2>/dev/null; then
        log "Database backup oluşturuldu"
    else
        log "Database backup hatası!"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Copy important files
    cp -r "$BOT_DIR" "$temp_dir/bot_files" 2>/dev/null || log "Dosya kopyalama hatası"
    
    # Create full backup
    if tar -czf "$backup_file" -C "$temp_dir" . 2>/dev/null; then
        log "Tam backup başarılı: $backup_file"
        
        # Cleanup
        rm -rf "$temp_dir"
        return 0
    else
        log "Tam backup hatası!"
        rm -rf "$temp_dir"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Eski backup'lar temizleniyor..."
    
    local deleted_count=0
    
    # Find and delete old backups
    while IFS= read -r -d '' file; do
        local file_age=$(( ($(date +%s) - $(stat -c %Y "$file")) / 86400 ))
        
        if [ $file_age -gt $RETENTION_DAYS ]; then
            rm "$file"
            deleted_count=$((deleted_count + 1))
            log "Eski backup silindi: $file"
        fi
    done < <(find "$BACKUP_DIR" -name "*.sql.gz" -o -name "*.tar.gz" -print0)
    
    log "$deleted_count eski backup silindi"
}

# Verify backup
verify_backup() {
    local backup_file="$1"
    
    if [[ "$backup_file" == *.gz ]]; then
        if gzip -t "$backup_file" 2>/dev/null; then
            log "Backup doğrulandı: $backup_file"
            return 0
        else
            log "Backup bozuk: $backup_file"
            return 1
        fi
    else
        log "Backup dosya formatı tanınmıyor: $backup_file"
        return 1
    fi
}

# List backups
list_backups() {
    echo -e "${BLUE}📋 Mevcut Backup'lar:${NC}"
    
    if [ -d "$BACKUP_DIR" ]; then
        local backup_count=0
        
        while IFS= read -r -d '' file; do
            local file_size=$(du -h "$file" | cut -f1)
            local file_date=$(stat -c %y "$file" | cut -d' ' -f1)
            local file_time=$(stat -c %y "$file" | cut -d' ' -f2 | cut -d'.' -f1)
            
            echo -e "${YELLOW}$file${NC}"
            echo -e "  Boyut: $file_size, Tarih: $file_date $file_time"
            echo ""
            
            backup_count=$((backup_count + 1))
        done < <(find "$BACKUP_DIR" -name "*.sql.gz" -o -name "*.tar.gz" -print0 | sort -z)
        
        if [ $backup_count -eq 0 ]; then
            echo -e "${YELLOW}Backup bulunamadı${NC}"
        else
            echo -e "${GREEN}Toplam $backup_count backup${NC}"
        fi
    else
        echo -e "${RED}Backup dizini bulunamadı${NC}"
    fi
}

# Restore backup
restore_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log "Backup dosyası bulunamadı: $backup_file"
        return 1
    fi
    
    log "Backup geri yükleniyor: $backup_file"
    
    # Stop bot
    systemctl stop kirvehub-bot
    
    # Restore based on file type
    if [[ "$backup_file" == *database_backup* ]]; then
        # Database restore
        gunzip -c "$backup_file" | psql -h localhost -U $DATABASE_USER -d $DATABASE_NAME
        log "Database geri yüklendi"
    elif [[ "$backup_file" == *full_backup* ]]; then
        # Full restore
        local temp_dir=$(mktemp -d)
        tar -xzf "$backup_file" -C "$temp_dir"
        
        # Restore database
        if [ -f "$temp_dir/database_backup.sql" ]; then
            psql -h localhost -U $DATABASE_USER -d $DATABASE_NAME < "$temp_dir/database_backup.sql"
            log "Database geri yüklendi"
        fi
        
        # Restore files
        if [ -d "$temp_dir/bot_files" ]; then
            cp -r "$temp_dir/bot_files"/* "$BOT_DIR/"
            log "Dosyalar geri yüklendi"
        fi
        
        rm -rf "$temp_dir"
    else
        log "Backup dosya formatı tanınmıyor"
        return 1
    fi
    
    # Start bot
    systemctl start kirvehub-bot
    log "Bot yeniden başlatıldı"
}

# Main function
main() {
    log "Backup script başlatıldı"
    
    case "$1" in
        "database")
            backup_database
            ;;
        "files")
            backup_files
            ;;
        "full")
            backup_full
            ;;
        "list")
            list_backups
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "restore")
            if [ -z "$2" ]; then
                echo "Kullanım: $0 restore <backup_file>"
                exit 1
            fi
            restore_backup "$2"
            ;;
        "verify")
            if [ -z "$2" ]; then
                echo "Kullanım: $0 verify <backup_file>"
                exit 1
            fi
            verify_backup "$2"
            ;;
        "auto")
            if check_backup_needed; then
                backup_database
                backup_files
                cleanup_old_backups
            fi
            ;;
        *)
            echo "Kullanım: $0 {database|files|full|list|cleanup|restore|verify|auto}"
            echo ""
            echo "Komutlar:"
            echo "  database  - Sadece database backup"
            echo "  files     - Sadece dosya backup"
            echo "  full      - Tam backup (database + files)"
            echo "  list      - Backup listesi"
            echo "  cleanup   - Eski backup'ları temizle"
            echo "  restore   - Backup geri yükle"
            echo "  verify    - Backup doğrula"
            echo "  auto      - Otomatik backup (cron için)"
            exit 1
            ;;
    esac
    
    log "Backup script tamamlandı"
}

# Run main function
main "$@" 