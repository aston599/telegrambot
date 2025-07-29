"""
🎯 Kayıt Teşvik Sistemi - KirveHub Bot
Otomatik kayıt teşvik mesajları ve özel bilgilendirme
"""

import logging
import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Set
from aiogram import Bot, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import is_user_registered, save_user_info, get_db_pool
from config import get_config

logger = logging.getLogger(__name__)

# Teşvik sistemi ayarları
recruitment_system_active = False  # Production'da kapalı
recruitment_interval = 120  # 2 dakika (saniye)
recruitment_message_cooldown = 120  # 2 dakika (saniye)
last_recruitment_time = 0
last_recruited_user = None

# Grup reply mesajları (daha nazik ve az agresif)
GROUP_REPLY_MESSAGES = [
    "💎 Kirvem! Kayıt olmak ister misin? Özelden yazabilirsin!",
    "🎯 Kirve! Sistemde kayıtlı değilsin. Özelden yaz, detayları vereyim!",
    "💎 Kirvem! Kayıt olarak point kazanabilirsin. Özelden yaz!",
    "🎮 Kirve! Hala kayıtsız mısın? Özelden yaz, sistemini anlatayım!",
    "💎 Kirvem! Kayıt olarak etkinliklere katılabilirsin!",
    "🎯 Kirve! Özelden yaz, market sistemini anlatayım!",
    "💎 Kirvem! Kayıt olarak çok daha fazlasını kazanabilirsin!",
    "🎮 Kirve! Özelden yaz, tüm özellikleri anlatayım!",
    "💎 Kirvem! Kayıt olarak günlük point kazanabilirsin!",
    "🎯 Kirve! Özelden yaz, bonus sistemini anlatayım!",
    "💎 Kirvem! Kayıt olarak sıralamada yer alabilirsin!",
    "🎮 Kirve! Özelden yaz, çekiliş sistemini anlatayım!",
    "💎 Kirvem! Kayıt olarak özel ayrıcalıklar kazanabilirsin!"
]

# Özel mesaj şablonları (daha etkili ve yönlendirici)
RECRUITMENT_MESSAGES = [
    "🎯 **Kirvem!** Hala gruba kayıt olmadığını görüyorum. Bana özelden yaz, tüm bonusları anlatayım! 💎",
    "💎 **Kirve!** Kayıt olarak çok daha fazlasını kazanabilirsin. Özelden yaz, detayları vereyim! 🚀",
    "🎮 **Kirvem!** Sistemde kayıtlı değilsin. Özelden yaz, Kirve Point sistemini anlatayım! 💎",
    "💎 **Kirve!** Hala kayıtsız mısın? Özelden yaz, market sistemi ve etkinlikleri anlatayım! 🎯",
    "🚀 **Kirvem!** Kayıt olarak günlük 5 Kirve Point kazanabilirsin. Özelden yaz, her şeyi anlatayım! 💎",
    "💎 **Kirve!** Hala sistemde yoksun. Özelden yaz, KirveHub'ın tüm özelliklerini anlatayım! 🎮",
    "🎯 **Kirvem!** Kayıt olmadan çok şey kaçırıyorsun. Özelden yaz, bonus sistemini anlatayım! 💎",
    "💎 **Kirve!** Hala gruba kayıtlı değilsin. Özelden yaz, çekiliş sistemini keşfet! 🚀",
    "🎮 **Kirvem!** Özelden yaz, günlük 5 KP kazanma sistemini anlatayım! 💎",
    "💎 **Kirve!** Hala sistemde yoksun! Özelden yaz, tüm detayları vereyim! 🎯",
    "🏆 **Kirvem!** Özelden yaz, sıralama sistemini anlatayım! 💎",
    "🎯 **Kirve!** Özelden yaz, hızlı kazanım sistemini anlatayım! 🚀",
    "💎 **Kirve!** Özelden yaz, özel ayrıcalıkları anlatayım! 🎮"
]

