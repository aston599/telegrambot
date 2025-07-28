"""
🤖 Telegram Bot Konfigürasyon Dosyası - aiogram
DigitalOcean Ubuntu Production Environment için optimize edilmiş
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Global config instance
_config = None

class Config:
    def __init__(self):
        # Core Bot Settings
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        self.ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        
        # Environment Settings
        self.MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
        self.PRODUCTION_MODE = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        # Server Settings
        self.SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
        self.SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))
        self.WORKER_PROCESSES = int(os.getenv('WORKER_PROCESSES', 1))
        
        # Database Settings
        self.DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 10))
        self.DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', 20))
        self.DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', 30))
        
        # Logging Settings
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
        self.LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
        
        # Performance Settings
        self.MAX_CONCURRENT_UPDATES = int(os.getenv('MAX_CONCURRENT_UPDATES', 100))
        self.UPDATE_TIMEOUT = int(os.getenv('UPDATE_TIMEOUT', 30))
        self.RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', 0.1))
        
        # Security Settings
        self.ENABLE_RATE_LIMITING = os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
        self.MAX_MESSAGES_PER_MINUTE = int(os.getenv('MAX_MESSAGES_PER_MINUTE', 60))
        self.ENABLE_IP_WHITELIST = os.getenv('ENABLE_IP_WHITELIST', 'false').lower() == 'true'
        
        # File Paths
        self.BASE_DIR = Path(__file__).parent
        self.LOGS_DIR = self.BASE_DIR / 'logs'
        self.DATA_DIR = self.BASE_DIR / 'data'
        
        # Create directories if they don't exist
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.DATA_DIR.mkdir(exist_ok=True)

def get_config():
    """Bot konfigürasyonunu döndür"""
    global _config
    if _config is None:
        _config = Config()
    return _config

def validate_config() -> bool:
    """Konfigürasyonu doğrula"""
    config = get_config()
    
    # Required fields
    required_fields = {
        'BOT_TOKEN': config.BOT_TOKEN,
        'DATABASE_URL': config.DATABASE_URL,
        'ADMIN_USER_ID': config.ADMIN_USER_ID
    }
    
    missing_fields = []
    for field_name, field_value in required_fields.items():
        if not field_value:
            missing_fields.append(field_name)
    
    if missing_fields:
        raise ValueError(f"Eksik konfigürasyon alanları: {', '.join(missing_fields)}")
    
    # Validate numeric fields
    if config.ADMIN_USER_ID <= 0:
        raise ValueError("ADMIN_USER_ID geçerli bir değer olmalı")
    
    if config.SERVER_PORT < 1 or config.SERVER_PORT > 65535:
        raise ValueError("SERVER_PORT 1-65535 arasında olmalı")
    
    return True

def get_production_config():
    """Production ortamı için özel konfigürasyon"""
    config = get_config()
    
    # Production optimizations
    if config.PRODUCTION_MODE:
        config.LOG_LEVEL = 'WARNING'
        config.ENABLE_RATE_LIMITING = True
        config.MAX_CONCURRENT_UPDATES = 50  # Lower for production
    
    return config

 