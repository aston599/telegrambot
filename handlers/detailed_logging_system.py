"""
🔍 Gelişmiş Detaylı Log Sistemi - Telegram Bot
Tüm işlemleri, hataları, eksiklikleri ve sistem durumunu Telegram grubuna gönderir
"""

import asyncio
import logging
import traceback
import psutil
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import get_config
from database import get_db_pool
from utils.logger import logger

# Global bot instance
_bot_instance = None

class LogLevel(Enum):
    """Log seviyeleri"""
    DEBUG = "🔍"
    INFO = "ℹ️"
    WARNING = "⚠️"
    ERROR = "❌"
    CRITICAL = "🚨"
    SUCCESS = "✅"
    SYSTEM = "🔧"
    USER = "👤"
    ADMIN = "👑"
    DATABASE = "🗄️"
    NETWORK = "🌐"
    SECURITY = "🔒"
    PERFORMANCE = "⚡"
    MONEY = "💰"
    EVENT = "🎮"
    MARKET = "🛍️"
    MEMORY = "🧠"
    CPU = "🔥"
    DISK = "💾"
    CONNECTION = "🔗"
    TIMEOUT = "⏰"
    MISSING = "❓"
    DEPRECATED = "📝"
    CONFLICT = "⚔️"
    INVALID = "🚫"
    OVERFLOW = "💥"
    DEADLOCK = "🔒"
    CORRUPTION = "💀"

class LogCategory(Enum):
    """Log kategorileri"""
    SYSTEM_STARTUP = "🚀 Sistem Başlatma"
    SYSTEM_SHUTDOWN = "🛑 Sistem Kapatma"
    USER_REGISTRATION = "📝 Kullanıcı Kayıt"
    USER_ACTIVITY = "💬 Kullanıcı Aktivite"
    ADMIN_ACTION = "👑 Admin İşlem"
    DATABASE_OPERATION = "🗄️ Veritabanı"
    ERROR_HANDLING = "❌ Hata Yönetimi"
    SECURITY_EVENT = "🔒 Güvenlik"
    PERFORMANCE_METRIC = "⚡ Performans"
    MONEY_TRANSACTION = "💰 Para İşlem"
    EVENT_PARTICIPATION = "🎮 Etkinlik Katılım"
    MARKET_ORDER = "🛍️ Market Sipariş"
    BROADCAST_MESSAGE = "📢 Toplu Mesaj"
    COMMAND_EXECUTION = "⚙️ Komut Çalıştırma"
    CALLBACK_EXECUTION = "🔘 Callback Çalıştırma"
    NETWORK_REQUEST = "🌐 Ağ İsteği"
    CACHE_OPERATION = "💾 Önbellek"
    MEMORY_USAGE = "🧠 Bellek Kullanımı"
    CPU_USAGE = "🔥 CPU Kullanımı"
    DISK_USAGE = "💾 Disk Kullanımı"
    CONNECTION_STATUS = "🔗 Bağlantı Durumu"
    TIMEOUT_EVENT = "⏰ Zaman Aşımı"
    MISSING_DATA = "❓ Eksik Veri"
    DEPRECATED_FEATURE = "📝 Eski Özellik"
    CONFLICT_RESOLUTION = "⚔️ Çakışma Çözümü"
    INVALID_INPUT = "🚫 Geçersiz Giriş"
    OVERFLOW_PROTECTION = "💥 Taşma Koruması"
    DEADLOCK_DETECTION = "🔒 Kilit Tespiti"
    DATA_CORRUPTION = "💀 Veri Bozulması"
    SYSTEM_HEALTH = "🏥 Sistem Sağlığı"
    RESOURCE_MONITORING = "📊 Kaynak İzleme"
    DEPENDENCY_CHECK = "🔗 Bağımlılık Kontrolü"
    CONFIGURATION_ERROR = "⚙️ Konfigürasyon Hatası"
    PERMISSION_DENIED = "🚫 İzin Reddedildi"
    RATE_LIMIT_EXCEEDED = "🚦 Hız Limiti Aşıldı"
    VALIDATION_FAILED = "❌ Doğrulama Başarısız"
    INTEGRITY_CHECK = "🔍 Bütünlük Kontrolü"
    BACKUP_STATUS = "💾 Yedekleme Durumu"
    MAINTENANCE_MODE = "🔧 Bakım Modu"