# Özel bilgilendirme mesajları
INFO_MESSAGES = [
    "💎 **KİRVE POİNT NEDİR?**\n\nKirve Point, KirveHub'ın özel para birimidir. Sohbet ederek, etkinliklere katılarak ve aktif olarak kazanabilirsin.\n\n🎯 **Günlük 5 Kirve Point** kazanabilirsin!",
    
    "🛍️ **MARKET SİSTEMİ**\n\nKazandığın Kirve Point'lerle market'ten alışveriş yapabilirsin. Freespinler, site bakiyeleri ve daha fazlası!\n\n💎 **Her mesajın point kazandırır!**",
    
    "🎮 **ETKİNLİK SİSTEMİ**\n\nÇekilişler, bonus hunt'lar ve özel etkinliklere katılabilirsin. Büyük ödüller kazanabilirsin!\n\n🚀 **Sadece kayıtlı üyeler katılabilir!**",
    
    "📊 **PROFİL SİSTEMİ**\n\n/menu komutu ile profiline bakabilir, istatistiklerini görebilir ve sıralamadaki yerini takip edebilirsin.\n\n💎 **Detaylı istatistikler seni bekliyor!**",
    
    "🎯 **NASIL KAZANIRIM?**\n\n• Grup sohbetlerinde mesaj yaz\n• Etkinliklere katıl\n• Günlük aktivitelerini tamamla\n• Arkadaşlarını davet et\n\n💎 **Günlük 5 Kirve Point limiti var!**",
    
    "🏆 **SIRALAMA SİSTEMİ**\n\nEn aktif üyeler arasında yer al! Sıralamada yükselerek özel ayrıcalıklar kazanabilirsin.\n\n🚀 **Rekabetçi ortamda yarış!**",
    
    "🎯 **HIZLI KAZANIM**\n\nKayıt olduktan hemen sonra point kazanmaya başlayabilirsin! Her mesajın değeri var.\n\n💎 **Anında kazanım sistemi!**"
]

async def start_recruitment_system():
    """Kayıt teşvik sistemini başlat"""
    global recruitment_system_active
    
    while recruitment_system_active:
        try:
            await send_recruitment_messages()
            await asyncio.sleep(recruitment_interval)
        except Exception as e:
            logger.error(f"❌ Recruitment system hatası: {e}")
            await asyncio.sleep(300)  # 5 dakika bekle

async def send_recruitment_messages():
    """Kayıt teşvik mesajlarını gönder - Sıralı sistem"""
    try:
        if not recruitment_system_active:
            return
            
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        # Ana grup ID'si (config'den alınabilir)
        main_group_id = -1002746043354  # Ana grup ID'si
        
        # Yeni kayıtsız kullanıcıları bul
        unregistered_users = await get_unregistered_users_in_group(main_group_id)
        
        if not unregistered_users:
            logger.info("📭 Yeni kayıtsız kullanıcı bulunamadı")
            await bot.session.close()
            return
        
        # SIRALI SİSTEM: Kullanıcı bazlı cooldown kontrolü
        current_time = datetime.now()
        available_users = []
        
        for user_id in unregistered_users:
            # Son 24 saatte bu kullanıcıya mesaj gönderilmiş mi kontrol et
            if user_id not in last_recruitment_users:
                # Bu kullanıcıya son ne zaman teşvik gönderildi?
                last_time = user_recruitment_times.get(user_id)
                if not last_time or (current_time - last_time).total_seconds() >= recruitment_message_cooldown:
                    available_users.append(user_id)
        
        if not available_users:
            logger.info("📭 Spam koruması: Tüm kullanıcılar cooldown'da")
            await bot.session.close()
            return
        
        # Sadece 1 kullanıcıya mesaj gönder (sıralı sistem)
        target_user = available_users[0]
        
        # Rastgele mesaj seç
        message = random.choice(RECRUITMENT_MESSAGES)
        
        # Mesajı gönder
        await bot.send_message(
            chat_id=main_group_id,
            text=message,
            parse_mode="Markdown"
        )
        
        # Teşvik edilen kullanıcıyı kaydet
        last_recruitment_users.add(target_user)
        user_recruitment_times[target_user] = current_time
        
        # 24 saat sonra kullanıcıları listeden çıkar (otomatik temizlik)
        if len(last_recruitment_users) > 100:  # Liste çok büyükse temizle
            last_recruitment_users.clear()
            user_recruitment_times.clear()
        
        await bot.session.close()
        logger.info(f"🎯 Kayıt teşvik mesajı gönderildi - User: {target_user} (1dk cooldown aktif)")
        
    except Exception as e:
        logger.error(f"❌ Recruitment message hatası: {e}")

