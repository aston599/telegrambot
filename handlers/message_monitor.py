"""
💎 Mesaj Monitoring Sistemi
Grup mesajlarında Kirve Point kazanımı
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set, List
from aiogram import types
from aiogram.types import Message

from database import (
    is_user_registered, is_group_registered, add_points_to_user, 
    save_user_info, get_user_points, db_pool, get_db_pool, get_user_points_cached
)

# Sistem ayarlarını getiren fonksiyon
async def get_system_settings() -> dict:
    """Sistem ayarlarını getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {
                'points_per_message': DEFAULT_POINT_PER_MESSAGE,
                'daily_limit': DAILY_POINT_LIMIT,
                'weekly_limit': WEEKLY_POINT_LIMIT
            }
            
        async with pool.acquire() as conn:
            # Sistem ayarlarını al
            settings = await conn.fetchrow("""
                SELECT 
                    points_per_message,
                    daily_limit,
                    weekly_limit
                FROM system_settings 
                WHERE id = 1
            """)
            
            if not settings:
                # Varsayılan ayarları döndür
                return {
                    'points_per_message': DEFAULT_POINT_PER_MESSAGE,
                    'daily_limit': DAILY_POINT_LIMIT,
                    'weekly_limit': WEEKLY_POINT_LIMIT
                }
                
            return {
                'points_per_message': float(settings['points_per_message']),
                'daily_limit': float(settings['daily_limit']),
                'weekly_limit': float(settings['weekly_limit'])
            }
            
    except Exception as e:
        logger.error(f"❌ Sistem ayarları hatası: {e}")
        return {
            'points_per_message': DEFAULT_POINT_PER_MESSAGE,
            'daily_limit': DAILY_POINT_LIMIT,
            'weekly_limit': WEEKLY_POINT_LIMIT
        }

logger = logging.getLogger(__name__)

# Flood koruması için user mesaj cache'i  
user_last_message: Dict[int, datetime] = {}
user_message_count: Dict[int, int] = {}
user_last_messages: Dict[int, List[str]] = {}  # Son mesajları takip et
user_message_timestamps: Dict[int, List[datetime]] = {}  # Mesaj zamanlarını takip et

# Point sistemi ayarları (dinamik - database'den okunur)
FLOOD_INTERVAL = 10  # Saniye - mesajlar arası minimum süre
MIN_MESSAGE_LENGTH = 5  # Minimum mesaj uzunluğu (5 harf)
DEFAULT_POINT_PER_MESSAGE = 0.04  # Varsayılan mesaj başına point
DAILY_POINT_LIMIT = 5.0  # Günlük limit
WEEKLY_POINT_LIMIT = 20.0  # Haftalık limit


async def update_daily_stats(user_id: int, group_id: int):
    """Günlük istatistikleri güncelle"""
    try:
        from database import db_pool
        if not db_pool:
            return
        
        async with db_pool.acquire() as conn:
            # Günlük mesaj sayısını artır
            await conn.execute("""
                UPDATE users 
                SET daily_messages = daily_messages + 1,
                    last_activity = NOW()
                WHERE user_id = $1
            """, user_id)
            
            # Haftalık mesaj sayısını artır
            await conn.execute("""
                UPDATE users 
                SET weekly_messages = weekly_messages + 1
                WHERE user_id = $1
            """, user_id)
            
            logger.debug(f"📊 Daily stats güncellendi - User: {user_id}, Group: {group_id}")
            
    except Exception as e:
        logger.error(f"❌ Daily stats güncelleme hatası: {e}")

