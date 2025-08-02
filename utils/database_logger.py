#!/usr/bin/env python3
"""
🗄️ Veritabanı Log Sistemi - SQL bağlantı ve tablo durumlarını loglar
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from asyncpg import Connection, Pool

from utils.logger import log_system, log_error, log_warning, log_info

class DatabaseLogger:
    """Veritabanı log sistemi"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def log_connection_attempt(self, database_url: str):
        """Bağlantı denemesi logla"""
        try:
            log_system(f"🔌 Database bağlantı denemesi: {database_url.split('@')[1] if '@' in database_url else 'Unknown'}")
        except Exception as e:
            log_error(f"Database bağlantı log hatası: {e}")
    
    async def log_connection_success(self, database_url: str):
        """Bağlantı başarı logu"""
        try:
            log_system(f"✅ Database bağlantısı başarılı: {database_url.split('@')[1] if '@' in database_url else 'Unknown'}")
        except Exception as e:
            log_error(f"Database bağlantı başarı log hatası: {e}")
    
    async def log_connection_failure(self, database_url: str, error: str):
        """Bağlantı hata logu"""
        try:
            log_error(f"❌ Database bağlantı hatası: {database_url.split('@')[1] if '@' in database_url else 'Unknown'} - Error: {error}")
        except Exception as e:
            log_error(f"Database bağlantı hata log hatası: {e}")
    
    async def log_query_attempt(self, query: str, table: str = "Unknown"):
        """Sorgu denemesi logla"""
        try:
            # Hassas bilgileri gizle
            safe_query = query.replace("'", "''")[:100] + "..." if len(query) > 100 else query
            log_system(f"🔍 SQL Sorgu: {safe_query} - Tablo: {table}")
        except Exception as e:
            log_error(f"SQL sorgu log hatası: {e}")
    
    async def log_query_success(self, query: str, table: str = "Unknown", rows_affected: int = 0):
        """Sorgu başarı logu"""
        try:
            safe_query = query.replace("'", "''")[:100] + "..." if len(query) > 100 else query
            log_system(f"✅ SQL Başarılı: {safe_query} - Tablo: {table} - Etkilenen: {rows_affected}")
        except Exception as e:
            log_error(f"SQL başarı log hatası: {e}")
    
    async def log_query_failure(self, query: str, table: str = "Unknown", error: str = ""):
        """Sorgu hata logu"""
        try:
            safe_query = query.replace("'", "''")[:100] + "..." if len(query) > 100 else query
            log_error(f"❌ SQL Hatası: {safe_query} - Tablo: {table} - Error: {error}")
        except Exception as e:
            log_error(f"SQL hata log hatası: {e}")
    
    async def log_table_check(self, table_name: str, exists: bool, row_count: int = 0):
        """Tablo kontrol logu"""
        try:
            if exists:
                log_system(f"📊 Tablo kontrolü: {table_name} ✅ Mevcut - Satır: {row_count}")
            else:
                log_warning(f"⚠️ Tablo kontrolü: {table_name} ❌ Mevcut değil")
        except Exception as e:
            log_error(f"Tablo kontrol log hatası: {e}")
    
    async def log_database_health_check(self, tables_status: Dict[str, Dict[str, Any]]):
        """Veritabanı sağlık kontrolü logu"""
        try:
            total_tables = len(tables_status)
            existing_tables = sum(1 for status in tables_status.values() if status.get('exists', False))
            total_rows = sum(status.get('row_count', 0) for status in tables_status.values())
            
            log_system(f"🏥 Database Sağlık Raporu:")
            log_system(f"   📊 Toplam Tablo: {total_tables}")
            log_system(f"   ✅ Mevcut Tablo: {existing_tables}")
            log_system(f"   ❌ Eksik Tablo: {total_tables - existing_tables}")
            log_system(f"   📈 Toplam Satır: {total_rows}")
            
            # Eksik tabloları listele
            missing_tables = [name for name, status in tables_status.items() if not status.get('exists', False)]
            if missing_tables:
                log_warning(f"   ⚠️ Eksik Tablolar: {', '.join(missing_tables)}")
            
        except Exception as e:
            log_error(f"Database sağlık kontrol log hatası: {e}")

# Global instance
_database_logger = DatabaseLogger()

def get_database_logger():
    """Database logger'ı al"""
    return _database_logger

# Decorator fonksiyonları
def log_database_operation(func):
    """Database operasyonu logla decorator'ı"""
    async def wrapper(*args, **kwargs):
        try:
            # Fonksiyon adını al
            func_name = func.__name__
            log_system(f"🗄️ Database operasyonu başladı: {func_name}")
            
            # Fonksiyonu çalıştır
            result = await func(*args, **kwargs)
            
            # Başarı logu
            log_system(f"✅ Database operasyonu başarılı: {func_name}")
            
            return result
            
        except Exception as e:
            # Hata logu
            log_error(f"❌ Database operasyonu hatası: {func.__name__} - Error: {e}")
            raise
            
    return wrapper 