"""
Profil handler - Kullanici profil sistemi
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user_points, get_user_rank, get_today_stats, get_market_history, get_system_stats
from utils.logger import logger

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
        
        # Kullanici verilerini al
        user_points = await get_user_points(user.id)
        user_rank = await get_user_rank(user.id)
        today_stats = await get_today_stats(user.id)
        market_history = await get_market_history(user.id)
        system_stats = await get_system_stats()
        
        # Ana menü butonları
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Profil Detayları", callback_data="profile_detailed"),
                InlineKeyboardButton(text="🏆 Sıralama", callback_data="profile_ranking")
            ],
            [
                InlineKeyboardButton(text="🛍️ Market", callback_data="profile_market"),
                InlineKeyboardButton(text="📋 Komutlar", callback_data="profile_commands")
            ],
            [
                InlineKeyboardButton(text="🎮 Etkinlikler", callback_data="profile_events"),
                InlineKeyboardButton(text="📈 İstatistikler", callback_data="profile_stats")
            ],
            [
                InlineKeyboardButton(text="❌ Kapat", callback_data="profile_close")
            ]
        ])
        
        # Ana profil mesajı
        profile_response = f"""
**{user.first_name}'IN PROFİLİ**

**💎 POINT DURUMU**

**💰 Toplam Point:** `{user_points.get('kirve_points', 0):.2f} KP`

**🏆 RÜTBE BİLGİLERİ**

**👑 Rütbe:** {user_rank.get('rank_name', 'Üye')}
**⭐ Seviye:** {user_rank.get('rank_level', 1)}

**📊 AKTİVİTE İSTATİSTİKLERİ**

**💬 Toplam Mesaj:** {user_points.get('total_messages', 0)}
**📅 Bugünkü Mesaj:** {today_stats.get('message_count', 0)}
**⏰ Son Aktivite:** {today_stats.get('last_activity', 'Bilinmiyor')}

**🛒 MARKET GEÇMİŞİ**

**📦 Toplam Sipariş:** {market_history.get('total_orders', 0)} adet
**💸 Toplam Harcama:** {market_history.get('total_spent', 0):.2f} KP
**✅ Onaylanan Sipariş:** {market_history.get('approved_orders', 0)} adet
**📋 Son Sipariş:** {market_history.get('last_order_date', 'Hiç sipariş yok')}

**🔧 SİSTEM DURUMU**

**👥 Toplam Üye:** {system_stats.get('total_users', 0)}
**📝 Kayıtlı:** {system_stats.get('registered_users', 0)}
**🏠 Aktif Grup:** {system_stats.get('active_groups', 0)}

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
        
        # Kullanici verilerini al
        user_points = await get_user_points(user_id)
        user_rank = await get_user_rank(user_id)
        today_stats = await get_today_stats(user_id)
        market_history = await get_market_history(user_id)
        system_stats = await get_system_stats()
        
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
                InlineKeyboardButton(text="📋 Komutlar", callback_data="profile_commands")
            ],
            [
                InlineKeyboardButton(text="🎮 Etkinlikler", callback_data="profile_events"),
                InlineKeyboardButton(text="📈 İstatistikler", callback_data="profile_stats")
            ],
            [
                InlineKeyboardButton(text="❌ Kapat", callback_data="profile_close")
            ]
        ])
        
        # Ana profil mesajı
        profile_response = f"""
**{user_name}'IN PROFİLİ**

**💎 POINT DURUMU**

**💰 Toplam Point:** `{user_points.get('kirve_points', 0):.2f} KP`

**🏆 RÜTBE BİLGİLERİ**

**👑 Rütbe:** {user_rank.get('rank_name', 'Üye')}
**⭐ Seviye:** {user_rank.get('rank_level', 1)}

**📊 AKTİVİTE İSTATİSTİKLERİ**

**💬 Toplam Mesaj:** {user_points.get('total_messages', 0)}
**📅 Bugünkü Mesaj:** {today_stats.get('message_count', 0)}
**⏰ Son Aktivite:** {today_stats.get('last_activity', 'Bilinmiyor')}

**🛒 MARKET GEÇMİŞİ**

**📦 Toplam Sipariş:** {market_history.get('total_orders', 0)} adet
**💸 Toplam Harcama:** {market_history.get('total_spent', 0):.2f} KP
**✅ Onaylanan Sipariş:** {market_history.get('approved_orders', 0)} adet
**📋 Son Sipariş:** {market_history.get('last_order_date', 'Hiç sipariş yok')}

**🔧 SİSTEM DURUMU**

**👥 Toplam Üye:** {system_stats.get('total_users', 0)}
**📝 Kayıtlı:** {system_stats.get('registered_users', 0)}
**🏠 Aktif Grup:** {system_stats.get('active_groups', 0)}

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
        await _bot_instance.send_message(user_id, "❌ Profil bilgileri yüklenemedi!")


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
        elif data == "profile_commands":
            logger.info(f"Komutlar butonu tıklandı - User: {callback.from_user.id}")
            from handlers.register_handler import komutlar_command
            # Komutlar mesajını gönder
            await komutlar_command(callback.message)
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
        else:
            logger.warning(f"Bilinmeyen profil callback: {data}")
            await callback.answer("Bilinmeyen işlem!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Profile callback handler hatası: {e}")
        try:
            await callback.answer("İşlem sırasında hata oluştu!", show_alert=True)
        except:
            pass


async def show_detailed_stats(callback: types.CallbackQuery) -> None:
    """Detaylı istatistikler göster"""
    try:
        user = callback.from_user
        
        # Detaylı veriler
        user_points = await get_user_points(user.id)
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
**📅 Kayıt Tarihi:** {user_points.get('registration_date', 'Bilinmiyor')}
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
**🌍 Genel Sıralama:** #{ranking_data.get('global_rank', 'N/A')}
**💰 Point Sıralaması:** #{ranking_data.get('point_rank', 'N/A')}
**💬 Mesaj Sıralaması:** #{ranking_data.get('message_rank', 'N/A')}

**📊 DETAYLAR**
**🎯 En Yakın Rakip:** {ranking_data.get('next_competitor', 'Yok')}
**📈 Bir Üst Sıra İçin:** {ranking_data.get('points_needed', 0):.2f} KP gerekli
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


# Yardımcı fonksiyonlar
async def get_weekly_stats(user_id: int) -> Dict[str, Any]:
    """Haftalık istatistikler"""
    try:
        # Bu fonksiyon database.py'de implement edilmeli
        return {
            'weekly_points': 0.0,
            'weekly_messages': 0
        }
    except Exception as e:
        logger.error(f"Weekly stats hatası: {e}")
        return {'weekly_points': 0.0, 'weekly_messages': 0}


async def get_user_ranking(user_id: int) -> Dict[str, Any]:
    """Kullanıcı sıralama bilgileri"""
    try:
        # Bu fonksiyon database.py'de implement edilmeli
        return {
            'global_rank': 'N/A',
            'point_rank': 'N/A', 
            'message_rank': 'N/A',
            'next_competitor': 'Yok',
            'points_needed': 0.0
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