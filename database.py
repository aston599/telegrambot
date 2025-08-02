"""
🗄️ Database Modülü - aiogram uyumlu + Kirve Point Sistemi
"""

import asyncpg
import logging
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
import asyncio

from config import get_config

# Gelişmiş log sistemi import'ları - Circular import önlemek için kaldırıldı
# from handlers.detailed_logging_system import (
#     log_database_operation, log_error, log_missing_data,
#     log_deadlock_detection, log_data_corruption, log_overflow_protection
# )

# Log sistemi yardımcı fonksiyonları
from utils.logging_utils import (
    log_database_operation, log_error, log_missing_data,
    log_deadlock_detection, log_data_corruption, log_overflow_protection
)
from utils.database_logger import get_database_logger, log_database_operation as db_log_operation

logger = logging.getLogger(__name__)

# Global database pool
db_pool: Optional[asyncpg.Pool] = None

# Connection pool ayarları - Performance optimized
POOL_MIN_SIZE = 10  # Artırıldı - 100-200 kullanıcı için
POOL_MAX_SIZE = 25  # Artırıldı - Daha fazla concurrent connection
POOL_TIMEOUT = 10.0  # Düşürüldü - Hızlı timeout
POOL_COMMAND_TIMEOUT = 5.0  # Düşürüldü - Hızlı query timeout
POOL_STATEMENT_CACHE_SIZE = 0  # PgBouncer için zorunlu
POOL_ACQUIRE_TIMEOUT = 2.0  # Connection acquire timeout

async def get_db_pool():
    """Ultra-fast database pool - Performance optimized"""
    global db_pool
    
    # Database logger'ı al
    db_logger = get_database_logger()
    
    # Pool kontrolü - is_closed() yerine try-catch kullan
    if db_pool is None:
        try:
            config = get_config()
            db_url = config.DATABASE_URL
            
            # Bağlantı denemesi logu
            await db_logger.log_connection_attempt(db_url)
            
            # URL encoding düzeltmesi
            if '!' in db_url:
                import urllib.parse
                parts = db_url.split('@')
                if len(parts) == 2:
                    auth_part = parts[0]
                    rest_part = parts[1]
                    
                    if ':' in auth_part:
                        user_pass = auth_part.split(':')
                        if len(user_pass) == 2:
                            user = user_pass[0]
                            password = user_pass[1]
                            encoded_password = urllib.parse.quote_plus(password)
                            db_url = f"{user}:{encoded_password}@{rest_part}"
            
            # Performance optimized pool ayarları
            db_pool = await asyncpg.create_pool(
                db_url,
                min_size=POOL_MIN_SIZE,
                max_size=POOL_MAX_SIZE,
                command_timeout=POOL_COMMAND_TIMEOUT,
                statement_cache_size=POOL_STATEMENT_CACHE_SIZE,
                server_settings={
                    'application_name': 'KirveHub Bot',
                    'jit': 'off',  # JIT'i kapat (performans için)
                    'synchronous_commit': 'off',  # Async commit
                    'wal_buffers': '32MB',  # WAL buffer artırıldı
                    'shared_buffers': '256MB',  # Shared buffer artırıldı
                    'tcp_keepalives_idle': '30',  # Keepalive düşürüldü
                    'tcp_keepalives_interval': '5',  # Keepalive interval düşürüldü
                    'tcp_keepalives_count': '3',  # Keepalive count düşürüldü
                    'statement_timeout': '5000',  # 5 saniye statement timeout
                    'idle_in_transaction_session_timeout': '10000'  # 10 saniye idle timeout
                },
                # Connection retry ayarları
                setup=setup_connection_fast
            )
            
            # Başarı logu
            await db_logger.log_connection_success(db_url)
            logger.info(f"✅ Database pool oluşturuldu - Min: {POOL_MIN_SIZE}, Max: {POOL_MAX_SIZE}")
            
        except Exception as e:
            # Hata logu
            await db_logger.log_connection_failure(db_url, str(e))
            logger.error(f"❌ Database pool hatası: {e}")
            return None
    else:
        # Pool var mı kontrol et - timeout ile
        try:
            async with asyncio.timeout(1.0):  # 1 saniye timeout (düşürüldü)
                async with db_pool.acquire() as conn:
                    await conn.execute("SELECT 1")
        except Exception:
            # Pool bozulmuş, yeniden oluştur
            logger.warning("⚠️ Database pool bozulmuş, yeniden oluşturuluyor...")
            db_pool = None
            return await get_db_pool()
            
    return db_pool

async def setup_connection_fast(conn):
    """Fast connection setup - Performance optimization"""
    try:
        # Minimal connection ayarları - Hızlı setup
        await conn.execute("SET application_name = 'KirveHub Bot'")
        await conn.execute("SET statement_timeout = 5000")  # 5 saniye
        await conn.execute("SET idle_in_transaction_session_timeout = 10000")  # 10 saniye
        await conn.execute("SET lock_timeout = 2000")  # 2 saniye
        logger.debug("✅ Fast connection setup tamamlandı")
    except Exception as e:
        logger.warning(f"⚠️ Fast connection setup hatası: {e}")

async def cleanup_connection_fast(conn):
    """Fast connection cleanup"""
    try:
        # Rollback any pending transactions
        await conn.execute("ROLLBACK")
        logger.debug("✅ Fast connection cleanup tamamlandı")
    except Exception as e:
        logger.warning(f"⚠️ Fast connection cleanup hatası: {e}")

async def execute_query(query: str, *args, timeout: float = 3.0):
    """Ultra-fast query execution - Minimal timeout"""
    try:
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool yok!")
            return None
            
        async with pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.fetch(query, *args, timeout=timeout)
                return result
                
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Database query timeout: {query[:50]}...")
        return None
    except Exception as e:
        logger.error(f"❌ Database query hatası: {e}")
        return None

async def execute_single_query(query: str, *args, timeout: float = 3.0):
    """Ultra-fast single query execution - Minimal timeout"""
    try:
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool yok!")
            return None
            
        async with pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.fetchrow(query, *args, timeout=timeout)
                return result
                
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Database single query timeout: {query[:50]}...")
        return None
    except Exception as e:
        logger.error(f"❌ Database single query hatası: {e}")
        return None

async def execute_value_query(query: str, *args, timeout: float = 3.0):
    """Ultra-fast value query execution - Minimal timeout"""
    try:
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool yok!")
            return None
            
        async with pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.fetchval(query, *args, timeout=timeout)
                return result
                
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Database value query timeout: {query[:50]}...")
        return None
    except Exception as e:
        logger.error(f"❌ Database value query hatası: {e}")
        return None

async def execute_command(query: str, *args, timeout: float = 3.0):
    """Ultra-fast command execution - Minimal timeout"""
    try:
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool yok!")
            return None
            
        async with pool.acquire() as conn:
            async with conn.transaction():
                result = await conn.execute(query, *args, timeout=timeout)
                return result
                
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Database command timeout: {query[:50]}...")
        return None
    except Exception as e:
        logger.error(f"❌ Database command hatası: {e}")
        return None

async def init_database() -> bool:
    """Database connection pool'unu başlat"""
    global db_pool
    
    try:
        logger.info("Database bağlantısı kuruluyor...")
        
        # Database pool'u oluştur
        config = get_config()
        db_url = config.DATABASE_URL
        
        # URL encoding düzeltmesi
        if '!' in db_url:
            import urllib.parse
            parts = db_url.split('@')
            if len(parts) == 2:
                auth_part = parts[0]
                rest_part = parts[1]
                
                if ':' in auth_part:
                    user_pass = auth_part.split(':')
                    if len(user_pass) == 2:
                        user = user_pass[0]
                        password = user_pass[1]
                        encoded_password = urllib.parse.quote_plus(password)
                        db_url = f"{user}:{encoded_password}@{rest_part}"
        
        db_pool = await asyncpg.create_pool(
            db_url,
            min_size=POOL_MIN_SIZE,
            max_size=POOL_MAX_SIZE,
            command_timeout=POOL_TIMEOUT,
            statement_cache_size=0,  # Pgbouncer uyumluluğu için
            server_settings={
                'application_name': 'KirveHub Bot',
                'jit': 'off'  # JIT'i kapat (performans için)
            }
        )
        
        # Tabloları oluştur
        await create_tables()
        
        # Dinamik komutlar tablosunu oluştur
        await create_custom_commands_table()
        
        # Test verilerini ekle
        await insert_test_data()
        
        logger.info("Database bağlantısı ve tablolar hazır!")
        return True
        
    except Exception as e:
        logger.error(f"Database başlatma hatası: {e}")
        return False


