"""
Profil handler - Kullanici profil sistemi
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user_points, get_user_points_cached, get_user_rank, get_today_stats, get_market_history, get_system_stats, get_user_info
from utils.logger import logger

# Bot instance setter
_bot_instance = None

def set_bot_instance(bot_instance):
    global _bot_instance
    _bot_instance = bot_instance

async def menu_command(message: types.Message) -> None:
    """
    /menu komutu - Kullanici profil menusu
    """
    try:
        user = message.from_user
        
        # Kullanici kayitli mi kontrol et
        from database import is_user_registered
        if not await is_user_registered(user.id):
            await message.answer(
                "Henuz kayit olmadınız!\n"
                "Kayit olmak icin /kirvekayit komutunu kullanın.",
                reply_to_message_id=message.message_id
            )
            return
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Menu komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_menu_privately(user.id)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        logger.info(f"/menu komutu - User: {user.first_name} ({user.id})")
        
        # Detaylı log
        from handlers.detailed_logging_system import log_command_execution
        await log_command_execution(
            user_id=user.id,
            username=user.username or user.first_name,
            command="menu",
            chat_id=message.chat.id,
            chat_type=message.chat.type
        )
        
        # Database bağlantısını kontrol et
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await message.answer(
                "❌ Database bağlantısı kurulamadı!\n"
                "Lütfen daha sonra tekrar deneyin.",
                reply_to_message_id=message.message_id
            )
            return
        
        # Kullanici verilerini al - Hata kontrolü ile
        try:
            user_points = await get_user_points_cached(user.id)  # Cache'li versiyon kullan
            user_rank = await get_user_rank(user.id)
            today_stats = await get_today_stats(user.id)
            market_history = await get_market_history(user.id)
            system_stats = await get_system_stats()
        except Exception as db_error:
            logger.error(f"❌ Database veri alma hatası: {db_error}")
            await message.answer(
                "❌ Profil bilgileri yüklenirken hata oluştu!\n"
                "Lütfen daha sonra tekrar deneyin.",
                reply_to_message_id=message.message_id
            )
            return
        
        # Ana menü butonları
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Profil Detayları", callback_data="profile_detailed"),
                InlineKeyboardButton(text="🏆 Sıralama", callback_data="profile_ranking")
            ],
            [
                InlineKeyboardButton(text="🛍️ Market", callback_data="profile_market"),
                InlineKeyboardButton(text="❓ Yardım", callback_data="profile_help")
            ],
            [
                InlineKeyboardButton(text="🎮 Etkinlikler", callback_data="profile_events")
            ],
            [
                InlineKeyboardButton(text="❌ Kapat", callback_data="profile_close")
            ]
        ])
        
        # Ana profil mesajı
        profile_response = f"""
**👤 {user.first_name}'IN PROFİLİ**

**💎 POINT DURUMU**
**💰 Toplam Point:** `{user_points.get('kirve_points', 0):.2f} KP`

**🏆 RÜTBE BİLGİLERİ**
**👑 Rütbe:** {user_rank.get('rank_name', 'Üye')}
**⭐ Seviye:** {user_rank.get('rank_level', 1)}

**📊 AKTİVİTE İSTATİSTİKLERİ**
**💬 Toplam Mesaj:** {user_points.get('total_messages', 0)}
**📅 Bugünkü Mesaj:** {today_stats.get('message_count', 0)}
**⏰ Son Aktivite:** {today_stats.get('last_activity', 'Bilinmiyor')}

