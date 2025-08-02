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
• Her mesajın **1 Kirve Point** kazandırır
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

_💡 Her mesajın 1 Kirve Point kazandırır!_
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
• Her mesajın **1 Kirve Point** kazandırır
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

_💡 Her mesajın 1 Kirve Point kazandırır!_
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
                    # Kayıt başarısız
                    response_text = f"""
❌ **Kayıt Hatası!**

**KirveHub**'a kayıt olurken bir sorun oluştu.

🔄 **Lütfen daha sonra tekrar dene:**
• Bot'u yeniden başlat
• `/start` komutunu tekrar yaz
• Teknik destek için admin ile iletişime geç

⚠️ **Sistem geçici olarak bakımda olabilir.**
                    """
                    
                    await message.reply(
                        response_text,
                        parse_mode="Markdown"
                    )
        else:
            # Database bağlantısı yok
            response_text = f"""
🎉 **Merhaba {user.first_name}!**

**KirveHub**'a hoş geldin! 💎

⚠️ **Sistem geçici olarak bakımda!** Lütfen daha sonra tekrar dene.

🎮 **Sistem aktif olduğunda yapabileceklerin:**
• 💎 **Point kazan** - Her mesajın point kazandırır!
• 🛍️ **Market alışverişi** - Freespinler, site bakiyeleri
• 🎯 **Etkinliklere katıl** - Çekilişler, bonus hunt'lar
• 📊 **Profilini gör** - İstatistiklerin ve sıralaman
• 🏆 **Sıralamada yarış** - En aktif üyeler arasında yer al!

🔄 **Lütfen daha sonra tekrar dene!**
            """
            
            await message.reply(
                response_text,
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"❌ Start command hatası: {e}")
        await message.reply("❌ Bir hata oluştu! Lütfen daha sonra tekrar dene.")

async def _send_start_privately(user_id: int):
    """Özel mesajla start komutunu gönder"""
    try:
        if _bot_instance:
            await _bot_instance.send_message(
                user_id,
                "🎯 **Start komutu özel mesajda çalışır!**\n\n"
                "Lütfen botun özel mesajına gidip `/start` yazın.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"❌ Özel start mesajı gönderilemedi: {e}") 