async def create_tables() -> None:
    """Gerekli tabloları oluştur ve güncelle"""
    if not db_pool:
        return
    
    try:
        async with db_pool.acquire() as conn:
            # Kullanıcılar tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(100),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    phone VARCHAR(20),
                    email VARCHAR(255),
                    interests TEXT[],
                    status VARCHAR(50) DEFAULT 'active',
                    notes TEXT,
                    kirve_points DECIMAL(10,2) DEFAULT 0.00,
                    daily_points DECIMAL(10,2) DEFAULT 0.00,
                    last_point_date DATE,
                    rank_id INTEGER DEFAULT 1,
                    total_messages INTEGER DEFAULT 0,
                    is_registered BOOLEAN DEFAULT FALSE,
                    registration_date TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Eksik kolonları ekle (eğer yoksa)
            try:
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_registered BOOLEAN DEFAULT FALSE")
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_date TIMESTAMP")
                await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
                # kirve_points kolonunu DECIMAL yap
                await conn.execute("ALTER TABLE users ALTER COLUMN kirve_points TYPE DECIMAL(10,2)")
                await conn.execute("ALTER TABLE users ALTER COLUMN daily_points TYPE DECIMAL(10,2)")
                
                logger.info("✅ Users tablosu kolonları güncellendi")
            except Exception as e:
                logger.info(f"ℹ️ Users tablosu kolonları zaten mevcut: {e}")
            
            # Kayıtlı gruplar tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS registered_groups (
                    group_id BIGINT PRIMARY KEY,
                    group_name VARCHAR(200),
                    group_username VARCHAR(100),
                    registered_by BIGINT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    point_multiplier DECIMAL(3,2) DEFAULT 1.00,
                    unregistered_at TIMESTAMP
                )
            """)
            
            # Eksik kolonları ekle (eğer yoksa)
            try:
                await conn.execute("ALTER TABLE registered_groups ADD COLUMN IF NOT EXISTS unregistered_at TIMESTAMP")
                logger.info("✅ Registered groups tablosu kolonları güncellendi")
            except Exception as e:
                logger.info(f"ℹ️ Registered groups tablosu kolonları zaten mevcut: {e}")
            
            # Kullanıcı rütbeleri tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_ranks (
                    rank_id SERIAL PRIMARY KEY,
                    rank_name VARCHAR(100) NOT NULL UNIQUE,
                    min_points DECIMAL(10,2) DEFAULT 0.00,
                    max_points DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Point sistemi ayarları tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS point_settings (
                    setting_key VARCHAR(50) PRIMARY KEY,
                    setting_value DECIMAL(10,2),
                    description TEXT,
                    updated_by BIGINT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sistem ayarları tablosu - YENİ EKLENDİ
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    id SERIAL PRIMARY KEY,
                    points_per_message DECIMAL(5,2) DEFAULT 0.04,
                    daily_limit DECIMAL(5,2) DEFAULT 5.00,
                    weekly_limit DECIMAL(5,2) DEFAULT 20.00,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Günlük istatistikler tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    group_id BIGINT NOT NULL,
                    message_date DATE NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    points_earned DECIMAL(10,2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Unique constraint ekle (eğer yoksa)
            try:
                await conn.execute("""
                    ALTER TABLE daily_stats 
                    ADD CONSTRAINT daily_stats_unique 
                    UNIQUE (user_id, group_id, message_date)
                """)
            except Exception as e:
                logger.info(f"ℹ️ Unique constraint zaten var: {e}")
            
            # Bakiye logları tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS balance_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    admin_id BIGINT,
                    action VARCHAR(20) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Etkinlikler tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    event_type VARCHAR(50) DEFAULT 'lottery',
                    cost DECIMAL(10,2) DEFAULT 0.00,
                    max_participants INTEGER,
                    current_participants INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'active',
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    ends_at TIMESTAMP,
                    winner_count INTEGER DEFAULT 1,
                    group_id BIGINT
                )
            """)
            
            # Etkinlik katılımları tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS event_participants (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    user_id BIGINT NOT NULL,
                    payment_amount DECIMAL(10,2) NOT NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    joined_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    UNIQUE(event_id, user_id)
                )
            """)
            
                        # Market ürünleri tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS market_products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    company_name VARCHAR(100) NOT NULL,
                    company_link VARCHAR(500),
                    product_name VARCHAR(200) NOT NULL,
                    category VARCHAR(100),
                    price DECIMAL(10,2) NOT NULL,
                    stock INTEGER DEFAULT 0,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Market siparişleri tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS market_orders (
                    id SERIAL PRIMARY KEY,
                    order_number VARCHAR(50) UNIQUE NOT NULL,
                    user_id BIGINT NOT NULL,
                    product_id INTEGER REFERENCES market_products(id),
                    quantity INTEGER DEFAULT 1,
                    total_price DECIMAL(10,2) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'delivered')),
                    admin_notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Eski unit_price kolonunu kaldır (eğer varsa)
            try:
                await conn.execute("ALTER TABLE market_orders DROP COLUMN IF EXISTS unit_price")
                logger.info("✅ Eski unit_price kolonu kaldırıldı")
            except Exception as e:
                logger.info(f"ℹ️ unit_price kolonu zaten yok: {e}")
            
            # Varsayılan rütbeleri ekle
            await conn.execute("""
                INSERT INTO user_ranks (rank_id, rank_name, min_points, max_points) 
                VALUES 
                    (1, 'Üye', 0.00, 0.00),
                    (2, 'Admin 1', 0.00, 0.00),
                    (3, 'Üst Yetkili - Admin 2', 0.00, 0.00),
                    (4, 'Super Admin', 0.00, 0.00)
                ON CONFLICT (rank_id) DO NOTHING
            """)
            
            # Varsayılan point ayarlarını ekle
            await conn.execute("""
                INSERT INTO point_settings (setting_key, setting_value, description) 
                VALUES 
                    ('daily_limit', 5.00, 'Günlük maksimum kazanılabilir point'),
                    ('point_per_message', 0.04, 'Mesaj başına kazanılan point'),
                    ('min_message_length', 5, 'Point kazanmak için minimum mesaj uzunluğu (YENİ: 5 harf)'),
                    ('flood_interval', 10, 'Mesajlar arası minimum saniye (flood önlemi)')
                ON CONFLICT (setting_key) DO NOTHING
            """)
            
                        # Bot durumu tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_status (
                    id SERIAL PRIMARY KEY,
                    status VARCHAR(255) NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Zamanlanmış mesajlar ayarları tablosu
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_messages_settings (
                    id SERIAL PRIMARY KEY,
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Varsayılan sistem ayarlarını ekle - YENİ EKLENDİ
            await conn.execute("""
                INSERT INTO system_settings (id, points_per_message, daily_limit, weekly_limit)
                VALUES (1, 0.04, 5.00, 20.00)
                ON CONFLICT (id) DO NOTHING
            """)
            
            logger.info("✅ Tüm tablolar başarıyla oluşturuldu/güncellendi")
            
    except Exception as e:
        logger.error(f"❌ Tablo oluşturma hatası: {e}")
        raise


async def insert_test_data() -> None:
    """Test verisi ekle"""
    if not db_pool:
        return
    
    async with db_pool.acquire() as conn:
        # Bot status
        await conn.execute("""
            INSERT INTO bot_status (status) 
            VALUES ('aiogram bot + point sistemi çalışıyor! 🚀') 
        """)
        
        # Test kullanıcıları ekle
        logger.info("🔍 Test kullanıcıları ekleniyor...")
        result = await conn.execute("""
            INSERT INTO users (user_id, first_name, username, kirve_points, is_registered, registration_date)
            VALUES 
            (8154732274, 'KirveHub', 'kirvehub', 0.00, TRUE, NOW()),
            (1234567890, 'TestUser', 'testuser', 0.00, TRUE, NOW()),
            (9876543210, 'DemoUser', 'demouser', 0.00, TRUE, NOW()),
            (6513506166, 'TestReplyUser', 'testreplyuser', 0.00, TRUE, NOW())
            ON CONFLICT (user_id) DO NOTHING
        """)
        logger.info(f"✅ Test kullanıcıları eklendi! Result: {result}")
        
        # Eklenen kullanıcıları kontrol et (sadece sayı)
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        logger.info(f"✅ Database'de toplam {user_count} kullanıcı var")
        
        # Test market ürünleri ekle (sadece yoksa)
        logger.info("🔍 Test market ürünleri kontrol ediliyor...")
        
        # Önce mevcut ürün sayısını kontrol et
        existing_count = await conn.fetchval("SELECT COUNT(*) FROM market_products")
        logger.info(f"🔍 Mevcut ürün sayısı: {existing_count}")
        
        if existing_count == 0:
            # Sadece hiç ürün yoksa ekle
            result = await conn.execute("""
                INSERT INTO market_products (name, company_name, product_name, price, stock, description, created_by, is_active)
                VALUES 
                ('Test Freespin Paketi', 'Test Casino', 'Test Freespin Paketi', 25.00, 10, 'Test casino için 100 freespin paketi', 8154732274, TRUE),
                ('Demo Bonus Paketi', 'Demo Casino', 'Demo Bonus Paketi', 15.00, 5, 'Demo casino için 50 bonus paketi', 8154732274, TRUE)
            """)
            logger.info(f"✅ Test market ürünleri eklendi! Result: {result}")
        else:
            # Duplicate ürünleri temizle (aynı isimde olanları)
            await conn.execute("""
                DELETE FROM market_products 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM market_products 
                    GROUP BY name, company_name
                )
            """)
            cleaned_count = await conn.fetchval("SELECT COUNT(*) FROM market_products")
            logger.info(f"✅ Duplicate ürünler temizlendi! Kalan ürün sayısı: {cleaned_count}")


# ==============================================
# USER FONKSİYONLARI
# ==============================================

async def save_user_info(user_id: int, username: str, first_name: str, last_name: str) -> None:
    """Kullanıcı bilgilerini kaydet/güncelle (henüz kayıt olmamış)"""
    if not db_pool:
        return
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, last_activity)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_activity = NOW()
            """, user_id, username, first_name, last_name)
            
    except Exception as e:
        logger.error(f"❌ User save hatası: {e}")


