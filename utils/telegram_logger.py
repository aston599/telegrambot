"""
📱 Telegram Logger - Tüm logları Telegram grubuna gönderir
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from aiogram import Bot

class TelegramLogHandler(logging.Handler):
    """Telegram grubuna log gönderen handler"""
    
    def __init__(self, bot: Bot, chat_id: int, level=logging.INFO):
        super().__init__(level)
        self.bot = bot
        self.chat_id = chat_id
        self.log_queue = []
        self.max_queue_size = 10
        self.send_interval = 30  # 30 saniyede bir gönder (flood control için)
        self.last_send_time = 0
        self.rate_limit_delay = 30  # 30 saniye bekle
        
    def emit(self, record):
        """Log kaydını işle"""
        try:
            # Log seviyesine göre emoji
            level_emoji = {
                'DEBUG': '🔍',
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨',
                'SYSTEM': '🔧'
            }.get(record.levelname, '📝')
            
            # Mesaj formatı
            timestamp = datetime.now().strftime('%H:%M:%S')
            # HTML karakterlerini escape et
            safe_message = record.getMessage().replace('<', '&lt;').replace('>', '&gt;')
            message = f"{level_emoji} <b>{record.levelname}</b> - {safe_message}"
            
            # Kullanıcı bilgisi varsa ekle
            if hasattr(record, 'user_id') and record.user_id:
                message += f"\n👤 User: {record.user_id}"
            if hasattr(record, 'username') and record.username:
                safe_username = record.username.replace('<', '&lt;').replace('>', '&gt;')
                message += f" (@{safe_username})"
                
            # Chat bilgisi varsa ekle
            if hasattr(record, 'chat_id') and record.chat_id:
                message += f"\n💬 Chat: {record.chat_id}"
                
            # Ek bilgiler varsa ekle
            if hasattr(record, 'additional_data') and record.additional_data:
                for key, value in record.additional_data.items():
                    safe_key = str(key).replace('<', '&lt;').replace('>', '&gt;')
                    safe_value = str(value).replace('<', '&lt;').replace('>', '&gt;')
                    message += f"\n📊 {safe_key}: {safe_value}"
            
            # Queue'ya ekle
            self.log_queue.append({
                'timestamp': timestamp,
                'level': record.levelname,
                'message': message,
                'severity': self._calculate_severity(record.levelname)
            })
            
            # Queue doluysa gönder
            if len(self.log_queue) >= self.max_queue_size:
                asyncio.create_task(self.send_logs())
                
        except Exception as e:
            # Fallback - console'a yaz
            print(f"Telegram log handler hatası: {e}")
            
    def _calculate_severity(self, level: str) -> int:
        """Severity score hesapla"""
        severity_map = {
            'DEBUG': 1,
            'INFO': 2,
            'WARNING': 4,
            'ERROR': 7,
            'CRITICAL': 10,
            'SYSTEM': 3
        }
        return severity_map.get(level, 5)
        
    async def send_logs(self):
        """Logları Telegram'a gönder"""
        if not self.log_queue:
            return
            
        try:
            # Rate limiting kontrolü
            import time
            current_time = time.time()
            if current_time - self.last_send_time < self.rate_limit_delay:
                # Henüz bekleme süresi dolmamış, queue'yu temizle ve çık
                self.log_queue.clear()
                return
                
            # Logları seviyeye göre grupla
            grouped_logs = {}
            for log in self.log_queue:
                level = log['level']
                if level not in grouped_logs:
                    grouped_logs[level] = []
                grouped_logs[level].append(log)
            
            # Her seviye için ayrı mesaj gönder (maksimum 3 seviye)
            sent_count = 0
            for level, logs in list(grouped_logs.items())[:3]:
                if sent_count >= 2:  # Maksimum 2 mesaj gönder
                    break
                await self.send_level_logs(level, logs)
                sent_count += 1
                await asyncio.sleep(2)  # 2 saniye bekle
                
            # Queue'yu temizle
            self.log_queue.clear()
            self.last_send_time = current_time
            
        except Exception as e:
            print(f"Log gönderme hatası: {e}")
            
    async def send_level_logs(self, level: str, logs: list):
        """Seviye loglarını gönder - Estetik versiyon"""
        if not logs:
            return
            
        try:
            # Mesaj formatı
            level_emoji = {
                'DEBUG': '🔍',
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨',
                'SYSTEM': '🔧'
            }.get(level, '📝')
            
            # En yüksek severity'li log'u bul
            max_severity = max(log['severity'] for log in logs)
            health_status = "🟢" if max_severity <= 5 else "🟡" if max_severity <= 7 else "🔴"
            
            # Estetik başlık
            message = f"<b>📊 {level_emoji} {level} Raporu</b>\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Özet bilgiler
            message += f"📈 <b>Özet:</b>\n"
            message += f"• 📊 Toplam Log: <code>{len(logs)}</code>\n"
            message += f"• ⏰ Zaman: <code>{datetime.now().strftime('%H:%M:%S')}</code>\n"
            message += f"• 🎯 Severity: <code>{max_severity}/10</code>\n"
            message += f"• {health_status} Durum: <code>{'İyi' if max_severity <= 5 else 'Orta' if max_severity <= 7 else 'Kritik'}</code>\n\n"
            
            # Log detayları - Daha temiz format
            message += f"📋 <b>Detaylar:</b>\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, log in enumerate(logs[:3]):  # İlk 3 log'u göster
                # HTML karakterlerini escape et
                safe_message = log['message'].replace('<', '&lt;').replace('>', '&gt;')
                # Daha temiz timestamp formatı
                clean_timestamp = log['timestamp']
                message += f"<code>{clean_timestamp}</code> {safe_message}\n\n"
                
            if len(logs) > 3:
                message += f"<i>... ve {len(logs) - 3} log daha</i>\n"
            
            message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"<i>🤖 KirveBot Log Sistemi</i>"
                
            # Mesajı gönder
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML"
            )
            
        except Exception as e:
            print(f"Seviye log gönderme hatası: {e}")
            # Flood control hatası varsa daha uzun bekle
            if "Flood control exceeded" in str(e) or "Too Many Requests" in str(e):
                self.rate_limit_delay = 60  # 60 saniyeye çıkar
                print(f"⚠️ Flood control tespit edildi! Rate limit 60 saniyeye çıkarıldı.")

# Global telegram logger
_telegram_logger = None

def setup_telegram_logger(bot: Bot, chat_id: int):
    """Telegram logger'ı kur"""
    global _telegram_logger
    
    if _telegram_logger:
        return _telegram_logger
        
    # Telegram handler oluştur
    telegram_handler = TelegramLogHandler(bot, chat_id)
    telegram_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    telegram_handler.setFormatter(formatter)
    
    # Root logger'a ekle
    root_logger = logging.getLogger()
    root_logger.addHandler(telegram_handler)
    
    _telegram_logger = telegram_handler
    return _telegram_logger

def get_telegram_logger():
    """Telegram logger'ı al"""
    return _telegram_logger 