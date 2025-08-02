import asyncio
import logging
from database import get_db_pool, init_database, get_today_stats
from handlers.message_monitor import monitor_group_message

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockMessage:
    def __init__(self, user_id: int, first_name: str, text: str, chat_id: int = -1001234567890):
        self.from_user = MockUser(user_id, first_name)
        self.chat = MockChat(chat_id)
        self.text = text
        self.message_id = 12345

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

async def test_single_message():
    """Tek mesaj test"""
    try:
        # Database başlat
        await init_database()
        
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool alınamadı!")
            return
        
        test_user_id = 6513506166
        test_user_name = "TestUser"
        test_chat_id = -1001234567890
        
        # Başlangıç durumunu kontrol et
        async with pool.acquire() as conn:
            # Başlangıç total_messages
            initial_total = await conn.fetchval("""
                SELECT total_messages FROM users WHERE user_id = $1
            """, test_user_id)
            logger.info(f"📊 Başlangıç total_messages: {initial_total}")
            
            # Başlangıç daily_stats
            initial_daily = await conn.fetchval("""
                SELECT message_count FROM daily_stats 
                WHERE user_id = $1 AND group_id = $2 AND message_date = CURRENT_DATE
            """, test_user_id, test_chat_id)
            logger.info(f"📅 Başlangıç daily_stats: {initial_daily or 0}")
        
        # Tek mesaj gönder
        logger.info("📤 Test mesajı gönderiliyor...")
        mock_message = MockMessage(test_user_id, test_user_name, "Test mesajı - tek mesaj test")
        await monitor_group_message(mock_message)
        
        # Son durumu kontrol et
        async with pool.acquire() as conn:
            # Son total_messages
            final_total = await conn.fetchval("""
                SELECT total_messages FROM users WHERE user_id = $1
            """, test_user_id)
            logger.info(f"📊 Son total_messages: {final_total}")
            
            # Son daily_stats
            final_daily = await conn.fetchval("""
                SELECT message_count FROM daily_stats 
                WHERE user_id = $1 AND group_id = $2 AND message_date = CURRENT_DATE
            """, test_user_id, test_chat_id)
            logger.info(f"📅 Son daily_stats: {final_daily or 0}")
        
        # Değişiklikleri hesapla
        total_change = final_total - initial_total
        daily_change = (final_daily or 0) - (initial_daily or 0)
        
        logger.info(f"📈 Total messages değişimi: {total_change}")
        logger.info(f"📈 Daily stats değişimi: {daily_change}")
        
        if total_change > 0 and daily_change > 0:
            logger.info("✅ Mesaj sayısı başarıyla artırıldı!")
        else:
            logger.error("❌ Mesaj sayısı artırılmadı!")
            
    except Exception as e:
        logger.error(f"❌ Test hatası: {e}")

if __name__ == "__main__":
    asyncio.run(test_single_message()) 