async def register_user(user_id: int) -> bool:
    """Kullanıcıyı sisteme kayıt et"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Kullanıcıyı kayıtlı olarak işaretle
            result = await conn.execute("""
                UPDATE users 
                SET is_registered = TRUE, 
                    registration_date = NOW(),
                    last_activity = NOW()
                WHERE user_id = $1
            """, user_id)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ User register hatası: {e}")
        return False


async def is_user_registered(user_id: int) -> bool:
    """Kullanıcının kayıtlı olup olmadığını kontrol et"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT is_registered FROM users 
                WHERE user_id = $1
            """, user_id)
            
            return result is True
            
    except Exception as e:
        logger.error(f"❌ Registration check hatası: {e}")
        return False


async def get_registered_users_count() -> int:
    """Kayıtlı kullanıcı sayısını al"""
    if not db_pool:
        return 0
    
    try:
        async with db_pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE is_registered = TRUE
            """)
            
            return count or 0
            
    except Exception as e:
        logger.error(f"❌ Registered users count hatası: {e}")
        return 0


async def unregister_user(user_id: int) -> bool:
    """Kullanıcının kaydını sil (test için)"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Kullanıcının kaydını sil
            result = await conn.execute("""
                UPDATE users 
                SET is_registered = FALSE, 
                    registration_date = NULL,
                    last_activity = NOW()
                WHERE user_id = $1
            """, user_id)
            
            logger.info(f"🗑️ Kullanıcı kaydı silindi - User: {user_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ User unregister hatası: {e}")
        return False


# ==============================================
# POINT SİSTEMİ FONKSİYONLARI
# ==============================================

async def get_user_info(user_id: int) -> Dict[str, Any]:
    """Kullanıcının tüm bilgilerini al"""
    if not db_pool:
        return {}
    
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT user_id, username, first_name, last_name, phone, email, 
                       interests, status, notes, kirve_points, daily_points, 
                       last_point_date, rank_id, total_messages, is_registered, 
                       registration_date, last_activity
                FROM users 
                WHERE user_id = $1
            """, user_id)
            
            if result:
                return {
                    "user_id": result["user_id"],
                    "username": result["username"],
                    "first_name": result["first_name"],
                    "last_name": result["last_name"],
                    "phone": result["phone"],
                    "email": result["email"],
                    "interests": result["interests"],
                    "status": result["status"],
                    "notes": result["notes"],
                    "kirve_points": float(result["kirve_points"]) if result["kirve_points"] else 0.0,
                    "daily_points": float(result["daily_points"]) if result["daily_points"] else 0.0,
                    "last_point_date": result["last_point_date"],
                    "rank_id": result["rank_id"] or 1,
                    "total_messages": result["total_messages"] or 0,
                    "is_registered": result["is_registered"],
                    "registration_date": result["registration_date"],
                    "last_activity": result["last_activity"]
                }
            return {}
            
    except Exception as e:
        logger.error(f"❌ Get user info hatası: {e}")
        return {}

async def get_user_points(user_id: int) -> Dict[str, Any]:
    """Kullanıcının point bilgilerini al"""
    if not db_pool:
        return {}
    
    start_time = datetime.now()
    success = False
    
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT kirve_points, daily_points, last_point_date, total_messages, rank_id
                FROM users 
                WHERE user_id = $1
            """, user_id)
            
            if result:
                success = True
                return {
                    "kirve_points": float(result["kirve_points"]) if result["kirve_points"] else 0.0,
                    "daily_points": float(result["daily_points"]) if result["daily_points"] else 0.0,
                    "last_point_date": result["last_point_date"],
                    "total_messages": result["total_messages"] or 0,
                    "rank_id": result["rank_id"] or 1
                }
            return {}
            
    except Exception as e:
        logger.error(f"❌ Get user points hatası: {e}")
        return {}
    finally:
        # Detaylı log
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        await log_database_operation(
            operation="get_user_points",
            table="users",
            success=success,
            duration_ms=duration_ms
        )

async def get_user_points_cached(user_id: int) -> Dict[str, Any]:
    """Kullanıcı point'lerini cache ile al"""
    try:
        from utils.memory_manager import memory_manager
        cache_manager = memory_manager.get_cache_manager()
        
        # Cache key
        cache_key = f"user_points_{user_id}"
        
        # Cache'den kontrol et
        cached_result = cache_manager.get_cache(cache_key)
        if cached_result:
            return cached_result
            
        # Database'den al
        pool = await get_db_pool()
        if not pool:
            return {}
            
        async with pool.acquire() as conn:
            user_data = await conn.fetchrow("""
                SELECT 
                    kirve_points, daily_points, total_messages, 
                    last_point_date, last_activity
                FROM users 
                WHERE user_id = $1
            """, user_id)
            
            # Haftalık point bilgisini al
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            weekly_points = await conn.fetchval("""
                SELECT COALESCE(SUM(points_earned), 0) 
                FROM daily_stats 
                WHERE user_id = $1 AND message_date >= $2
            """, user_id, week_start)
            
            if user_data:
                result = {
                    'kirve_points': float(user_data['kirve_points']),
                    'daily_points': float(user_data['daily_points']),
                    'weekly_points': float(weekly_points or 0),
                    'total_messages': user_data['total_messages'],
                    'last_point_date': user_data['last_point_date'],
                    'last_activity': user_data['last_activity']
                }
                
                # Cache'e kaydet (5 saniye TTL - daha kısa)
                cache_manager.set_cache(cache_key, result, ttl=5)
                return result
                
        return {}
        
    except Exception as e:
        logger.error(f"❌ Get user points cached hatası: {e}")
        return {}