---
_Profilinizi geliştirmek için grup sohbetlerine katılın!_
        """
        
        await message.answer(
            profile_response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"Profil menüsü gösterildi - User: {user.id}")
        
    except Exception as e:
        logger.error(f"/menu handler hatası: {e}")
        await message.answer(
            "Profil bilgileri yüklenirken hata oluştu!\n"
            "Lütfen daha sonra tekrar deneyin.",
            reply_to_message_id=message.message_id
        )

async def _send_menu_privately(user_id: int):
    """Menu'yu özel mesajla gönder"""
    try:
        if not _bot_instance:
            logger.error("❌ Bot instance bulunamadı!")
            return
        
        # Database bağlantısını kontrol et
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await _bot_instance.send_message(
                user_id,
                "❌ Database bağlantısı kurulamadı!\nLütfen daha sonra tekrar deneyin."
            )
            return
        
        # Kullanici verilerini al - Hata kontrolü ile
        try:
            user_points = await get_user_points_cached(user_id)  # Cache'li versiyon kullan
            user_rank = await get_user_rank(user_id)
            market_history = await get_market_history(user_id)
            system_stats = await get_system_stats()
        except Exception as db_error:
            logger.error(f"❌ Database veri alma hatası: {db_error}")
            await _bot_instance.send_message(
                user_id,
                "❌ Profil bilgileri yüklenirken hata oluştu!\nLütfen daha sonra tekrar deneyin."
            )
            return
        
        # Kullanıcı bilgilerini al
        from database import get_user_info
        user_info = await get_user_info(user_id)
        user_name = user_info.get('first_name', 'Kullanıcı') if user_info else 'Kullanıcı'
        
        # Ana menü butonları
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Profil Detayları", callback_data="profile_detailed"),
                InlineKeyboardButton(text="🏆 Sıralama", callback_data="profile_ranking")
            ],
            [
                InlineKeyboardButton(text="🛍️ Market", callback_data="profile_market"),
                InlineKeyboardButton(text="❓ Yardım", callback_data="profile_help")
            ],
            [
                InlineKeyboardButton(text="🎮 Etkinlikler", callback_data="profile_events")
            ],
            [
                InlineKeyboardButton(text="❌ Kapat", callback_data="profile_close")
            ]
        ])
        
        # Ana profil mesajı
        profile_response = f"""
**👤 {user_name}'IN PROFİLİ**

**💎 POINT DURUMU**
**💰 Toplam Point:** `{user_points.get('kirve_points', 0):.2f} KP`

**🏆 RÜTBE BİLGİLERİ**
**👑 Rütbe:** {user_rank.get('rank_name', 'Üye')}
**⭐ Seviye:** {user_rank.get('rank_level', 1)}

---
_Profilinizi geliştirmek için grup sohbetlerine katılın!_
        """
        
        await _bot_instance.send_message(
            user_id,
            profile_response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"Profil menüsü özel mesajla gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Private menu hatası: {e}")
        if _bot_instance:
            await _bot_instance.send_message(user_id, "❌ Profil bilgileri yüklenemedi!")
        else:
            logger.error("❌ Bot instance bulunamadı - private menu hatası")


