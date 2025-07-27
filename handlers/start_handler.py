"""
🎯 /start Komut Handler'ı - aiogram
"""

import logging
from aiogram import types
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import get_db_stats, save_user_info

logger = logging.getLogger(__name__)


async def start_command(message: Message) -> None:
    """
    /start komutunu işle
    """
    try:
        user = message.from_user
        logger.info(f"🚀 START COMMAND DEBUG - User: {user.first_name} ({user.id}), Text: '{message.text}'")
        
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
        
        # Database istatistiklerini al
        db_stats = await get_db_stats()
        
        if db_stats.get("database_active", False):
            # Kayıtlı mı kontrol et
            from database import is_user_registered
            is_registered = await is_user_registered(user.id)
            
            if is_registered:
                # Kayıtlı kullanıcı için hoş geldin mesajı
                response_text = f"""
🎉 **Merhaba {user.first_name}!**

**KirveHub**'a tekrar hoş geldin! 💎

✅ **Zaten kayıtlısın!** Artık tüm özellikleri kullanabilirsin.

🎮 **Ne yapabilirsin:**
• 💎 **Point kazan** - Her mesajın point kazandırır!
• 🛍️ **Market alışverişi** - Freespinler, site bakiyeleri
• 🎯 **Etkinliklere katıl** - Çekilişler, bonus hunt'lar
• 📊 **Profilini gör** - İstatistiklerin ve sıralaman
• 🏆 **Sıralamada yarış** - En aktif üyeler arasında yer al!

🎯 **Hızlı Komutlar:**
• `/menu` - Profil menüsü ve detaylı istatistikler
• `/market` - Market ürünleri ve alışveriş sistemi
• `/etkinlikler` - Aktif etkinlikler ve çekilişler
• `/yardim` - Detaylı yardım menüsü ve rehber

💎 **Hemen sohbete katıl ve point kazanmaya başla!** 🚀

_💡 İpucu: Grup sohbetlerinde mesaj atarak günlük 5 Kirve Point kazanabilirsin!_
_🎯 Bonus: Etkinliklere katılarak ekstra bonuslar kazanabilirsin!_
                """
            else:
                # Kayıtsız kullanıcı için kayıt teşviki
                response_text = f"""
🎉 **Merhaba {user.first_name}!**

**KirveHub**'a hoş geldin! 💎

❌ **Henüz kayıtlı değilsin!** Kayıt olarak çok daha fazlasını kazanabilirsin.

🎁 **Kayıt olduktan sonra:**
• 💎 **Günlük 5 Kirve Point** - Her mesajın point kazandırır!
• 🛍️ **Market sistemi** - Freespinler, site bakiyeleri ve daha fazlası!
• 🎮 **Etkinliklere katılım** - Çekilişler, bonus hunt'lar, büyük ödüller!
• 📊 **Detaylı istatistikler** - Sıralamadaki yerini takip et!
• 🏆 **Özel ayrıcalıklar** - Sadece kayıtlı üyeler!
• 🚀 **Hızlı kazanım** - Hemen point kazanmaya başla!

👥 **Şu anda {db_stats.get('registered_users', 0)} kişi kayıtlı!**

🎯 **Hemen kayıt ol:**
• `/kirvekayit` - Hemen kayıt ol
• `/yardim` - Detaylı bilgi ve yardım

💎 **Kayıt ol ve KirveHub'ın bir parçası ol!** 🚀

_💡 İpucu: Kayıt olduktan sonra grup sohbetlerinde mesaj atarak hemen point kazanmaya başlayabilirsin!_
_🎯 Bonus: Etkinliklere katılarak ekstra bonuslar kazanabilirsin!_
                """
        else:
            error_info = db_stats.get("error", "Bilinmeyen hata")
            response_text = f"""
🎉 **Merhaba {user.first_name}!**

**KirveHub Bot**'a hoş geldiniz! 🤖

📊 **Sistem Durumu:**
✅ Bot: Aktif ve çalışıyor
❌ Database: {error_info}
✅ Temel işlevler: Mevcut
⚠️ Komutlar: Sınırlı

🎯 **Kullanılabilir Komutlar:**
• `/start` - Bot'u başlat
• `/menu` - Profil (sınırlı)

_Database bağlantısı kontrol ediliyor..._ ⚠️
            """
        
        await message.answer(response_text, parse_mode="Markdown")
        logger.info(f"✅ /start yanıtı gönderildi - User: {user.id}")
        
    except Exception as e:
        logger.error(f"❌ /start handler hatası: {e}")
        await message.answer("Bir hata oluştu! Lütfen daha sonra tekrar deneyin.") 