async def add_points_to_user(user_id: int, points: float, group_id: int = None) -> bool:
    """Kullanıcıya point ekle"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Transaction başlat
            async with conn.transaction():
                today = date.today()
            
            # Sistem ayarlarını al (point_settings tablosundan)
            system_settings = await conn.fetchrow("""
                SELECT 
                    setting_value
                FROM point_settings 
                WHERE setting_key = 'daily_limit'
            """)
            
            # Varsayılan değerler
            daily_limit = 5.0
            weekly_limit = 20.0
            
            if system_settings:
                daily_limit = float(system_settings['setting_value'])
            
            # Günlük limit kontrolü
            daily_points = await conn.fetchval("""
                SELECT daily_points FROM users 
                WHERE user_id = $1 AND last_point_date = $2
            """, user_id, today)
            
            if daily_points and daily_points >= daily_limit:
                logger.info(f"⚠️ Günlük point limiti aşıldı - User: {user_id}, Daily: {daily_points}/{daily_limit}")
                return False
            
            # Haftalık limit kontrolü
            week_start = today - timedelta(days=today.weekday())
            weekly_points = await conn.fetchval("""
                SELECT COALESCE(SUM(points_earned), 0) 
                FROM daily_stats 
                WHERE user_id = $1 AND message_date >= $2
            """, user_id, week_start)
            
            if weekly_points and weekly_points >= weekly_limit:
                logger.info(f"⚠️ Haftalık point limiti aşıldı - User: {user_id}, Weekly: {weekly_points}/{weekly_limit}")
                return False
            
            # Point ekle
            result = await conn.execute("""
                UPDATE users 
                SET kirve_points = kirve_points + $2,
                    daily_points = CASE 
                        WHEN last_point_date = $3 THEN daily_points + $2
                        ELSE $2 
                    END,
                    last_point_date = $3,
                    total_messages = total_messages + 1,
                    last_activity = NOW()
                WHERE user_id = $1
            """, user_id, points, today)
            
            # Update sonucunu kontrol et
            logger.info(f"💎 Point ekleme sonucu: {result}")
            
            # Güncellenen satır sayısını kontrol et
            if result == "UPDATE 0":
                logger.warning(f"⚠️ Kullanıcı bulunamadı veya güncellenmedi - User: {user_id}")
                return False
            
            # Daily stats güncelle (basit INSERT)
            if group_id:
                try:
                    await conn.execute("""
                        INSERT INTO daily_stats (user_id, group_id, message_date, message_count, points_earned)
                        VALUES ($1, $2, $3, 1, $4)
                    """, user_id, group_id, today, points)
                except Exception as e:
                    logger.warning(f"⚠️ Daily stats INSERT hatası: {e}")
            
            # Cache'i temizle
            try:
                from utils.memory_manager import memory_manager
                cache_manager = memory_manager.get_cache_manager()
                cache_key = f"user_points_{user_id}"
                # Cache'i sil (farklı metod)
                if hasattr(cache_manager, 'clear_cache'):
                    cache_manager.clear_cache()
                elif hasattr(cache_manager, 'delete_cache'):
                    cache_manager.delete_cache(cache_key)
                else:
                    # Cache'i manuel olarak temizle
                    cache_manager._cache.pop(cache_key, None)
            except Exception as e:
                logger.warning(f"⚠️ Cache temizleme hatası: {e}")
            
            logger.info(f"💎 Sistem aktivitesi - User: {user_id}")
            return True
                
    except Exception as e:
        logger.error(f"❌ Add points hatası: {e}")
        return False


# ==============================================
# GRUP YÖNETİMİ FONKSİYONLARI
# ==============================================

async def register_group(group_id: int, group_name: str, group_username: str, registered_by: int) -> bool:
    """Grubu sisteme kayıt et"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO registered_groups (group_id, group_name, group_username, registered_by)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (group_id)
                DO UPDATE SET
                    group_name = EXCLUDED.group_name,
                    group_username = EXCLUDED.group_username,
                    is_active = TRUE
            """, group_id, group_name, group_username, registered_by)
            
            logger.info(f"✅ Grup kayıt edildi - Group: {group_name} ({group_id})")
            return True
            
    except Exception as e:
        logger.error(f"❌ Group register hatası: {e}")
        return False


async def is_group_registered(group_id: int) -> bool:
    """Grubun kayıtlı olup olmadığını kontrol et"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT is_active FROM registered_groups 
                WHERE group_id = $1
            """, group_id)
            
            return result is True
            
    except Exception as e:
        logger.error(f"❌ Group check hatası: {e}")
        return False


async def unregister_group(group_id: int) -> bool:
    """Grubu sistemden kaldır"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE registered_groups 
                SET is_active = FALSE, unregistered_at = NOW()
                WHERE group_id = $1
            """, group_id)
            
            if result == "UPDATE 1":
                logger.info(f"✅ Grup kaldırıldı - Group ID: {group_id}")
                return True
            else:
                logger.warning(f"⚠️ Grup bulunamadı veya zaten kaldırılmış - Group ID: {group_id}")
                return False
            
    except Exception as e:
        logger.error(f"❌ Group unregister hatası: {e}")
        return False


# ==============================================
# ADMIN & RANK FONKSİYONLARI
# ==============================================

async def get_user_rank(user_id: int) -> Dict[str, Any]:
    """Kullanıcının rütbe bilgilerini al"""
    if not db_pool:
        return {}
    
    try:
        # Admin kontrolü
        config = get_config()
        if user_id == config.ADMIN_USER_ID:
            return {
                "rank_name": "Super Admin",
                "rank_level": 10,
                "permissions": ["basic_commands", "register_group", "admin_panel", "delete_group", "manage_users"],
                "rank_id": 10
            }
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT ur.rank_name, ur.rank_id, u.rank_id
                FROM users u
                LEFT JOIN user_ranks ur ON u.rank_id = ur.rank_id
                WHERE u.user_id = $1
            """, user_id)
            
            if result:
                return {
                    "rank_name": result["rank_name"] or "Üye",
                    "rank_level": result["rank_id"] or 1,
                    "permissions": ["basic_commands"],  # Basit yetkiler
                    "rank_id": result["rank_id"] or 1
                }
            return {"rank_name": "Üye", "rank_level": 1, "permissions": ["basic_commands"], "rank_id": 1}
            
    except Exception as e:
        logger.error(f"❌ Get user rank hatası: {e}")
        return {"rank_name": "Üye", "rank_level": 1, "permissions": ["basic_commands"], "rank_id": 1}


async def has_permission(user_id: int, permission: str) -> bool:
    """Kullanıcının belirli bir yetkisi var mı kontrol et"""
    rank_info = await get_user_rank(user_id)
    permissions = rank_info.get("permissions", [])
    return permission in permissions


# ==============================================
# SİSTEM FONKSİYONLARI
# ==============================================

