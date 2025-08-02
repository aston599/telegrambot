import asyncio
import logging
from database import get_db_pool, init_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_daily_stats():
    """Daily stats tablosunu kontrol et"""
    try:
        # Database başlat
        await init_database()
        
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool alınamadı!")
            return
        
        async with pool.acquire() as conn:
            # Test kullanıcısının daily_stats kayıtlarını kontrol et
            test_user_id = 6513506166
            
            # Daily stats kayıtları
            daily_stats = await conn.fetch("""
                SELECT * FROM daily_stats 
                WHERE user_id = $1 
                ORDER BY message_date DESC
            """, test_user_id)
            
            logger.info(f"📊 Daily stats kayıtları: {len(daily_stats)}")
            
            for record in daily_stats:
                logger.info(f"📊 Kayıt: {dict(record)}")
            
            # Users tablosundaki total_messages
            user_info = await conn.fetchrow("""
                SELECT user_id, total_messages, last_activity 
                FROM users 
                WHERE user_id = $1
            """, test_user_id)
            
            if user_info:
                logger.info(f"👤 User bilgileri: {dict(user_info)}")
            else:
                logger.warning(f"⚠️ Kullanıcı bulunamadı: {test_user_id}")
            
            # Bugünkü kayıtları kontrol et
            from datetime import date
            today = date.today()
            
            today_stats = await conn.fetch("""
                SELECT * FROM daily_stats 
                WHERE user_id = $1 AND message_date = $2
            """, test_user_id, today)
            
            logger.info(f"📅 Bugünkü kayıtlar: {len(today_stats)}")
            
            for record in today_stats:
                logger.info(f"📅 Bugünkü kayıt: {dict(record)}")
                
    except Exception as e:
        logger.error(f"❌ Hata: {e}")

if __name__ == "__main__":
    asyncio.run(check_daily_stats()) 