async def profile_callback_handler(callback: types.CallbackQuery) -> None:
    """
    Profil menüsü callback'lerini işle
    """
    try:
        user = callback.from_user
        data = callback.data
        
        # Rate limiting - callback spam önlemi
        from utils.rate_limiter import rate_limiter
        await rate_limiter.wait_if_needed(user.id, "callback")
        
        # Memory management - cache kontrolü
        from utils.memory_manager import memory_manager
        cache_key = f"profile_callback_{user.id}_{data}"
        cached_result = memory_manager.get_cache_manager().get_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit - User: {user.id}, Data: {data}")
            return
        
        logger.info(f"Profil callback - User: {user.first_name} ({user.id}) - Data: {data}")
        
        # Hızlı response - timeout önlemi (en başta)
        try:
            await callback.answer()
        except Exception as answer_error:
            logger.warning(f"Callback answer hatası: {answer_error}")
            # Answer başarısız olsa bile devam et
        
        if data == "profile_detailed":
            await show_detailed_stats(callback)
        elif data == "profile_ranking":
            await show_ranking(callback)
        elif data == "profile_market":
            logger.info(f"Market butonu tıklandı - User: {callback.from_user.id}")
            from handlers.market_system import show_market_menu_modern
            await show_market_menu_modern(callback)
        elif data == "profile_help":
            logger.info(f"Yardım butonu tıklandı - User: {callback.from_user.id}")
            await show_help_menu(callback)
        elif data == "profile_events":
            logger.info(f"Etkinlikler butonu tıklandı - User: {callback.from_user.id}")
            from handlers.events_list import list_active_lotteries
            await list_active_lotteries(callback.message)
        elif data == "profile_stats":
            logger.info(f"İstatistikler butonu tıklandı - User: {callback.from_user.id}")
            from handlers.statistics_system import system_stats_command
            await system_stats_command(callback.message)
        elif data and data.startswith("view_product_"):
            logger.info(f"VIEW PRODUCT CALLBACK - Data: {data}")
            from handlers.market_system import show_product_details_modern
            await show_product_details_modern(callback, data)
        elif data and data.startswith("buy_product_"):
            from handlers.market_system import handle_buy_product_modern
            await handle_buy_product_modern(callback, data)
        elif data and data.startswith("confirm_buy_"):
            from handlers.market_system import confirm_buy_product_modern
            await confirm_buy_product_modern(callback, data)
        elif data == "my_orders":
            logger.info(f"Siparişlerim butonu tıklandı - User: {callback.from_user.id}")
            from handlers.market_system import show_my_orders
            await show_my_orders(callback)
        elif data == "profile_orders":
            logger.info(f"Profil siparişlerim butonu tıklandı - User: {callback.from_user.id}")
            from handlers.market_system import show_my_orders
            await show_my_orders(callback)
        elif data == "profile_back":
            logger.info(f"Profil geri butonu tıklandı - User: {callback.from_user.id}")
            await menu_command(callback.message)
        elif data == "insufficient_balance":
            # Alert gösterme, sadece log yaz
            logger.warning(f"Yetersiz bakiye - User: {user.id}")
            await callback.answer("Yetersiz bakiye!", show_alert=True)
        elif data == "ranking_top_kp":
            await show_top_kp_ranking(callback)
        elif data == "ranking_top_messages":
            await show_top_messages_ranking(callback)
        elif data == "profile_close":
            # Menüyü kapat
            try:
                await callback.message.delete()
            except:
                await callback.answer("Menü kapatıldı!")
        else:
            logger.warning(f"Bilinmeyen profil callback: {data}")
            await callback.answer("Bilinmeyen işlem!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Profile callback handler hatası: {e}")
        try:
            await callback.answer("İşlem sırasında hata oluştu!", show_alert=True)
        except:
            pass


async def show_help_menu(callback: types.CallbackQuery) -> None:
    """Yardım menüsü göster"""
    try:
        response = f"""
**❓ KİRVEHUB YARDIM MERKEZİ**

**💎 POINT SİSTEMİ**
• Grup sohbetlerinde aktif ol, point kazan!
• Point'lerini market'te harcayabilirsin

**🛍️ MARKET SİSTEMİ**
• Point'lerinle freespinler, bakiyeler al
• Admin onayından sonra kodlar gönderilir
• Satın alma işlemi geri alınamaz

**🏆 SIRALAMA SİSTEMİ**
• Top 10 KP sıralaması
• Top 10 mesaj sıralaması
• Kendi sıralamanı gör

**🎮 ETKİNLİKLER**
• Çekilişlere katıl
• Point'lerinle özel ödüller kazan
• Aktif etkinlikleri takip et

**📊 PROFİL SİSTEMİ**
• Detaylı istatistiklerin
• Haftalık ve günlük kazanımların
• Aktivite geçmişin

**💡 İPUÇLARI**
• Grup sohbetlerine aktif katıl
• Günlük limitini doldurmaya çalış
• Etkinlikleri kaçırma
• Market'ten faydalan

**🔧 DESTEK**
Sorun yaşarsan admin ile iletişime geç!
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ana Menüye Dön", callback_data="profile_back")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Yardım menü hatası: {e}")
        await callback.answer("Yardım menüsü yüklenirken hata oluştu!", show_alert=True)


async def show_detailed_stats(callback: types.CallbackQuery) -> None:
    """Detaylı istatistikler göster"""
    try:
        user = callback.from_user
        
        # Detaylı veriler
        user_points = await get_user_points_cached(user.id)  # Cache'li versiyon kullan
        user_info = await get_user_info(user.id)  # registration_date ve last_activity için
        today_stats = await get_today_stats(user.id)
        weekly_stats = await get_weekly_stats(user.id)
        
        response = f"""