async def get_db_stats() -> Dict[str, Any]:
    """Database istatistiklerini al"""
    if not db_pool:
        return {"error": "Database bağlantısı yok!"}
    
    try:
        async with db_pool.acquire() as conn:
            # Son status
            last_status = await conn.fetchval("""
                SELECT status FROM bot_status 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            # Temel sayılar
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            registered_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_registered = TRUE")
            group_count = await conn.fetchval("SELECT COUNT(*) FROM registered_groups WHERE is_active = TRUE")
            
            # Point istatistikleri
            total_points = await conn.fetchval("SELECT SUM(kirve_points) FROM users WHERE is_registered = TRUE")
            
            return {
                "last_status": last_status,
                "total_users": user_count or 0,
                "registered_users": registered_count or 0,
                "active_groups": group_count or 0,
                "total_points_in_system": float(total_points) if total_points else 0.0,
                "database_active": True
            }
            
    except Exception as e:
        logger.error(f"❌ Database stats hatası: {e}")
        return {"error": str(e), "database_active": False}


async def get_registered_groups() -> list:
    """Kayıtlı grupları getir"""
    if not db_pool:
        return []
    
    try:
        async with db_pool.acquire() as conn:
            groups = await conn.fetch("""
                SELECT group_id, group_name, group_username, registration_date as registered_at
                FROM registered_groups 
                WHERE is_active = true
                ORDER BY registration_date ASC
            """)
            
            result = [dict(group) for group in groups]
            
            # Eğer hiç grup yoksa test grupları ekle
            if not result:
                logger.info("📝 Test grupları ekleniyor...")
                test_groups = [
                    (-1001234567890, "KirveHub Ana Grup", "kirvehub", 1),
                    (-1001987654321, "KirveHub Test Grup", "kirvehub_test", 1)
                ]
                
                for group_id, group_name, group_username, registered_by in test_groups:
                    await conn.execute("""
                        INSERT INTO registered_groups (group_id, group_name, group_username, registered_by)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (group_id) DO NOTHING
                    """, group_id, group_name, group_username, registered_by)
                
                # Test gruplarını tekrar getir
                groups = await conn.fetch("""
                    SELECT group_id, group_name, group_username, registration_date as registered_at
                    FROM registered_groups 
                    WHERE is_active = true
                    ORDER BY registration_date ASC
                """)
                result = [dict(group) for group in groups]
            
            return result
            
    except Exception as e:
        logger.error(f"❌ Get registered groups hatası: {e}")
        return []

async def close_database() -> None:
    """Database bağlantısını kapat"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("🗄️ Database bağlantısı kapatıldı.")
        db_pool = None

# ==============================================
# EVENT MANAGEMENT FONKSİYONLARI
# ==============================================

async def can_user_join_event(user_id: int, event_id: int) -> bool:
    """Kullanıcı etkinliğe katılabilir mi kontrol et"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Daha önce katılmış mı?
            existing = await conn.fetchval("""
                SELECT id FROM event_participations 
                WHERE user_id = $1 AND event_id = $2 AND status = 'active'
            """, user_id, event_id)
            
            # Etkinlik aktif mi?
            event_active = await conn.fetchval("""
                SELECT id FROM events 
                WHERE id = $1 AND status = 'active'
            """, event_id)
            
            return existing is None and event_active is not None
            
    except Exception as e:
        logger.error(f"❌ Can user join event hatası: {e}")
        return False

async def get_user_event_participation(user_id: int, event_id: int) -> dict:
    """Kullanıcının etkinlik katılım bilgilerini getir"""
    if not db_pool:
        return {}
    
    try:
        async with db_pool.acquire() as conn:
            participation = await conn.fetchrow("""
                SELECT user_id, event_id, payment_amount, status, joined_at 
                FROM event_participations 
                WHERE user_id = $1 AND event_id = $2
            """, user_id, event_id)
            
            if participation:
                return dict(participation)
            return {}
            
    except Exception as e:
        logger.error(f"❌ Get user event participation hatası: {e}")
        return {}

async def get_event_participant_count(event_id: int) -> int:
    """Etkinlik katılımcı sayısını getir"""
    if not db_pool:
        return 0
    
    try:
        async with db_pool.acquire() as conn:
            # Önce event_participations tablosundan kontrol et
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM event_participations 
                WHERE event_id = $1 AND status = 'active'
            """, event_id)
            
            if count and count > 0:
                logger.info(f"✅ Event participant count (participations): {count}")
                return count
            
            # Eğer event_participations'da yoksa event_participants'tan kontrol et
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM event_participants 
                WHERE event_id = $1 AND status = 'active'
            """, event_id)
            
            logger.info(f"✅ Event participant count (participants): {count}")
            return count or 0
            
    except Exception as e:
        logger.error(f"❌ Get event participant count hatası: {e}")
        return 0

# ==============================================
# EVENT PARTICIPATION FONKSİYONLARI
# ==============================================

async def join_event(user_id: int, event_id: int, payment_amount: float) -> bool:
    """Etkinliğe katılım kaydet"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Daha önce katılım var mı kontrol et
            existing = await conn.fetchval("""
                SELECT id FROM event_participants 
                WHERE user_id = $1 AND event_id = $2
            """, user_id, event_id)
            
            if existing:
                logger.warning(f"⚠️ Zaten katılım var: User {user_id} -> Event {event_id}")
                return False
            
            # Katılımı kaydet
            await conn.execute("""
                INSERT INTO event_participants (user_id, event_id, payment_amount)
                VALUES ($1, $2, $3)
            """, user_id, event_id, payment_amount)
            
            logger.info(f"✅ Event katılımı kaydedildi: User {user_id} -> Event {event_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Join event hatası: {e}")
        return False

async def withdraw_from_event(user_id: int, event_id: int) -> bool:
    """Etkinlikten çekilme"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Katılımı bul
            participation = await conn.fetchrow("""
                SELECT id, payment_amount, status FROM event_participants 
                WHERE user_id = $1 AND event_id = $2 AND status = 'active'
            """, user_id, event_id)
            
            if not participation:
                logger.warning(f"⚠️ Aktif katılım bulunamadı: User {user_id} -> Event {event_id}")
                return False
            
            # Çekilmeyi kaydet
            await conn.execute("""
                UPDATE event_participants 
                SET status = 'withdrawn'
                WHERE id = $1
            """, participation['id'])
            
            logger.info(f"✅ Event çekilme kaydedildi: User {user_id} -> Event {event_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Withdraw event hatası: {e}")
        return False

async def get_user_event_participation(user_id: int, event_id: int) -> Optional[Dict]:
    """Kullanıcının etkinlik katılım bilgilerini getir"""
    if not db_pool:
        return None
    
    try:
        async with db_pool.acquire() as conn:
            participation = await conn.fetchrow("""
                SELECT id, user_id, event_id, joined_at, payment_amount, status
                FROM event_participants 
                WHERE user_id = $1 AND event_id = $2
            """, user_id, event_id)
            
            if participation:
                return dict(participation)
            return None
            
    except Exception as e:
        logger.error(f"❌ Get participation hatası: {e}")
        return None

async def can_user_join_event(user_id: int, event_id: int) -> bool:
    """Kullanıcı etkinliğe katılabilir mi kontrol et"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Daha önce katılım var mı
            existing = await conn.fetchval("""
                SELECT id FROM event_participants 
                WHERE user_id = $1 AND event_id = $2
            """, user_id, event_id)
            
            if existing:
                return False
            
            # Etkinlik aktif mi
            event = await conn.fetchrow("""
                SELECT id, is_active FROM events WHERE id = $1
            """, event_id)
            
            if not event or not event['is_active']:
                return False
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Can join event hatası: {e}")
        return False

async def get_event_participant_count(event_id: int) -> int:
    """Etkinlik katılımcı sayısını getir"""
    if not db_pool:
        return 0
    
    try:
        async with db_pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM event_participants 
                WHERE event_id = $1 AND status = 'active'
            """, event_id)
            
            return count or 0
            
    except Exception as e:
        logger.error(f"❌ Get participant count hatası: {e}")
        return 0

async def get_event_info_for_end(event_id: int) -> dict:
    """Etkinlik bilgilerini al (end için)"""
    if not db_pool:
        return {}
    
    try:
        async with db_pool.acquire() as conn:
            event = await conn.fetchrow("""
                SELECT id, event_name, max_participants, event_type, created_by
                FROM events WHERE id = $1
            """, event_id)
            
            if event:
                return dict(event)
            return {}
            
    except Exception as e:
        logger.error(f"❌ Get event info for end hatası: {e}")
        return {}

async def get_event_winners(event_id: int, winner_count: int) -> list:
    """Etkinlik kazananlarını seç - Gelişmiş algoritma"""
    if not db_pool:
        return []
    
    try:
        async with db_pool.acquire() as conn:
            # Katılımcı sayısını kontrol et
            participant_count = await conn.fetchval("""
                SELECT COUNT(*) FROM event_participants 
                WHERE event_id = $1 AND status = 'active'
            """, event_id)
            
            logger.info(f"🔍 Event {event_id} - get_event_winners participant_count: {participant_count}")
            
            if participant_count == 0:
                logger.info(f"🎯 No participants for event: {event_id}")
                return []
            
            # Kazanan sayısını katılımcı sayısına göre ayarla
            actual_winners = min(winner_count, participant_count)
            
            # Kazanan seçim algoritması
            winners = await conn.fetch("""
                WITH weighted_participants AS (
                    SELECT 
                        ep.user_id, 
                        ep.payment_amount, 
                        u.first_name, 
                        u.last_name, 
                        u.username,
                        -- Katılım miktarına göre ağırlık (daha fazla ödeyen daha şanslı)
                        (ep.payment_amount * 10 + RANDOM()) as weight
                    FROM event_participants ep
                    JOIN users u ON ep.user_id = u.user_id
                    WHERE ep.event_id = $1 AND ep.status = 'active'
                )
                SELECT user_id, payment_amount, first_name, last_name, username
                FROM weighted_participants
                ORDER BY weight DESC
                LIMIT $2
            """, event_id, actual_winners)
            
            logger.info(f"🔍 Event {event_id} - event_participants'tan kazananlar: {winners}")
            
            result = [dict(winner) for winner in winners]
            logger.info(f"🎯 Get event winners - Event: {event_id}, Winners: {len(result)}, Participants: {participant_count}, Details: {result}")
            
            result = [dict(winner) for winner in winners]
            logger.info(f"🎯 Get event winners - Event: {event_id}, Winners: {len(result)}, Participants: {participant_count}")
            return result
            
    except Exception as e:
        logger.error(f"❌ Get event winners hatası: {e}")
        return []

async def get_latest_active_event_in_group(group_id: int) -> Optional[int]:
    """Belirtilen gruptaki son aktif etkinliğin ID'sini getir"""
    if not db_pool:
        return None
    
    try:
        async with db_pool.acquire() as conn:
            event_id = await conn.fetchval("""
                SELECT id FROM events 
                WHERE group_id = $1 AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """, group_id)
            
            return event_id
            
    except Exception as e:
        logger.error(f"❌ Get latest active event hatası: {e}")
        return None