async def monitor_group_message(message: Message) -> None:
    """Grup mesajlarını monitör et - Performance optimized"""
    
    try:
        # Temel kontroller - Hızlı
        if not message.text or not message.from_user or not message.chat:
            return
            
        user = message.from_user
        chat = message.chat
        message_text = message.text.strip()
        
        # Sadece kayıtlı gruplarda aktif ol
        if not await is_group_registered(chat.id):
            return
            
        # Bot mesajlarını ignore et
        if user.is_bot:
            return
            
        # Sadece grup ve supergroup'larda çalış
        if chat.type not in ['group', 'supergroup']:
            return
            
        # Komutları ignore et (/ ile başlayanlar)
        if message_text and message_text.startswith('/'):
            return
            
        # Mesaj uzunluğu kontrolü
        message_length = len(message_text)
        min_length = MIN_MESSAGE_LENGTH
        
        if message_length < min_length:
            return
            
        # Kelime tekrarı kontrolü
        words = message_text.split()
        unique_words = len(set(words))
        
        if unique_words < len(words):
            return
            
        # Kullanıcı kayıt durumu kontrolü
        is_registered = await is_user_registered(user.id)
        
        if not is_registered:
            # Recruitment sistemi kontrolü
            if await check_recruitment_eligibility(user.id, user.username, user.first_name, chat.title):
                await send_recruitment_message(user.id, user.username, user.first_name, chat.title)
        else:
            # Kayıtlı kullanıcılar için point sistemi
            point_per_message = await get_dynamic_point_amount()
            
            # Mevcut bakiyeyi al
            current_balance = await get_user_points_cached(user.id)
            old_balance = current_balance.get('kirve_points', 0.0) if current_balance else 0.0
            
            # Point ekle
            await add_points_to_user(user.id, point_per_message)
            
            # Yeni bakiyeyi al
            new_balance = old_balance + point_per_message
            
            # Milestone kontrolü - 1.00 KP'ye ulaştı mı?
            if old_balance < 1.0 and new_balance >= 1.0:
                await send_milestone_notification(user.id, user.first_name, new_balance)
            
            # Haftalık limit kontrolü
            weekly_points = current_balance.get('weekly_points', 0.0) if current_balance else 0.0
            new_weekly_points = weekly_points + point_per_message
            
            # Haftalık limit kontrolü (20.00 KP)
            if weekly_points < 20.0 and new_weekly_points >= 20.0:
                await send_weekly_limit_notification(user.id, user.first_name, 20.0)
            
            # Günlük istatistikleri güncelle
            await update_daily_stats(user.id, chat.id)
            
    except Exception as e:
        logger.error(f"❌ Group message handler hatası: {e}")

    # --- SOHBET ZEKASI ENTEGRE ---
    try:
        from handlers.chat_system import handle_chat_message, send_chat_response
        from utils.cooldown_manager import cooldown_manager
        
        # Cooldown kontrolü
        can_respond = await cooldown_manager.can_respond_to_user(message.from_user.id)
        if can_respond:
            response = await handle_chat_message(message)
            if response:
                await send_chat_response(message, response)
                # Mesajı kaydet
                await cooldown_manager.record_user_message(message.from_user.id)
    except Exception as e:
        logger.error(f"❌ Chat system (entegre) hatası: {e}")


async def check_flood_protection(user_id: int) -> bool:
    """
    Flood koruması kontrolü
    """
    try:
        now = datetime.now()
        
        # Son mesaj zamanını kontrol et
        if user_id in user_last_message:
            time_diff = now - user_last_message[user_id]
            
            # Çok hızlı mesaj gönderiyorsa
            if time_diff.total_seconds() < FLOOD_INTERVAL:
                return False
                
        # Artık dakikalık limit kontrolü yok - sadece 10 saniye aralık
                
        # Kullanıcının son mesaj zamanını güncelle
        user_last_message[user_id] = now
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Flood protection hatası: {e}")
        return False


async def check_message_uniqueness(user_id: int, message_text: str) -> bool:
    """
    Mesaj benzersizlik kontrolü - Kelime tekrarı koruması (Daha esnek)
    """
    try:
        current_time = datetime.now()
        
        # Kullanıcının son mesajlarını al
        if user_id not in user_last_messages:
            user_last_messages[user_id] = []
        if user_id not in user_message_timestamps:
            user_message_timestamps[user_id] = []
        
        last_messages = user_last_messages[user_id]
        timestamps = user_message_timestamps[user_id]
        
        # Zaman kontrolü - Son 60 saniyede aynı mesaj varsa spam
        if len(timestamps) >= 1:
            for i, timestamp in enumerate(timestamps):
                time_diff = (current_time - timestamp).total_seconds()
                if time_diff < 60 and last_messages[i] == message_text:
                    logger.info(f"⚠️ Aynı mesaj tekrarı tespit edildi - User: {user_id}")
                    return False
        
        # Son 3 mesajı kontrol et (daha esnek)
        for last_msg in last_messages:
            # Mesajlar çok benzer mi kontrol et
            if await calculate_similarity(message_text, last_msg) > 0.85:  # %85 benzerlik (daha esnek)
                logger.info(f"⚠️ Benzer mesaj tespit edildi - User: {user_id}")
                return False
        
        # Yeni mesajı listeye ekle
        last_messages.append(message_text)
        timestamps.append(current_time)
        
        # Listeyi 3 mesajla sınırla (daha esnek)
        if len(last_messages) > 3:
            last_messages.pop(0)
            timestamps.pop(0)
        
        user_last_messages[user_id] = last_messages
        user_message_timestamps[user_id] = timestamps
        return True
        
    except Exception as e:
        logger.error(f"❌ Message uniqueness hatası: {e}")
        return True  # Hata durumunda geç