@dataclass
class LogEntry:
    """Log girişi"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    chat_id: Optional[int] = None
    chat_type: Optional[str] = None
    command: Optional[str] = None
    callback_data: Optional[str] = None
    error_details: Optional[str] = None
    performance_data: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None
    system_metrics: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    severity_score: Optional[int] = None

class DetailedLoggingSystem:
    """Gelişmiş detaylı log sistemi"""
    
    def __init__(self):
        self.config = get_config()
        self.log_group_id = self.config.LOG_GROUP_ID
        self.enabled = self.config.DETAILED_LOGGING_ENABLED
        self.batch_size = 10  # Toplu gönderim için
        self.log_queue: List[LogEntry] = []
        self.last_send_time = datetime.now()
        self.send_interval = 5  # 5 saniyede bir gönder
        self.error_count = 0
        self.warning_count = 0
        self.critical_count = 0
        self.performance_issues = []
        self.system_health = {}
        
    def set_bot_instance(self, bot_instance):
        """Bot instance'ını set et"""
        global _bot_instance
        _bot_instance = bot_instance
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Sistem metriklerini al"""
        try:
            # CPU kullanımı
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Bellek kullanımı
            memory = psutil.virtual_memory()
            
            # Disk kullanımı
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Process bilgileri
            process = psutil.Process(os.getpid())
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_memory_mb": round(process.memory_info().rss / (1024**2), 2),
                "process_cpu_percent": process.cpu_percent(),
                "open_files": len(process.open_files()),
                "threads": process.num_threads()
            }
        except Exception as e:
            logger.error(f"Sistem metrikleri alınamadı: {e}")
            return {}
        
    async def check_system_health(self) -> Dict[str, Any]:
        """Sistem sağlığını kontrol et"""
        metrics = await self.get_system_metrics()
        
        health_issues = []
        
        # CPU kontrolü
        if metrics.get("cpu_percent", 0) > 80:
            health_issues.append(f"🔥 CPU kullanımı yüksek: {metrics['cpu_percent']}%")
            
        # Bellek kontrolü
        if metrics.get("memory_percent", 0) > 85:
            health_issues.append(f"🧠 Bellek kullanımı kritik: {metrics['memory_percent']}%")
            
        # Disk kontrolü
        if metrics.get("disk_percent", 0) > 90:
            health_issues.append(f"💾 Disk kullanımı kritik: {metrics['disk_percent']}%")
            
        # Process kontrolü
        if metrics.get("process_memory_mb", 0) > 500:
            health_issues.append(f"📊 Process bellek kullanımı yüksek: {metrics['process_memory_mb']}MB")
            
        return {
            "metrics": metrics,
            "health_issues": health_issues,
            "overall_health": "🟢 İyi" if not health_issues else "🔴 Kritik" if len(health_issues) > 2 else "🟡 Uyarı"
        }
        
    async def log(self, 
                  level: LogLevel, 
                  category: LogCategory, 
                  message: str,
                  user_id: Optional[int] = None,
                  username: Optional[str] = None,
                  chat_id: Optional[int] = None,
                  chat_type: Optional[str] = None,
                  command: Optional[str] = None,
                  callback_data: Optional[str] = None,
                  error_details: Optional[str] = None,
                  performance_data: Optional[Dict[str, Any]] = None,
                  additional_data: Optional[Dict[str, Any]] = None,
                  stack_trace: Optional[str] = None,
                  severity_score: Optional[int] = None):
        
        """Gelişmiş log kaydı"""
        if not self.enabled:
            return
            
        # Sistem metriklerini al
        system_metrics = await self.get_system_metrics()
        
        # Severity score hesapla
        if severity_score is None:
            severity_score = self._calculate_severity_score(level, category, message)
            
        # Log entry oluştur
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            user_id=user_id,
            username=username,
            chat_id=chat_id,
            chat_type=chat_type,
            command=command,
            callback_data=callback_data,
            error_details=error_details,
            performance_data=performance_data,
            additional_data=additional_data,
            system_metrics=system_metrics,
            stack_trace=stack_trace,
            severity_score=severity_score
        )
        
        # Log queue'ya ekle
        self.log_queue.append(log_entry)
        
        # Counter'ları güncelle
        if level == LogLevel.ERROR:
            self.error_count += 1
        elif level == LogLevel.WARNING:
            self.warning_count += 1
        elif level == LogLevel.CRITICAL:
            self.critical_count += 1
            
        # Performance issue'ları takip et
        if performance_data and performance_data.get("duration_ms", 0) > 1000:
            self.performance_issues.append({
                "timestamp": datetime.now(),
                "operation": performance_data.get("operation", "unknown"),
                "duration_ms": performance_data.get("duration_ms", 0)
            })
            
        # Queue'yu kontrol et
        if len(self.log_queue) >= self.batch_size:
            await self.send_logs()
            
    def _calculate_severity_score(self, level: LogLevel, category: LogCategory, message: str) -> int:
        """Severity score hesapla (1-10)"""
        base_score = {
            LogLevel.DEBUG: 1,
            LogLevel.INFO: 2,
            LogLevel.SUCCESS: 2,
            LogLevel.WARNING: 4,
            LogLevel.ERROR: 7,
            LogLevel.CRITICAL: 10
        }.get(level, 5)
        
        # Category'ye göre bonus
        critical_categories = [
            LogCategory.DATA_CORRUPTION,
            LogCategory.DEADLOCK_DETECTION,
            LogCategory.SECURITY_EVENT,
            LogCategory.SYSTEM_HEALTH
        ]
        
        if category in critical_categories:
            base_score += 2
            
        # Mesaj içeriğine göre bonus
        critical_keywords = ["kritik", "critical", "fatal", "corruption", "deadlock", "security", "hack"]
        if any(keyword in message.lower() for keyword in critical_keywords):
            base_score += 1
            
        return min(base_score, 10)
        
    async def send_logs(self):
        """Logları Telegram'a gönder"""
        if not self.log_queue or not _bot_instance:
            return
            
        try:
            # Logları kategorilere göre grupla
            grouped_logs = self.group_logs_by_category()
            
            # Her kategori için ayrı mesaj gönder
            for category, logs in grouped_logs.items():
                await self.send_category_logs(category, logs)
                
            # Log queue'yu temizle
            self.log_queue.clear()
            self.last_send_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Log gönderme hatası: {e}")
            
    def group_logs_by_category(self) -> Dict[LogCategory, List[LogEntry]]:
        """Logları kategorilere göre grupla"""
        grouped = {}
        for log in self.log_queue:
            if log.category not in grouped:
                grouped[log.category] = []
            grouped[log.category].append(log)
        return grouped
        
    async def send_category_logs(self, category: LogCategory, logs: List[LogEntry]):
        """Kategori loglarını gönder"""
        if not logs:
            return
            
        try:
            # Mesaj formatını oluştur
            message = self.format_category_message(category, logs)
            
            # Keyboard oluştur
            keyboard = self.create_log_keyboard(logs)
            
            # Mesajı gönder
            await _bot_instance.send_message(
                chat_id=self.log_group_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Kategori log gönderme hatası: {e}")
            
    def format_category_message(self, category: LogCategory, logs: List[LogEntry]) -> str:
        """Kategori mesajını formatla"""
        if not logs:
            return ""
            
        # En yüksek severity'li log'u bul
        max_severity_log = max(logs, key=lambda x: x.severity_score or 0)
        
        # Sistem sağlığı kontrolü
        health_status = "🟢" if max_severity_log.severity_score <= 5 else "🟡" if max_severity_log.severity_score <= 7 else "🔴"
        
        # Mesaj başlığı
        message = f"{health_status} <b>{category.value}</b>\n"
        message += f"📊 <b>Toplam Log:</b> {len(logs)}\n"
        message += f"⏰ <b>Zaman:</b> {datetime.now().strftime('%H:%M:%S')}\n"
        message += f"🎯 <b>En Yüksek Severity:</b> {max_severity_log.severity_score}/10\n\n"
        
        # Sistem metrikleri
        if max_severity_log.system_metrics:
            metrics = max_severity_log.system_metrics
            message += f"💻 <b>Sistem Durumu:</b>\n"
            message += f"🔥 CPU: {metrics.get('cpu_percent', 0)}%\n"
            message += f"🧠 RAM: {metrics.get('memory_percent', 0)}% ({metrics.get('memory_used_gb', 0)}GB/{metrics.get('memory_total_gb', 0)}GB)\n"
            message += f"💾 Disk: {metrics.get('disk_percent', 0)}% (Boş: {metrics.get('disk_free_gb', 0)}GB)\n"
            message += f"📊 Process: {metrics.get('process_memory_mb', 0)}MB\n\n"
        
        # Log detayları
        message += f"📋 <b>Log Detayları:</b>\n"
        
        for i, log in enumerate(logs[:5]):  # İlk 5 log'u göster
            level_emoji = log.level.value
            time_str = log.timestamp.strftime('%H:%M:%S')
            
            message += f"{level_emoji} <b>{time_str}</b> - {log.message}\n"
            
            if log.error_details:
                message += f"   ❌ <i>{log.error_details[:100]}...</i>\n"
                
            if log.performance_data:
                duration = log.performance_data.get("duration_ms", 0)
                if duration > 1000:
                    message += f"   ⏱️ <i>Yavaş işlem: {duration}ms</i>\n"
                    
        if len(logs) > 5:
            message += f"\n... ve {len(logs) - 5} log daha\n"
            
        # Hata istatistikleri
        if self.error_count > 0 or self.warning_count > 0 or self.critical_count > 0:
            message += f"\n📈 <b>Hata İstatistikleri:</b>\n"
            message += f"❌ Hatalar: {self.error_count}\n"
            message += f"⚠️ Uyarılar: {self.warning_count}\n"
            message += f"🚨 Kritik: {self.critical_count}\n"
            
        return message
        
    def create_log_keyboard(self, logs: List[LogEntry]) -> Optional[InlineKeyboardMarkup]:
        """Log keyboard'u oluştur"""
        if not logs:
            return None
            
        keyboard = []
        
        # Detay butonları
        if any(log.error_details for log in logs):
            keyboard.append([InlineKeyboardButton("🔍 Hata Detayları", callback_data="log_error_details")])
            
        if any(log.performance_data for log in logs):
            keyboard.append([InlineKeyboardButton("⚡ Performans Raporu", callback_data="log_performance_report")])
            
        if any(log.system_metrics for log in logs):
            keyboard.append([InlineKeyboardButton("💻 Sistem Durumu", callback_data="log_system_status")])
            
        if any(log.stack_trace for log in logs):
            keyboard.append([InlineKeyboardButton("📋 Stack Trace", callback_data="log_stack_trace")])
            
        return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

# Global logging system instance
logging_system = DetailedLoggingSystem()

# Helper functions
async def log_system_startup():
    """Sistem başlatma logu"""
    await logging_system.log(
        LogLevel.SUCCESS,
        LogCategory.SYSTEM_STARTUP,
        "🚀 Bot başarıyla başlatıldı",
        additional_data={"startup_time": datetime.now().isoformat()}
    )

async def log_system_shutdown():
    """Sistem kapatma logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.SYSTEM_SHUTDOWN,
        "🛑 Bot kapatılıyor",
        additional_data={"shutdown_time": datetime.now().isoformat()}
    )

async def log_user_activity(user_id: int, username: str, action: str, chat_id: Optional[int] = None, chat_type: Optional[str] = None):
    """Kullanıcı aktivite logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.USER_ACTIVITY,
        f"👤 Kullanıcı aktivitesi: {action}",
        user_id=user_id,
        username=username,
        chat_id=chat_id,
        chat_type=chat_type
    )

