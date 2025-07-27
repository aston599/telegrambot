"""
🎯 Kayıt Sistemi Handler'ı
/kirvekayit komutu ve kayıt işlemleri
"""

import logging
from aiogram import types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import save_user_info, register_user, is_user_registered, get_registered_users_count, unregister_user, get_user_rank
from config import get_config

logger = logging.getLogger(__name__)


async def yardim_command(message: Message) -> None:
    """
    /yardim komutunu işle
    """
    try:
        user = message.from_user
        config = get_config()
        
        logger.info(f"👤 /yardim komutu - User: {user.first_name} ({user.id})")
        
        # Kullanıcı bilgilerini kaydet
        await save_user_info(user.id, user.username, user.first_name, user.last_name)
        
        # Kayıtlı mı kontrol et
        is_registered = await is_user_registered(user.id)
        
        if is_registered:
            # Kayıtlı kullanıcı için yardım
            response = f"""
🤖 *KirveHub Bot - Yardım Menüsü*

Merhaba {user.first_name}! İşte kullanabileceğin komutlar:

📋 *Ana Komutlar:*
/start - Ana menü ve bot durumu
/menu - Profil menüsü ve istatistikler
/yardim - Bu yardım menüsü

🎮 *Etkinlik Komutları:*
/etkinlikler - Aktif etkinlikleri gör
/katil - Etkinliğe katıl

🛍️ *Market Komutları:*
/market - Market ürünlerini gör
/siparislerim - Sipariş geçmişim

📊 *İstatistik Komutları:*
/siralama - Point sıralaması
/profil - Detaylı profil

💡 *İpuçları:*
• Grup sohbetlerinde mesaj atarak point kazanabilirsin
• Günlük 5.00 KP limitin var
• Etkinliklere katılarak bonus kazanabilirsin
• Market'ten freespin ve bakiye alabilirsin

_Herhangi bir sorun yaşarsan admin ile iletişime geç! 🎯_
            """
        else:
            # Kayıtsız kullanıcı için yardım
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎯 Hemen Kayıt Ol!", callback_data="register_user")]
            ])
            
            response = f"""
🤖 *KirveHub Bot - Yardım Menüsü*

Merhaba {user.first_name}! 

❌ *Şu anda kayıtlı değilsin!*

Bu özellikleri kullanabilmek için önce sisteme kayıt olman gerekiyor.

🎯 *Kayıt olduktan sonra:*
✅ Point kazanma sistemi
✅ Etkinliklere katılma
✅ Market alışverişi
✅ Profil ve istatistikler
✅ Topluluk özellikleri

⬇️ **Hemen kayıt ol ve sisteme katıl!**
            """
            
            await message.answer(
                response, 
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            return
        
        await message.answer(response, parse_mode="Markdown")
        logger.info(f"✅ /yardim mesajı gönderildi - User: {user.id}")
        
    except Exception as e:
        logger.error(f"❌ /yardim handler hatası: {e}")
        await message.answer("Bir hata oluştu! Lütfen daha sonra tekrar deneyin.")


async def kirvekayit_command(message: Message) -> None:
    """
    /kirvekayit komutunu işle
    """
    try:
        user = message.from_user
        config = get_config()
        
        logger.info(f"👤 /kirvekayit komutu - User: {user.first_name} ({user.id})")
        
        # Kullanıcı bilgilerini kaydet
        await save_user_info(user.id, user.username, user.first_name, user.last_name)
        
        # Zaten kayıtlı mı kontrol et
        if await is_user_registered(user.id):
            await message.answer("✅ Zaten sistemde kayıtlısınız!")
            return
        
        # Kayıt butonu oluştur
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Kayıt Ol!", callback_data="register_user")]
        ])
        
        # Kayıt mesajı
        welcome_text = f"""
🌟 *KirveHub Kayıt Sistemi*

Merhaba {user.first_name}! 

KirveHub topluluğuna katılmak için aşağıdaki butona tıklayın.

📊 *Sistem Bilgileri:*
✅ Güvenli kayıt sistemi
✅ Özel özellikler erişimi
✅ Topluluk etkileşimi

👥 Şu anda *{await get_registered_users_count()}* kişi kayıtlı!

Hazırsanız kayıt olun! ⬇️
        """
        
        await message.answer(
            welcome_text, 
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ /kirvekayit mesajı gönderildi - User: {user.id}")
        
    except Exception as e:
        logger.error(f"❌ /kirvekayit handler hatası: {e}")
        await message.answer("Bir hata oluştu! Lütfen daha sonra tekrar deneyin.")


async def private_message_handler(message: Message) -> None:
    """
    Özel mesajları karşıla (komut olmayan mesajlar)
    """
    try:
        user = message.from_user
        config = get_config()
        
        logger.info(f"👤 Private mesaj - User: {user.first_name} ({user.id}) - Text: {message.text[:50] if message.text else 'No text'}")
        
        # Admin kontrolü - adminler için mesaj gösterme
        user_rank = await get_user_rank(user.id)
        rank_level = user_rank.get("rank_level", 1)
        
        # Admin 1 ve üstü için mesaj gösterme (rank_level >= 2)
        if rank_level >= 2:
            logger.info(f"🔒 Admin private mesajı - yanıt verilmiyor - User: {user.id}, Rank: {user_rank.get('rank_name', 'Unknown')}")
            return
        
        # Kullanıcı bilgilerini kaydet
        await save_user_info(user.id, user.username, user.first_name, user.last_name)
        
        # Zaten kayıtlı mı kontrol et
        if await is_user_registered(user.id):
            # Kayıtlı kullanıcı - komut olmayan mesaj uyarısı
            response = f"""
⚠️ *Komut Bulunamadı - {user.first_name}*

Yazdığınız şey bir komut değil ya da bir karşılığı yok.

💬 *Mesajınız:* _{message.text[:50] if message.text else 'Dosya/medya'}..._

🤖 *Kullanılabilir Komutlar:*
/start - Ana menü ve bot durumu
/menu - Profil menüsü ve istatistikler
/kirvekayit - Kayıt durumu kontrolü

ℹ️ *Yardım için:* /yardim yazarak komutları öğrenebilirsin ya da /menu gibi şeyler yaz.

_Lütfen geçerli bir komut kullanın! 🎯_
            """
            
            await message.answer(response, parse_mode="Markdown")
        else:
            # KAYIT OLMASI GEREKİYOR - Uyarı ver
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎯 Hemen Kayıt Ol!", callback_data="register_user")],
                [InlineKeyboardButton(text="ℹ️ Neden Kayıt?", callback_data="get_info")]
            ])
            
            registered_count = await get_registered_users_count()
            
            response = f"""
⚠️ *Kayıt Gerekli - {user.first_name}!*

Bu özelliği kullanabilmek için önce sisteme kayıt olmanız gerekiyor.

🚫 *Şu anda erişiminiz yok:*
❌ Mesaj gönderme
❌ Özel içerikler
❌ Topluluk özellikleri

🎯 *Kayıt olduktan sonra:*
✅ Tam erişim
✅ Özel özellikler
✅ Topluluk etkileşimi

👥 Şu anda *{registered_count}* kişi kayıtlı!

⬇️ **Hemen kayıt olun ve sisteme katılın!**
            """
            
            await message.answer(
                response, 
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        
        logger.info(f"✅ Private message yanıtı gönderildi - User: {user.id}")
        
    except Exception as e:
        logger.error(f"❌ Private message handler hatası: {e}")
        await message.answer("Bir hata oluştu! Lütfen daha sonra tekrar deneyin.")


async def register_callback_handler(callback: CallbackQuery) -> None:
    """
    Kayıt butonu callback'ini işle
    """
    try:
        user = callback.from_user
        
        if callback.data == "register_user":
            logger.info(f"🎯 Kayıt callback - User: {user.first_name} ({user.id})")
            
            # Zaten kayıtlı mı kontrol et
            if await is_user_registered(user.id):
                await callback.answer("✅ Zaten kayıtlısınız!", show_alert=True)
                return
            
            # Kullanıcıyı kayıt et
            success = await register_user(user.id)
            
            if success:
                # Başarılı kayıt
                registered_count = await get_registered_users_count()
                
                success_message = f"""
🎉 *Kayıt Başarılı!*

Tebrikler {user.first_name}! KirveHub topluluğuna başarıyla katıldınız!

📊 *Kayıt Bilgileri:*
✅ Üye ID: {user.id}
✅ Kayıt Tarihi: Şimdi
✅ Durum: Aktif

👥 Siz {registered_count}. üyemizsiniz!

🚀 *Artık Erişebileceğiniz Özellikler:*
🎯 Özel komutlar
📊 İstatistikler  
🎪 Etkinlikler
💬 Topluluk sohbeti

_Hoş geldiniz! 🌟_
                """
                
                # Eski mesajı düzenle
                await callback.message.edit_text(
                    success_message,
                    parse_mode="Markdown"
                )
                
                await callback.answer("🎉 Başarıyla kayıt oldunuz!")
                
                logger.info(f"✅ Kullanıcı kayıt edildi - User: {user.id}")
                
            else:
                await callback.answer("❌ Kayıt sırasında hata oluştu!", show_alert=True)
                logger.error(f"❌ Kayıt başarısız - User: {user.id}")
        
        elif callback.data == "get_info":
            info_text = """
ℹ️ *KirveHub Hakkında*

KirveHub, teknoloji meraklıları için özel bir topluluktur.

🎯 *Özellikler:*
• Güncel teknoloji haberleri
• Özel eğitim içerikleri  
• Projeler ve iş birlikleri
• Networking imkanları

📝 *Kayıt Süreci:*
1. "Kayıt Ol!" butonuna tıklayın
2. Otomatik kayıt tamamlanır
3. Özel özelliklere erişim kazanırsınız

_Bizi tercih ettiğiniz için teşekkürler! 🙏_
            """
            
            await callback.answer()
            await callback.message.answer(info_text, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"❌ Register callback hatası: {e}")
        await callback.answer("Bir hata oluştu!", show_alert=True)


async def kayitsil_command(message: Message) -> None:
    """
    /kayitsil test komutu - kullanıcının kaydını sil
    """
    try:
        user = message.from_user
        logger.info(f"🗑️ /kayitsil komutu - User: {user.first_name} ({user.id})")
        
        # Kullanıcı kayıtlı mı kontrol et
        if not await is_user_registered(user.id):
            await message.answer("❌ Zaten kayıtlı değilsiniz!")
            return
        
        # Kaydı sil
        success = await unregister_user(user.id)
        
        if success:
            registered_count = await get_registered_users_count()
            
            response = f"""
🗑️ *Kayıt Silindi!*

{user.first_name}, kaydınız başarıyla silindi.

📊 *Durum:*
❌ Artık kayıtlı değilsiniz
🔄 Yeniden kayıt olabilirsiniz
👥 Kalan kayıtlı: {registered_count} kişi

⚠️ *Bu bir test komutuydu!*

🎯 Yeniden kayıt olmak için:
/kirvekayit komutunu kullanın

_Test başarılı! 🧪_
            """
            
            await message.answer(response, parse_mode="Markdown")
            logger.info(f"✅ Kayıt silme işlemi tamamlandı - User: {user.id}")
            
        else:
            await message.answer("❌ Kayıt silme sırasında hata oluştu!")
            
    except Exception as e:
        logger.error(f"❌ /kayitsil handler hatası: {e}")
        await message.answer("Bir hata oluştu! Lütfen daha sonra tekrar deneyin.") 