async def get_unregistered_users_in_group(group_id: int) -> List[int]:
    """Gruptaki kayıtsız kullanıcıları bul - Yeni kullanıcı odaklı"""
    try:
        pool = await get_db_pool()
        if not pool:
            return []
            
        async with pool.acquire() as conn:
            # İlk defa mesaj atan kayıtsız kullanıcıları bul
            # Son 1 saatte aktif olan, ama daha önce hiç mesaj atmamış olanlar
            users = await conn.fetch("""
                SELECT DISTINCT u.user_id, 
                       u.last_activity,
                       COALESCE(SUM(ds.message_count), 0) as total_messages
                FROM users u
                LEFT JOIN daily_stats ds ON u.user_id = ds.user_id 
                    AND ds.message_date >= CURRENT_DATE - INTERVAL '7 days'
                WHERE u.is_registered = FALSE 
                  AND u.last_activity >= NOW() - INTERVAL '1 hour'  -- Son 1 saatte aktif
                  AND u.last_activity <= NOW() - INTERVAL '2 minutes'  -- 2 dk önce aktif olanlar
                GROUP BY u.user_id, u.last_activity
                HAVING COALESCE(SUM(ds.message_count), 0) <= 3  -- En fazla 3 mesaj atmış olanlar (yeni kullanıcılar)
                ORDER BY u.last_activity DESC
                LIMIT 10  -- Spam önlemi - maksimum 10 kullanıcı
            """)
            
            return [user['user_id'] for user in users]
            
    except Exception as e:
        logger.error(f"❌ Get unregistered users hatası: {e}")
        return []

async def handle_recruitment_response(message: Message):
    """Kayıt teşvik mesajına gelen yanıtları işle"""
    try:
        user = message.from_user
        
        # Kullanıcı kayıtlı mı kontrol et
        if await is_user_registered(user.id):
            return
            
        # Özel mesaj kontrolü
        if message.chat.type != "private":
            return
            
        # Kullanıcı bilgilerini kaydet (kayıt olmadan)
        await save_user_info(user.id, user.username, user.first_name, user.last_name)
        
        # Bilgilendirme mesajı gönder
        await send_recruitment_info(user.id, user.first_name)
        
    except Exception as e:
        logger.error(f"❌ Recruitment response hatası: {e}")