**📊 DETAYLI İSTATİSTİKLER**

**💎 POINT DETAYLARI**
**💰 Toplam Point:** `{user_points.get('kirve_points', 0):.2f} KP`
**📅 Günlük Kazanım:** `{user_points.get('daily_points', 0):.2f} KP`
**📊 Haftalık Kazanım:** `{weekly_stats.get('weekly_points', 0):.2f} KP`

**💬 MESAJ İSTATİSTİKLERİ**
**📝 Toplam Mesaj:** {user_points.get('total_messages', 0)}
**📅 Bugünkü Mesaj:** {today_stats.get('message_count', 0)}
**📊 Bu Hafta:** {weekly_stats.get('weekly_messages', 0)}

**⏰ ZAMAN BİLGİLERİ**
**📅 Kayıt Tarihi:** {user_info.get('registration_date', 'Bilinmiyor')}
**🕐 Son Aktivite:** {today_stats.get('last_activity', 'Bilinmiyor')}
**⏱️ Aktif Süre:** {today_stats.get('active_duration', 'Bilinmiyor')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ana Menüye Dön", callback_data="profile_back")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Detaylı stats hatası: {e}")
        await callback.answer("İstatistikler yüklenirken hata oluştu!", show_alert=True)


async def show_ranking(callback: types.CallbackQuery) -> None:
    """Sıralama göster"""
    try:
        user = callback.from_user
        
        # Sıralama verileri
        ranking_data = await get_user_ranking(user.id)
        
        response = f"""
**🏆 SIRALAMA DURUMU**

**👤 SENİN DURUMUN**
**💰 Point Sıralaması:** #{ranking_data.get('point_rank', 'N/A')}
**💬 Mesaj Sıralaması:** #{ranking_data.get('message_rank', 'N/A')}

**🏅 SIRALAMA BİLGİLERİ**
**📊 Toplam Katılımcı:** {ranking_data.get('total_participants', 'N/A')}
**🎖️ Senin Seviyen:** {ranking_data.get('user_level', 'N/A')}
**⭐ Aktiflik Puanın:** {ranking_data.get('activity_score', 'N/A')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 Top 10 KP", callback_data="ranking_top_kp"),
                InlineKeyboardButton(text="📝 Top 10 Mesaj", callback_data="ranking_top_messages")
            ],
            [InlineKeyboardButton(text="⬅️ Ana Menüye Dön", callback_data="profile_back")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Ranking hatası: {e}")
        await callback.answer("Sıralama bilgileri yüklenirken hata oluştu!", show_alert=True)


async def show_market_menu(callback: types.CallbackQuery) -> None:
    """Market menüsü göster"""
    try:
        from handlers.market_system import show_market_menu_modern
        await show_market_menu_modern(callback)
        
    except Exception as e:
        logger.error(f"Market menü hatası: {e}")
        await callback.answer("Market menüsü yüklenirken hata oluştu!", show_alert=True)


async def show_top_kp_ranking(callback: types.CallbackQuery) -> None:
    """Top 10 KP sıralaması göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await callback.answer("Database bağlantısı yok!", show_alert=True)
            return
        
        async with pool.acquire() as conn:
            # Top 10 KP sıralaması
            top_kp_users = await conn.fetch("""
                SELECT u.first_name, u.username, u.kirve_points, u.total_messages
                FROM users u
                WHERE u.is_registered = TRUE AND u.kirve_points > 0
                ORDER BY u.kirve_points DESC
                LIMIT 10
            """)
            
            # Kullanıcının kendi sıralaması
            user_id = callback.from_user.id
            user_rank = await conn.fetchval("""
                SELECT COUNT(*) + 1
                FROM users u
                WHERE u.is_registered = TRUE AND u.kirve_points > (
                    SELECT kirve_points FROM users WHERE user_id = $1
                )
            """, user_id)
            
            user_points = await conn.fetchval("""
                SELECT kirve_points FROM users WHERE user_id = $1
            """, user_id)
            
            # Sıralama listesi oluştur
            ranking_text = ""
            for i, user in enumerate(top_kp_users, 1):
                points = user.get('kirve_points', 0)
                name = user.get('first_name', 'Anonim')
                
                ranking_text += f"{i}. 💎 **{points:.2f} KP** | 👤 {name}\n"
            
            response = f"""
**💎 TOP 10 KP SIRALAMASI**

{ranking_text}

**👤 SENİN DURUMUN**
**🏆 Sıralama:** #{user_rank or 'N/A'}
**💰 Point:** {user_points or 0:.2f} KP
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Sıralamaya Dön", callback_data="profile_ranking")]
            ])
            
            await callback.message.edit_text(
                response,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Top KP ranking hatası: {e}")
        await callback.answer("KP sıralaması yüklenirken hata oluştu!", show_alert=True)


async def show_top_messages_ranking(callback: types.CallbackQuery) -> None:
    """Top 10 mesaj sıralaması göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await callback.answer("Database bağlantısı yok!", show_alert=True)
            return
        
        async with pool.acquire() as conn:
            # Top 10 mesaj sıralaması
            top_message_users = await conn.fetch("""
                SELECT u.first_name, u.username, u.kirve_points, u.total_messages
                FROM users u
                WHERE u.is_registered = TRUE AND u.total_messages > 0
                ORDER BY u.total_messages DESC
                LIMIT 10
            """)
            
            # Kullanıcının kendi sıralaması
            user_id = callback.from_user.id
            user_rank = await conn.fetchval("""
                SELECT COUNT(*) + 1
                FROM users u
                WHERE u.is_registered = TRUE AND u.total_messages > (
                    SELECT total_messages FROM users WHERE user_id = $1
                )
            """, user_id)
            
            user_messages = await conn.fetchval("""
                SELECT total_messages FROM users WHERE user_id = $1
            """, user_id)
            
            # Sıralama listesi oluştur
            ranking_text = ""
            for i, user in enumerate(top_message_users, 1):
                messages = user.get('total_messages', 0)
                name = user.get('first_name', 'Anonim')
                
                ranking_text += f"{i}. 📝 **{messages} mesaj** | 👤 {name}\n"
            
            response = f"""
**📝 TOP 10 MESAJ SIRALAMASI**

{ranking_text}

**👤 SENİN DURUMUN**
**🏆 Sıralama:** #{user_rank or 'N/A'}
**📝 Mesaj:** {user_messages or 0} mesaj
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Sıralamaya Dön", callback_data="profile_ranking")]
            ])
            
            await callback.message.edit_text(
                response,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Top messages ranking hatası: {e}")
        await callback.answer("Mesaj sıralaması yüklenirken hata oluştu!", show_alert=True)


# Kaldırılan fonksiyonlar: show_top_general_ranking ve show_detailed_ranking_analysis


# Yardımcı fonksiyonlar
async def get_weekly_stats(user_id: int) -> Dict[str, Any]:
    """Haftalık istatistikler"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            return {'weekly_points': 0.0, 'weekly_messages': 0}
        
        async with pool.acquire() as conn:
            # Bu haftanın başlangıcını hesapla
            from datetime import date, timedelta
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            
            # Haftalık point ve mesaj sayısını al
            weekly_data = await conn.fetchrow("""
                SELECT 
                    COALESCE(SUM(points_earned), 0) as weekly_points,
                    COALESCE(SUM(message_count), 0) as weekly_messages
                FROM daily_stats 
                WHERE user_id = $1 AND message_date >= $2
            """, user_id, week_start)
            
            if weekly_data:
                return {
                    'weekly_points': float(weekly_data['weekly_points'] or 0),
                    'weekly_messages': int(weekly_data['weekly_messages'] or 0)
                }
            
            return {'weekly_points': 0.0, 'weekly_messages': 0}
            
    except Exception as e:
        logger.error(f"Weekly stats hatası: {e}")
        return {'weekly_points': 0.0, 'weekly_messages': 0}