async def send_daily_limit_notification(user_id: int, first_name: str, daily_limit: float) -> None:
    """Günlük limit dolu bildirimi"""
    try:
        from config import get_config
        from aiogram import Bot
        
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        message = f"""
🎯 **GÜNLÜK LİMİT DOLU!**

Merhaba {first_name}! 

📅 **Günlük kazanım limitinizi doldurdunuz!**
💰 **Limit:** {daily_limit} Kirve Point

⏰ **Tekrar kazanmak için 24 saatin geçmesini bekleyin.**

🔄 **Yarın tekrar aktif olacaksınız!**
        """
        
        await bot.send_message(
            user_id,
            message,
            parse_mode="Markdown"
        )
        
        logger.info(f"📅 Günlük limit bildirimi gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Günlük limit bildirimi hatası: {e}")


async def send_weekly_limit_notification(user_id: int, first_name: str, weekly_limit: float) -> None:
    """Haftalık limit dolu bildirimi"""
    try:
        from config import get_config
        from aiogram import Bot
        
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        message = f"""
🎯 **HAFTALIK LİMİT DOLU!**

Merhaba {first_name}! 

📊 **Haftalık kazanım limitinizi doldurdunuz!**
💰 **Limit:** {weekly_limit} Kirve Point

⏰ **Tekrar kazanmak için haftanın sonunu bekleyin.**

🔄 **Pazartesi tekrar aktif olacaksınız!**
        """
        
        await bot.send_message(
            user_id,
            message,
            parse_mode="Markdown"
        )
        
        logger.info(f"📊 Haftalık limit bildirimi gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Haftalık limit bildirimi hatası: {e}")


async def calculate_similarity(text1: str, text2: str) -> float:
    """
    İki metin arasındaki benzerlik oranını hesapla
    """
    try:
        # Basit benzerlik hesaplama
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
        
    except Exception as e:
        logger.error(f"❌ Similarity calculation hatası: {e}")
        return 0.0


async def cleanup_flood_cache() -> None:
    """
    Eski flood cache verilerini temizle (bellek tasarrufu)
    """
    try:
        now = datetime.now()
        cutoff_time = now - timedelta(hours=1)  # 1 saat öncesini temizle
        
        # Eski mesaj zamanlarını temizle
        old_users = [
            user_id for user_id, last_time in user_last_message.items()
            if last_time < cutoff_time
        ]
        
        for user_id in old_users:
            user_last_message.pop(user_id, None)
            user_last_messages.pop(user_id, None)  # Mesaj geçmişini de temizle
            
        if old_users:
            logger.info(f"🧹 Flood cache temizlendi - {len(old_users)} kullanıcı")
            
    except Exception as e:
        logger.error(f"❌ Flood cache cleanup hatası: {e}")


# Periyodik temizlik için background task
async def start_cleanup_task():
    """
    Her 30 dakikada bir cache temizliği yap
    """
    while True:
        try:
            await asyncio.sleep(1800)  # 30 dakika bekle
            await cleanup_flood_cache()
        except Exception as e:
            logger.error(f"❌ Cleanup task hatası: {e}")
            await asyncio.sleep(60)  # Hata durumunda 1 dakika bekle


async def get_dynamic_point_amount() -> float:
    """
    Database'den dinamik point miktarını al
    """
    try:
        if not db_pool:
            return DEFAULT_POINT_PER_MESSAGE
            
        async with db_pool.acquire() as conn:
            point_amount = await conn.fetchval("""
                SELECT setting_value FROM point_settings 
                WHERE setting_key = 'point_per_message'
            """)
            
            return float(point_amount) if point_amount else DEFAULT_POINT_PER_MESSAGE
            
    except Exception as e:
        logger.error(f"❌ Dinamik point miktarı alınamadı: {e}")
        return DEFAULT_POINT_PER_MESSAGE