async def log_command_execution(user_id: int, username: str, command: str, chat_id: Optional[int] = None, chat_type: Optional[str] = None):
    """Komut çalıştırma logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.COMMAND_EXECUTION,
        f"⚙️ Komut çalıştırıldı: /{command}",
        user_id=user_id,
        username=username,
        chat_id=chat_id,
        chat_type=chat_type,
        command=command
    )

async def log_callback_execution(user_id: int, username: str, callback_data: str, chat_id: Optional[int] = None, chat_type: Optional[str] = None):
    """Callback çalıştırma logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.CALLBACK_EXECUTION,
        f"🔘 Callback çalıştırıldı: {callback_data}",
        user_id=user_id,
        username=username,
        chat_id=chat_id,
        chat_type=chat_type,
        callback_data=callback_data
    )

async def log_error(error: Exception, context: str = "", user_id: Optional[int] = None, username: Optional[str] = None):
    """Hata logu"""
    error_details = str(error)
    stack_trace = traceback.format_exc()
    
    # Hata tipine göre kategori belirle
    category = LogCategory.ERROR_HANDLING
    if "database" in error_details.lower() or "connection" in error_details.lower():
        category = LogCategory.DATABASE_OPERATION
    elif "timeout" in error_details.lower():
        category = LogCategory.TIMEOUT_EVENT
    elif "permission" in error_details.lower():
        category = LogCategory.PERMISSION_DENIED
    elif "validation" in error_details.lower():
        category = LogCategory.VALIDATION_FAILED
        
    await logging_system.log(
        LogLevel.ERROR,
        category,
        f"❌ Hata oluştu: {context}",
        user_id=user_id,
        username=username,
        error_details=error_details,
        stack_trace=stack_trace
    )