async def end_event(event_id: int) -> bool:
    """Etkinliği bitir ve kazananları seç - Point dağıtımı ile"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Etkinlik bilgilerini al
            event = await conn.fetchrow("""
                SELECT id, event_name, max_participants, created_by FROM events 
                WHERE id = $1 AND is_active = TRUE
            """, event_id)
            
            if not event:
                return False
            
            # Toplam katılımcı sayısını al
            participant_count = await conn.fetchval("""
                SELECT COUNT(*) FROM event_participants 
                WHERE event_id = $1 AND status = 'active'
            """, event_id)
            
            logger.info(f"🔍 Event {event_id} - event_participants count: {participant_count}")
            
            # Detaylı katılımcı bilgilerini logla
            participants = await conn.fetch("""
                SELECT user_id, payment_amount, status FROM event_participants 
                WHERE event_id = $1
            """, event_id)
            logger.info(f"🔍 Event {event_id} - All participants: {participants}")
            
            if participant_count == 0:
                # Katılımcı yoksa etkinliği iptal et
                await conn.execute("""
                    UPDATE events SET is_active = FALSE
                    WHERE id = $1
                """, event_id)
                logger.info(f"✅ Event iptal edildi (katılımcı yok): {event_id}")
                return True
            
            # Etkinliği bitir (kazanan seçimi ve point dağıtımı end_lottery_command'da yapılacak)
            await conn.execute("""
                UPDATE events SET is_active = FALSE
                WHERE id = $1
            """, event_id)
            
            logger.info(f"✅ Event bitirildi (sadece durum güncellendi): {event_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ End event hatası: {e}")
        return False 

async def cancel_event(event_id: int) -> bool:
    """Etkinliği iptal et ve katılımcılara point geri ver"""
    if not db_pool:
        return False
    
    try:
        async with db_pool.acquire() as conn:
            # Etkinlik bilgilerini al
            event = await conn.fetchrow("""
                SELECT id, event_name, created_by FROM events 
                WHERE id = $1 AND is_active = TRUE
            """, event_id)
            
            if not event:
                return False
            
            # Katılımcıları al
            participants = await conn.fetch("""
                SELECT user_id, payment_amount FROM event_participants 
                WHERE event_id = $1 AND status = 'active'
            """, event_id)
            
            # Etkinliği iptal et
            await conn.execute("""
                UPDATE events SET is_active = FALSE
                WHERE id = $1
            """, event_id)
            
            # Katılımcılara point geri ver
            for participant in participants:
                await add_points_to_user(participant['user_id'], participant['payment_amount'], event['group_id'])
                logger.info(f"💰 Point geri verildi: User {participant['user_id']}, Amount: {participant['payment_amount']:.2f}")
            
            # Katılımcıları iptal et
            await conn.execute("""
                UPDATE event_participants 
                SET status = 'cancelled'
                WHERE event_id = $1 AND status = 'active'
            """, event_id)
            
            logger.info(f"✅ Event iptal edildi: {event_id} - {len(participants)} katılımcıya point geri verildi")
            return True
            
    except Exception as e:
        logger.error(f"❌ Cancel event hatası: {e}")
        return False

async def get_event_status(event_id: int) -> dict:
    """Etkinlik durumunu getir"""
    if not db_pool:
        return {}
    
    try:
        async with db_pool.acquire() as conn:
            # Etkinlik bilgilerini al
            event = await conn.fetchrow("""
                SELECT id, event_name, max_participants, is_active, created_at
                FROM events WHERE id = $1
            """, event_id)
            
            if not event:
                return {}
            
            # Katılımcı sayısını al
            participant_count = await conn.fetchval("""
                SELECT COUNT(*) FROM event_participants 
                WHERE event_id = $1 AND status = 'active'
            """, event_id)
            
            return {
                'id': event['id'],
                'title': event['event_name'],
                'entry_cost': 0,  # Şimdilik 0
                'max_winners': event['max_participants'],
                'status': 'active' if event['is_active'] else 'completed',
                'participant_count': participant_count,
                'created_at': event['created_at'].strftime('%d.%m.%Y %H:%M') if event['created_at'] else 'Bilinmiyor',
                'completed_at': None
            }
            
    except Exception as e:
        logger.error(f"❌ Get event status hatası: {e}")
        return {}

# Market sistemi için gelişmiş fonksiyonlar
async def get_market_products_with_details() -> list:
    """Market ürünlerini detaylarıyla getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return []
        
        async with pool.acquire() as conn:
            products = await conn.fetch("""
                SELECT 
                    p.id,
                    p.name,
                    p.description,
                    p.company_name,
                    p.price,
                    p.stock,
                    p.is_active,
                    p.created_at,
                    p.category as category_name
                FROM market_products p
                WHERE p.is_active = TRUE
                ORDER BY p.created_at DESC
            """)
            
            return [dict(p) for p in products]
            
    except Exception as e:
        logger.error(f"❌ Market ürünleri getirme hatası: {e}")
        return []

async def get_user_orders_with_details(user_id: int, limit: int = 10) -> list:
    """Kullanıcının siparişlerini detaylarıyla getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return []
        
        async with pool.acquire() as conn:
            orders = await conn.fetch("""
                SELECT 
                    o.id,
                    o.order_number,
                    o.total_price,
                    o.status,
                    o.created_at,
                    o.updated_at,
                    o.admin_notes,
                    p.name as product_name,
                    p.company_name,
                    p.description as product_description
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                WHERE o.user_id = $1
                ORDER BY o.created_at DESC
                LIMIT $2
            """, user_id, limit)
            
            return [dict(o) for o in orders]
            
    except Exception as e:
        logger.error(f"❌ Kullanıcı siparişleri getirme hatası: {e}")
        return []

async def get_pending_orders_with_details() -> list:
    """Bekleyen siparişleri detaylarıyla getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return []
        
        async with pool.acquire() as conn:
            orders = await conn.fetch("""
                SELECT 
                    o.id,
                    o.order_number,
                    o.total_price,
                    o.status,
                    o.created_at,
                    o.admin_notes,
                    p.name as product_name,
                    p.company_name,
                    p.description as product_description,
                    u.first_name,
                    u.username,
                    u.user_id
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.status = 'pending'
                ORDER BY o.created_at ASC
            """)
            
            return [dict(o) for o in orders]
            
    except Exception as e:
        logger.error(f"❌ Bekleyen siparişler getirme hatası: {e}")
        return []

async def get_market_statistics() -> dict:
    """Market istatistiklerini getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {}
        
        async with pool.acquire() as conn:
            # Toplam ürün sayısı
            total_products = await conn.fetchval("""
                SELECT COUNT(*) FROM market_products WHERE is_active = TRUE
            """)
            
            # Toplam sipariş sayısı
            total_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders
            """)
            
            # Bekleyen sipariş sayısı
            pending_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders WHERE status = 'pending'
            """)
            
            # Onaylanan sipariş sayısı
            approved_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders WHERE status = 'approved'
            """)
            
            # Reddedilen sipariş sayısı
            rejected_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders WHERE status = 'rejected'
            """)
            
            # Toplam satış tutarı
            total_sales = await conn.fetchval("""
                SELECT COALESCE(SUM(total_price), 0) FROM market_orders WHERE status = 'approved'
            """)
            
            # Bugünkü sipariş sayısı
            today_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            
            return {
                'total_products': total_products,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'approved_orders': approved_orders,
                'rejected_orders': rejected_orders,
                'total_sales': float(total_sales) if total_sales else 0.0,
                'today_orders': today_orders
            }
            
    except Exception as e:
        logger.error(f"❌ Market istatistikleri getirme hatası: {e}")
        return {}

async def update_order_status(order_number: str, status: str, admin_notes: str = None) -> bool:
    """Sipariş durumunu güncelle"""
    try:
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE market_orders 
                SET status = $1, admin_notes = $2, updated_at = NOW()
                WHERE order_number = $3
            """, status, admin_notes, order_number)
            
            logger.info(f"✅ Sipariş durumu güncellendi: {order_number} -> {status}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Sipariş durumu güncelleme hatası: {e}")
        return False