async def send_private_point_notification(user_id: int, first_name: str, total_points: float, total_messages: int, group_name: str, earned_points: float = 0.04, is_milestone: bool = False) -> None:
    """
    Kullanıcıya özel mesajla point bildirimi gönder
    """
    try:
        from aiogram import Bot
        from config import get_config
        config = get_config()
        
        # Geçici bot instance
        temp_bot = Bot(token=config.BOT_TOKEN)
        
        if is_milestone:
            # 1.00 point milestone bildirimi
            notification = f"""
🎊 ┌─────────────────────────────────┐ 🎊
🏆 │      **MILESTONE BAŞARISI!**       │ 🏆
🎊 └─────────────────────────────────┘ 🎊

🌟 **Tebrikler {first_name}!**

🎯 **{int(total_points)}.00 KP** hedefine ulaştınız! 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **MEVCUT DURUMUNUZ:**
💰 **Toplam Point:** `{total_points:.2f} KP`
📝 **Mesaj Sayısı:** `{total_messages}`
🏛️ **Aktif Grup:** {group_name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 **Her 1.00 KP'de özel bildirim alırsınız!**

📱 _Detaylı profil için:_ `/menu`
🎮 **Böyle devam edin!** ✨
            """
        else:
            # Normal point kazanım bildirimi - ARTIK GÖNDERİLMİYOR
            # Bu kısım hiç çalışmayacak çünkü sadece milestone'larda bildirim var
            return
        
        await temp_bot.send_message(
            chat_id=user_id,
            text=notification,
            parse_mode="Markdown"
        )
        
        await temp_bot.session.close()
        logger.info(f"✅ Point bildirimi gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Point bildirimi gönderilemedi: {e}")


async def check_new_user_recruitment(user_id: int, first_name: str, group_name: str, message_length: int, message: Message = None) -> None:
    """Yeni kullanıcı teşvik sistemi - Sıralı sistem"""
    try:
        # DEBUG: Kullanıcı bilgilerini logla
        logger.info(f"🔍 Recruitment kontrolü - User: {user_id}, Name: {first_name}, Group: {group_name}")
        
        # Günlük limit kontrolü (kullanıcı başına 1 kez) - TEST İÇİN KAPALI
        # daily_sent = await is_recruitment_sent_today(user_id)
        # if daily_sent:
        #     logger.info(f"⏰ Günlük limit: User {user_id} için bugün zaten teşvik gönderilmiş")
        #     return
            
        # Kullanıcının toplam mesaj sayısını kontrol et
        pool = await get_db_pool()
        if not pool:
            logger.error(f"❌ Database pool bulunamadı - User: {user_id}")
            return
            
        async with pool.acquire() as conn:
            # Son 7 günde toplam mesaj sayısını al
            total_messages = await conn.fetchval("""
                SELECT COALESCE(SUM(message_count), 0)
                FROM daily_stats 
                WHERE user_id = $1 
                  AND message_date >= CURRENT_DATE - INTERVAL '7 days'
            """, user_id)
            
            logger.info(f"📊 Mesaj sayısı kontrolü - User: {user_id}, Total: {total_messages}")
            
            # Aktif kullanıcı kontrolü (spam önlemi)
            if total_messages <= 50:  # En fazla 50 mesaj atmış olanlar (PRODUCTION AYARI)
                logger.info(f"🎯 Teşvik gönderiliyor - User: {user_id}, Messages: {total_messages}")
                await send_new_user_recruitment(user_id, first_name, group_name, total_messages, message)
            else:
                logger.info(f"📊 Çok mesaj atmış kullanıcı - User: {user_id}, Messages: {total_messages}")
            
    except Exception as e:
        logger.error(f"❌ New user recruitment hatası: {e}")

