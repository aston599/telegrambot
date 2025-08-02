"""
💬 Chat Mesaj Handler'ı - Kayıtlı kullanıcıları menu'ye yönlendir
"""

import logging
import time
from aiogram import types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import is_user_registered, save_user_info

logger = logging.getLogger(__name__)

# Bot instance setter
_bot_instance = None

# Kayıtsız kullanıcılar için cooldown sistemi
unregistered_user_cooldowns = {}

# Kayıtlı kullanıcılar için menü cooldown sistemi
registered_user_menu_cooldowns = {}

def set_bot_instance(bot_instance):
    global _bot_instance
    _bot_instance = bot_instance

async def handle_chat_message(message: Message) -> None:
    """
    Chat'te yazılan mesajları yakala ve kayıtlı kullanıcıları menu'ye yönlendir
    """
    logger.info(f"🔍 CHAT MESSAGE HANDLER ÇAĞRILDI - User: {message.from_user.first_name if message.from_user else 'Unknown'}, Chat: {message.chat.id if message.chat else 'Unknown'}")
    
    try:
        user = message.from_user
        
        # Komut mesajlarını atla
        if message.text and message.text.startswith('/'):
            return
        
        # Sadece grup/süper grup mesajlarını işle
        if message.chat.type not in ["group", "supergroup"]:
            return
        
        # Sadece kayıtlı gruplarda çalış
        from database import is_group_registered
        if not await is_group_registered(message.chat.id):
            return
        
        # Kullanıcı bilgilerini kaydet
        await save_user_info(user.id, user.username, user.first_name, user.last_name)
        
        # Kayıtlı mı kontrol et
        is_registered = await is_user_registered(user.id)
        
        if is_registered:
            # Kayıtlı kullanıcı - Sadece log kaydı (mesaj sayısı message_monitor.py'de artırılıyor)
            logger.info(f"💬 Kayıtlı kullanıcı grupta mesaj yazdı - User: {user.first_name} ({user.id})")
            return
        
        else:
            # Kayıtsız kullanıcı - Cooldown kontrolü
            current_time = time.time()
            cooldown_duration = 600  # 10 dakika
            
            # Kullanıcının son mesaj zamanını kontrol et
            if user.id in unregistered_user_cooldowns:
                last_message_time = unregistered_user_cooldowns[user.id]
                if current_time - last_message_time < cooldown_duration:
                    # Cooldown aktif, mesaj gönderme
                    logger.info(f"⏰ Kayıtsız kullanıcı cooldown'da - User: {user.first_name} ({user.id})")
                    return
            
            # Cooldown geçmişse veya ilk mesajsa
            unregistered_user_cooldowns[user.id] = current_time
            
            # Özelden kayıt mesajı gönder
            from handlers.chat_system import send_registration_reminder
            await send_registration_reminder(user.id, user.first_name)
            
            logger.info(f"💬 Chat mesajı - Kayıtsız kullanıcı - Özelden mesaj gönderildi - User: {user.first_name} ({user.id})")
            
    except Exception as e:
        logger.error(f"❌ Chat message handler hatası: {e}") 