async def log_database_operation(operation: str, table: str, success: bool, duration_ms: Optional[float] = None):
    """Veritabanı işlem logu"""
    level = LogLevel.SUCCESS if success else LogLevel.ERROR
    message = f"🗄️ DB işlemi: {operation} - {table}"
    
    performance_data = {"operation": operation, "table": table, "duration_ms": duration_ms}
    
    await logging_system.log(
        level,
        LogCategory.DATABASE_OPERATION,
        message,
        performance_data=performance_data
    )

async def log_admin_action(admin_id: int, admin_username: str, action: str, target_user_id: Optional[int] = None):
    """Admin işlem logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.ADMIN_ACTION,
        f"👑 Admin işlemi: {action}",
        user_id=admin_id,
        username=admin_username,
        additional_data={"target_user_id": target_user_id}
    )

async def log_money_transaction(user_id: int, username: str, transaction_type: str, amount: float, balance_after: float):
    """Para işlem logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.MONEY_TRANSACTION,
        f"💰 Para işlemi: {transaction_type} - {amount}₺",
        user_id=user_id,
        username=username,
        additional_data={"amount": amount, "balance_after": balance_after}
    )

async def log_event_participation(user_id: int, username: str, event_name: str, action: str, payment: Optional[float] = None):
    """Etkinlik katılım logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.EVENT_PARTICIPATION,
        f"🎮 Etkinlik: {action} - {event_name}",
        user_id=user_id,
        username=username,
        additional_data={"event_name": event_name, "payment": payment}
    )

async def log_market_order(user_id: int, username: str, product_name: str, quantity: int, total_price: float, order_number: str):
    """Market sipariş logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.MARKET_ORDER,
        f"🛍️ Market siparişi: {product_name} x{quantity}",
        user_id=user_id,
        username=username,
        additional_data={"product_name": product_name, "quantity": quantity, "total_price": total_price, "order_number": order_number}
    )

