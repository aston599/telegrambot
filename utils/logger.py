"""
🔧 Gelişmiş Log Sistemi - KirveHub Bot
Sadece önemli sistem logları için optimize edilmiş
"""

import logging
import sys
from datetime import datetime
from typing import Optional

# Log seviyeleri
SYSTEM_LOG = 25  # Sistem logları için özel seviye
BOT_LOG = 26     # Bot logları için özel seviye
ERROR_LOG = 27   # Hata logları için özel seviye

# Özel log seviyelerini kaydet
logging.addLevelName(SYSTEM_LOG, "SYSTEM")
logging.addLevelName(BOT_LOG, "BOT")
logging.addLevelName(ERROR_LOG, "ERROR")

class KirveLogger:
    """KirveHub Bot için özel logger"""
    
    def __init__(self, name: str = "kirvebot"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Handler yoksa ekle
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Handler'ları kur"""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler('bot.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def system(self, message: str):
        """Sistem logları - Sadece önemli sistem olayları"""
        self.logger.log(SYSTEM_LOG, f"🔧 {message}")
    
    def bot(self, message: str):
        """Bot logları - Bot durumu ve komutları"""
        self.logger.log(BOT_LOG, f"🤖 {message}")
    
    def error(self, message: str):
        """Hata logları - Kritik hatalar"""
        self.logger.log(ERROR_LOG, f"❌ {message}")
    
    def info(self, message: str):
        """Bilgi logları - Genel bilgiler"""
        self.logger.info(f"ℹ️ {message}")
    
    def warning(self, message: str):
        """Uyarı logları"""
        self.logger.warning(f"⚠️ {message}")
    
    def debug(self, message: str):
        """Debug logları - Sadece geliştirme sırasında"""
        self.logger.debug(f"🔍 {message}")

# Global logger instance
kirve_logger = KirveLogger()

def log_system(message: str):
    """Sistem logu"""
    kirve_logger.system(message)

def log_bot(message: str):
    """Bot logu"""
    kirve_logger.bot(message)

def log_error(message: str):
    """Hata logu"""
    kirve_logger.error(message)

def log_info(message: str):
    """Bilgi logu"""
    kirve_logger.info(message)

def log_warning(message: str):
    """Uyarı logu"""
    kirve_logger.warning(message)

def log_debug(message: str):
    """Debug logu"""
    kirve_logger.debug(message)

def log_market_purchase(order_number: str, user_id: int, product_name: str, amount: float):
    """Market satın alma logu"""
    log_system(f"MARKET SATIS - Order: {order_number}, User: {user_id}, Product: {product_name}, Amount: {amount} KP")

def log_order_approval(order_id: int, order_number: str, user_id: int, username: str, 
                     product_name: str, company_name: str, amount: float, admin_message: str):
    """Sipariş onaylama logu"""
    log_system(f"SIPARIS ONAYLANDI - Order: {order_number}, User: {username}, Product: {product_name}, Amount: {amount} KP")

def log_order_rejection(order_id: int, order_number: str, user_id: int, username: str,
                      product_name: str, company_name: str, amount: float, admin_message: str):
    """Sipariş reddetme logu"""
    log_system(f"SIPARIS REDDEDILDI - Order: {order_number}, User: {username}, Product: {product_name}, Amount: {amount} KP")

def log_point_earned(user_id: int, points: float, total_points: float):
    """Point kazanma logu"""
    if points >= 1.0:  # 1 KP ve üstü için log
        log_system(f"POINT KAZANIMI - User: {user_id}, Earned: {points} KP, Total: {total_points} KP")

def log_admin_action(admin_id: int, action: str, details: str):
    """Admin işlem logu"""
    log_system(f"ADMIN ISLEM - Admin: {admin_id}, Action: {action}, Details: {details}")

def log_performance(operation: str, duration: float):
    """Performans logu"""
    if duration > 1.0:  # 1 saniyeden uzun işlemler
        log_warning(f"PERFORMANS - Operation: {operation}, Duration: {duration:.2f}s")

# Eski logger fonksiyonları (geriye uyumluluk için)
def setup_logger(name="bot", log_level=logging.INFO):
    """Eski logger fonksiyonu - Geriye uyumluluk"""
    return kirve_logger

# Global logger instance'ı döndür
logger = kirve_logger 