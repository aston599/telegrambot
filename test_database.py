"""
Database Bağlantı Testi
"""

import asyncio
from database import get_db_pool, init_database

async def test_database():
    """Database bağlantısını test et"""
    try:
        print("🗄️ Database başlatılıyor...")
        await init_database()
        
        print("🔗 Database pool alınıyor...")
        pool = await get_db_pool()
        
        if not pool:
            print("❌ Database pool alınamadı!")
            return
        
        print("✅ Database pool alındı")
        
        async with pool.acquire() as conn:
            # Basit query test
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Basit query: {result}")
            
            # Users tablosu test
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            print(f"✅ Users tablosu: {user_count} kullanıcı")
            
            # Point sistemi test
            point_sum = await conn.fetchval("SELECT COALESCE(SUM(kirve_points), 0) FROM users")
            print(f"✅ Toplam points: {point_sum}")
            
        print("✅ Database test tamamlandı!")
        
    except Exception as e:
        print(f"❌ Database test hatası: {e}")

if __name__ == "__main__":
    asyncio.run(test_database()) 