async def get_user_ranking(user_id: int) -> Dict[str, Any]:
    """Kullanıcı sıralama bilgileri"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            return {
                'global_rank': 'N/A',
                'point_rank': 'N/A', 
                'message_rank': 'N/A',
                'next_competitor': 'Yok',
                'points_needed': 0.0
            }
        
        async with pool.acquire() as conn:
            # Kullanıcının point ve mesaj sayısını al
            user_data = await conn.fetchrow("""
                SELECT kirve_points, total_messages 
                FROM users 
                WHERE user_id = $1
            """, user_id)
            
            if not user_data:
                return {
                    'global_rank': 'N/A',
                    'point_rank': 'N/A', 
                    'message_rank': 'N/A',
                    'next_competitor': 'Yok',
                    'points_needed': 0.0
                }
            
            user_points = float(user_data['kirve_points'] or 0)
            user_messages = int(user_data['total_messages'] or 0)
            
            # Point sıralaması
            point_rank = await conn.fetchval("""
                SELECT COUNT(*) + 1 
                FROM users 
                WHERE kirve_points > $1 AND is_registered = true
            """, user_points)
            
            # Mesaj sıralaması
            message_rank = await conn.fetchval("""
                SELECT COUNT(*) + 1 
                FROM users 
                WHERE total_messages > $1 AND is_registered = true
            """, user_messages)
            
            # Genel sıralama (point + mesaj kombinasyonu)
            general_rank = await conn.fetchval("""
                SELECT COUNT(*) + 1 
                FROM users 
                WHERE (kirve_points + total_messages * 0.1) > $1 AND is_registered = true
            """, user_points + user_messages * 0.1)
            
            # Toplam katılımcı sayısı
            total_participants = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM users 
                WHERE is_registered = true
            """)
            
            # Kullanıcı seviyesi (point bazlı)
            user_level = "Yeni Üye"
            if user_points >= 10.0:
                user_level = "Aktif Üye"
            elif user_points >= 5.0:
                user_level = "Orta Seviye"
            elif user_points >= 1.0:
                user_level = "Başlangıç"
            
            # Aktiflik puanı (point + mesaj kombinasyonu)
            activity_score = user_points + (user_messages * 0.01)
            
            # Milestone sistemi
            milestones = [1.0, 5.0, 10.0, 25.0, 50.0, 100.0]
            next_milestone = "N/A"
            milestone_points_needed = 0.0
            
            for milestone in milestones:
                if user_points < milestone:
                    next_milestone = f"{milestone:.0f} KP"
                    milestone_points_needed = milestone - user_points
                    break
            
            # Limit sıfırlama zamanı
            from datetime import datetime, timedelta
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            next_week = now + timedelta(days=7 - now.weekday())
            
            daily_reset = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            weekly_reset = next_week.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Hangi limit daha yakın
            if daily_reset < weekly_reset:
                limit_reset_time = f"Günlük: {daily_reset.strftime('%d.%m.%Y %H:%M')}"
            else:
                limit_reset_time = f"Haftalık: {weekly_reset.strftime('%d.%m.%Y %H:%M')}"
            
            return {
                'global_rank': general_rank or 'N/A',
                'point_rank': point_rank or 'N/A',
                'message_rank': message_rank or 'N/A',
                'total_participants': total_participants or 'N/A',
                'user_level': user_level,
                'activity_score': f"{activity_score:.2f}",
                'next_milestone': next_milestone,
                'milestone_points_needed': milestone_points_needed,
                'daily_limit': 5.00,
                'weekly_limit': 20.00,
                'limit_reset_time': limit_reset_time
            }
            
    except Exception as e:
        logger.error(f"Ranking hatası: {e}")
        return {
            'global_rank': 'N/A',
            'point_rank': 'N/A',
            'message_rank': 'N/A', 
            'next_competitor': 'Yok',
            'points_needed': 0.0
        } 

