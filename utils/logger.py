"""
📝 Logging Sistemi - Optimized for Production
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Global logger instance
logger = logging.getLogger(__name__)

def setup_logger():
    """Logger'ı kur"""
    # Production için log seviyesini ayarla - Daha az log
    log_level = logging.INFO  # WARNING yerine INFO - Bot çalıştığını görmek için
    
    # Logger'ı yapılandır
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    return logging.getLogger(__name__)

# Production'da sadece önemli loglar - Emoji'siz versiyon
def log_important(message: str, level: str = "INFO"):
    """Sadece önemli logları console'a yazdır - Emoji'siz"""
    logger = logging.getLogger(__name__)
    
    # Emoji'leri kaldır (Windows uyumluluğu için)
    clean_message = message
    emoji_chars = ['🤖', '✅', '❌', '⚠️', '🎯', '🧹', '👤', '🎉', '⏹️', '📢', '🔔', '📬', '🛍️', '💎', '🛡️', '🚨', '⏱️', '🗄️', '🔍']
    for emoji in emoji_chars:
        clean_message = clean_message.replace(emoji, '')
    
    # Başındaki boşlukları temizle
    clean_message = clean_message.strip()
    
    try:
        if level == "ERROR":
            logger.error(clean_message)
        elif level == "WARNING":
            logger.warning(clean_message)
        else:
            logger.info(clean_message)
    except Exception as e:
        # Console buffer sorunu varsa sadece file'a yaz
        print(f"LOGGING ERROR: {e} - Message: {clean_message}")

def log_order_approval(order_id: int, order_number: str, user_id: int, username: str, 
                      product_name: str, company_name: str, amount: float, admin_message: str):
    """Sipariş onaylama logu - Önemli işlem"""
    log_important(f"SIPARIS ONAYLANDI - Order: {order_number}, User: {username}, Product: {product_name}, Amount: {amount} KP")

def log_order_rejection(order_id: int, order_number: str, user_id: int, username: str,
                       product_name: str, company_name: str, amount: float, admin_message: str):
    """Sipariş reddetme logu - Önemli işlem"""
    log_important(f"SIPARIS REDDEDILDI - Order: {order_number}, User: {username}, Product: {product_name}, Amount: {amount} KP")

def log_market_purchase(order_number: str, user_id: int, product_name: str, amount: float):
    """Market satın alma logu - Önemli işlem"""
    log_important(f"MARKET SATIS - Order: {order_number}, User: {user_id}, Product: {product_name}, Amount: {amount} KP")

def log_point_earned(user_id: int, points: float, total_points: float):
    """Point kazanma logu - Sadece önemli durumlar"""
    if points >= 1.0:  # 1 KP ve üstü için log
        log_important(f"POINT KAZANIMI - User: {user_id}, Earned: {points} KP, Total: {total_points} KP")

def log_admin_action(admin_id: int, action: str, details: str):
    """Admin işlem logu - Önemli işlemler"""
    log_important(f"ADMIN ISLEM - Admin: {admin_id}, Action: {action}, Details: {details}")

def log_system_error(error: str, context: str = ""):
    """Sistem hatası logu - Kritik"""
    log_important(f"SISTEM HATASI - Error: {error}, Context: {context}", "ERROR")

def log_performance(operation: str, duration: float):
    """Performans logu - Sadece yavaş işlemler"""
    if duration > 1.0:  # 1 saniyeden uzun işlemler
        log_important(f"PERFORMANS - Operation: {operation}, Duration: {duration:.2f}s", "WARNING") 