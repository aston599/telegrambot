"""
Registered_groups tablosunun kolonlarını kontrol et
"""

import asyncio
import logging
from database import get_db_pool, init_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_groups_table():
    """Registered_groups tablosunun kolonlarını kontrol et"""
    try:
        await init_database()
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Registered_groups tablosu kolonları
            group_cols = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'registered_groups' 
                ORDER BY ordinal_position
            """)
            
            logger.info("📋 Registered_groups kolonları:")
            for col in group_cols:
                logger.info(f"  - {col['column_name']}: {col['data_type']}")
            
            # Mevcut grupları listele
            groups = await conn.fetch("""
                SELECT * FROM registered_groups LIMIT 5
            """)
            
            logger.info(f"\n📊 Mevcut gruplar ({len(groups)} adet):")
            for group in groups:
                logger.info(f"  - {dict(group)}")
                
    except Exception as e:
        logger.error(f"❌ Hata: {e}")

if __name__ == "__main__":
    asyncio.run(check_groups_table()) 