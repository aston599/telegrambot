"""
Botun yer aldığı grupları listele
"""

import asyncio
import logging
from database import get_db_pool, init_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def list_bot_groups():
    """Botun yer aldığı grupları listele"""
    try:
        await init_database()
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Kayıtlı grupları listele
            groups = await conn.fetch("""
                SELECT 
                    group_id,
                    group_name,
                    group_username,
                    registered_by,
                    registration_date,
                    is_active
                FROM registered_groups 
                ORDER BY registration_date DESC
            """)
            
            logger.info(f"📋 Botun yer aldığı gruplar ({len(groups)} adet):")
            logger.info("=" * 60)
            
            for group in groups:
                status = "✅ Aktif" if group['is_active'] else "❌ Pasif"
                username = f"@{group['group_username']}" if group['group_username'] else "Kullanıcı adı yok"
                
                logger.info(f"🏷️ Grup Adı: {group['group_name']}")
                logger.info(f"👤 Kullanıcı Adı: {username}")
                logger.info(f"🆔 Grup ID: {group['group_id']}")
                logger.info(f"📅 Kayıt Tarihi: {group['registration_date']}")
                logger.info(f"📊 Durum: {status}")
                logger.info(f"👨‍💼 Kayıt Eden: {group['registered_by']}")
                logger.info("-" * 40)
            
            # Aktif grup sayısı
            active_groups = await conn.fetchval("""
                SELECT COUNT(*) FROM registered_groups WHERE is_active = true
            """)
            
            logger.info(f"📈 Özet:")
            logger.info(f"  - Toplam grup: {len(groups)}")
            logger.info(f"  - Aktif grup: {active_groups}")
            logger.info(f"  - Pasif grup: {len(groups) - active_groups}")
            
    except Exception as e:
        logger.error(f"❌ Hata: {e}")

if __name__ == "__main__":
    asyncio.run(list_bot_groups()) 