async def log_broadcast_message(admin_id: int, admin_username: str, message_type: str, target_count: int, success_count: int):
    """Toplu mesaj logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.BROADCAST_MESSAGE,
        f"📢 Toplu mesaj: {message_type} - {success_count}/{target_count}",
        user_id=admin_id,
        username=admin_username,
        additional_data={"target_count": target_count, "success_count": success_count}
    )

async def log_performance_metric(metric_name: str, value: float, unit: str = ""):
    """Performans metrik logu"""
    level = LogLevel.WARNING if value > 1000 else LogLevel.INFO
    await logging_system.log(
        level,
        LogCategory.PERFORMANCE_METRIC,
        f"⚡ Performans: {metric_name} = {value}{unit}",
        performance_data={"metric_name": metric_name, "value": value, "unit": unit}
    )

async def log_security_event(event_type: str, user_id: Optional[int] = None, username: Optional[str] = None, details: Optional[str] = None):
    """Güvenlik olay logu"""
    await logging_system.log(
        LogLevel.WARNING,
        LogCategory.SECURITY_EVENT,
        f"🔒 Güvenlik: {event_type}",
        user_id=user_id,
        username=username,
        additional_data={"event_type": event_type, "details": details}
    )

async def log_system_health_check():
    """Sistem sağlık kontrolü logu"""
    health = await logging_system.check_system_health()
    
    if health["health_issues"]:
        await logging_system.log(
            LogLevel.WARNING,
            LogCategory.SYSTEM_HEALTH,
            f"🏥 Sistem sağlığı: {len(health['health_issues'])} sorun tespit edildi",
            additional_data={"health_issues": health["health_issues"]},
            system_metrics=health["metrics"]
        )
    else:
        await logging_system.log(
            LogLevel.SUCCESS,
            LogCategory.SYSTEM_HEALTH,
            "🏥 Sistem sağlığı: Tüm sistemler normal",
            system_metrics=health["metrics"]
        )

async def log_missing_data(table: str, field: str, context: str = ""):
    """Eksik veri logu"""
    await logging_system.log(
        LogLevel.WARNING,
        LogCategory.MISSING_DATA,
        f"❓ Eksik veri: {table}.{field}",
        additional_data={"table": table, "field": field, "context": context}
    )

async def log_deprecated_feature(feature: str, alternative: str = ""):
    """Eski özellik logu"""
    await logging_system.log(
        LogLevel.WARNING,
        LogCategory.DEPRECATED_FEATURE,
        f"📝 Eski özellik kullanıldı: {feature}",
        additional_data={"feature": feature, "alternative": alternative}
    )

async def log_conflict_resolution(conflict_type: str, resolution: str):
    """Çakışma çözümü logu"""
    await logging_system.log(
        LogLevel.INFO,
        LogCategory.CONFLICT_RESOLUTION,
        f"⚔️ Çakışma çözüldü: {conflict_type}",
        additional_data={"conflict_type": conflict_type, "resolution": resolution}
    )

async def log_invalid_input(input_type: str, value: str, reason: str):
    """Geçersiz giriş logu"""
    await logging_system.log(
        LogLevel.WARNING,
        LogCategory.INVALID_INPUT,
        f"🚫 Geçersiz giriş: {input_type}",
        additional_data={"input_type": input_type, "value": value, "reason": reason}
    )

async def log_overflow_protection(operation: str, limit: int, actual: int):
    """Taşma koruması logu"""
    await logging_system.log(
        LogLevel.WARNING,
        LogCategory.OVERFLOW_PROTECTION,
        f"💥 Taşma koruması: {operation} limiti aşıldı",
        additional_data={"operation": operation, "limit": limit, "actual": actual}
    )

async def log_deadlock_detection(table: str, duration_ms: int):
    """Kilit tespiti logu"""
    await logging_system.log(
        LogLevel.CRITICAL,
        LogCategory.DEADLOCK_DETECTION,
        f"🔒 Kilit tespit edildi: {table}",
        additional_data={"table": table, "duration_ms": duration_ms}
    )

async def log_data_corruption(table: str, record_id: int, details: str):
    """Veri bozulması logu"""
    await logging_system.log(
        LogLevel.CRITICAL,
        LogCategory.DATA_CORRUPTION,
        f"💀 Veri bozulması: {table}.{record_id}",
        additional_data={"table": table, "record_id": record_id, "details": details}
    )

def set_bot_instance(bot_instance):
    """Bot instance'ını set et"""
    logging_system.set_bot_instance(bot_instance)