async def get_user_market_history(user_id: int) -> dict:
    """Kullanıcının market geçmişini getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {}
        
        async with pool.acquire() as conn:
            # Toplam sipariş sayısı
            total_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders WHERE user_id = $1
            """, user_id)
            
            # Toplam harcama
            total_spent = await conn.fetchval("""
                SELECT COALESCE(SUM(total_price), 0) FROM market_orders WHERE user_id = $1
            """, user_id)
            
            # Onaylanan sipariş sayısı
            approved_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders 
                WHERE user_id = $1 AND status = 'approved'
            """, user_id)
            
            # Son sipariş tarihi
            last_order = await conn.fetchval("""
                SELECT created_at FROM market_orders 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT 1
            """, user_id)
            
            return {
                'total_orders': total_orders,
                'total_spent': float(total_spent) if total_spent else 0.0,
                'approved_orders': approved_orders,
                'last_order_date': last_order
            }
            
    except Exception as e:
        logger.error(f"❌ Kullanıcı market geçmişi getirme hatası: {e}")
        return {}

async def get_product_by_id(product_id: int) -> dict:
    """Ürün detaylarını getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {}
        
        async with pool.acquire() as conn:
            product = await conn.fetchrow("""
                SELECT 
                    p.id,
                    p.product_name,
                    p.description,
                    p.company_name,
                    p.price,
                    p.stock,
                    p.is_active,
                    p.created_at,
                    c.name as category_name
                FROM market_products p
                LEFT JOIN market_categories c ON p.category_id = c.id
                WHERE p.id = $1 AND p.is_active = TRUE
            """, product_id)
            
            return dict(product) if product else {}
            
    except Exception as e:
        logger.error(f"❌ Ürün detayı getirme hatası: {e}")
        return {}

async def check_product_stock(product_id: int) -> int:
    """Ürün stoğunu kontrol et"""
    try:
        pool = await get_db_pool()
        if not pool:
            return 0
        
        async with pool.acquire() as conn:
            stock = await conn.fetchval("""
                SELECT stock FROM market_products 
                WHERE id = $1 AND is_active = TRUE
            """, product_id)
            
            return stock if stock else 0
            
    except Exception as e:
        logger.error(f"❌ Ürün stok kontrolü hatası: {e}")
        return 0

async def decrease_product_stock(product_id: int, quantity: int = 1) -> bool:
    """Ürün stoğunu azalt"""
    try:
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE market_products 
                SET stock = stock - $1 
                WHERE id = $2 AND stock >= $1
            """, quantity, product_id)
            
            return "UPDATE 1" in result
            
    except Exception as e:
        logger.error(f"❌ Ürün stok azaltma hatası: {e}")
        return False

async def get_order_by_number(order_number: str) -> dict:
    """Sipariş numarasına göre sipariş detaylarını getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {}
        
        async with pool.acquire() as conn:
            order = await conn.fetchrow("""
                SELECT 
                    o.id,
                    o.order_number,
                    o.user_id,
                    o.product_id,
                    o.quantity,
                    o.total_price,
                    o.status,
                    o.admin_notes,
                    o.created_at,
                    o.updated_at,
                    p.name as product_name,
                    p.company_name,
                    p.description as product_description,
                    u.first_name,
                    u.username
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.order_number = $1
            """, order_number)
            
            return dict(order) if order else {}
            
    except Exception as e:
        logger.error(f"❌ Sipariş detayı getirme hatası: {e}")
        return {} 

