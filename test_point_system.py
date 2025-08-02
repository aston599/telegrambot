"""
💎 Point Sistemi Test Scripti - Düzeltilmiş
"""

import asyncio
import logging
from datetime import datetime, timedelta
from database import (
    get_db_pool, is_user_registered, add_points_to_user, 
    get_user_points, save_user_info, register_user
)
from handlers.message_monitor import (
    monitor_group_message, check_flood_protection, 
    get_dynamic_point_amount, update_daily_stats
)

# Test için logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockMessage:
    """Test için mock message objesi"""
    def __init__(self, user_id: int, first_name: str, text: str, chat_id: int = -1001234567890):
        self.from_user = MockUser(user_id, first_name)
        self.chat = MockChat(chat_id)
        self.text = text
        self.message_id = 12345  # message_id eklendi

class MockUser:
    def __init__(self, user_id: int, first_name: str):
        self.id = user_id
        self.first_name = first_name
        self.username = f"testuser{user_id}"
        self.last_name = None
        self.is_bot = False

class MockChat:
    def __init__(self, chat_id: int):
        self.id = chat_id
        self.type = "group"
        self.title = "Test Group"

async def clear_cache():
    """Cache'i temizle"""
    try:
        from utils.memory_manager import memory_manager
        cache_manager = memory_manager.get_cache_manager()
        if hasattr(cache_manager, 'clear_cache'):
            cache_manager.clear_cache()
            logger.info("🧹 Cache temizlendi")
    except Exception as e:
        logger.warning(f"⚠️ Cache temizleme hatası: {e}")

