"""
🎁 İlk Üye Bonus Sistemi
İlk üye olanlara özel 1 Kirve Point bonusu verir
"""

import logging
from aiogram.types import Message
from database import get_user_info, add_points_to_user, is_user_registered, save_user_info
from config import get_config

logger = logging.getLogger(__name__)

# İlk üye bonus sistemi ayarları
FIRST_USER_BONUS_AMOUNT = 1.00  # 1 Kirve Point
FIRST_USER_BONUS_MESSAGE = """
🎁 **HOŞ GELDİN BONUSU!**

🎉 **Tebrikler! İlk üye oldunuz!**

💰 **Bonus:** +1.00 Kirve Point
🎯 **Durum:** Hesabınıza eklendi

📊 **Mevcut Bakiyeniz:** {current_points:.2f} KP

💡 **Nasıl Point Kazanabilirsiniz:**
• Grup sohbetlerinde mesaj atın
• Etkinliklere katılın
• Market'ten alışveriş yapın

🎮 **Hemen başlayın ve daha fazla point kazanın!**

_İyi eğlenceler! 🚀_
"""

async def check_and_give_first_user_bonus(message: Message) -> bool:
    """
    İlk üye olan kullanıcıya bonus ver
    Returns: True if bonus was given, False if already received or error
    """
    try:
        user = message.from_user
        user_id = user.id
        
        # Kullanıcı bilgilerini kaydet (eğer yoksa)
        await save_user_info(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Kullanıcının mevcut durumunu kontrol et
        user_info = await get_user_info(user_id)
        
        if not user_info:
            logger.error(f"❌ User info bulunamadı - User: {user_id}")
            return False
        
        # Kullanıcı zaten kayıtlı mı kontrol et
        is_registered = await is_user_registered(user_id)
        
        if is_registered:
            # Kullanıcı zaten kayıtlı, bonus verilmiş olabilir
            logger.info(f"ℹ️ Kullanıcı zaten kayıtlı - User: {user_id}")
            return False
        
        # İlk üye bonusu ver
        bonus_success = await add_points_to_user(
            user_id=user_id,
            points=FIRST_USER_BONUS_AMOUNT,
            group_id=None  # Bonus için grup ID yok
        )
        
        if bonus_success:
            # Kullanıcıyı kayıtlı olarak işaretle
            from database import register_user
            await register_user(user_id)
            
            # Bonus mesajını gönder
            current_points = await get_user_points_after_bonus(user_id)
            
            bonus_message = FIRST_USER_BONUS_MESSAGE.format(
                current_points=current_points
            )
            
            await message.reply(
                bonus_message,
                parse_mode="Markdown"
            )
            
            logger.info(f"🎁 İlk üye bonusu verildi - User: {user_id}, Bonus: {FIRST_USER_BONUS_AMOUNT} KP")
            return True
        else:
            logger.error(f"❌ Bonus verilemedi - User: {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ İlk üye bonus hatası: {e}")
        return False

async def get_user_points_after_bonus(user_id: int) -> float:
    """Bonus sonrası kullanıcının point'ini al"""
    try:
        from database import get_user_points
        points_info = await get_user_points(user_id)
        return points_info.get('kirve_points', 0.0)
    except Exception as e:
        logger.error(f"❌ Point bilgisi alınamadı: {e}")
        return 0.0

async def is_first_time_user(user_id: int) -> bool:
    """Kullanıcının ilk kez mi geldiğini kontrol et"""
    try:
        user_info = await get_user_info(user_id)
        if not user_info:
            return True  # Kullanıcı hiç yok, ilk kez
        
        # Kullanıcının kayıt tarihini kontrol et
        registration_date = user_info.get('registration_date')
        if not registration_date:
            return True  # Kayıt tarihi yok, ilk kez
        
        return False  # Daha önce kayıt olmuş
        
    except Exception as e:
        logger.error(f"❌ İlk kullanıcı kontrolü hatası: {e}")
        return False

# Bonus sistemi istatistikleri
class FirstUserBonusStats:
    def __init__(self):
        self.total_bonuses_given = 0
        self.total_bonus_amount = 0.0
    
    def add_bonus(self, amount: float):
        self.total_bonuses_given += 1
        self.total_bonus_amount += amount
    
    def get_stats(self) -> dict:
        return {
            "total_bonuses_given": self.total_bonuses_given,
            "total_bonus_amount": self.total_bonus_amount,
            "average_bonus": self.total_bonus_amount / self.total_bonuses_given if self.total_bonuses_given > 0 else 0
        }

# Global bonus istatistikleri
bonus_stats = FirstUserBonusStats()

async def get_bonus_stats() -> dict:
    """Bonus sistemi istatistiklerini al"""
    return bonus_stats.get_stats() 