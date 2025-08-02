"""
🔧 Logger - Tüm logları Telegram grubuna da gönderir
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Logger'ı al
logger = logging.getLogger(__name__)

def log_system(message: str, user_id: Optional[int] = None, username: Optional[str] = None, chat_id: Optional[int] = None, additional_data: Optional[Dict[str, Any]] = None):
    """Sistem logu - Telegram grubuna da gönderir"""
    # CMD'ye yazdır
    print(f"🔧 SYSTEM: {message}")
    
    # Log record oluştur
    record = logging.LogRecord(
        name="system",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Ek bilgiler ekle
    if user_id:
        record.user_id = user_id
    if username:
        record.username = username
    if chat_id:
        record.chat_id = chat_id
    if additional_data:
        record.additional_data = additional_data
        
    # Logger'a gönder
    logger.handle(record)

def log_bot(message: str, user_id: Optional[int] = None, username: Optional[str] = None, chat_id: Optional[int] = None, additional_data: Optional[Dict[str, Any]] = None):
    """Bot logu - Telegram grubuna da gönderir"""
    # Log record oluştur
    record = logging.LogRecord(
        name="bot",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Ek bilgiler ekle
    if user_id:
        record.user_id = user_id
    if username:
        record.username = username
    if chat_id:
        record.chat_id = chat_id
    if additional_data:
        record.additional_data = additional_data
        
    # Logger'a gönder
    logger.handle(record)

def log_error(message: str, user_id: Optional[int] = None, username: Optional[str] = None, chat_id: Optional[int] = None, additional_data: Optional[Dict[str, Any]] = None):
    """Hata logu - Telegram grubuna da gönderir"""
    # CMD'ye yazdır
    print(f"❌ ERROR: {message}")
    
    # Log record oluştur
    record = logging.LogRecord(
        name="error",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Ek bilgiler ekle
    if user_id:
        record.user_id = user_id
    if username:
        record.username = username
    if chat_id:
        record.chat_id = chat_id
    if additional_data:
        record.additional_data = additional_data
        
    # Logger'a gönder
    logger.handle(record)

def log_info(message: str, user_id: Optional[int] = None, username: Optional[str] = None, chat_id: Optional[int] = None, additional_data: Optional[Dict[str, Any]] = None):
    """Bilgi logu - Telegram grubuna da gönderir"""
    # CMD'ye yazdır
    print(f"ℹ️ INFO: {message}")
    
    # Log record oluştur
    record = logging.LogRecord(
        name="info",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Ek bilgiler ekle
    if user_id:
        record.user_id = user_id
    if username:
        record.username = username
    if chat_id:
        record.chat_id = chat_id
    if additional_data:
        record.additional_data = additional_data
        
    # Logger'a gönder
    logger.handle(record)

def log_warning(message: str, user_id: Optional[int] = None, username: Optional[str] = None, chat_id: Optional[int] = None, additional_data: Optional[Dict[str, Any]] = None):
    """Uyarı logu - Telegram grubuna da gönderir"""
    # CMD'ye yazdır
    print(f"⚠️ WARNING: {message}")
    
    # Log record oluştur
    record = logging.LogRecord(
        name="warning",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Ek bilgiler ekle
    if user_id:
        record.user_id = user_id
    if username:
        record.username = username
    if chat_id:
        record.chat_id = chat_id
    if additional_data:
        record.additional_data = additional_data
        
    # Logger'a gönder
    logger.handle(record)

def log_debug(message: str, user_id: Optional[int] = None, username: Optional[str] = None, chat_id: Optional[int] = None, additional_data: Optional[Dict[str, Any]] = None):
    """Debug logu - Telegram grubuna da gönderir"""
    # Log record oluştur
    record = logging.LogRecord(
        name="debug",
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Ek bilgiler ekle
    if user_id:
        record.user_id = user_id
    if username:
        record.username = username
    if chat_id:
        record.chat_id = chat_id
    if additional_data:
        record.additional_data = additional_data
        
    # Logger'a gönder
    logger.handle(record)

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
    return logger

# Global logger instance'ı döndür
logger = logger 