async def send_recruitment_info(user_id: int, first_name: str):
    """Kayıt bilgilendirme mesajı gönder"""
    try:
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        # Rastgele bilgilendirme mesajı seç
        info_message = random.choice(INFO_MESSAGES)
        
        # Ana bilgilendirme mesajı
        main_message = f"""
🎯 **Merhaba {first_name}!**

{info_message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 **KAYIT OLMAK İÇİN:**

1. **Grup sohbetinde:** `/kirvekayit` yaz
2. **Butona bas:** "Kayıt Ol!" butonuna tıkla
3. **Hemen başla:** Point kazanmaya başla!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎮 **KOMUTLAR:**
• `/start` - Ana menü ve bot durumu
• `/kirvekayit` - Hemen kayıt ol
• `/yardim` - Detaylı bilgi ve yardım

🚀 **Hemen kayıt ol ve KirveHub'ın bir parçası ol!** 💎

_💡 İpucu: Kayıt olduktan sonra grup sohbetlerinde mesaj atarak günlük 5 Kirve Point kazanabilirsin!_
        """
        
        # Butonlu mesaj
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Hemen Kayıt Ol!", callback_data="register_user")],
            [InlineKeyboardButton(text="📊 Detaylı Bilgi", callback_data="recruitment_info")],
            [InlineKeyboardButton(text="🎮 Komutları Gör", callback_data="show_commands")],
            [InlineKeyboardButton(text="❌ Kapat", callback_data="close_recruitment")]
        ])
        
        await bot.send_message(
            chat_id=user_id,
            text=main_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        await bot.session.close()
        logger.info(f"🎯 Recruitment info gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Recruitment info hatası: {e}")

# Admin panel fonksiyonları
def toggle_recruitment_system(enable: bool):
    """Kayıt teşvik sistemini aç/kapat"""
    global recruitment_system_active
    recruitment_system_active = enable
    
    status = "✅ Açıldı" if enable else "❌ Kapatıldı"
    logger.info(f"🎯 Recruitment system {status}")
    
    return recruitment_system_active

def get_recruitment_status() -> bool:
    """Kayıt teşvik sistemi durumunu al"""
    return recruitment_system_active

def set_recruitment_interval(seconds: int):
    """Kayıt teşvik mesaj aralığını ayarla"""
    global recruitment_interval
    recruitment_interval = seconds
    logger.info(f"🎯 Recruitment interval: {seconds} saniye")

# Background task başlatıcı
async def start_recruitment_background():
    """Background recruitment task'ını başlat"""
    asyncio.create_task(start_recruitment_system())
    logger.info("🎯 Recruitment background task başlatıldı")

# ==============================================
# CALLBACK HANDLER'LARI
# ==============================================

async def handle_recruitment_callback(callback: CallbackQuery):
    """Recruitment callback handler"""
    try:
        user_id = callback.from_user.id
        data = callback.data
        
        logger.info(f"🎯 Recruitment callback - User: {user_id}, Data: {data}")
        
        if data == "register_user":
            # Kayıt ol butonu
            await callback.answer("🎯 Kayıt sayfasına yönlendiriliyorsunuz...")
            
            # Kayıt mesajı gönder
            from handlers.register_handler import send_registration_message
            await send_registration_message(callback.from_user.id, callback.from_user.first_name)
            
        elif data == "recruitment_info":
            # Detaylı bilgi butonu
            await callback.answer("📊 Detaylı bilgi gönderiliyor...")
            
            info_message = f"""
📊 **KIRVEHUB DETAYLI BİLGİ**

💎 **Point Sistemi:**
• Her mesaj: 0.04 KP
• Günlük limit: 5.00 KP
• Flood koruması: 10 saniye

🎯 **Kayıt Avantajları:**
• Point kazanma
• Etkinlik katılımı
• Market alışverişi
• Sıralama sistemi

🏆 **Başarımlar:**
• Point Milyoneri (1000 KP)
• Sohbet Uzmanı (100 mesaj)
• Günlük Hedef (5 KP/gün)

🎮 **Komutlar:**
• `/start` - Ana menü
• `/menu` - Profil ve istatistikler
• `/etkinlikler` - Aktif etkinlikler
• `/yardim` - Yardım menüsü

💡 **İpucu:** Grup sohbetlerinde aktif olun!
            """
            
            await callback.message.edit_text(
                info_message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Geri", callback_data="recruitment_back")]
                ])
            )
            
        elif data == "show_commands":
            # Komutları göster butonu
            await callback.answer("🎮 Komutlar gösteriliyor...")
            
            commands_message = f"""
🎮 **KIRVEHUB KOMUTLARI**

📋 **Ana Komutlar:**
• `/start` - Bot durumu ve ana menü
• `/menu` - Profil ve istatistikler
• `/yardim` - Yardım ve bilgi

💎 **Point Sistemi:**
• `/kirvekayit` - Hemen kayıt ol
• `/etkinlikler` - Aktif etkinlikler
• `/cekilisler` - Çekiliş listesi

🎯 **Etkinlikler:**
• `/etkinlik` - Yeni etkinlik oluştur (Admin)
• `/cekilisbitir ID` - Çekiliş bitir (Admin)

🛍️ **Market:**
• Market menüsü profil içinde
• Ürün satın alma
• Sipariş takibi

📊 **İstatistikler:**
• Detaylı profil istatistikleri
• Point geçmişi
• Sıralama sistemi

💡 **İpucu:** Kayıt olduktan sonra tüm özellikler açılır!
            """
            
            await callback.message.edit_text(
                commands_message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Geri", callback_data="recruitment_back")]
                ])
            )
            
        elif data == "close_recruitment":
            # Kapat butonu
            await callback.answer("❌ Mesaj kapatılıyor...")
            await callback.message.delete()
            
        elif data == "recruitment_back":
            # Geri butonu - Ana recruitment mesajına dön
            await callback.answer("⬅️ Geri dönülüyor...")
            await send_recruitment_info(user_id, callback.from_user.first_name)
            
    except Exception as e:
        logger.error(f"❌ Recruitment callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True) 

async def check_recruitment_eligibility(user_id: int, username: str, first_name: str, group_name: str) -> bool:
    """Kullanıcının teşvik için uygun olup olmadığını kontrol et"""
    global last_recruitment_time, last_recruited_user
    
    # Sistem kapalıysa False döndür
    if not recruitment_system_active:
        return False
    
    current_time = time.time()
    
    # Son teşvik zamanından 2 dakika geçmemişse False döndür
    if current_time - last_recruitment_time < recruitment_interval:
        return False
    
    # Aynı kullanıcıya tekrar teşvik yapma
    if last_recruited_user == user_id:
        return False
    
    # Kullanıcı kayıtlı mı kontrol et
    pool = await get_db_pool()
    if not pool:
        return False
        
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT id FROM users WHERE telegram_id = $1",
            user_id
        )
        
        # Kayıtlı kullanıcıları teşvik etme
        if result:
            return False
    
    # Tüm koşullar sağlanıyorsa True döndür
    return True

async def send_recruitment_message(user_id: int, username: str, first_name: str, group_name: str):
    """Teşvik mesajı gönder"""
    global last_recruitment_time, last_recruited_user
    
    try:
        # Rastgele mesaj seç
        message = random.choice(GROUP_REPLY_MESSAGES)
        
        # Mesajı gönder
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML"
        )
        
        # Zaman damgalarını güncelle
        last_recruitment_time = time.time()
        last_recruited_user = user_id
        
        await bot.session.close()
        logger.info(f"🎯 Teşvik mesajı gönderildi - User: {user_id}, Name: {first_name}")
        
    except Exception as e:
        logger.error(f"❌ Teşvik mesajı gönderilemedi - User: {user_id}, Error: {e}") 