async def send_new_user_recruitment(user_id: int, first_name: str, group_name: str, message_count: int, original_message: Message = None) -> None:
    """Yeni kullanıcıya teşvik mesajı gönder - Sıralı sistem"""
    try:
        from aiogram import Bot
        from config import get_config
        import random
        from datetime import datetime
        config = get_config()
        
        # SIRALI SİSTEM: Kullanıcı bazlı cooldown kontrolü - AÇIK
        from handlers.recruitment_system import user_recruitment_times, recruitment_message_cooldown
        
        current_time = datetime.now()
        
        # Bu kullanıcıya son ne zaman teşvik gönderildi?
        last_time = user_recruitment_times.get(user_id)
        if last_time:
            time_diff = (current_time - last_time).total_seconds()
            if time_diff < recruitment_message_cooldown:
                remaining_time = recruitment_message_cooldown - time_diff
                logger.info(f"⏰ Kullanıcı cooldown: User {user_id} için henüz çok erken ({remaining_time:.0f}s kaldı)")
                return
        
        # Geçici bot instance
        temp_bot = Bot(token=config.BOT_TOKEN)
        
        # 1. GRUP REPLY MESAJI (kısa ve etkili - özelden yazmaya yönlendirici)
        if original_message:
            group_reply_messages = [
                "🎯 Kirvem! Özelden yaz, tüm bonusları anlatayım! 💎",
                "💎 Kirve! Hala kayıtsız mısın? Özelden yaz, detayları vereyim! 🚀",
                "🎮 Kirvem! Özelden yaz, Kirve Point sistemini anlatayım! 💎",
                "💎 Kirve! Sistemde yoksun! Özelden yaz, her şeyi anlatayım! 🎯",
                "🚀 Kirvem! Özelden yaz, market ve etkinlikleri anlatayım! 💎",
                "💎 Kirve! Hala gruba kayıtlı değilsin! Özelden yaz! 🎮",
                "🎯 Kirvem! Özelden yaz, günlük 5 KP kazanma sistemini anlatayım! 💎",
                "💎 Kirve! Kayıt olmadan çok şey kaçırıyorsun! Özelden yaz! 🚀",
                "🎮 Kirvem! Özelden yaz, çekiliş ve bonus sistemini anlatayım! 💎",
                "💎 Kirve! Hala sistemde yoksun! Özelden yaz, tüm detayları vereyim! 🎯",
                "🏆 Kirvem! Özelden yaz, sıralama sistemini anlatayım! 💎",
                "🎯 Kirve! Özelden yaz, hızlı kazanım sistemini anlatayım! 🚀",
                "💎 Kirvem! Özelden yaz, özel ayrıcalıkları anlatayım! 🎮"
            ]
            
            reply_message = random.choice(group_reply_messages)
            
            try:
                await temp_bot.send_message(
                    chat_id=original_message.chat.id,
                    text=reply_message,
                    reply_to_message_id=original_message.message_id
                )
                logger.info(f"💬 Grup reply gönderildi - User: {user_id}, Group: {group_name}")
            except Exception as e:
                logger.error(f"❌ Grup reply hatası: {e}")
        
        # 2. ÖZEL MESAJ (detaylı bilgilendirme)
        recruitment_message = f"""
🎯 **Merhaba {first_name}!**

💎 **KirveHub'a hoş geldin!** 

Grupta mesajlaşmaya başladığını görüyorum! Kayıt olarak çok daha fazlasını kazanabilirsin.

**🎁 KAYIT OLARAK KAZANABİLECEKLERİN:**
• 💎 **Günlük 5 Kirve Point** - Her mesajın point kazandırır!
• 🛍️ **Market sistemi** - Freespinler, site bakiyeleri ve daha fazlası!
• 🎮 **Etkinliklere katılım** - Çekilişler, bonus hunt'lar, büyük ödüller!
• 📊 **Detaylı istatistikler** - Sıralamadaki yerini takip et!
• 🏆 **Özel ayrıcalıklar** - Sadece kayıtlı üyeler!

**🚀 KAYIT OLMAK İÇİN:** `/kirvekayit` yaz!

💎 **Hemen kayıt ol ve KirveHub'ın bir parçası ol!** 🚀
        """
        
        # ÖZEL MESAJ KAPALI - TELEGRAM KISITLAMASI
        # Bot sadece daha önce mesaj atmış kullanıcılara özel mesaj gönderebilir
        # Bu yüzden sadece grup reply kullanıyoruz
        
        # Kullanıcı bazlı cooldown kaydı - AÇIK
        user_recruitment_times[user_id] = current_time
        
        await temp_bot.session.close()
        logger.info(f"🎯 Yeni kullanıcı teşviki tamamlandı - User: {user_id}, Messages: {message_count} (sadece grup reply)")
        
    except Exception as e:
        logger.error(f"❌ New user recruitment hatası: {e}")

