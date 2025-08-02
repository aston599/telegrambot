"""
🔍 Bot Sistemleri Kapsamlı Test Scripti
"""

import asyncio
import logging
from datetime import datetime
from database import get_db_pool, init_database

# Test için logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Database bağlantısı test"""
    try:
        logger.info("🗄️ Database bağlantısı test ediliyor...")
        
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database bağlantısı başarısız!")
            return False
        
        async with pool.acquire() as conn:
            # Temel tabloları kontrol et
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            logger.info(f"📊 Mevcut tablolar: {[t['table_name'] for t in tables]}")
            
            # Kullanıcı sayısını kontrol et
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            logger.info(f"👥 Toplam kullanıcı sayısı: {user_count}")
            
            # Market ürün sayısını kontrol et
            product_count = await conn.fetchval("SELECT COUNT(*) FROM market_products")
            logger.info(f"🛍️ Market ürün sayısı: {product_count}")
            
        logger.info("✅ Database bağlantısı başarılı!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test hatası: {e}")
        return False

async def test_market_system():
    """Market sistemi test"""
    try:
        logger.info("🛍️ Market sistemi test ediliyor...")
        
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            # Market ürünlerini kontrol et
            products = await conn.fetch("""
                SELECT id, name, price, category_id, is_available 
                FROM market_products 
                LIMIT 5
            """)
            
            logger.info(f"📦 Market ürünleri: {len(products)} adet")
            for product in products:
                logger.info(f"  - {product['name']}: {product['price']} KP, Kategori: {product['category_id']}")
            
            # Market kategorilerini kontrol et
            categories = await conn.fetch("""
                SELECT DISTINCT category_id 
                FROM market_products 
                WHERE category_id IS NOT NULL
            """)
            
            logger.info(f"📂 Market kategorileri: {[c['category_id'] for c in categories]}")
        
        logger.info("✅ Market sistemi test tamamlandı!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Market test hatası: {e}")
        return False

async def test_event_system():
    """Event sistemi test"""
    try:
        logger.info("🎉 Event sistemi test ediliyor...")
        
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            # Event sayısını kontrol et
            event_count = await conn.fetchval("SELECT COUNT(*) FROM events")
            logger.info(f"🎪 Toplam event sayısı: {event_count}")
            
            # Aktif eventleri kontrol et
            active_events = await conn.fetch("""
                SELECT id, event_name, event_date, max_participants, is_active
                FROM events 
                WHERE event_date >= CURRENT_DATE AND is_active = true
                ORDER BY event_date
            """)
            
            logger.info(f"📅 Aktif eventler: {len(active_events)} adet")
            for event in active_events:
                logger.info(f"  - {event['event_name']}: {event['event_date']}")
        
        logger.info("✅ Event sistemi test tamamlandı!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Event test hatası: {e}")
        return False

async def test_user_statistics():
    """Kullanıcı istatistikleri test"""
    try:
        logger.info("📊 Kullanıcı istatistikleri test ediliyor...")
        
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            # En aktif kullanıcıları kontrol et
            top_users = await conn.fetch("""
                SELECT user_id, first_name, kirve_points, total_messages
                FROM users 
                ORDER BY total_messages DESC 
                LIMIT 5
            """)
            
            logger.info("🏆 En aktif kullanıcılar:")
            for user in top_users:
                logger.info(f"  - {user['first_name']}: {user['total_messages']} mesaj, {user['kirve_points']} KP")
            
            # Günlük istatistikleri kontrol et
            today_stats = await conn.fetch("""
                SELECT COUNT(*) as user_count, 
                       SUM(total_messages) as total_messages,
                       SUM(kirve_points) as total_points
                FROM users
            """)
            
            if today_stats:
                stats = today_stats[0]
                logger.info(f"📈 Genel istatistikler:")
                logger.info(f"  - Toplam kullanıcı: {stats['user_count']}")
                logger.info(f"  - Toplam mesaj: {stats['total_messages']}")
                logger.info(f"  - Toplam KP: {stats['total_points']:.2f}")
        
        logger.info("✅ Kullanıcı istatistikleri test tamamlandı!")
        return True
        
    except Exception as e:
        logger.error(f"❌ İstatistik test hatası: {e}")
        return False