async def test_point_system():
    """Point sistemi test"""
    try:
        logger.info("🧪 Point sistemi test başlatılıyor...")
        
        # Cache'i temizle
        await clear_cache()
        
        # Database bağlantısı
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database bağlantısı kurulamadı!")
            return
        
        # Test kullanıcısı
        test_user_id = 6513506166  # @mikedahjenko
        test_user_name = "TestUser"
        
        # Kullanıcıyı kaydet
        await save_user_info(test_user_id, f"testuser{test_user_id}", test_user_name, None)
        
        # Kayıtlı mı kontrol et
        is_registered = await is_user_registered(test_user_id)
        if not is_registered:
            logger.info("📝 Test kullanıcısı kayıt ediliyor...")
            await register_user(test_user_id)
        
        # Test grubunu kayıt et
        test_chat_id = -1001234567890
        from database import register_group
        await register_group(test_chat_id, "Test Group", "testgroup", test_user_id)
        
        # Mevcut bakiyeyi al (cache olmadan)
        async with pool.acquire() as conn:
            initial_balance = await conn.fetchval("""
                SELECT kirve_points FROM users WHERE user_id = $1
            """, test_user_id)
            logger.info(f"💰 Başlangıç bakiyesi (database): {initial_balance:.2f} KP")
        
        # Cache'li versiyon
        current_points = await get_user_points(test_user_id)
        logger.info(f"💰 Başlangıç bakiyesi (cache): {current_points.get('kirve_points', 0.0):.2f} KP")
        
        # Test mesajları - hızlı mesajlar test
        test_messages = [
            "Mesaj 1 - hemen",
            "Mesaj 2 - 1 saniye sonra",
            "Mesaj 3 - 1 saniye sonra", 
            "Mesaj 4 - 1 saniye sonra",
            "Mesaj 5 - 1 saniye sonra",
            "Mesaj 6 - 10 saniye sonra (point için)",
            "Mesaj 7 - 1 saniye sonra",
            "Mesaj 8 - 1 saniye sonra"
        ]
        
        logger.info("📝 Hızlı mesajlar test ediliyor...")
        
        for i, message_text in enumerate(test_messages):
            logger.info(f"📤 Mesaj {i+1}: {message_text}")
            
            # Mock message oluştur
            mock_message = MockMessage(test_user_id, test_user_name, message_text)
            
            # Message monitor'ı çağır
            await monitor_group_message(mock_message)
            
            # Bekle (mesaj 6'dan sonra 10 saniye bekle)
            if i == 4:  # Mesaj 6'dan önce
                logger.info("⏰ 10 saniye bekleniyor (point cooldown)...")
                await asyncio.sleep(10)
            elif i < len(test_messages) - 1:
                logger.info("⏰ 1 saniye bekleniyor...")
                await asyncio.sleep(1)
        
        # Son bakiyeyi kontrol et (cache olmadan)
        async with pool.acquire() as conn:
            final_balance = await conn.fetchval("""
                SELECT kirve_points FROM users WHERE user_id = $1
            """, test_user_id)
            logger.info(f"💰 Son bakiye (database): {final_balance:.2f} KP")
            
            # Kullanıcı bilgilerini kontrol et
            user_info = await conn.fetchrow("""
                SELECT user_id, kirve_points, daily_points, total_messages, is_registered,
                       pg_typeof(kirve_points) as points_type
                FROM users WHERE user_id = $1
            """, test_user_id)
            if user_info:
                logger.info(f"📊 Kullanıcı bilgileri: {dict(user_info)}")
            else:
                logger.warning(f"⚠️ Kullanıcı bulunamadı: {test_user_id}")
            
            # Point ekleme loglarını kontrol et
            point_logs = await conn.fetch("""
                SELECT * FROM daily_stats 
                WHERE user_id = $1 AND message_date = CURRENT_DATE
                ORDER BY message_date DESC
            """, test_user_id)
            logger.info(f"📊 Point logları: {len(point_logs)} kayıt")
            
            for log in point_logs:
                logger.info(f"📊 Log: {dict(log)}")
        
        # Cache'li versiyon
        final_points = await get_user_points(test_user_id)
        logger.info(f"💰 Son bakiye (cache): {final_points.get('kirve_points', 0.0):.2f} KP")
        
        # Toplam mesaj sayısını kontrol et
        total_messages = final_points.get('total_messages', 0)
        logger.info(f"📊 Toplam mesaj sayısı: {total_messages}")
        
        # Günlük istatistikleri kontrol et
        from database import get_today_stats
        today_stats = await get_today_stats(test_user_id)
        daily_messages = today_stats.get('message_count', 0)
        logger.info(f"📅 Günlük mesaj sayısı: {daily_messages}")
        
        logger.info("✅ Test tamamlandı!")
        
    except Exception as e:
        logger.error(f"❌ Test hatası: {e}")

async def test_flood_protection():
    """Flood protection test"""
    try:
        logger.info("🛡️ Flood protection test başlatılıyor...")
        
        test_user_id = 6513506166
        
        # Hızlı mesajlar test
        for i in range(5):
            can_send = await check_flood_protection(test_user_id)
            logger.info(f"Mesaj {i+1}: {'✅ Gönderilebilir' if can_send else '❌ Flood protection'}")
            await asyncio.sleep(1)  # 1 saniye aralık
        
        logger.info("✅ Flood protection test tamamlandı!")
        
    except Exception as e:
        logger.error(f"❌ Flood protection test hatası: {e}")

async def test_dynamic_point_amount():
    """Dinamik point miktarı test"""
    try:
        logger.info("💎 Dinamik point miktarı test başlatılıyor...")
        
        point_amount = await get_dynamic_point_amount()
        logger.info(f"💰 Dinamik point miktarı: {point_amount}")
        
        logger.info("✅ Dinamik point test tamamlandı!")
        
    except Exception as e:
        logger.error(f"❌ Dinamik point test hatası: {e}")

async def main():
    """Ana test fonksiyonu"""
    logger.info("🚀 Point sistemi testleri başlatılıyor...")
    
    # Database başlat
    from database import init_database
    await init_database()
    
    # Testleri çalıştır
    await test_dynamic_point_amount()
    await test_flood_protection()
    await test_point_system()
    
    logger.info("🎉 Tüm testler tamamlandı!")

if __name__ == "__main__":
    asyncio.run(main()) 