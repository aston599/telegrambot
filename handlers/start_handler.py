"""
🎯 /start Komut Handler'ı - aiogram
"""

import logging
from aiogram import types
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import get_db_stats, save_user_info

logger = logging.getLogger(__name__)

# Bot instance setter
_bot_instance = None

def set_bot_instance(bot_instance):
    global _bot_instance
    _bot_instance = bot_instance

async def start_command(message: Message) -> None:
    """
    /start komutunu işle
    """
    try:
        user = message.from_user
        logger.info(f"🚀 START COMMAND DEBUG - User: {user.first_name} ({user.id}), Text: '{message.text}'")
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Start komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_start_privately(user.id)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        # Komut oluşturma sürecini iptal et (eğer varsa)
        try:
            from handlers.dynamic_command_creator import force_cancel_command_creation
            cancelled = await force_cancel_command_creation(user.id)
            if cancelled:
                logger.info(f"✅ Komut oluşturma süreci iptal edildi - User: {user.id}")
            else:
                logger.info(f"ℹ️ Komut oluşturma süreci yoktu - User: {user.id}")
        except Exception as e:
            logger.warning(f"⚠️ Komut oluşturma iptal hatası: {e}")
        
        # Kullanıcı bilgilerini kaydet
        await save_user_info(user.id, user.username, user.first_name, user.last_name)
        
        # Detaylı log
        from handlers.detailed_logging_system import log_command_execution
        await log_command_execution(
            user_id=user.id,
            username=user.username or user.first_name,
            command="start",
            chat_id=message.chat.id,
            chat_type=message.chat.type
        )
        
        # Database istatistiklerini al
        db_stats = await get_db_stats()
        
        if db_stats.get("database_active", False):
            # Kayıtlı mı kontrol et
            from database import is_user_registered
            is_registered = await is_user_registered(user.id)
            
            if is_registered:
                # Zaten kayıtlı kullanıcı için hoş geldin mesajı
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎮 Ana Menü", callback_data="menu_command")],
                    [InlineKeyboardButton(text="🛍️ Market", callback_data="market_command")],
                    [InlineKeyboardButton(text="🎯 Etkinlikler", callback_data="events_command")],
                    [InlineKeyboardButton(text="📊 Profilim", callback_data="profile_command")],
                    [InlineKeyboardButton(text="🏆 Sıralama", callback_data="ranking_command")]
                ])
                
                response_text = f"""
**Tekrar Hoş Geldin {user.first_name}!** 🎉

**KirveHub**'a geri döndün! Zaten kayıtlısın ve tüm özellikleri kullanabilirsin.

**💎 Kirve Point Sistemi:**
• Her mesajın point kazandırır
• Point'lerini **Market'te** freespinler, bakiyeler için kullanabilirsin
• **Etkinliklere** point'lerinle katılabilirsin
• Günlük **5 bonus point** kazanabilirsin

**🛍️ Market Özellikleri:**
• Point'lerini **freespinler** için kullan
• **Site bakiyeleri** satın al
• **Bonus paketleri** al
• **Özel indirimler**den yararlan

**🎯 Etkinlik Sistemi:**
• Point'lerinle **çekilişlere** katıl
• **Bonus hunt** etkinliklerine katıl
• **Özel yarışmalara** katıl
• **Sınırlı süreli** etkinlikleri kaçırma

**📊 Profil ve Sıralama:**
• **İstatistiklerini** görüntüle
• **Sıralamada** yer al
• **Başarılarını** takip et
• **Gelişimini** izle

**🎮 Ana Menü:**
Tüm özelliklere **Ana Menü**'den ulaşabilirsin!

**Hemen başla:**
✅ Zaten kayıtlısın!
💎 Grup sohbetlerinde mesaj at, point kazan!
🛍️ Market'te point'lerini kullan!
🎯 Etkinliklere katıl, bonuslar kazan!
🎮 Ana Menü'den her şeye ulaş!

_💡 Her mesajın point kazandırır!_
_🎯 Market'te point'lerini freespinler için kullanabilirsin!_
_🏆 Etkinliklerde point'lerinle özel ödüller kazanabilirsin!_
_🎮 Ana Menü'den tüm özelliklere ulaşabilirsin!_
                """
                
                await message.reply(
                    response_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
            else:
                # Otomatik kayıt işlemi
                from database import register_user
                registration_success = await register_user(user.id)
                
                if registration_success:
                    # Başarılı kayıt - Güzel tanıtım mesajı
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎮 Ana Menü", callback_data="menu_command")],
                        [InlineKeyboardButton(text="🛍️ Market", callback_data="market_command")],
                        [InlineKeyboardButton(text="🎯 Etkinlikler", callback_data="events_command")],
                        [InlineKeyboardButton(text="📊 Profilim", callback_data="profile_command")],
                        [InlineKeyboardButton(text="🏆 Sıralama", callback_data="ranking_command")]
                    ])
                    
                    response_text = f"""
**Hoş Geldin {user.first_name}!** 🎉

**KirveHub**'a başarıyla kayıt oldun! Artık tüm özellikleri kullanabilirsin.

**💎 Kirve Point Sistemi:**
• Her mesajın point kazandırır
• Point'lerini **Market'te** freespinler, bakiyeler için kullanabilirsin
• **Etkinliklere** point'lerinle katılabilirsin
• Günlük **5 bonus point** kazanabilirsin

**🛍️ Market Özellikleri:**
• Point'lerini **freespinler** için kullan
• **Site bakiyeleri** satın al
• **Bonus paketleri** al
• **Özel indirimler**den yararlan

**🎯 Etkinlik Sistemi:**
• Point'lerinle **çekilişlere** katıl
• **Bonus hunt** etkinliklerine katıl
• **Özel yarışmalara** katıl
• **Sınırlı süreli** etkinlikleri kaçırma

**📊 Profil ve Sıralama:**
• **İstatistiklerini** görüntüle
• **Sıralamada** yer al
• **Başarılarını** takip et
• **Gelişimini** izle

**🎮 Ana Menü:**
Tüm özelliklere **Ana Menü**'den ulaşabilirsin!

**Hemen başla:**
✅ Kayıt tamamlandı!
💎 Grup sohbetlerinde mesaj at, point kazan!
🛍️ Market'te point'lerini kullan!
🎯 Etkinliklere katıl, bonuslar kazan!
🎮 Ana Menü'den her şeye ulaş!

_💡 Her mesajın point kazandırır!_
_🎯 Market'te point'lerini freespinler için kullanabilirsin!_
_🏆 Etkinliklerde point'lerinle özel ödüller kazanabilirsin!_
_🎮 Ana Menü'den tüm özelliklere ulaşabilirsin!_
                    """
                    
                    await message.reply(
                        response_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    
                    logger.info(f"✅ Kullanıcı başarıyla kayıt oldu - User: {user.id}")
                    
                else:
                    # Kayıt başarısız
                    error_text = f"""
❌ **Kayıt Hatası**

Üzgünüm {user.first_name}, kayıt işlemi sırasında bir hata oluştu.

**Lütfen şunları kontrol edin:**
• İnternet bağlantınızın stabil olduğundan emin olun
• Birkaç dakika sonra tekrar deneyin
• Sorun devam ederse admin ile iletişime geçin

**Tekrar denemek için:**
/start komutunu tekrar kullanın
                    """
                    
                    await message.reply(error_text, parse_mode="Markdown")
                    logger.error(f"❌ Kullanıcı kayıt hatası - User: {user.id}")
            
        else:
            # Database bağlantı sorunu
            error_text = f"""
❌ **Sistem Hatası**

Üzgünüm {user.first_name}, sistem şu anda kullanılamıyor.

**Lütfen şunları yapın:**
• Birkaç dakika sonra tekrar deneyin
• Sorun devam ederse admin ile iletişime geçin

**Tekrar denemek için:**
/start komutunu tekrar kullanın
            """
            
            await message.reply(error_text, parse_mode="Markdown")
            logger.error(f"❌ Database bağlantı hatası - User: {user.id}")
                
    except Exception as e:
        logger.error(f"❌ Start command hatası - User: {message.from_user.id}, Error: {e}")
        
        error_text = f"""
❌ **Sistem Hatası**

Üzgünüm {message.from_user.first_name}, bir hata oluştu.

**Lütfen şunları yapın:**
• Birkaç dakika sonra tekrar deneyin
• Sorun devam ederse admin ile iletişime geçin

**Tekrar denemek için:**
/start komutunu tekrar kullanın
        """
        
        await message.reply(error_text, parse_mode="Markdown")

async def _send_start_privately(user_id: int):
    """Start mesajını özel mesajla gönder"""
    try:
        if not _bot_instance:
            logger.error("❌ Bot instance bulunamadı!")
            return
        
        # Kullanıcı bilgilerini al
        user_info = await _bot_instance.get_chat(user_id)
        
        # Kayıtlı olup olmadığını kontrol et
        from database import is_user_registered
        is_registered = await is_user_registered(user_id)
        
        if is_registered:
            # Kayıtlı kullanıcı - menüye yönlendir
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Ana Menü", callback_data="menu_command")],
                [InlineKeyboardButton(text="🛍️ Market", callback_data="market_command")],
                [InlineKeyboardButton(text="🎯 Etkinlikler", callback_data="events_command")],
                [InlineKeyboardButton(text="📊 Profilim", callback_data="profile_command")],
                [InlineKeyboardButton(text="🏆 Sıralama", callback_data="ranking_command")]
            ])
            
            response_text = f"""
**Hoş Geldin {user_info.first_name}!** 🎉

**KirveHub**'a zaten kayıtlısın! Tüm özellikleri kullanabilirsin.

**💎 Özellikler:**
• Her mesajın point kazandırır
• **Market'te** freespinler, bakiyeler
• **Etkinliklere** katıl, bonuslar kazan
• **Sıralamada** yer al

**🎮 Ana Menü'den başla!**
        """
            
            await _bot_instance.send_message(
                chat_id=user_id,
                text=response_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
        else:
            # Kayıtlı olmayan kullanıcı - kayıt olmaya yönlendir
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Hemen Kayıt Ol", callback_data="start_command")]
            ])
            
            response_text = f"""
**Hoş Geldin {user_info.first_name}!** 🎉

**KirveHub**'a kayıt olarak şunları kazanabilirsin:

**💎 Özellikler:**
• Her mesajın point kazandırır
• **Market'te** freespinler, bakiyeler
• **Etkinliklere** katıl, bonuslar kazan
• **Sıralamada** yer al

**🎮 Hemen başla:**
Kayıt ol butonuna bas veya `/start` yaz!
        """
            
            await _bot_instance.send_message(
                chat_id=user_id,
                text=response_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        
        logger.info(f"✅ Start özel mesajı gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Start özel mesaj hatası: {e}")
        # Hata durumunda basit mesaj gönder
        try:
            if _bot_instance:
                await _bot_instance.send_message(
                    chat_id=user_id,
                    text="❌ Mesaj gönderme hatası. Lütfen daha sonra tekrar deneyin."
                )
        except Exception as inner_e:
            logger.error(f"❌ Hata mesajı da gönderilemedi: {inner_e}") 