async def get_user_registered_cached(user_id: int) -> bool:
    """Kullanıcı kayıt durumunu cache ile kontrol et"""
    try:
        from utils.memory_manager import memory_manager
        cache_manager = memory_manager.get_cache_manager()
        
        # Cache key
        cache_key = f"user_registered_{user_id}"
        
        # Cache'den kontrol et
        cached_result = cache_manager.get_cache(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Database'den kontrol et
        pool = await get_db_pool()
        if not pool:
            return False
            
        async with pool.acquire() as conn:
            is_registered = await conn.fetchval("""
                SELECT is_registered FROM users WHERE user_id = $1
            """, user_id)
            
            result = bool(is_registered)
            
            # Cache'e kaydet (60 saniye TTL)
            cache_manager.set_cache(cache_key, result, ttl=60)
            return result
            
    except Exception as e:
        logger.error(f"❌ Is user registered cached hatası: {e}")
        return False

async def get_db_pool_with_retry(max_retries: int = 3):
    """Database pool with retry mechanism"""
    for attempt in range(max_retries):
        try:
            pool = await get_db_pool()
            if pool:
                # Pool'u test et
                async with asyncio.timeout(3.0):
                    async with pool.acquire() as conn:
                        await conn.execute("SELECT 1")
                logger.info(f"✅ Database pool hazır (attempt {attempt + 1})")
                return pool
        except Exception as e:
            logger.warning(f"⚠️ Database pool attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error("❌ Database pool tüm denemeler başarısız!")
                return None
    
    return None

async def execute_query_with_retry(query: str, *args, max_retries: int = 2, timeout: float = 8.0):
    """Query execution with retry mechanism"""
    for attempt in range(max_retries):
        try:
            pool = await get_db_pool_with_retry()
            if not pool:
                return None
                
            async with pool.acquire() as conn:
                async with conn.transaction():
                    result = await conn.fetch(query, *args, timeout=timeout)
                    return result
                    
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Query timeout (attempt {attempt + 1}): {query[:50]}...")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
            else:
                logger.error(f"❌ Query timeout after {max_retries} attempts")
                return None
        except Exception as e:
            logger.warning(f"⚠️ Query error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
            else:
                logger.error(f"❌ Query failed after {max_retries} attempts")
                return None 

# =============================
# DİNAMİK KOMUT TABLOSU
# =============================

async def create_custom_commands_table():
    """Dinamik komutlar için tabloyu oluşturur (varsa atla)"""
    pool = await get_db_pool()
    if not pool:
        return
    async with pool.acquire() as conn:
        # Tablo var mı kontrol et
        table_exists = await conn.fetchval('''
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'custom_commands'
            )
        ''')
        
        if not table_exists:
            # Tablo yoksa oluştur
            await conn.execute('''
            CREATE TABLE custom_commands (
                id SERIAL PRIMARY KEY,
                command_name VARCHAR(64) UNIQUE NOT NULL,
                scope SMALLINT NOT NULL, -- 1: grup, 2: özel, 3: ikisi
                reply_text TEXT NOT NULL,
                button_text VARCHAR(128),
                button_url VARCHAR(256),
                created_by BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
            ''')
            logger.info("✅ Custom commands tablosu oluşturuldu")
        else:
            # Tablo varsa eksik kolonları ekle
            try:
                await conn.execute('ALTER TABLE custom_commands ADD COLUMN IF NOT EXISTS reply_text TEXT')
                await conn.execute('ALTER TABLE custom_commands ADD COLUMN IF NOT EXISTS scope SMALLINT DEFAULT 3')
                await conn.execute('ALTER TABLE custom_commands ADD COLUMN IF NOT EXISTS button_text VARCHAR(128)')
                await conn.execute('ALTER TABLE custom_commands ADD COLUMN IF NOT EXISTS button_url VARCHAR(256)')
                await conn.execute('ALTER TABLE custom_commands ADD COLUMN IF NOT EXISTS created_by BIGINT')
                await conn.execute('ALTER TABLE custom_commands ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()')
                logger.info("✅ Custom commands tablosu güncellendi")
            except Exception as e:
                logger.warning(f"⚠️ Tablo güncelleme hatası: {e}")

async def add_custom_command(command_name: str, scope: int, response_message: str, button_text: str, button_url: str, created_by: int) -> bool:
    pool = await get_db_pool()
    if not pool:
        return False
    async with pool.acquire() as conn:
        try:
            await conn.execute('''
                INSERT INTO custom_commands (command_name, scope, response_message, button_text, button_url, created_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (command_name, scope) DO UPDATE SET
                    response_message = EXCLUDED.response_message,
                    button_text = EXCLUDED.button_text,
                    button_url = EXCLUDED.button_url,
                    created_by = EXCLUDED.created_by,
                    updated_at = NOW()
            ''', command_name, scope, response_message, button_text, button_url, created_by)
            logger.info(f"✅ Dinamik komut kaydedildi: {command_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Dinamik komut ekleme hatası: {e}")
            return False

async def get_custom_command(command_name: str, scope: int) -> dict:
    pool = await get_db_pool()
    if not pool:
        return None
    async with pool.acquire() as conn:
        cmd = await conn.fetchrow('''
            SELECT * FROM custom_commands WHERE command_name = $1 AND (scope = $2 OR scope = 3) AND is_active = TRUE
        ''', command_name, scope)
        
        if cmd:
            logger.info(f"✅ Database'den komut bulundu - Command: {command_name}, Scope: {scope}")
        else:
            logger.info(f"❌ Database'de komut bulunamadı - Command: {command_name}, Scope: {scope}")
            
        return dict(cmd) if cmd else None

async def list_custom_commands() -> list:
    pool = await get_db_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        cmds = await conn.fetch('''
            SELECT 
                id, command_name, scope, response_message, 
                button_text, button_url, created_by, created_at, is_active
            FROM custom_commands 
            ORDER BY created_at DESC
        ''')
        return [dict(cmd) for cmd in cmds]

async def delete_custom_command(command_name: str) -> bool:
    """Dinamik komutu sil"""
    pool = await get_db_pool()
    if not pool:
        return False
    async with pool.acquire() as conn:
        try:
            result = await conn.execute('''
                DELETE FROM custom_commands WHERE command_name = $1
            ''', command_name)
            return result == "DELETE 1"
        except Exception as e:
            logger.error(f"❌ Dinamik komut silme hatası: {e}")
            return False

async def delete_custom_command_by_id(command_id: int) -> bool:
    """ID ile dinamik komutu sil"""
    pool = await get_db_pool()
    if not pool:
        return False
    async with pool.acquire() as conn:
        try:
            result = await conn.execute('''
                DELETE FROM custom_commands WHERE id = $1
            ''', command_id)
            return result == "DELETE 1"
        except Exception as e:
            logger.error(f"❌ ID ile komut silme hatası: {e}")
            return False

# =============================
# ADMIN YETKİ YÖNETİMİ - MODÜLER YAPIDA (admin_permission_manager.py)
# =============================
# Bu fonksiyonlar artık handlers/admin_permission_manager.py dosyasında bulunuyor
# Modüler yapı için ayrı dosyaya taşındı 

async def get_today_stats(user_id: int) -> Dict[str, Any]:
    """Bugünkü kullanıcı istatistikleri"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {'message_count': 0, 'points_earned': 0.0, 'last_activity': 'Bilinmiyor'}
            
        async with pool.acquire() as conn:
            today = date.today()
            
            # Bugünkü mesaj sayısını doğru hesapla (tüm gruplardan topla)
            today_messages = await conn.fetchval("""
                SELECT COALESCE(SUM(message_count), 0) 
                FROM daily_stats 
                WHERE user_id = $1 AND message_date = $2
            """, user_id, today)
            
            # Bugünkü kazanılan pointler
            today_points = await conn.fetchval("""
                SELECT COALESCE(SUM(points_earned), 0) 
                FROM daily_stats 
                WHERE user_id = $1 AND message_date = $2
            """, user_id, today)
            
            # Son aktivite
            last_activity = await conn.fetchval("""
                SELECT last_activity FROM users WHERE user_id = $1
            """, user_id)
            
            # Son aktiviteyi formatla
            if last_activity:
                now = datetime.now()
                time_diff = now - last_activity
                
                if time_diff.days > 0:
                    activity_text = f"{time_diff.days} gün önce"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    activity_text = f"{hours} saat önce"
                elif time_diff.seconds > 60:
                    minutes = time_diff.seconds // 60
                    activity_text = f"{minutes} dakika önce"
                else:
                    activity_text = "Az önce"
            else:
                activity_text = "Bilinmiyor"
            
            return {
                'message_count': today_messages or 0,
                'points_earned': float(today_points) if today_points else 0.0,
                'last_activity': activity_text
            }
            
    except Exception as e:
        logger.error(f"❌ Today stats hatası: {e}")
        return {
            'message_count': 0,
            'points_earned': 0.0,
            'last_activity': 'Hata'
        }


async def get_market_history(user_id: int) -> Dict[str, Any]:
    """Kullanıcının market geçmişi"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {'total_orders': 0, 'total_spent': 0.0, 'approved_orders': 0, 'last_order_date': 'Hiç sipariş yok'}
            
        async with pool.acquire() as conn:
            # Market geçmişi
            market_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total_price), 0) as total_spent,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_orders,
                    MAX(created_at) as last_order_date
                FROM market_orders 
                WHERE user_id = $1
            """, user_id)
            
            if not market_stats:
                return {'total_orders': 0, 'total_spent': 0.0, 'approved_orders': 0, 'last_order_date': 'Hiç sipariş yok'}
                
            last_order_date = market_stats['last_order_date']
            if last_order_date:
                last_order_date = last_order_date.strftime('%d.%m.%Y')
            else:
                last_order_date = 'Hiç sipariş yok'
                
            return {
                'total_orders': market_stats['total_orders'] or 0,
                'total_spent': float(market_stats['total_spent']) if market_stats['total_spent'] else 0.0,
                'approved_orders': market_stats['approved_orders'] or 0,
                'last_order_date': last_order_date
            }
            
    except Exception as e:
        logger.error(f"❌ Market history hatası: {e}")
        return {'total_orders': 0, 'total_spent': 0.0, 'approved_orders': 0, 'last_order_date': 'Hiç sipariş yok'}


async def get_system_stats() -> Dict[str, Any]:
    """Sistem istatistikleri"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {'total_users': 0, 'registered_users': 0, 'active_groups': 0}
            
        async with pool.acquire() as conn:
            # Sistem istatistikleri
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN is_registered = TRUE THEN 1 END) as registered_users,
                    (SELECT COUNT(*) FROM registered_groups WHERE is_active = TRUE) as active_groups
                FROM users
            """)
            
            if not stats:
                return {'total_users': 0, 'registered_users': 0, 'active_groups': 0}
                
            return {
                'total_users': stats['total_users'] or 0,
                'registered_users': stats['registered_users'] or 0,
                'active_groups': stats['active_groups'] or 0
            }
            
    except Exception as e:
        logger.error(f"❌ System stats hatası: {e}")
        return {'total_users': 0, 'registered_users': 0, 'active_groups': 0}

async def get_all_active_products() -> list:
    """Aktif tüm ürünleri getir"""
    if not db_pool:
        return []
    
    try:
        async with db_pool.acquire() as conn:
            products = await conn.fetch("""
                SELECT id, product_name, description, company_name, price, stock, is_active
                FROM market_products 
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            """)
            
            return [dict(product) for product in products]
            
    except Exception as e:
        logger.error(f"❌ Get all active products hatası: {e}")
        return []


async def delete_user_account(user_id: int) -> bool:
    """Kullanıcı hesabını tamamen sil"""
    try:
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool bulunamadı")
            return False
            
        async with pool.acquire() as conn:
            # Transaction başlat
            async with conn.transaction():
                # Önce kullanıcının var olup olmadığını kontrol et
                user_exists = await conn.fetchval("""
                    SELECT COUNT(*) FROM users WHERE user_id = $1
                """, user_id)
                
                if user_exists == 0:
                    logger.warning(f"⚠️ Kullanıcı zaten mevcut değil - User ID: {user_id}")
                    return True  # Zaten silinmiş sayılır
                
                # Kullanıcının tüm verilerini sil
                
                # 1. Market siparişlerini sil
                await conn.execute("""
                    DELETE FROM market_orders WHERE user_id = $1
                """, user_id)
                
                # 2. Event katılımlarını sil
                await conn.execute("""
                    DELETE FROM event_participants WHERE user_id = $1
                """, user_id)
                
                # 3. Custom commands'ları sil (bu kullanıcı tarafından oluşturulan)
                await conn.execute("""
                    DELETE FROM custom_commands WHERE created_by = $1
                """, user_id)
                
                # 4. Kullanıcı bilgilerini sil
                result = await conn.execute("""
                    DELETE FROM users WHERE user_id = $1
                """, user_id)
                
                logger.critical(f"🚨 Kullanıcı hesabı tamamen silindi - User ID: {user_id}")
                return True
                    
    except Exception as e:
        logger.error(f"❌ Delete user account hatası: {e}")
        return False