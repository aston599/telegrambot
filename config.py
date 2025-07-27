"""
🤖 Telegram Bot Konfigürasyon Dosyası - aiogram
"""

import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Global config instance
_config = None

class Config:
    def __init__(self):
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        self.ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        self.MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
        self.PRODUCTION_MODE = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'

def get_config():
    """Bot konfigürasyonunu döndür"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def validate_config() -> bool:
    """Konfigürasyonu doğrula"""
    config = get_config()
    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN eksik!")
    
    if not config.DATABASE_URL:
        raise ValueError("DATABASE_URL eksik!")
    
    if not config.ADMIN_USER_ID:
        raise ValueError("ADMIN_USER_ID eksik!")
    
    return True 

 