async def siparislerim_command(message: types.Message) -> None:
    """Siparişlerim komutu"""
    try:
        user = message.from_user
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Siparişlerim komutu mesajı silindi - Group: {message.chat.id}")
                if _bot_instance:
                    await _send_siparislerim_privately(user.id)
                return
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        await _send_siparislerim_privately(user.id)
        
    except Exception as e:
        logger.error(f"❌ Siparişlerim komutu hatası: {e}")
        await message.reply("❌ Siparişler yüklenirken hata oluştu!")


async def _send_siparislerim_privately(user_id: int):
    """Siparişlerim bilgisini özel mesajla gönder"""
    try:
        from handlers.market_system import show_my_orders
        from aiogram.types import CallbackQuery
        
        # Mock callback oluştur
        mock_callback = type('MockCallback', (), {
            'from_user': type('MockUser', (), {'id': user_id})(),
            'message': type('MockMessage', (), {'edit_text': lambda *args, **kwargs: None})()
        })()
        
        await show_my_orders(mock_callback)
        
    except Exception as e:
        logger.error(f"❌ Özel siparişlerim gönderme hatası: {e}")
        if _bot_instance:
            await _bot_instance.send_message(
                user_id,
                "❌ Siparişler yüklenirken hata oluştu!"
            )


async def siralama_command(message: types.Message) -> None:
    """Sıralama komutu"""
    try:
        user = message.from_user
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Sıralama komutu mesajı silindi - Group: {message.chat.id}")
                if _bot_instance:
                    await _send_siralama_privately(user.id)
                return
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        await _send_siralama_privately(user.id)
        
    except Exception as e:
        logger.error(f"❌ Sıralama komutu hatası: {e}")
        await message.reply("❌ Sıralama yüklenirken hata oluştu!")