async def auto_recruit_user(user_id: int, first_name: str, group_name: str) -> None:
    """
    Kayıtsız kullanıcıya auto-recruitment mesajı gönder (günde 1 kez)
    """
    try:
        # Bugün bu kullanıcıya mesaj gönderildi mi kontrol et
        if await is_recruitment_sent_today(user_id):
            return
            
        from aiogram import Bot
        from config import get_config
        config = get_config()
        
        # Geçici bot instance
        temp_bot = Bot(token=config.BOT_TOKEN)
        
        recruitment_message = f"""
🎯 **Merhaba {first_name}!**

**{group_name}** grubunda mesajlaşıyorsun fakat kayıt olarak çok daha fazlasını kazanabilirsin! 

💎 **Kayıt olduktan sonra:**
• Otomatik sistem aktif olur
• Özel etkinliklere katılabilirsin  
• Market'ten alışveriş yapabilirsin
• Sıralamada yükselirsin

🚀 **Detaylar için bana özel mesaj at!**

_Komutlar: /start veya /kirvekayit_
        """
        
        await temp_bot.send_message(
            chat_id=user_id,
            text=recruitment_message,
            parse_mode="Markdown"
        )
        
        # Bugün gönderildi olarak işaretle
        await mark_recruitment_sent_today(user_id)
        
        await temp_bot.session.close()
        logger.info(f"🎯 Auto-recruitment gönderildi - User: {user_id} - Group: {group_name}")
        
    except Exception as e:
        logger.error(f"❌ Auto-recruitment gönderilemedi: {e}")


async def is_recruitment_sent_today(user_id: int) -> bool:
    """Bugün bu kullanıcıya recruitment mesajı gönderildi mi?"""
    try:
        if not db_pool:
            return False
            
        from datetime import date
        today = date.today()
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT 1 FROM daily_stats 
                WHERE user_id = $1 AND message_date = $2 AND character_count = -1
            """, user_id, today)
            
            return result is not None
            
    except Exception as e:
        logger.error(f"❌ Recruitment check hatası: {e}")
        return False


async def mark_recruitment_sent_today(user_id: int) -> None:
    """Bugün recruitment gönderildi olarak işaretle"""
    try:
        if not db_pool:
            return
            
        from datetime import date
        today = date.today()
        
        async with db_pool.acquire() as conn:
            # character_count = -1 → recruitment marker
            await conn.execute("""
                INSERT INTO daily_stats (user_id, group_id, message_date, message_count, character_count)
                VALUES ($1, 0, $2, 0, -1)
                ON CONFLICT (user_id, group_id, message_date) DO NOTHING
            """, user_id, today)
            
    except Exception as e:
        logger.error(f"❌ Recruitment marking hatası: {e}") 

async def send_milestone_notification(user_id: int, first_name: str, new_balance: float) -> None:
    """Milestone bildirimi gönder (1.00 KP'ye ulaşınca)"""
    try:
        from config import get_config
        from aiogram import Bot
        
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        # Milestone mesajları
        milestone_messages = [
            f"""
🎉 **TEBRİKLER! İLK MİLESTONE'A ULAŞTIN!** 🎉

Merhaba {first_name}! 

💰 **Yeni Bakiyen:** {new_balance:.2f} KP
🎯 **Milestone:** 1.00 KP'ye ulaştın!

🚀 **Artık şunları yapabilirsin:**
✅ Market'ten ürün alabilirsin
✅ Etkinliklere katılabilirsin
✅ Sıralamada yer alabilirsin

💡 **İpucu:** Günlük 5.00 KP limitini doldurmaya devam et!

🎮 **Devam et ve daha fazla kazan!** 💎
            """,
            f"""
🏆 **MİLESTONE BAŞARISI!** 🏆

Merhaba {first_name}! 

💰 **Bakiyen:** {new_balance:.2f} KP
🎯 **Başarı:** İlk 1.00 KP'ye ulaştın!

🎉 **Bu başarının anlamı:**
✅ Sistemde aktif kullanıcısın
✅ Point kazanma sistemini öğrendin
✅ Topluluğa katkı sağlıyorsun

💎 **Devam et ve daha fazla kazan!**

🎮 **İyi şanslar!** 🚀
            """,
            f"""
💎 **1.00 KP MİLESTONE!** 💎

Merhaba {first_name}! 

💰 **Yeni Bakiyen:** {new_balance:.2f} KP
🎯 **Başarı:** İlk milestone'a ulaştın!

🌟 **Bu ne anlama geliyor:**
✅ Point sistemini anladın
✅ Aktif bir üyesin
✅ Market'e erişim kazandın

🎮 **Şimdi market'ten ürün alabilirsin!**

💫 **Devam et ve daha fazla kazan!** 🚀
            """
        ]
        
        # Rastgele mesaj seç
        message = random.choice(milestone_messages)
        
        await bot.send_message(
            user_id,
            message,
            parse_mode="Markdown"
        )
        
        await bot.session.close()
        logger.info(f"🎉 Milestone bildirimi gönderildi - User: {user_id}, Balance: {new_balance}")
        
    except Exception as e:
        logger.error(f"❌ Milestone bildirimi hatası: {e}") 