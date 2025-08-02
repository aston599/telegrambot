"""
⚙️ Konfigürasyon Yöneticisi - KirveHub Bot
Tüm bot ayarlarını merkezi olarak yönetir
"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class Config:
    """Bot konfigürasyonu"""
    
    # 🤖 Bot Token (@KirveLastBot)
    BOT_TOKEN: str = "7633083532:AAFG8ba4hElj_rXjHOEt7BTeLKuJnW1kvTU"
    
    # 👤 Admin User IDs (Birden fazla admin)
    ADMIN_USER_IDS: list = None  # Birden fazla admin ID'si
    
    # 👤 Ana Admin User ID (Eski uyumluluk için)
    ADMIN_USER_ID: int = 8154732274  # Test kullanıcısı için güncellendi
    
    # 🔐 Bot Owner ID (Gizli komutlar için)
    OWNER_ID: int = 8154732274  # Test kullanıcısı için güncellendi
    
    # 🗄️ Database URL (PostgreSQL - Supabase Connection Pooling)
    DATABASE_URL: str = "postgresql://postgres.yfbyyuejqdwiomycksxg:KirveHub2025!@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
    
    # 🚀 Production Mode (true/false)
    PRODUCTION_MODE: bool = True
    
    # ⚙️ Bot Ayarları
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    
    # 🗄️ Database Pool Ayarları
    DB_MIN_SIZE: int = 2
    DB_MAX_SIZE: int = 10
    DB_COMMAND_TIMEOUT: int = 30
    
    # 📊 Detailed Logging Settings
    DETAILED_LOGGING_ENABLED: bool = True
    LOG_GROUP_ID: int = -1002513057876
    LOG_BATCH_SIZE: int = 10
    LOG_SEND_INTERVAL: int = 30
    
    # 🔗 Supabase Settings
    SUPABASE_URL: str = "https://yfbyyuejqdwiomycksxg.supabase.co"
    SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlmYnl5dWVqcWR3aW9teWNrc3hnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4OTg3NDEsImV4cCI6MjA2OTQ3NDc0MX0.nqTWXX7opBVeurutxyjwhytKdWrFF7tYY9_anqk32TQ"
    
    def __post_init__(self):
        """Admin ID'lerini ayarla"""
        if self.ADMIN_USER_IDS is None:
            # Ana admin + mikedahjenko hesabı
            self.ADMIN_USER_IDS = [
                8154732274,  # Ana admin
                69398854,    # mikedahjenko hesabı
            ]

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Konfigürasyon instance'ını döndür"""
    global _config
    
    if _config is None:
        _config = Config()
        
        # Environment variables'dan override et
        if os.getenv("BOT_TOKEN"):
            _config.BOT_TOKEN = os.getenv("BOT_TOKEN")
        
        if os.getenv("ADMIN_USER_ID"):
            _config.ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
        
        if os.getenv("OWNER_ID"):
            _config.OWNER_ID = int(os.getenv("OWNER_ID"))
        
        if os.getenv("DATABASE_URL"):
            _config.DATABASE_URL = os.getenv("DATABASE_URL")
        
        if os.getenv("PRODUCTION_MODE"):
            _config.PRODUCTION_MODE = os.getenv("PRODUCTION_MODE").lower() == "true"
        
        if os.getenv("DEBUG"):
            _config.DEBUG = os.getenv("DEBUG").lower() == "true"
        
        if os.getenv("LOG_LEVEL"):
            _config.LOG_LEVEL = os.getenv("LOG_LEVEL")
        
        if os.getenv("DB_MIN_SIZE"):
            _config.DB_MIN_SIZE = int(os.getenv("DB_MIN_SIZE"))
        
        if os.getenv("DB_MAX_SIZE"):
            _config.DB_MAX_SIZE = int(os.getenv("DB_MAX_SIZE"))
        
        if os.getenv("DB_COMMAND_TIMEOUT"):
            _config.DB_COMMAND_TIMEOUT = int(os.getenv("DB_COMMAND_TIMEOUT"))
        
        if os.getenv("DETAILED_LOGGING_ENABLED"):
            _config.DETAILED_LOGGING_ENABLED = os.getenv("DETAILED_LOGGING_ENABLED").lower() == "true"
        
        if os.getenv("LOG_GROUP_ID"):
            _config.LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID"))
        
        if os.getenv("LOG_BATCH_SIZE"):
            _config.LOG_BATCH_SIZE = int(os.getenv("LOG_BATCH_SIZE"))
        
        if os.getenv("LOG_SEND_INTERVAL"):
            _config.LOG_SEND_INTERVAL = int(os.getenv("LOG_SEND_INTERVAL"))
        
        if os.getenv("SUPABASE_URL"):
            _config.SUPABASE_URL = os.getenv("SUPABASE_URL")
        
        if os.getenv("SUPABASE_ANON_KEY"):
            _config.SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    return _config

def is_admin(user_id: int) -> bool:
    """Kullanıcının admin olup olmadığını kontrol et"""
    config = get_config()
    return user_id in config.ADMIN_USER_IDS

def is_owner(user_id: int) -> bool:
    """Kullanıcının owner olup olmadığını kontrol et"""
    config = get_config()
    return user_id == config.OWNER_ID

def reload_config() -> Config:
    """Konfigürasyonu yeniden yükle"""
    global _config
    _config = None
    return get_config()

def validate_config() -> bool:
    """Konfigürasyon değerlerini doğrula"""
    config = get_config()
    
    # Gerekli alanları kontrol et
    if not config.BOT_TOKEN or config.BOT_TOKEN == "":
        print("❌ BOT_TOKEN eksik!")
        return False
    
    if not config.DATABASE_URL or config.DATABASE_URL == "":
        print("❌ DATABASE_URL eksik!")
        return False
    
    if config.ADMIN_USER_ID <= 0:
        print("❌ ADMIN_USER_ID geçersiz!")
        return False
    
    # Database URL formatını kontrol et
    if not config.DATABASE_URL.startswith(("postgresql://", "postgres://")):
        print("❌ DATABASE_URL PostgreSQL formatında değil!")
        return False
    
    # Supabase ayarlarını kontrol et
    if not config.SUPABASE_URL or config.SUPABASE_URL == "":
        print("❌ SUPABASE_URL eksik!")
        return False
    
    if not config.SUPABASE_ANON_KEY or config.SUPABASE_ANON_KEY == "":
        print("❌ SUPABASE_ANON_KEY eksik!")
        return False
    
    print("✅ Konfigürasyon doğrulaması başarılı!")
    return True

 