async def _send_siralama_privately(user_id: int):
    """Sıralama bilgisini özel mesajla gönder"""
    try:
        # Mock callback oluştur
        mock_callback = type('MockCallback', (), {
            'from_user': type('MockUser', (), {'id': user_id})(),
            'message': type('MockMessage', (), {'edit_text': lambda *args, **kwargs: None})()
        })()
        
        await show_ranking(mock_callback)
        
    except Exception as e:
        logger.error(f"❌ Özel sıralama gönderme hatası: {e}")
        if _bot_instance:
            await _bot_instance.send_message(
                user_id,
                "❌ Sıralama yüklenirken hata oluştu!"
            )


async def profil_command(message: types.Message) -> None:
    """Profil komutu (menu ile aynı)"""
    try:
        user = message.from_user
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Profil komutu mesajı silindi - Group: {message.chat.id}")
                if _bot_instance:
                    await _send_profil_privately(user.id)
                return
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        await _send_profil_privately(user.id)
        
    except Exception as e:
        logger.error(f"❌ Profil komutu hatası: {e}")
        await message.reply("❌ Profil yüklenirken hata oluştu!")


async def _send_profil_privately(user_id: int):
    """Profil bilgisini özel mesajla gönder"""
    try:
        if _bot_instance:
            await _send_menu_privately(user_id)
        
    except Exception as e:
        logger.error(f"❌ Özel profil gönderme hatası: {e}")
        if _bot_instance:
            await _bot_instance.send_message(
                user_id,
                "❌ Profil yüklenirken hata oluştu!"
            ) 