# Router for callback handling
from aiogram import Router
router = Router()

@router.callback_query(lambda c: c.data and c.data.startswith("log_"))
async def handle_log_callback(callback: types.CallbackQuery):
    """Log callback'lerini işle"""
    try:
        if callback.data == "log_error_details":
            await show_error_details(callback)
        elif callback.data == "log_performance_report":
            await show_performance_report(callback)
        elif callback.data == "log_system_status":
            await show_system_status(callback)
        elif callback.data == "log_stack_trace":
            await show_stack_trace(callback)
    except Exception as e:
        logger.error(f"Log callback hatası: {e}")
        await callback.answer("❌ Hata oluştu")

async def show_error_details(callback: types.CallbackQuery):
    """Hata detaylarını göster"""
    await callback.answer("🔍 Hata detayları gösteriliyor...")

async def show_performance_report(callback: types.CallbackQuery):
    """Performans raporunu göster"""
    await callback.answer("⚡ Performans raporu hazırlanıyor...")

async def show_system_status(callback: types.CallbackQuery):
    """Sistem durumunu göster"""
    await callback.answer("💻 Sistem durumu kontrol ediliyor...")

async def show_stack_trace(callback: types.CallbackQuery):
    """Stack trace'i göster"""
    await callback.answer("📋 Stack trace gösteriliyor...") 