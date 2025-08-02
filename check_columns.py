"""
Database kolonlarını kontrol et
"""

import asyncio
import logging
from database import get_db_pool, init_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_table_columns():
    """Database tablolarının kolonlarını kontrol et"""
    try:
        await init_database()
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Market products tablosu
            market_cols = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'market_products' 
                ORDER BY ordinal_position
            """)
            
            logger.info("📦 Market Products kolonları:")
            for col in market_cols:
                logger.info(f"  - {col['column_name']}: {col['data_type']}")
            
            # Events tablosu
            event_cols = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'events' 
                ORDER BY ordinal_position
            """)
            
            logger.info("🎉 Events kolonları:")
            for col in event_cols:
                logger.info(f"  - {col['column_name']}: {col['data_type']}")
            
            # Custom commands tablosu
            custom_cols = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'custom_commands' 
                ORDER BY ordinal_position
            """)
            
            logger.info("⚙️ Custom Commands kolonları:")
            for col in custom_cols:
                logger.info(f"  - {col['column_name']}: {col['data_type']}")
                
    except Exception as e:
        logger.error(f"❌ Hata: {e}")

if __name__ == "__main__":
    asyncio.run(check_table_columns()) 