async def test_custom_commands():
    """Özel komutlar test"""
    try:
        logger.info("⚙️ Özel komutlar test ediliyor...")
        
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            # Özel komut sayısını kontrol et
            command_count = await conn.fetchval("SELECT COUNT(*) FROM custom_commands")
            logger.info(f"🔧 Özel komut sayısı: {command_count}")
            
            # Özel komutları listele
            commands = await conn.fetch("""
                SELECT command_name, reply_text, created_by
                FROM custom_commands 
                LIMIT 5
            """)
            
            logger.info("📝 Özel komutlar:")
            for cmd in commands:
                logger.info(f"  - /{cmd['command_name']}: {cmd['reply_text'][:50]}...")
        
        logger.info("✅ Özel komutlar test tamamlandı!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Özel komut test hatası: {e}")
        return False

async def test_point_settings():
    """Point ayarları test"""
    try:
        logger.info("💎 Point ayarları test ediliyor...")
        
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            # Point ayarlarını kontrol et
            settings = await conn.fetch("""
                SELECT setting_key, setting_value, description
                FROM point_settings
                ORDER BY setting_key
            """)
            
            logger.info("⚙️ Point ayarları:")
            for setting in settings:
                logger.info(f"  - {setting['setting_key']}: {setting['setting_value']}")
        
        logger.info("✅ Point ayarları test tamamlandı!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Point ayarları test hatası: {e}")
        return False

async def test_handler_imports():
    """Handler import testleri"""
    try:
        logger.info("🔧 Handler import testleri başlatılıyor...")
        
        # Handler modüllerini test et
        handlers_to_test = [
            "handlers.start_handler",
            "handlers.admin_panel", 
            "handlers.secret_commands",
            "handlers.chat_message_handler",
            "handlers.message_monitor",
            "handlers.market_system",
            "handlers.statistics_system",
            "handlers.scheduled_messages"
        ]
        
        for handler in handlers_to_test:
            try:
                module = __import__(handler, fromlist=[''])
                logger.info(f"✅ {handler} import başarılı")
            except ImportError as e:
                logger.error(f"❌ {handler} import hatası: {e}")
            except Exception as e:
                logger.error(f"⚠️ {handler} beklenmeyen hata: {e}")
        
        logger.info("✅ Handler import testleri tamamlandı!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Handler import test hatası: {e}")
        return False

async def test_utility_modules():
    """Utility modülleri test"""
    try:
        logger.info("🛠️ Utility modülleri test ediliyor...")
        
        # Utility modüllerini test et
        utilities_to_test = [
            "utils.memory_manager",
            "utils.telegram_logger",
            "config"
        ]
        
        for utility in utilities_to_test:
            try:
                module = __import__(utility, fromlist=[''])
                logger.info(f"✅ {utility} import başarılı")
            except ImportError as e:
                logger.error(f"❌ {utility} import hatası: {e}")
            except Exception as e:
                logger.error(f"⚠️ {utility} beklenmeyen hata: {e}")
        
        logger.info("✅ Utility modülleri test tamamlandı!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Utility test hatası: {e}")
        return False

async def main():
    """Ana test fonksiyonu"""
    logger.info("🚀 Bot sistemleri kapsamlı test başlatılıyor...")
    
    # Database başlat
    await init_database()
    
    # Test sonuçları
    test_results = {}
    
    # Testleri çalıştır
    tests = [
        ("Database Bağlantısı", test_database_connection),
        ("Market Sistemi", test_market_system),
        ("Event Sistemi", test_event_system),
        ("Kullanıcı İstatistikleri", test_user_statistics),
        ("Özel Komutlar", test_custom_commands),
        ("Point Ayarları", test_point_settings),
        ("Handler Importları", test_handler_imports),
        ("Utility Modülleri", test_utility_modules)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 {test_name} test ediliyor...")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            test_results[test_name] = result
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            logger.error(f"❌ {test_name} test hatası: {e}")
            test_results[test_name] = False
    
    # Sonuçları özetle
    logger.info(f"\n{'='*60}")
    logger.info("📊 TEST SONUÇLARI ÖZETİ")
    logger.info(f"{'='*60}")
    
    successful_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n🎯 Genel Sonuç: {successful_tests}/{total_tests} test başarılı")
    
    if successful_tests == total_tests:
        logger.info("🎉 Tüm sistemler başarıyla çalışıyor!")
    else:
        logger.warning(f"⚠️ {total_tests - successful_tests} test başarısız!")
    
    logger.info("🏁 Kapsamlı sistem testi tamamlandı!")

if __name__ == "__main__":
    asyncio.run(main()) 