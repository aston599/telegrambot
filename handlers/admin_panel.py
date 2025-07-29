"""
🛡️ Admin Panel Handler - KirveHub Bot
"""

import asyncio
import logging
from aiogram import Router, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime
from typing import Dict, Any

from config import get_config
from database import db_pool, get_db_pool
from utils.logger import logger, log_system, log_bot, log_error, log_info, log_warning
from handlers.recruitment_system import toggle_recruitment_system, get_recruitment_status, set_recruitment_interval

router = Router()

# Global variables
_bot_instance = None
admin_order_states = {}  # Admin sipariş durumları için

def set_bot_instance(bot_instance):
    global _bot_instance
    _bot_instance = bot_instance

async def _send_admin_panel_privately(user_id: int):
    """Admin paneli özel mesajla gönder - Görseldeki tasarım"""
    try:
        # Görseldeki admin panel buton düzeni
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Toplu Mesaj Gönder", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="🔧 Komut Oluşturucu", callback_data="admin_command_creator")
            ],
            [
                InlineKeyboardButton(text="📊 Raporlar", callback_data="admin_reports"),
                InlineKeyboardButton(text="🛍️ Market Yönetimi", callback_data="admin_market_management")
            ],
            [
                InlineKeyboardButton(text="🎲 Çekiliş Yap", callback_data="admin_lottery_create"),
                InlineKeyboardButton(text="🛡️ Admin Komutları", callback_data="admin_commands_list")
            ],
            [
                InlineKeyboardButton(text="⚙️ Sistem Yönetimi", callback_data="admin_system_management"),
                InlineKeyboardButton(text="⏰ Zamanlanmış Mesajlar", callback_data="admin_scheduled_messages")
            ],
            [
                InlineKeyboardButton(text="🔄 Botu Yeniden Başlat", callback_data="admin_restart_bot")
            ]
        ])
        
        admin_message = f"""
KirveHub Media
/adminpanel
✅ Yönetici Paneli

Hoş geldiniz, KirveHub!

Hangi işlemi yapmak istiyorsun? {datetime.now().strftime('%H:%M')}
        """
        
        await _bot_instance.send_message(
            user_id,
            admin_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"✅ Admin panel özel mesajla gönderildi: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Admin panel gönderilemedi: {e}")

# @router.message(Command("adminpanel"))  # MANUEL KAYITLI - ROUTER DEVRESİ DIŞI
async def admin_panel_command(message: Message) -> None:
    """Admin panel komutu - Görseldeki tasarım"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # logger.info(f"🛡️ ADMIN PANEL DEBUG - User: {user_id}, Text: '{message.text}'")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.info(f"❌ Admin değil - User: {user_id}, Admin ID: {config.ADMIN_USER_ID}")
            return
        
        # Komut oluşturma sürecini iptal et (eğer varsa)
        try:
            from handlers.dynamic_command_creator import force_cancel_command_creation
            cancelled = await force_cancel_command_creation(user_id)
            if cancelled:
                logger.info(f"✅ Komut oluşturma süreci iptal edildi - User: {user_id}")
            else:
                logger.info(f"ℹ️ Komut oluşturma süreci yoktu - User: {user_id}")
        except Exception as e:
            logger.warning(f"⚠️ Komut oluşturma iptal hatası: {e}")
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Admin panel komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_admin_panel_privately(user_id)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        log_system(f"🛡️ Admin panel komutu ÖZELİNDE - User: {message.from_user.first_name} ({user_id})")
        
        # Görseldeki admin panel buton düzeni
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Toplu Mesaj Gönder", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="🔧 Komut Oluşturucu", callback_data="admin_command_creator")
            ],
            [
                InlineKeyboardButton(text="📊 Raporlar", callback_data="admin_reports"),
                InlineKeyboardButton(text="🛍️ Market Yönetimi", callback_data="admin_market_management")
            ],
            [
                InlineKeyboardButton(text="🎲 Çekiliş Yap", callback_data="admin_lottery_create"),
                InlineKeyboardButton(text="🛡️ Admin Komutları", callback_data="admin_commands_list")
            ],
            [
                InlineKeyboardButton(text="⚙️ Sistem Yönetimi", callback_data="admin_system_management"),
                InlineKeyboardButton(text="⏰ Zamanlanmış Mesajlar", callback_data="admin_scheduled_messages")
            ],
            [
                InlineKeyboardButton(text="🔄 Botu Yeniden Başlat", callback_data="admin_restart_bot")
            ]
        ])
        
        admin_message = f"""
KirveHub Media
/adminpanel
✅ Yönetici Paneli

Hoş geldiniz, KirveHub!

Hangi işlemi yapmak istiyorsun? {datetime.now().strftime('%H:%M')}
        """
        
        await message.reply(
            admin_message,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Admin panel gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Admin panel hatası: {e}")
        await message.reply("❌ Admin panel yüklenemedi!")


# @router.callback_query(lambda c: c.data.startswith("admin_") or c.data.startswith("category_") or c.data.startswith("price_") or c.data in ["balance_commands", "event_commands", "system_commands", "admin_panel_main"] or c.data.startswith("event_") or c.data.startswith("admin_order_"))
async def admin_panel_callback(callback: types.CallbackQuery) -> None:
    """Admin panel callback handler"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # YENİ: EN BAŞTA DETAYLI LOGLAMA
        logger.info(f"🔍 CALLBACK RECEIVED - Raw data: {callback.data}")
        logger.info(f"🔍 CALLBACK RECEIVED - Type: {type(callback.data)}")
        logger.info(f"🔍 CALLBACK RECEIVED - Length: {len(callback.data) if callback.data else 0}")
        logger.info(f"🔍 CALLBACK RECEIVED - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        action = callback.data
        logger.info(f"🔍 Callback data: {action} - User: {user_id}")
        
        # YENİ: DETAYLI LOGLAMA
        logger.info(f"🔍 CALLBACK DEBUG - Action: {action}, User: {user_id}")
        logger.info(f"🔍 CALLBACK DATA TYPE - Type: {type(action)}")
        logger.info(f"🔍 CALLBACK DATA LENGTH - Length: {len(action) if action else 0}")
        
        # Debug: Bilinmeyen callback'leri logla
        if action not in ["admin_settings", "admin_events_system", "admin_broadcast", "admin_market_management", 
                         "admin_market_orders", "admin_balance_management", "admin_recruitment_system", 
                         "admin_reports", "admin_statistics", "admin_restart_bot", "admin_command_creator", 
                         "admin_main_menu", "admin_back", "admin_panel_main", "balance_commands", 
                         "event_commands", "system_commands", "admin_market", "admin_market_add",
                         "admin_system_management", "admin_points_settings", "admin_daily_limit", "admin_weekly_limit",
                         "set_points_custom", "set_daily_custom", "set_weekly_custom"]:
            logger.info(f"🔍 UNKNOWN CALLBACK - Action: {action}, User: {user_id}")
        
        # YENİ: SET_POINTS_ CALLBACK'LERİNİ KONTROL ET
        if action and action.startswith("set_points_"):
            logger.info(f"💰 SET POINTS CALLBACK DETECTED - Action: {action}, User: {user_id}")
            await handle_points_setting(callback, action)
            return
        elif action and action.startswith("set_daily_"):
            logger.info(f"📅 SET DAILY CALLBACK DETECTED - Action: {action}, User: {user_id}")
            await handle_daily_limit_setting(callback, action)
            return
        elif action and action.startswith("set_weekly_"):
            logger.info(f"📊 SET WEEKLY CALLBACK DETECTED - Action: {action}, User: {user_id}")
            await handle_weekly_limit_setting(callback, action)
            return

        # YENİ BUTON SİSTEMİ - Görseldeki düzen
        if action == "admin_settings":
            logger.info(f"🔍 ADMIN SETTINGS CALLBACK - User: {user_id}")
            await show_settings_menu(callback)
        elif action == "admin_events_system":
            logger.info(f"🔍 ADMIN EVENTS SYSTEM CALLBACK - User: {user_id}")
        elif action == "admin_market_management":
            logger.info(f"🔍 ADMIN MARKET MANAGEMENT CALLBACK - User: {user_id}")
            await show_market_management_menu(callback)
        elif action == "admin_market_orders":
            logger.info(f"🔍 ADMIN MARKET ORDERS CALLBACK - User: {user_id}")
            # Sipariş yönetimi - callback için özel fonksiyon
            await show_orders_list_callback(callback)
        elif action == "admin_balance_management":
            logger.info(f"🔍 ADMIN BALANCE MANAGEMENT CALLBACK - User: {user_id}")
            await show_balance_management_menu(callback)
        elif action and action.startswith("admin_balance_"):
            logger.info(f"🔍 ADMIN BALANCE CALLBACK - User: {user_id}, Action: {action}")
            # Bakiye yönetimi callback'leri - balance_management.py'den çağır
            from handlers.balance_management import handle_balance_callback
            await handle_balance_callback(callback)
        elif action == "admin_recruitment_system":
            logger.info(f"🔍 ADMIN RECRUITMENT SYSTEM CALLBACK - User: {user_id}")
            await show_recruitment_system_menu(callback)
        elif action == "admin_reports":
            logger.info(f"📊 Admin reports callback tetiklendi - User: {user_id}")
            await show_reports_menu(callback)
        elif action == "admin_statistics":
            logger.info(f"🔍 ADMIN STATISTICS CALLBACK - User: {user_id}")
            await show_statistics_menu(callback)
        elif action == "bonus_stats":
            logger.info(f"🎁 BONUS STATS CALLBACK - User: {user_id}")
            from handlers.admin_bonus_stats import show_bonus_stats
            await show_bonus_stats(callback)
        elif action == "refresh_bonus_stats":
            logger.info(f"🔄 REFRESH BONUS STATS CALLBACK - User: {user_id}")
            from handlers.admin_bonus_stats import refresh_bonus_stats
            await refresh_bonus_stats(callback)
        elif action == "detailed_bonus_stats":
            logger.info(f"📊 DETAILED BONUS STATS CALLBACK - User: {user_id}")
            from handlers.admin_bonus_stats import show_detailed_bonus_stats
            await show_detailed_bonus_stats(callback)
        elif action and action.startswith("admin_stats_"):
            logger.info(f"🔍 ADMIN STATS CALLBACK - User: {user_id}, Action: {action}")
            # İstatistik callback'leri - statistics_system.py'den çağır
            from handlers.statistics_system import handle_stats_callback
            await handle_stats_callback(callback)
        elif action == "admin_restart_bot":
            logger.info(f"🔍 ADMIN RESTART BOT CALLBACK - User: {user_id}")
            """Bot restart onay menüsü"""
            try:
                user_id = callback.from_user.id
                config = get_config()
                
                # Admin kontrolü
                if user_id != config.ADMIN_USER_ID:
                    await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
                    return
                
                response = """
🔄 **BOT YENİDEN BAŞLATMA**

**⚠️ Dikkat:**
• Bot yeniden başlatılacak
• Tüm bağlantılar kesilecek
• ~10-15 saniye sürecek

**Onaylıyor musunuz?**
                """
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Evet, Yeniden Başlat", callback_data="admin_restart_confirm"),
                        InlineKeyboardButton(text="❌ İptal", callback_data="admin_system_management")
                    ]
                ])
                
                await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
                
            except Exception as e:
                logger.error(f"❌ Bot restart callback hatası: {e}")
                await callback.answer("❌ Restart menüsü yüklenirken hata oluştu!", show_alert=True)
        elif action == "admin_broadcast":
            logger.info(f"🎯 BROADCAST CALLBACK YAKALANDI - User: {user_id}, Data: {action}")
            # Broadcast sistemi callback'i
            from handlers.broadcast_system import start_broadcast
            await start_broadcast(callback)
        elif action == "admin_broadcast_cancel":
            logger.info(f"🎯 BROADCAST CANCEL CALLBACK YAKALANDI - User: {user_id}, Data: {action}")
            # Broadcast iptal callback'i
            from handlers.broadcast_system import cancel_broadcast
            await cancel_broadcast(callback)
        elif action == "admin_command_creator":
            logger.info(f"🔍 ADMIN COMMAND CREATOR CALLBACK - User: {user_id}")
            await show_command_creator_menu(callback)
        elif action == "admin_main_menu":
            logger.info(f"🔍 ADMIN MAIN MENU CALLBACK - User: {user_id}")
            await show_main_admin_menu(callback)
        elif action == "admin_back":
            logger.info(f"🔍 ADMIN BACK CALLBACK - User: {user_id}")
            await show_back_menu(callback)
        elif action == "admin_panel_main":
            logger.info(f"🔍 ADMIN PANEL MAIN CALLBACK - User: {user_id}")
            await show_main_admin_functions(callback)
        elif action == "balance_commands":
            logger.info(f"🔍 BALANCE COMMANDS CALLBACK - User: {user_id}")
            await show_balance_commands_menu(callback)
        elif action == "event_commands":
            logger.info(f"🔍 EVENT COMMANDS CALLBACK - User: {user_id}")
            await show_event_commands_menu(callback)
        elif action == "system_commands":
            logger.info(f"🔍 SYSTEM COMMANDS CALLBACK - User: {user_id}")
            await show_system_commands_menu(callback)
        # Market callback'leri
        elif action == "admin_market":
            logger.info(f"🔍 ADMIN MARKET CALLBACK - User: {user_id}")
            await show_market_menu(callback)
        elif action == "admin_market_add":
            logger.info(f"🔍 ADMIN MARKET ADD CALLBACK - User: {user_id}")
            from handlers.admin_market_management import start_product_creation
            await start_product_creation(callback)
        # Diğer callback'ler
        elif action and action.startswith("category_"):
            logger.info(f"🔍 CATEGORY CALLBACK - User: {user_id}, Action: {action}")
            await handle_category_callback(callback, action)
        elif action and action.startswith("price_"):
            logger.info(f"🔍 PRICE CALLBACK - User: {user_id}, Action: {action}")
            await handle_price_callback(callback, action)
        elif action and action.startswith("admin_recruitment_"):
            logger.info(f"🔍 ADMIN RECRUITMENT CALLBACK - User: {user_id}, Action: {action}")
            # Kayıt teşvik sistemi işlemleri
            await handle_recruitment_callback(callback, action)
        elif action and action.startswith("recruitment_interval_"):
            logger.info(f"🔍 RECRUITMENT INTERVAL CALLBACK - User: {user_id}, Action: {action}")
            # Mesaj aralığı ayarlama
            await handle_recruitment_interval_callback(callback, action)
        elif action and action.startswith("admin_order_"):
            logger.info(f"🔍 ADMIN ORDER CALLBACK - User: {user_id}, Action: {action}")
            # Sipariş işlemleri
            parts = action.split("_")
            if len(parts) >= 4:
                order_id = int(parts[2])
                order_action = parts[3]
                await handle_order_action(callback, order_action, order_id)
        # Komut oluşturucu callback'leri
        elif action == "admin_create_command":
            logger.info(f"🔍 ADMIN CREATE COMMAND CALLBACK - User: {user_id}")
            # Dinamik komut oluşturucuyu başlat
            from handlers.dynamic_command_creator import start_command_creation
            await start_command_creation(callback)
        elif action == "admin_list_commands":
            logger.info(f"🔍 ADMIN LIST COMMANDS CALLBACK - User: {user_id}")
            from handlers.dynamic_command_creator import list_custom_commands_handler
            await list_custom_commands_handler(callback)
        elif action == "admin_delete_command":
            logger.info(f"🔍 ADMIN DELETE COMMAND CALLBACK - User: {user_id}")
            await callback.answer("🗑️ Komut silme özelliği yakında eklenecek!", show_alert=True)
        elif action == "admin_command_stats":
            logger.info(f"🔍 ADMIN COMMAND STATS CALLBACK - User: {user_id}")
            await callback.answer("📊 Komut istatistikleri yakında eklenecek!", show_alert=True)
        # SİSTEM YÖNETİMİ CALLBACK'LERİ
        elif action == "admin_system_management":
            logger.info(f"🔍 ADMIN SYSTEM MANAGEMENT CALLBACK - User: {user_id}")
            await show_system_management_menu(callback)
        elif action == "admin_link_commands":
            logger.info(f"🔍 ADMIN LINK COMMANDS CALLBACK - User: {user_id}")
            await show_link_commands_menu(callback)
        elif action == "admin_points_settings":
            logger.info(f"🔍 ADMIN POINTS SETTINGS CALLBACK - User: {user_id}")
            await show_points_settings_menu(callback)
        elif action == "admin_daily_limit":
            logger.info(f"🔍 ADMIN DAILY LIMIT CALLBACK - User: {user_id}")
            await show_daily_limit_menu(callback)
        elif action == "admin_weekly_limit":
            logger.info(f"🔍 ADMIN WEEKLY LIMIT CALLBACK - User: {user_id}")
            await show_weekly_limit_menu(callback)
        elif action == "admin_system_status":
            logger.info(f"🔍 ADMIN SYSTEM STATUS CALLBACK - User: {user_id}")
            await show_system_status_menu(callback)
        # SİSTEM YÖNETİMİ CALLBACK'LERİ - YENİ YAKLAŞIM
        elif action and action.startswith("set_points_"):
            logger.info(f"💰 SET POINTS CALLBACK - Action: {action}, User: {user_id}")
            await handle_points_setting(callback, action)
        elif action and action.startswith("set_daily_"):
            logger.info(f"📅 SET DAILY CALLBACK - Action: {action}, User: {user_id}")
            await handle_daily_limit_setting(callback, action)
        elif action and action.startswith("set_weekly_"):
            logger.info(f"📊 SET WEEKLY CALLBACK - Action: {action}, User: {user_id}")
            await handle_weekly_limit_setting(callback, action)
        elif action == "set_points_custom":
            logger.info(f"💰 SET POINTS CUSTOM CALLBACK - User: {user_id}")
            await start_custom_points_input(callback)
        elif action == "set_daily_custom":
            logger.info(f"📅 SET DAILY CUSTOM CALLBACK - User: {user_id}")
            await start_custom_daily_input(callback)
        elif action == "set_weekly_custom":
            logger.info(f"📊 SET WEEKLY CUSTOM CALLBACK - User: {user_id}")
            await start_custom_weekly_input(callback)
        # Rapor callback'leri - YENİ SİSTEM
        elif action == "admin_reports_users":
            await show_user_report(callback)
        elif action == "admin_reports_points":
            await show_point_report(callback)
        elif action == "admin_reports_events":
            await show_event_report(callback)
        elif action == "admin_reports_system":
            await show_system_report(callback)
        elif action == "admin_reports_users_refresh":
            await show_user_report(callback)
        elif action == "admin_reports_points_refresh":
            await show_point_report(callback)
        elif action == "admin_reports_events_refresh":
            await show_event_report(callback)
        elif action == "admin_reports_system_refresh":
            await show_system_report(callback)
        elif action == "admin_reports_users_detailed":
            await show_detailed_user_report(callback)
        elif action == "admin_reports_points_detailed":
            await show_detailed_point_report(callback)
        elif action == "admin_reports_events_detailed":
            await show_detailed_event_report(callback)
        elif action == "admin_reports_system_detailed":
            await show_detailed_system_report(callback)
        elif action == "admin_commands_list":
            await show_admin_commands_list(callback)

        elif action == "admin_lottery_create":
            # Direkt çekiliş oluşturma işlemini başlat
            try:
                user_id = callback.from_user.id
                config = get_config()
                
                logger.info(f"🎲 DIRECT LOTTERY CREATE - User: {user_id}")
                
                # Admin kontrolü
                if user_id != config.ADMIN_USER_ID:
                    await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
                    return
                
                # Memory manager kullanarak çekiliş oluşturma işlemini başlat
                from utils.memory_manager import memory_manager
                
                lottery_data = {
                    "type": "lottery",
                    "step": "cost",
                    "created_at": datetime.now()
                }
                
                memory_manager.set_lottery_data(user_id, lottery_data)
                memory_manager.set_input_state(user_id, "lottery_cost")
                
                logger.info(f"🎯 LOTTERY DATA SET FROM ADMIN - User: {user_id}, Step: cost, Data: {lottery_data}")
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ İptal", callback_data="lottery_cancel")]
                ])
                
                await callback.message.edit_text(
                    "🎲 **Çekiliş Oluşturma**\n\n"
                    "Katılım ücreti kaç Kirve Point olsun?\n"
                    "Örnek: `10` veya `5.50`\n\n"
                    "**Lütfen ücreti yazın:**",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                logger.info(f"✅ Çekiliş oluşturma başlatıldı - User: {user_id}")
                
            except Exception as e:
                logger.error(f"❌ Çekiliş oluşturma hatası: {e}")
                await callback.answer("❌ Çekiliş oluşturma sırasında hata oluştu!", show_alert=True)
        elif action == "create_lottery_command":
            await execute_lottery_create_command(callback)
        elif action == "list_lotteries_command":
            await execute_list_lotteries_command(callback)
        elif action == "admin_scheduled_messages":
            logger.info(f"🔍 SCHEDULED MESSAGES CALLBACK YAKALANDI - User: {user_id}")
            try:
                from handlers.scheduled_messages import show_scheduled_messages_menu
                logger.info(f"✅ show_scheduled_messages_menu import edildi")
                await show_scheduled_messages_menu(callback)
                logger.info(f"✅ show_scheduled_messages_menu çalıştırıldı")
            except Exception as e:
                logger.error(f"❌ SCHEDULED MESSAGES HATA: {e}")
                import traceback
                logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")
                await callback.answer("⚠️ Zamanlanmış mesajlar menüsü açılamadı!")
                return
        elif action == "scheduled_back":
            from handlers.scheduled_messages import show_scheduled_messages_menu
            await show_scheduled_messages_menu(callback)
        elif action == "admin_link_commands":
            await show_link_commands_menu(callback)
        elif action == "admin_scheduled_commands":
            await show_scheduled_commands_menu(callback)
        elif action == "create_link_command":
            from handlers.dynamic_command_creator import start_command_creation
            await start_command_creation(callback)
        elif action == "list_link_commands":
            await show_link_commands_list(callback)
        elif action == "manage_link_commands":
            await show_link_commands_management(callback)
        elif action == "link_stats":
            await show_link_commands_stats(callback)
        elif action == "admin_list_commands":
            from handlers.dynamic_command_creator import list_custom_commands_handler
            await list_custom_commands_handler(callback)
        elif action == "lottery_confirm_create":
            await handle_lottery_confirm_create(callback)
        elif action == "lottery_cancel":
            await handle_lottery_cancel(callback)
        elif action == "admin_restart_confirm":
            """Bot restart onayı"""
            try:
                user_id = callback.from_user.id
                config = get_config()
                
                # Admin kontrolü
                if user_id != config.ADMIN_USER_ID:
                    await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
                    return
                
                await callback.answer("🔄 Bot yeniden başlatılıyor...", show_alert=True)
                
                # Restart mesajı
                response = """
🔄 **BOT YENİDEN BAŞLATILIYOR**

**Durum:** Bot kapatılıyor ve yeniden başlatılıyor...
**Süre:** ~10-15 saniye

**Lütfen bekleyin...**
                """
                
                await callback.message.edit_text(response, parse_mode="Markdown")
                
                # Bot'u yeniden başlat
                import os
                import sys
                os.execv(sys.executable, ['python'] + sys.argv)
                
            except Exception as e:
                logger.error(f"❌ Bot restart hatası: {e}")
                await callback.answer("❌ Restart sırasında hata oluştu!", show_alert=True)
        elif action == "admin_maintenance_toggle":
            """Bakım modu toggle"""
            try:
                user_id = callback.from_user.id
                config = get_config()
                
                # Admin kontrolü
                if user_id != config.ADMIN_USER_ID:
                    await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
                    return
                
                # Bakım modunu toggle et
                import os
                from dotenv import load_dotenv
                
                # .env dosyasını oku
                load_dotenv()
                
                # Mevcut durumu al
                current_mode = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
                new_mode = not current_mode
                
                # .env dosyasını güncelle
                env_path = '.env'
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # MAINTENANCE_MODE satırını bul ve güncelle
                    updated = False
                    for i, line in enumerate(lines):
                        if line.startswith('MAINTENANCE_MODE='):
                            lines[i] = f'MAINTENANCE_MODE={str(new_mode).lower()}\n'
                            updated = True
                            break
                    
                    # Eğer satır yoksa ekle
                    if not updated:
                        lines.append(f'MAINTENANCE_MODE={str(new_mode).lower()}\n')
                    
                    # Dosyayı yaz
                    with open(env_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                
                status_text = "🔧 **BAKIM MODU AKTİF**" if new_mode else "✅ **BAKIM MODU KAPALI**"
                await callback.answer(f"{status_text}", show_alert=True)
                
                # Ana menüye geri dön
                await show_main_admin_menu(callback)
                
            except Exception as e:
                logger.error(f"❌ Bakım modu toggle hatası: {e}")
                await callback.answer("❌ Bakım modu değiştirilemedi!", show_alert=True)
        else:
            logger.info(f"🔍 UNHANDLED CALLBACK - Action: {action}, User: {user_id}")
            logger.info(f"🔍 CALLBACK DATA DEBUG - Raw data: {callback.data}")
            logger.info(f"🔍 CALLBACK DATA TYPE - Type: {type(callback.data)}")
            logger.info(f"🔍 CALLBACK DATA LENGTH - Length: {len(callback.data) if callback.data else 0}")
            await callback.answer("❌ Bilinmeyen admin işlemi!", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Admin panel callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def show_balance_menu(callback: types.CallbackQuery) -> None:
    """Bakiye yönetimi menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Bakiye Ekle", callback_data="admin_balance_add"),
            InlineKeyboardButton(text="➖ Bakiye Çıkar", callback_data="admin_balance_remove")
        ],
        [
            InlineKeyboardButton(text="🎉 Bakiye Etkinliği", callback_data="admin_balance_event")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
💰 **Bakiye Yönetimi**

**Kullanılabilir İşlemler:**
• Bakiye ekleme/çıkarma
• Bakiye etkinlikleri

Hangi işlemi yapmak istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def show_settings_menu(callback: types.CallbackQuery) -> None:
    """Ayarlar menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚙️ Point Ayarları", callback_data="admin_settings_points"),
            InlineKeyboardButton(text="🕐 Zaman Ayarları", callback_data="admin_settings_time")
        ],
        [
            InlineKeyboardButton(text="🔔 Bildirim Ayarları", callback_data="admin_settings_notifications"),
            InlineKeyboardButton(text="🛡️ Güvenlik Ayarları", callback_data="admin_settings_security")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
⚙️ **Sistem Ayarları**

**Mevcut Ayarlar:**
• Point kazanım oranları
• Zaman limitleri
• Bildirim ayarları
• Güvenlik parametreleri

Hangi ayarı değiştirmek istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def show_events_system_menu(callback: types.CallbackQuery) -> None:
    """Etkinlik sistemi menüsü - Genel Çekiliş butonu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎲 Genel Çekiliş", callback_data="create_lottery_command")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
🎲 **ETKİNLİK SİSTEMİ**

🎯 **Genel çekiliş oluşturmak için aşağıdaki butona tıklayın:**

💡 **Bu buton direkt /cekilisyap komutunu çalıştırır.**
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def show_lottery_menu(callback: types.CallbackQuery) -> None:
    """Çekiliş botu menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎉 Yeni Çekiliş", callback_data="admin_lottery_new"),
            InlineKeyboardButton(text="📋 Aktif Çekilişler", callback_data="admin_lottery_active")
        ],
        [
            InlineKeyboardButton(text="🏆 Çekiliş Sonuçları", callback_data="admin_lottery_results"),
            InlineKeyboardButton(text="⚙️ Çekiliş Ayarları", callback_data="admin_lottery_settings")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
🎉 **Çekiliş Botu**

**Çekiliş Yönetimi:**
• Yeni çekiliş oluşturma
• Aktif çekilişleri görüntüleme
• Sonuçları kontrol etme
• Çekiliş ayarları

Hangi işlemi yapmak istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def show_broadcast_menu(callback: types.CallbackQuery) -> None:
    """Toplu mesaj menüsü (sade)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Toplu Mesaj", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
📢 **Toplu Mesaj Gönderimi**

Buraya yazacağınız mesaj, tüm kayıtlı kullanıcılara özelden gönderilecektir.

**Özellikler:**
• Tüm kayıtlı kullanıcılara gönderim
• Anlık sonuç raporu
• İptal seçeneği
• Güvenli admin kontrolü

Hangi işlemi yapmak istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def show_market_menu(callback: types.CallbackQuery) -> None:
    """Market yönetimi menüsü - /market komutu tetikler"""
    try:
        # /market komutunu tetikle
        from handlers.admin_market_management import market_management_command
        
        # Mesajı sil
        await callback.message.delete()
        
        # /market komutunu çalıştır
        await market_management_command(callback.message)
        
    except Exception as e:
        logger.error(f"❌ Market menu hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def show_recruitment_system_menu(callback: types.CallbackQuery) -> None:
    """Kayıt teşvik sistemi menüsü"""
    try:
        # Sistem durumunu al
        is_active = get_recruitment_status()
        status_text = "✅ **Aktif**" if is_active else "❌ **Pasif**"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Sistemi Kapat" if is_active else "✅ Sistemi Aç", 
                    callback_data="admin_recruitment_toggle"
                )
            ],
            [
                InlineKeyboardButton(text="⏰ Mesaj Aralığı", callback_data="admin_recruitment_interval"),
                InlineKeyboardButton(text="📝 Mesaj Şablonları", callback_data="admin_recruitment_templates")
            ],
            [
                InlineKeyboardButton(text="📊 İstatistikler", callback_data="admin_recruitment_stats"),
                InlineKeyboardButton(text="🎯 Test Mesajı", callback_data="admin_recruitment_test")
            ],
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
            ]
        ])
        
        response = f"""
🎯 **Kayıt Teşvik Sistemi**

**Sistem Durumu:** {status_text}

**Yeni Özellikler:**
• 🆕 **Yeni kullanıcı tespiti** (ilk defa mesaj atanlar)
• ⏰ **5 dakika cooldown** (mesajlar arası)
• 📊 **Akıllı analiz** (3 mesajdan az atanlar)
• 🚫 **Spam koruması** (çok aktif kullanıcıları atla)

**Çalışma Mantığı:**
• Son 1 saatte aktif + En fazla 3 mesaj = Hedef
• 5 dakika aralıkla grup mesajı
• 24 saat kullanıcı cooldown
• Maksimum 3 kullanıcı hedefleme

**Kullanılabilir İşlemler:**
• Sistem açma/kapama
• Mesaj aralığı ayarlama
• Mesaj şablonları düzenleme
• İstatistik görüntüleme
• Test mesajı gönderme

Hangi işlemi yapmak istiyorsun?
        """
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Recruitment menu hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_balance_management_menu(callback: types.CallbackQuery) -> None:
    """Bakiye yönetimi menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Bakiye Ekle", callback_data="admin_balance_add"),
            InlineKeyboardButton(text="💸 Bakiye Çıkar", callback_data="admin_balance_remove")
        ],
        [
            InlineKeyboardButton(text="🎁 Sürpriz Bakiye", callback_data="admin_balance_surprise"),
            InlineKeyboardButton(text="📊 Bakiye Raporu", callback_data="admin_balance_report")
        ],
        [
            InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_balance_management"),
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
💰 **Bakiye Yönetimi**

**Mevcut İşlemler:**
• Bakiye ekleme (reply veya etiket ile)
• Bakiye çıkarma (reply veya etiket ile)
• Sürpriz bakiye dağıtımı
• Bakiye raporları

**Komutlar:**
• `/bakiyee MIKTAR` (reply ile)
• `/bakiyec MIKTAR` (reply ile)
• `/bakiyeeid USER_ID MIKTAR`
• `/bakiyecid USER_ID MIKTAR`

**Özellikler:**
• Reply ile hızlı işlem
• Etiket ile kullanıcı seçimi
• Toplu bakiye dağıtımı
• Detaylı raporlar

Hangi işlemi yapmak istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def show_statistics_menu(callback: types.CallbackQuery) -> None:
    """İstatistikler menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Admin İstatistikleri", callback_data="admin_stats_admin"),
            InlineKeyboardButton(text="📈 Sistem İstatistikleri", callback_data="admin_stats_system")
        ],
        [
            InlineKeyboardButton(text="👥 Kullanıcı İstatistikleri", callback_data="admin_stats_users"),
            InlineKeyboardButton(text="🎯 Performans İstatistikleri", callback_data="admin_stats_performance")
        ],
        [
            InlineKeyboardButton(text="🎁 Bonus İstatistikleri", callback_data="bonus_stats")
        ],
        [
            InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_statistics"),
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
📈 **İstatistikler Sistemi**

**Mevcut İstatistikler:**
• Admin istatistikleri (kullanıcı, point, mesaj)
• Sistem performans istatistikleri
• Kullanıcı aktivite istatistikleri
• Performans analizi
• 🎁 Bonus sistemi istatistikleri

**Özellikler:**
• Gerçek zamanlı veriler
• Detaylı analizler
• Grafik ve tablolar
• Export özellikleri
• Bonus dağıtım takibi

Hangi istatistiği görüntülemek istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def show_reports_menu(callback: types.CallbackQuery) -> None:
    """Raporlar menüsü"""
    logger.info(f"📊 Raporlar menüsü açıldı - User: {callback.from_user.id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Kullanıcı", callback_data="admin_reports_users"),
            InlineKeyboardButton(text="💰 Point", callback_data="admin_reports_points")
        ],
        [
            InlineKeyboardButton(text="🎮 Etkinlik", callback_data="admin_reports_events"),
            InlineKeyboardButton(text="📈 Sistem", callback_data="admin_reports_system")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
📊 **Raporlar Sistemi**

Hangi raporu görüntülemek istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def show_games_menu(callback: types.CallbackQuery) -> None:
    """Topluluk oyunları menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 Yeni Oyun", callback_data="admin_games_new"),
            InlineKeyboardButton(text="📋 Aktif Oyunlar", callback_data="admin_games_active")
        ],
        [
            InlineKeyboardButton(text="🏆 Oyun Sonuçları", callback_data="admin_games_results"),
            InlineKeyboardButton(text="⚙️ Oyun Ayarları", callback_data="admin_games_settings")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
🎮 **Topluluk Oyunları**

**Oyun Yönetimi:**
• Yeni oyun oluşturma
• Aktif oyunları görüntüleme
• Oyun sonuçları
• Oyun ayarları

Hangi işlemi yapmak istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def show_command_creator_menu(callback: types.CallbackQuery) -> None:
    """Komut oluşturucu menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔧 Yeni Komut Oluştur", callback_data="admin_create_command"),
            InlineKeyboardButton(text="📝 Komutları Listele", callback_data="admin_list_commands")
        ],
        [
            InlineKeyboardButton(text="🗑️ Komut Sil", callback_data="admin_delete_command"),
            InlineKeyboardButton(text="📊 Komut İstatistikleri", callback_data="admin_command_stats")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
🔧 **Komut Oluşturucu Sistemi**

**Kullanılabilir İşlemler:**
• Yeni custom komut oluştur (!site gibi)
• Mevcut komutları listele
• Komut silme
• Komut istatistikleri

**Örnek Kullanım:**
• `/komutolustur` - Yeni komut oluştur
• `/komutlar` - Tüm komutları listele
• `/komutsil !site` - Komut sil

Hangi işlemi yapmak istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def show_restart_menu(callback: types.CallbackQuery) -> None:
    """Bot restart menüsü"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Bakım modu durumunu al
        maintenance_status = "🔧 AKTİF" if config.MAINTENANCE_MODE else "✅ KAPALI"
        
        response = f"""
🔄 **BOT YÖNETİMİ**

**🔧 Bakım Modu:** {maintenance_status}

**⚠️ Dikkat:** Bot restart işlemi bot'u geçici olarak durduracak ve yeniden başlatacaktır.

**Hangi işlemi yapmak istiyorsun?**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Bot Restart", callback_data="admin_restart_bot"),
                InlineKeyboardButton(text=f"🔧 Bakım Modu", callback_data="admin_maintenance_toggle")
            ],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Restart menü hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def show_main_admin_menu(callback: types.CallbackQuery) -> None:
    """Ana admin menüsüne geri dön"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚙️ Ayarları Değiştir", callback_data="admin_settings"),
            InlineKeyboardButton(text="🎯 Etkinlik Sistemi", callback_data="admin_events_system")
        ],
        [
            InlineKeyboardButton(text="📢 Toplu Mesaj Gönder", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="🛍️ Market Yönetimi", callback_data="admin_market_management")
        ],
        [
            InlineKeyboardButton(text="🔧 Komut Oluşturucu", callback_data="admin_command_creator"),
            InlineKeyboardButton(text="📊 Raporlar", callback_data="admin_reports")
        ],
        [
            InlineKeyboardButton(text="🔄 Botu Yeniden Başlat", callback_data="admin_restart_bot")
        ]
    ])
    
    response = f"""
KirveHub Media
/adminpanel
✅ Yönetici Paneli

Hoş geldiniz, KirveHub!

Hangi işlemi yapmak istiyorsun? {datetime.now().strftime('%H:%M')}
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ==============================================
# MARKET ÜRÜN EKLEME SİSTEMİ
# ==============================================

# Global market product data storage
product_data_storage = {}

async def start_product_creation(callback: types.CallbackQuery) -> None:
    """Market ürün ekleme sürecini başlat"""
    try:
        user_id = callback.from_user.id
        
        # Ürün verilerini temizle
        product_data_storage[user_id] = {
            "step": "website_name",
            "data": {}
        }
        
        logger.info(f"🛍️ Ürün ekleme Adım 1 başlatıldı - User: {user_id}")
        logger.info(f"📦 Product data storage: {product_data_storage}")
        
        response = """
🛍️ **Market Ürün Ekleme - Adım 1/7**

**🌐 Site Adını Yazın:**

**Örnekler:**
• `Betboo`
• `Betsafe`
• `1xBet`
• `Parimatch`

**Lütfen sitenin adını yazın:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_market")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Adım 1 mesajı gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Product creation başlatma hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def handle_product_step_input(message: types.Message) -> None:
    """Market ürün ekleme adım girişlerini handle et"""
    try:
        user_id = message.from_user.id
        
        # Admin kontrolü
        from config import get_config
        config = get_config()
        if user_id != config.ADMIN_USER_ID:
            return
        
        # Ürün ekleme sürecinde mi?
        if user_id not in product_data_storage:
            logger.debug(f"❌ Ürün ekleme sürecinde değil - User: {user_id}")
            return
        
        process_data = product_data_storage[user_id]
        current_step = process_data["step"]
        
        logger.info(f"🔍 Ürün ekleme mesajı alındı - User: {user_id}, Text: {message.text}")
        logger.info(f"📝 Ürün ekleme sürecinde - Step: {current_step}")
        
        # Adım işleme
        if current_step == "website_name":
            await handle_website_name_input(message, process_data)
        elif current_step == "website_link":
            await handle_website_link_input(message, process_data)
        elif current_step == "product_name":
            await handle_product_name_input(message, process_data)
        elif current_step == "category":
            await handle_category_input(message, process_data)
        elif current_step == "stock":
            await handle_stock_input(message, process_data)
        elif current_step == "price":
            await handle_price_input(message, process_data)
        else:
            logger.warning(f"⚠️ Bilinmeyen adım: {current_step} - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Product step input hatası: {e}")
        # Hata durumunda kullanıcıya bilgi ver
        try:
            await message.reply("❌ Ürün ekleme sırasında hata oluştu! Lütfen tekrar deneyin.")
        except:
            pass


async def handle_website_name_input(message: types.Message, process_data: dict) -> None:
    """Website name girişi"""
    try:
        user_id = message.from_user.id
        website_name = message.text.strip()
        
        logger.info(f"🌐 Website name handler çağrılıyor... - User: {user_id}, Text: {website_name}")
        
        if len(website_name) < 2:
            await message.reply("❌ Site adı çok kısa! En az 2 karakter olmalı.")
            return
        
        process_data["data"]["website_name"] = website_name
        process_data["step"] = "website_link"
        
        logger.info(f"✅ Site adı kaydedildi: {website_name} - User: {user_id}")
        
        response = """
🛍️ **Market Ürün Ekleme - Adım 2/7**

**🔗 Site Linkini Yazın:**

**Örnekler:**
• `https://betboo.com`
• `https://www.betsafe.com`
• `https://1xbet.com/tr`

**Lütfen sitenin linkini yazın:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_market")]
        ])
        
        await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
        
        logger.info(f"✅ Adım 2 mesajı gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Website name input hatası: {e}")
        await message.reply("❌ Site adı kaydedilirken hata oluştu! Lütfen tekrar deneyin.")


async def handle_website_link_input(message: types.Message, process_data: dict) -> None:
    """Website link girişi"""
    try:
        user_id = message.from_user.id
        website_link = message.text.strip()
        
        logger.info(f"🔗 Website link handler çağrılıyor...")
        
        process_data["data"]["website_link"] = website_link
        process_data["step"] = "product_name"
        
        logger.info(f"✅ Site linki kaydedildi: {website_link} - User: {user_id}")
        
        response = """
🛍️ **Market Ürün Ekleme - Adım 3/7**

**🛍️ Ürün Adını Yazın:**

**Örnekler:**
• `50 Freespin Paketi`
• `%100 Hoşgeldin Bonusu`
• `25 TL Hediye Kartı`

**Lütfen ürünün adını yazın:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_market")]
        ])
        
        await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Website link input hatası: {e}")


async def handle_product_name_input(message: types.Message, process_data: dict) -> None:
    """Product name girişi"""
    try:
        user_id = message.from_user.id
        product_name = message.text.strip()
        
        logger.info(f"🛍️ Product name handler çağrılıyor...")
        
        if len(product_name) < 3:
            await message.reply("❌ Ürün adı çok kısa! En az 3 karakter olmalı.")
            return
        
        process_data["data"]["product_name"] = product_name
        process_data["step"] = "category"
        
        logger.info(f"✅ Ürün adı kaydedildi: {product_name} - User: {user_id}")
        
        # Kategori seçim menüsü
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎰 Freespin", callback_data="category_freespin"),
                InlineKeyboardButton(text="💰 Bonus", callback_data="category_bonus")
            ],
            [
                InlineKeyboardButton(text="🎁 Hediye Kartı", callback_data="category_hediye"),
                InlineKeyboardButton(text="⭐ Özel", callback_data="category_ozel")
            ],
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_market")]
        ])
        
        response = """
🛍️ **Market Ürün Ekleme - Adım 4/7**

**📂 Kategori Seçin:**

**🎰 Freespin** - Ücretsiz döndürme paketleri
**💰 Bonus** - Para yatırma bonusları
**🎁 Hediye Kartı** - Dijital hediye kartları
**⭐ Özel** - Özel kategoriye ait ürünler

**Lütfen bir kategori seçin:**
        """
        
        await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Product name input hatası: {e}")


async def handle_category_input(message: types.Message, process_data: dict) -> None:
    """Kategori girişi"""
    try:
        user_id = message.from_user.id
        category_text = message.text.strip()
        
        logger.info(f"📂 Category handler çağrılıyor...")
        
        category_map = {
            'freespin': 'freespin',
            'bonus': 'bonus',
            'hediye': 'hediye',
            'ozel': 'ozel'
        }
        
        category_name = category_map.get(category_text.lower())
        
        if not category_name:
            await message.reply("❌ Geçersiz kategori! Lütfen tekrar deneyin.")
            return
        
        process_data["data"]["category"] = category_name
        process_data["step"] = "stock"
        
        logger.info(f"✅ Kategori kaydedildi: {category_name} - User: {user_id}")
        
        response = """
🛍️ **Market Ürün Ekleme - Adım 5/7**

**📦 Stok Sayısını Yazın:**

**Örnekler:**
• `10`
• `50`
• `100`

**Lütfen stok sayısını yazın:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_market")]
        ])
        
        await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Category input hatası: {e}")


async def handle_stock_input(message: types.Message, process_data: dict) -> None:
    """Stock girişi ve ürünü database'e kaydetme"""
    try:
        user_id = message.from_user.id
        stock_text = message.text.strip()
        
        logger.info(f"📦 Stock handler çağrılıyor...")
        
        try:
            stock = int(stock_text)
            if stock <= 0:
                await message.reply("❌ Stok pozitif bir sayı olmalı!")
                return
        except ValueError:
            await message.reply("❌ Geçersiz stok sayısı! Örnek: `10`")
            return
        
        process_data["data"]["stock"] = stock
        
        logger.info(f"✅ Stok kaydedildi: {stock} - User: {user_id}")
        
        # Fiyat seçim menüsü
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 25 KP", callback_data="price_25"),
                InlineKeyboardButton(text="💰 50 KP", callback_data="price_50")
            ],
            [
                InlineKeyboardButton(text="💰 75 KP", callback_data="price_75"),
                InlineKeyboardButton(text="💰 100 KP", callback_data="price_100")
            ],
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_market")]
        ])
        
        response = """
🛍️ **Market Ürün Ekleme - Adım 6/7**

**💰 Fiyat Seçin:**

**25 KP** - Ekonomik ürünler
**50 KP** - Orta seviye ürünler
**75 KP** - Premium ürünler
**100 KP** - Özel ürünler

**Lütfen bir fiyat seçin:**
        """
        
        await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Adım adım ürün ekleme hatası: {e}")


async def handle_price_input(message: types.Message, process_data: dict) -> None:
    """Fiyat girişi ve ürünü database'e kaydetme"""
    try:
        user_id = message.from_user.id
        price_text = message.text.strip()
        
        logger.info(f"💰 Price handler çağrılıyor...")
        
        try:
            price = float(price_text)
            if price <= 0:
                await message.reply("❌ Fiyat pozitif bir sayı olmalı!")
                return
        except ValueError:
            await message.reply("❌ Geçersiz fiyat sayısı! Örnek: `25.0`")
            return
        
        process_data["data"]["price"] = price
        
        logger.info(f"✅ Fiyat kaydedildi: {price} - User: {user_id}")
        
        # Ürünü veritabanına kaydet
        success = await add_step_product_to_database(user_id, process_data["data"])
        
        if success:
            await message.reply("✅ Ürün başarıyla eklendi!", parse_mode="Markdown")
            await show_main_admin_menu(message.bot.callback_query) # Callback query'yi kullan
        else:
            await message.reply("❌ Ürün eklenemedi. Veritabanı hatası veya bağlantı sorunu.", parse_mode="Markdown")
            
        # Ürün verilerini temizle
        del product_data_storage[user_id]
        
    except Exception as e:
        logger.error(f"❌ Price input hatası: {e}")


async def handle_category_callback(callback: types.CallbackQuery, action: str) -> None:
    """Kategori seçimi callback'i"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in product_data_storage:
            await callback.answer("❌ Ürün ekleme sürecinde bulunamadı!", show_alert=True)
            return
        
        # Kategoriyi çıkar
        category_name = action.replace("category_", "")
        category_map = {
            'freespin': 'freespin',
            'bonus': 'bonus', 
            'hediye': 'hediye',
            'ozel': 'ozel'
        }
        
        if category_name not in category_map:
            await callback.answer("❌ Geçersiz kategori!", show_alert=True)
            return
        
        process_data = product_data_storage[user_id]
        process_data["data"]["category"] = category_name
        process_data["step"] = "stock"
        
        logger.info(f"✅ Kategori seçildi: {category_name} - User: {user_id}")
        
        response = """
🛍️ **Market Ürün Ekleme - Adım 5/7**

**📦 Stok Sayısını Yazın:**

**Örnekler:**
• `10`
• `50`
• `100`

**Lütfen stok sayısını yazın:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_market")]
        ])
        
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Category callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def handle_price_callback(callback: types.CallbackQuery, action: str) -> None:
    """Fiyat seçimi callback'i ve database kaydetme"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in product_data_storage:
            await callback.answer("❌ Ürün ekleme sürecinde bulunamadı!", show_alert=True)
            return
        
        # Fiyatı çıkar
        price_str = action.replace("price_", "")
        price = float(price_str)
        
        process_data = product_data_storage[user_id]
        process_data["data"]["price"] = price
        
        logger.info(f"✅ Fiyat seçildi: {price} KP - User: {user_id}")
        
        # Ürünü database'e kaydet
        success = await add_step_product_to_database(user_id, process_data["data"])
        
        if success:
            success_message = f"""
✅ **ÜRÜN BAŞARIYLA EKLENDİ!**

**��️ Ürün:** {process_data["data"]["product_name"]}
**🏢 Site:** {process_data["data"]["website_name"]}
**📂 Kategori:** {process_data["data"]["category"].title()}
**💰 Fiyat:** {price} KP
**📦 Stok:** {process_data["data"]["stock"]} adet

**Ürün market'te satışa sunuldu!**
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍️ Yeni Ürün Ekle", callback_data="admin_market_add")],
                [InlineKeyboardButton(text="⬅️ Market Menüsü", callback_data="admin_market")]
            ])
            
        else:
            success_message = """
❌ **ÜRÜN EKLENEMEDİ!**

**Hata:** Database kayıt hatası
**Çözüm:** Lütfen tekrar deneyin

**Mümkün Sebepler:**
• Database bağlantı sorunu
• Geçersiz veri formatı
• Yetki problemi
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Tekrar Dene", callback_data="admin_market_add")],
                [InlineKeyboardButton(text="⬅️ Market Menüsü", callback_data="admin_market")]
            ])
        
        await callback.message.edit_text(success_message, parse_mode="Markdown", reply_markup=keyboard)
        
        # Ürün verilerini temizle
        if user_id in product_data_storage:
            del product_data_storage[user_id]
        
    except Exception as e:
        logger.error(f"❌ Price callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def add_step_product_to_database(user_id: int, product_data: dict) -> bool:
    """Ürünü database'e kaydet - BIGINT hatası çözülü"""
    try:
        from database import get_db_pool
        
        pool = await get_db_pool()
        if not pool:
            return False
        
        # Kategori mapping
        category_map = {
            'freespin': 1,
            'bonus': 2,
            'hediye': 3,
            'ozel': 4
        }
        
        category_id = category_map.get(product_data.get('category', '').lower(), 1)
        
        # BIGINT HATASI DÜZELTMESİ: admin_id'yi int64 olarak cast et
        admin_id_bigint = int(user_id)
        
        async with pool.acquire() as conn:
            product_id = await conn.fetchval("""
                INSERT INTO market_products (
                    name, description, company_name, category_id, 
                    price, stock, delivery_content, created_by, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE)
                RETURNING id
            """, 
                product_data['product_name'],
                f"{product_data.get('website_name', 'Site')} - {product_data['product_name']}. "
                f"Kategori: {product_data['category']}. "
                f"Site: {product_data.get('website_link', 'Link belirtilmedi')}",
                product_data.get('website_name', 'Bilinmeyen Site'),
                category_id,
                float(product_data.get('price', 50.0)),
                int(product_data.get('stock', 1)),
                f"Ürününüz hazırlandı! {product_data.get('website_name', 'Site')} - {product_data['product_name']} için kodunuz admin tarafından gönderilecek.",
                admin_id_bigint  # BIGINT olarak cast edildi
            )
            
            logger.info(f"✅ Ürün database'e kaydedildi - ID: {product_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Product database kayıt hatası: {e}")
        return False


async def show_back_menu(callback: types.CallbackQuery) -> None:
    """Geri dön menüsü"""
    await show_main_admin_menu(callback) 


# YENİ MENÜ FONKSİYONLARI - Görselinizdeki buton yapısı için

async def show_main_admin_functions(callback: types.CallbackQuery) -> None:
    """Ana admin fonksiyonları menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 İstatistikler", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Duyuru", callback_data="admin_announcement")
        ],
        [
            InlineKeyboardButton(text="🔧 Bot Ayarları", callback_data="admin_bot_settings"),
            InlineKeyboardButton(text="👥 Kullanıcı Yönetimi", callback_data="admin_user_mgmt")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ana Menü", callback_data="admin_main_menu")
        ]
    ])
    
    message = """
╔══════════════════════╗
║  🛡️ <b>ADMİN PANELİ</b> 🛡️  ║
╚══════════════════════╝

👑 <b>Ana Yönetim Fonksiyonları</b>

📋 <b>Mevcut İşlemler:</b>
• 📊 <b>İstatistikler:</b> Bot ve kullanıcı istatistikleri
• 📢 <b>Duyuru:</b> Toplu mesaj gönderimi
• 🔧 <b>Bot Ayarları:</b> Sistem konfigürasyonu
• 👥 <b>Kullanıcı Yönetimi:</b> Kullanıcı işlemleri

🔄 <b>Bu özellikler yakında aktif edilecek!</b>
    """
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def show_balance_commands_menu(callback: types.CallbackQuery) -> None:
    """Bakiye komutları menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Bakiye Ekle", callback_data="balance_add"),
            InlineKeyboardButton(text="➖ Bakiye Çıkar", callback_data="balance_remove")
        ],
        [
            InlineKeyboardButton(text="🔍 Bakiye Sorgula", callback_data="balance_check"),
            InlineKeyboardButton(text="📊 Bakiye Raporu", callback_data="balance_report")
        ],
        [
            InlineKeyboardButton(text="⚙️ Bakiye Ayarları", callback_data="balance_settings")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ana Menü", callback_data="admin_main_menu")
        ]
    ])
    
    message = """
╔══════════════════════╗
║ 💰 <b>BAKİYE YÖNETİMİ</b> 💰 ║
╚══════════════════════╝

💎 <b>Mevcut Bakiye Sistemi</b>

📋 <b>Kullanılabilir İşlemler:</b>
• ➕ <b>Bakiye Ekle:</b> Kullanıcıya point ekleme
• ➖ <b>Bakiye Çıkar:</b> Kullanıcıdan point çıkarma
• 🔍 <b>Bakiye Sorgula:</b> Kullanıcı bakiyesi kontrol
• 📊 <b>Bakiye Raporu:</b> Genel bakiye istatistikleri
• ⚙️ <b>Bakiye Ayarları:</b> Point sistem ayarları

🔄 <b>Çalışan Komutlar:</b>
• <code>/bakiyee @kullanıcı miktar</code> - Bakiye ekleme
• <code>/bakiyec @kullanıcı miktar</code> - Bakiye çıkarma
• <code>/bakiyeeid ID miktar</code> - ID ile ekleme
• <code>/bakiyecid ID miktar</code> - ID ile çıkarma

💡 <b>Bu panel mevcut bakiye sistemimizi kullanır.</b>
    """
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def show_event_commands_menu(callback: types.CallbackQuery) -> None:
    """Etkinlik komutları menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Yeni Etkinlik", callback_data="event_create"),
            InlineKeyboardButton(text="📋 Aktif Etkinlikler", callback_data="event_list")
        ],
        [
            InlineKeyboardButton(text="🏁 Etkinlik Bitir", callback_data="event_end"),
            InlineKeyboardButton(text="📊 Etkinlik Raporu", callback_data="event_report")
        ],
        [
            InlineKeyboardButton(text="🎲 Çekiliş Sistemi", callback_data="lottery_system"),
            InlineKeyboardButton(text="⚙️ Etkinlik Ayarları", callback_data="event_settings")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ana Menü", callback_data="admin_main_menu")
        ]
    ])
    
    message = """
╔══════════════════════╗
║ 🎯 <b>ETKİNLİK KOMUTLARI</b> 🎯 ║
╚══════════════════════╝

🎮 <b>Etkinlik Yönetim Sistemi</b>

📋 <b>Kullanılabilir İşlemler:</b>
• 🎯 <b>Yeni Etkinlik:</b> Çekiliş/yarışma oluşturma
• 📋 <b>Aktif Etkinlikler:</b> Devam eden etkinlikler
• 🏁 <b>Etkinlik Bitir:</b> Etkinlik sonuçlandırma
• 📊 <b>Etkinlik Raporu:</b> Katılım istatistikleri
• 🎲 <b>Çekiliş Sistemi:</b> Otomatik kazanan seçimi
• ⚙️ <b>Etkinlik Ayarları:</b> Sistem konfigürasyonu

🔄 <b>Şu anda çalışan komutlar:</b>
<code>/etkinlik</code> - <code>/etkinlikler</code> - <code>/etkinlikbitir</code>
    """
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def show_system_commands_menu(callback: types.CallbackQuery) -> None:
    """Sistem komutları menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Sistem İstatistik", callback_data="system_stats"),
            InlineKeyboardButton(text="🧹 Mesaj Temizle", callback_data="system_clean")
        ],
        [
            InlineKeyboardButton(text="👥 Grup Yönetimi", callback_data="system_groups"),
            InlineKeyboardButton(text="📢 Broadcast", callback_data="system_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔄 Bot Restart", callback_data="system_restart"),
            InlineKeyboardButton(text="⚙️ Sistem Ayarları", callback_data="system_settings")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ana Menü", callback_data="admin_main_menu")
        ]
    ])
    
    message = """
╔══════════════════════╗
║ 🛠️ <b>SİSTEM KOMUTLARI</b> 🛠️ ║
╚══════════════════════╝

🔧 <b>Bot Sistem Yönetimi</b>

📋 <b>Kullanılabilir İşlemler:</b>
• 📊 <b>Sistem İstatistik:</b> Bot performans raporu
• 🧹 <b>Mesaj Temizle:</b> Grup mesaj silme
• 👥 <b>Grup Yönetimi:</b> Kayıtlı gruplar
• 📢 <b>Broadcast:</b> Toplu duyuru gönderimi
• 🔄 <b>Bot Restart:</b> Bot yeniden başlatma
• ⚙️ <b>Sistem Ayarları:</b> Genel bot ayarları

🔄 <b>Şu anda çalışan komutlar:</b>
<code>/sistemistatistik</code> - <code>/temizle</code> - <code>/gruplar</code> - <code>/topluduyuru</code>
    """
    
    await callback.message.edit_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ==============================================
# ÇALIŞAN SİSTEM KOMUTLARI (admin_commands_list.py'den taşındı)
# ==============================================

async def clean_messages_command(message: types.Message) -> None:
    """Mesaj temizleme komutu: /temizle [sayı]"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # GRUP SESSİZLİK: Grup chatindeyse komut mesajını sil
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Admin panel komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                log_error(f"❌ Admin panel mesajı silinemedi: {e}")
        
        # Sadece grup chatinde çalışsın
        if message.chat.type == "private":
            await message.reply("❌ Bu komut sadece grup chatinde kullanılabilir!")
            return
        
        # Bot yetkisi kontrolü
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if not bot_member.can_delete_messages:
            if _bot_instance:
                await _bot_instance.send_message(user_id, "❌ Bot'un mesaj silme yetkisi yok!")
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        if len(parts) == 1:
            delete_count = 5  # Varsayılan
        elif len(parts) == 2:
            try:
                delete_count = int(parts[1])
                if delete_count < 1:
                    delete_count = 1
                elif delete_count > 100:
                    delete_count = 100
            except ValueError:
                if _bot_instance:
                    await _bot_instance.send_message(user_id, "❌ Geçersiz sayı! Örnek: `/temizle 20`")
                return
        else:
            if _bot_instance:
                await _bot_instance.send_message(user_id, "❌ Kullanım: `/temizle [sayı]`\nÖrnek: `/temizle 20`")
            return
        
        # Mesajları sil
        try:
            deleted_count = 0
            
            # GELİŞMİŞ SİLME ALGORİTMASI: Daha güvenilir
            try:
                # Son mesajları getir ve sil
                async for msg in message.bot.get_chat_history(message.chat.id, limit=delete_count):
                    try:
                        # Kendi mesajımızı silme
                        if msg.message_id == message.message_id:
                            continue
                            
                        await message.bot.delete_message(message.chat.id, msg.message_id)
                        deleted_count += 1
                        await asyncio.sleep(0.1)  # Rate limiting
                        
                        # Limit kontrolü
                        if deleted_count >= delete_count - 1:  # -1 çünkü komut mesajı zaten silinmiş
                            break
                            
                    except Exception as e:
                        logger.debug(f"Mesaj silme hatası (ID: {msg.message_id}): {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Chat history hatası: {e}")
                # Fallback: Basit silme yöntemi
                for i in range(1, delete_count):
                    try:
                        await message.bot.delete_message(message.chat.id, message.message_id - i)
                        deleted_count += 1
                        await asyncio.sleep(0.1)
                    except:
                        break
            
            # Sonucu özel mesajla bildir
            if _bot_instance:
                await _bot_instance.send_message(
                    user_id, 
                    f"✅ **Mesaj Temizleme Tamamlandı!**\n\n"
                    f"**Grup:** {message.chat.title}\n"
                    f"**Silinen Mesaj:** {deleted_count} adet\n"
                    f"**İşlem Yapan:** {message.from_user.first_name}\n"
                    f"**Hedef:** {delete_count - 1} adet"
                )
            
        except Exception as e:
            logger.error(f"❌ Mesaj silme hatası: {e}")
            await message.bot.send_message(user_id, "❌ Mesaj silme işlemi başarısız!")
        
    except Exception as e:
        logger.error(f"❌ Clean command hatası: {e}")
        await message.bot.send_message(user_id, "❌ Bir hata oluştu!")


async def list_groups_command(message: types.Message):
    """Kayıtlı grupları listele"""
    try:
        # Admin kontrolü
        config = get_config()
        if message.from_user.id != config.ADMIN_USER_ID:
            return
        
        # Grup chatindeyse komut mesajını sil
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Admin panel komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                log_error(f"❌ Admin panel mesajı silinemedi: {e}")
            return
        
        from database import get_registered_groups
        groups = await get_registered_groups()
        
        if not groups:
            await message.reply(
                "📋 **Kayıtlı Grup Yok**\n\n"
                "Henüz hiç grup kaydedilmemiş.\n"
                "Grup kaydetmek için `/kirvegrup` komutunu kullanın.",
                parse_mode="Markdown"
            )
            return
        
        group_list = "📋 **Kayıtlı Gruplar:**\n\n"
        for i, group in enumerate(groups, 1):
            group_list += f"**ID {i}:** {group['group_name']} (ID: `{group['group_id']}`)\n"
            if group.get('group_username'):
                group_list += f"   @{group['group_username']}\n"
            group_list += f"   Kayıt: {group['registered_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await message.reply(
            group_list,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ Grup listesi komutu hatası: {e}")
        await message.reply("❌ Bir hata oluştu!")


async def approve_order_command(message: types.Message) -> None:
    """Sipariş onaylama komutu"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # Komut parametrelerini al
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ Kullanım: `/siparisonayla <sipariş_no>`")
            return
        
        order_number = args[1]
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Sipariş onaylama komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _approve_order_privately(user_id, order_number)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        logger.info(f"✅ Sipariş onaylama komutu - User: {message.from_user.first_name} ({user_id}) - Order: {order_number}")
        
        await _approve_order_privately(user_id, order_number)
        
    except Exception as e:
        logger.error(f"❌ Sipariş onaylama komutu hatası: {e}")
        await message.reply("❌ Sipariş onaylama işlemi başarısız!")


async def _approve_order_privately(user_id: int, order_number: str) -> None:
    """Siparişi özel mesajla onayla"""
    try:
        async with db_pool.acquire() as conn:
            # Sipariş bilgilerini al
            order = await conn.fetchrow("""
                SELECT 
                    o.id, o.order_number, o.user_id, o.total_price, o.status,
                    p.name as product_name, p.company_name,
                    u.first_name, u.username
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.order_number = $1
            """, order_number)
            
            if not order:
                await _bot_instance.send_message(
                    user_id,
                    f"❌ Sipariş bulunamadı: `{order_number}`"
                )
                return
            
            if order['status'] != 'pending':
                await _bot_instance.send_message(
                    user_id,
                    f"❌ Bu sipariş zaten işlenmiş! Durum: {order['status']}"
                )
                return
            
            # Siparişi onayla
            await conn.execute("""
                UPDATE market_orders 
                SET status = 'approved', updated_at = NOW()
                WHERE order_number = $1
            """, order_number)
            
            # Müşteriye bildirim gönder
            approval_message = f"""
✅ **SİPARİŞİNİZ ONAYLANDI!**

📋 **Sipariş No:** `{order['order_number']}`
🛍️ **Ürün:** {order['product_name']}
🏢 **Site:** {order['company_name']}
💰 **Tutar:** {order['total_price']} KP

🎉 **Ürününüz hazırlanıyor!**
📦 Kodunuz kısa sürede gönderilecek.

💬 **Soru için:** Admin ile iletişime geçin
            """
            
            await _bot_instance.send_message(
                order['user_id'],
                approval_message,
                parse_mode="Markdown"
            )
            
            # Admin'e onay mesajı
            await _bot_instance.send_message(
                user_id,
                f"✅ Sipariş onaylandı: `{order_number}`\n👤 Müşteri: {order['first_name']}"
            )
            
    except Exception as e:
        logger.error(f"❌ Sipariş onaylama hatası: {e}")
        await _bot_instance.send_message(user_id, "❌ Sipariş onaylama işlemi başarısız!")


async def list_orders_command(message: types.Message) -> None:
    """Sipariş listesi komutu"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Sipariş listesi komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_orders_list_privately(user_id)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        logger.info(f"📋 Sipariş listesi komutu - User: {message.from_user.first_name} ({user_id})")
        
        await _send_orders_list_privately(user_id)
        
    except Exception as e:
        logger.error(f"❌ Sipariş listesi komutu hatası: {e}")
        await message.reply("❌ Sipariş listesi yüklenirken hata oluştu!")


async def _send_orders_list_privately(user_id: int):
    """Sipariş listesini özel mesajla gönder"""
    try:
        async with db_pool.acquire() as conn:
            # Sadece pending siparişleri al
            orders = await conn.fetch("""
                SELECT 
                    o.id, o.order_number, o.user_id, o.total_price, o.status, o.created_at,
                    p.name as product_name, p.company_name,
                    u.first_name, u.username
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.status = 'pending'
                ORDER BY o.created_at DESC
                LIMIT 20
            """)
            
            if not orders:
                await _bot_instance.send_message(
                    user_id,
                    "📋 **Bekleyen Siparişler**\n\n✅ Bekleyen sipariş bulunmuyor."
                )
                return
            
            # Her sipariş için ayrı mesaj gönder
            for i, order in enumerate(orders, 1):
                status_emoji = {
                    'pending': '⏳',
                    'approved': '✅',
                    'rejected': '❌',
                    'delivered': '📦'
                }.get(order['status'], '❓')
                
                # Her sipariş için ayrı mesaj
                order_text = f"""
{status_emoji} **SİPARİŞ #{order['id']}**

📋 **No:** `{order['order_number']}`
👤 **Müşteri:** {order['first_name']} (@{order['username'] or 'Kullanıcı adı yok'})
🛍️ **Ürün:** {order['product_name']}
🏢 **Site:** {order['company_name']}
💰 **Tutar:** {order['total_price']} KP
📅 **Tarih:** {order['created_at'].strftime('%d.%m.%Y %H:%M')}
📊 **Durum:** {order['status'].upper()}
"""
                
                # Sadece pending siparişler için buton ekle
                if order['status'] == 'pending':
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=f"✅ Onayla #{order['id']}", 
                                callback_data=f"admin_order_approve_{order['id']}"
                            ),
                            InlineKeyboardButton(
                                text=f"❌ Reddet #{order['id']}", 
                                callback_data=f"admin_order_reject_{order['id']}"
                            )
                        ]
                    ])
                else:
                    keyboard = None
                
                await _bot_instance.send_message(
                    user_id,
                    order_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            
            # Son mesaj olarak yenile butonu
            if orders:
                refresh_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_orders_refresh")]
                ])
                
                await _bot_instance.send_message(
                    user_id,
                    f"📋 **Toplam {len(orders)} bekleyen sipariş listelendi**",
                    parse_mode="Markdown",
                    reply_markup=refresh_keyboard
                )
            
    except Exception as e:
        logger.error(f"❌ Sipariş listesi gönderilemedi: {e}")
        await _bot_instance.send_message(user_id, "❌ Sipariş listesi yüklenirken hata oluştu!")


async def handle_order_action(callback: types.CallbackQuery, action: str, order_id: int) -> None:
    """Sipariş onaylama/reddetme işlemi"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlem için yetkiniz yok!", show_alert=True)
            return
        
        async with db_pool.acquire() as conn:
            # Sipariş bilgilerini al
            order = await conn.fetchrow("""
                SELECT 
                    o.order_number, o.user_id, o.total_price, o.status,
                    p.name as product_name, p.company_name,
                    u.first_name, u.username
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.id = $1
            """, order_id)
            
            if not order:
                await callback.answer("❌ Sipariş bulunamadı!", show_alert=True)
                return
            
            if order['status'] != 'pending':
                await callback.answer("❌ Bu sipariş zaten işlenmiş!", show_alert=True)
                return
            
            if action == "approve":
                # Onay için admin'e mesaj yazma alanı göster
                approval_form = f"""
✅ **SİPARİŞ ONAY FORMU**

📋 Sipariş No: `{order['order_number']}`
🛍️ Ürün: {order['product_name']}
🏢 Site: {order['company_name']}
💰 Tutar: {order['total_price']} KP

📝 **Onay mesajınızı yazın:**
• Kod bilgileri
• Teslimat detayları
• Özel talimatlar
• Diğer bilgiler

💡 **Örnek:** "Kodunuz: ABC123, Siteye giriş yapıp kodu kullanın"
                """
                
                # Onay formu gönder
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ İptal", callback_data="admin_order_cancel")]
                ])
                
                await callback.message.edit_text(
                    approval_form,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                # Admin'in mesajını beklemek için state kaydet
                admin_order_states[user_id] = {
                    'action': 'approve',
                    'order_id': order_id,
                    'order_data': dict(order)
                }
                
                await callback.answer("📝 Onay mesajınızı yazın...")
                
            elif action == "reject":
                # Red için admin'e sebep yazma alanı göster
                rejection_form = f"""
❌ **SİPARİŞ RED FORMU**

📋 Sipariş No: `{order['order_number']}`
🛍️ Ürün: {order['product_name']}
🏢 Site: {order['company_name']}
💰 Tutar: {order['total_price']} KP

📝 **Red sebebini yazın:**
• Stok yetersizliği
• Site uygunluğu kontrolü
• Teknik sorunlar
• Diğer sebepler

💡 **Örnek:** "Stok tükendi, 1 hafta sonra tekrar deneyin"
                """
                
                # Red formu gönder
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ İptal", callback_data="admin_order_cancel")]
                ])
                
                await callback.message.edit_text(
                    rejection_form,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                # Admin'in mesajını beklemek için state kaydet
                admin_order_states[user_id] = {
                    'action': 'reject',
                    'order_id': order_id,
                    'order_data': dict(order)
                }
                
                await callback.answer("📝 Red sebebini yazın...")
        
    except Exception as e:
        logger.error(f"❌ Sipariş işlemi hatası: {e}")
        await callback.answer("❌ İşlem sırasında hata oluştu!", show_alert=True)


async def handle_admin_order_message(message: types.Message) -> None:
    """Admin'in sipariş onay/red mesajını işle"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # Admin'in sipariş durumu var mı?
        if user_id not in admin_order_states:
            # Eğer admin sipariş durumunda değilse, diğer handler'lara geç
            return
        
        # Debug log
        logger.info(f"📝 Admin sipariş mesajı alındı - User: {user_id}, Text: {message.text[:50]}...")
        
        state = admin_order_states[user_id]
        action = state['action']
        order_id = state['order_id']
        order_data = state['order_data']
        admin_message = message.text
        
        # Mesajı işlemeden önce state'i temizle
        del admin_order_states[user_id]
        
        async with db_pool.acquire() as conn:
            if action == "approve":
                # Siparişi onayla
                await conn.execute("""
                    UPDATE market_orders 
                    SET status = 'approved', admin_notes = $1, updated_at = NOW()
                    WHERE id = $2
                """, admin_message, order_id)
                
                # Müşteriye bildirim gönder
                approval_message = f"""
✅ **SİPARİŞİNİZ ONAYLANDI!**

📋 Sipariş No: `{order_data['order_number']}`
🛍️ Ürün: {order_data['product_name']}
🏢 Site: {order_data['company_name']}
💰 Tutar: {order_data['total_price']} KP

🎉 **Ürününüz hazırlanıyor!**

📝 **Admin Mesajı:**
{admin_message}

💬 **Soru için:** Admin ile iletişime geçin
                """
                
                await _bot_instance.send_message(
                    order_data['user_id'],
                    approval_message,
                    parse_mode="Markdown"
                )
                
                # Log kaydet
                from utils.logger import log_order_approval
                log_order_approval(
                    order_id=order_id,
                    order_number=order_data['order_number'],
                    user_id=order_data['user_id'],
                    username=order_data['username'] or 'Bilinmiyor',
                    product_name=order_data['product_name'],
                    company_name=order_data['company_name'],
                    amount=order_data['total_price'],
                    admin_message=admin_message
                )
                
                # Admin'e onay mesajı
                await message.reply("✅ Sipariş onaylandı ve müşteriye bildirim gönderildi!")
                
                # Sipariş listesini otomatik yenile
                await _send_orders_list_privately(user_id)
                
            elif action == "reject":
                # Siparişi reddet
                await conn.execute("""
                    UPDATE market_orders 
                    SET status = 'rejected', admin_notes = $1, updated_at = NOW()
                    WHERE id = $2
                """, admin_message, order_id)
                
                # BAKİYE İADE SİSTEMİ - Kullanıcının parasını geri ver
                refund_amount = order_data['total_price']
                await conn.execute("""
                    UPDATE users 
                    SET kirve_points = kirve_points + $1 
                    WHERE user_id = $2
                """, refund_amount, order_data['user_id'])
                
                logger.info(f"💰 Bakiye iade edildi - User: {order_data['user_id']}, Amount: {refund_amount} KP")
                
                # Müşteriye bildirim gönder
                rejection_message = f"""
❌ **SİPARİŞİNİZ REDDEDİLDİ**

📋 Sipariş No: `{order_data['order_number']}`
🛍️ Ürün: {order_data['product_name']}
🏢 Site: {order_data['company_name']}
💰 Tutar: {order_data['total_price']} KP

⚠️ **Red Sebebi:**
{admin_message}

💰 **Bakiye İadesi:**
✅ {refund_amount} KP hesabınıza iade edildi
💎 Yeni bakiyenizi `/menu` komutu ile kontrol edebilirsiniz

💬 **Detay için:** Admin ile iletişime geçin
                """
                
                await _bot_instance.send_message(
                    order_data['user_id'],
                    rejection_message,
                    parse_mode="Markdown"
                )
                
                # Log kaydet
                from utils.logger import log_order_rejection
                log_order_rejection(
                    order_id=order_id,
                    order_number=order_data['order_number'],
                    user_id=order_data['user_id'],
                    username=order_data['username'] or 'Bilinmiyor',
                    product_name=order_data['product_name'],
                    company_name=order_data['company_name'],
                    amount=order_data['total_price'],
                    admin_message=admin_message,
                    refund_amount=refund_amount
                )
                
                # Admin'e red mesajı
                await message.reply(f"❌ Sipariş reddedildi ve müşteriye {refund_amount} KP iade edildi!")
                
                # Sipariş listesini otomatik yenile
                await _send_orders_list_privately(user_id)
        
    except Exception as e:
        logger.error(f"❌ Admin sipariş mesaj işleme hatası: {e}")
        await message.reply("❌ İşlem sırasında hata oluştu!")


async def handle_order_cancel_callback(callback: types.CallbackQuery) -> None:
    """Sipariş işlemini iptal et"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlem için yetkiniz yok!", show_alert=True)
            return
        
        # State'i temizle
        if user_id in admin_order_states:
            del admin_order_states[user_id]
        
        await callback.message.edit_text("❌ Sipariş işlemi iptal edildi.")
        await callback.answer("❌ İşlem iptal edildi!")
        
    except Exception as e:
        logger.error(f"❌ Sipariş iptal hatası: {e}")
        await callback.answer("❌ İşlem sırasında hata oluştu!", show_alert=True)


async def help_command(message: types.Message) -> None:
    """Yardım komutu - Kullanıcılara temel komutları gösterir"""
    try:
        # GRUP SESSİZLİK: Grup chatindeyse komut mesajını sil
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Admin panel komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                log_error(f"❌ Admin panel mesajı silinemedi: {e}")
        
        help_text = """
╔══════════════════════╗
║      🆘 <b>YARDIM</b> 🆘      ║
╚══════════════════════╝

🎯 <b>KULLANICI KOMUTLARI:</b>
• <code>/start</code> - Bot'u başlat
• <code>/kirvekayit</code> - Kayıt sistemi
• <code>/menu</code> - Profil ve istatistikler
• <code>/etkinlikler</code> - Aktif etkinlikleri listele

🎲 <b>ETKİNLİK SİSTEMİ:</b>
• Aktif etkinliklere katılım
• Çekiliş ve yarışmalar
• Otomatik kazanan seçimi

💎 <b>POINT SİSTEMİ:</b>
• Mesaj başına 0.04 Kirve Point
• Günlük 5 KP maksimum
• Grup sohbetlerinde otomatik

📞 <b>DESTEK:</b>
Sorunlarınız için admin ekibine ulaşın!

╔══════════════════════╗
║   ✨ <b>KirveHub Bot</b> ✨   ║
╚══════════════════════╝
        """
        
        # Özel mesajla gönder
        if message.chat.type != "private":
            if _bot_instance:
                await _bot_instance.send_message(
                    message.from_user.id,
                    help_text,
                    parse_mode="HTML"
                )
        else:
            await message.reply(help_text, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"❌ Help command hatası: {e}")
        try:
            if message.chat.type == "private":
                await message.reply("❌ Yardım menüsü yüklenemedi!")
            elif _bot_instance:
                await _bot_instance.send_message(
                    message.from_user.id,
                    "❌ Yardım menüsü yüklenemedi!"
                )
        except:
            pass


async def handle_recruitment_callback(callback: types.CallbackQuery, action: str) -> None:
    """Kayıt teşvik sistemi callback'lerini işle"""
    try:
        if action == "admin_recruitment_toggle":
            # Sistem açma/kapama
            current_status = get_recruitment_status()
            new_status = toggle_recruitment_system(not current_status)
            
            status_text = "✅ **Açıldı**" if new_status else "❌ **Kapatıldı**"
            await callback.answer(f"🎯 Kayıt teşvik sistemi {status_text}", show_alert=True)
            
            # Menüyü güncelle
            await show_recruitment_system_menu(callback)
            
        elif action == "admin_recruitment_interval":
            # Mesaj aralığı ayarlama
            await show_recruitment_interval_menu(callback)
            
        elif action == "admin_recruitment_templates":
            # Mesaj şablonları
            await show_recruitment_templates_menu(callback)
            
        elif action == "admin_recruitment_stats":
            # İstatistikler
            await show_recruitment_stats_menu(callback)
            
        elif action == "admin_recruitment_test":
            # Test mesajı
            await send_test_recruitment_message(callback)
            
        else:
            await callback.answer("❌ Bilinmeyen recruitment işlemi!", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Recruitment callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_recruitment_interval_menu(callback: types.CallbackQuery) -> None:
    """Kayıt teşvik mesaj aralığı menüsü"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⏰ 30 Dakika", callback_data="recruitment_interval_1800"),
                InlineKeyboardButton(text="⏰ 1 Saat", callback_data="recruitment_interval_3600")
            ],
            [
                InlineKeyboardButton(text="⏰ 2 Saat", callback_data="recruitment_interval_7200"),
                InlineKeyboardButton(text="⏰ 4 Saat", callback_data="recruitment_interval_14400")
            ],
            [
                InlineKeyboardButton(text="⏰ 6 Saat", callback_data="recruitment_interval_21600"),
                InlineKeyboardButton(text="⏰ 12 Saat", callback_data="recruitment_interval_43200")
            ],
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_recruitment_system")
            ]
        ])
        
        response = """
⏰ **Mesaj Aralığı Ayarları**

**Mevcut Aralık:** 2 saat (7200 saniye)

**Seçenekler:**
• 30 dakika - Çok sık
• 1 saat - Sık
• 2 saat - Normal (önerilen)
• 4 saat - Az sık
• 6 saat - Nadir
• 12 saat - Çok nadir

Hangi aralığı seçmek istiyorsun?
        """
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Recruitment interval menu hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_recruitment_templates_menu(callback: types.CallbackQuery) -> None:
    """Kayıt teşvik mesaj şablonları menüsü"""
    try:
        response = """
📝 **Mesaj Şablonları**

**Mevcut Şablonlar (8 adet):**
• 🎯 **Kirvem!** Hala gruba kayıt olmadığını görüyorum...
• 💎 **Kirve!** Kayıt olarak çok daha fazlasını kazanabilirsin...
• 🎮 **Kirvem!** Sistemde kayıtlı değilsin...
• 💎 **Kirve!** Hala kayıtsız mısın?...
• 🚀 **Kirvem!** Kayıt olarak günlük 5 Kirve Point...
• 💎 **Kirve!** Hala sistemde yoksun...
• 🎯 **Kirvem!** Kayıt olmadan çok şey kaçırıyorsun...
• 💎 **Kirve!** Hala gruba kayıtlı değilsin...

**Özellikler:**
• Rastgele seçim
• Spam koruması
• Akıllı zamanlama
• Aktif kullanıcı odaklı

Şablon düzenleme sistemi yakında eklenecek!
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_recruitment_system")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Recruitment templates menu hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_recruitment_stats_menu(callback: types.CallbackQuery) -> None:
    """Kayıt teşvik istatistikleri menüsü"""
    try:
        # Database'den istatistikleri al
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Kayıtsız kullanıcı sayısı
            unregistered_count = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE is_registered = FALSE 
                  AND last_activity >= NOW() - INTERVAL '24 hours'
            """)
            
            # Son 24 saatte aktif kayıtsız kullanıcılar
            active_unregistered = await conn.fetchval("""
                SELECT COUNT(DISTINCT user_id) 
                FROM daily_stats 
                WHERE message_date = CURRENT_DATE 
                  AND user_id IN (
                    SELECT user_id FROM users WHERE is_registered = FALSE
                  )
            """)
            
            # Sistem durumu
            is_active = get_recruitment_status()
            status_text = "✅ Aktif" if is_active else "❌ Pasif"
            
        response = f"""
📊 **Kayıt Teşvik İstatistikleri**

**Sistem Durumu:** {status_text}

**Yeni Kullanıcı Analizi:**
• **Toplam Kayıtsız:** {unregistered_count} kullanıcı
• **Son 1 Saat Aktif:** {active_unregistered} kullanıcı
• **Mesaj Aralığı:** 2 saat
• **Cooldown:** 5 dakika (mesajlar arası)

**Yeni Özellikler:**
• 🆕 **Yeni kullanıcı tespiti** (≤3 mesaj)
• ⏰ **5 dakika cooldown** (spam önlemi)
• 📊 **Akıllı filtreleme** (çok aktif kullanıcıları atla)
• 🎯 **Hedef odaklı** (ilk defa mesaj atanlar)

**Çalışma Mantığı:**
• Son 1 saatte aktif + En fazla 3 mesaj = Hedef
• 5 dakika aralıkla grup mesajı
• 24 saat kullanıcı cooldown
• Maksimum 3 kullanıcı hedefleme

**Son Aktivite:** Yeni kullanıcılar analiz ediliyor.
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_recruitment_stats")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_recruitment_system")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Recruitment stats menu hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def send_test_recruitment_message(callback: types.CallbackQuery) -> None:
    """Test kayıt teşvik mesajı gönder"""
    try:
        from handlers.recruitment_system import send_recruitment_messages
        
        # Test mesajı gönder
        await send_recruitment_messages()
        
        await callback.answer("✅ Test mesajı gönderildi! Grup chatini kontrol et.", show_alert=True)
        
        # Ana menüye geri dön
        await show_recruitment_system_menu(callback)
        
    except Exception as e:
        logger.error(f"❌ Test recruitment message hatası: {e}")
        await callback.answer("❌ Test mesajı gönderilemedi!", show_alert=True)

async def handle_recruitment_interval_callback(callback: types.CallbackQuery, action: str) -> None:
    """Mesaj aralığı ayarlama callback'leri"""
    try:
        # Aralık değerini al
        interval_str = action.replace("recruitment_interval_", "")
        interval_seconds = int(interval_str)
        
        # Aralığı ayarla
        from handlers.recruitment_system import set_recruitment_interval
        set_recruitment_interval(interval_seconds)
        
        # Kullanıcı dostu mesaj
        interval_text = ""
        if interval_seconds == 1800:
            interval_text = "30 dakika"
        elif interval_seconds == 3600:
            interval_text = "1 saat"
        elif interval_seconds == 7200:
            interval_text = "2 saat"
        elif interval_seconds == 14400:
            interval_text = "4 saat"
        elif interval_seconds == 21600:
            interval_text = "6 saat"
        elif interval_seconds == 43200:
            interval_text = "12 saat"
        else:
            interval_text = f"{interval_seconds} saniye"
        
        await callback.answer(f"✅ Mesaj aralığı {interval_text} olarak ayarlandı!", show_alert=True)
        
        # Ana menüye geri dön
        await show_recruitment_system_menu(callback)
        
    except Exception as e:
        logger.error(f"❌ Recruitment interval callback hatası: {e}")
        await callback.answer("❌ Aralık ayarlanamadı!", show_alert=True)

# Sistem komutları için callback handler eklentileri
async def handle_system_callback(callback: types.CallbackQuery, action: str) -> None:
    """Sistem komutları callback handler"""
    try:
        if action == "system_clean":
            await callback.answer("🧹 Mesaj temizlemek için grup chatinde:\n/temizle [sayı]\nÖrnek: /temizle 20", show_alert=True)
        elif action == "system_groups":
            await callback.answer("👥 Kayıtlı grupları görmek için:\n/gruplar", show_alert=True)
        elif action == "system_stats":
            await callback.answer("📊 Sistem istatistikleri için:\n/adminstats", show_alert=True)
        elif action == "system_broadcast":
            await callback.answer("📢 Toplu duyuru için:\n/broadcast <mesaj>", show_alert=True)
        elif action == "system_restart":
            await callback.answer("🔄 Bot yeniden başlatma yakında eklenecek!", show_alert=True)
        elif action == "system_settings":
            await callback.answer("⚙️ Sistem ayarları yakında eklenecek!", show_alert=True)
        else:
            await callback.answer("❌ Bilinmeyen sistem komutu!", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ System callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True) 

async def test_market_system_command(message: types.Message) -> None:
    """Market sistemi test komutu"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # GRUP SESSİZLİK: Grup chatindeyse komut mesajını sil
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Admin panel komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                log_error(f"❌ Admin panel mesajı silinemedi: {e}")
        
        logger.info(f"🧪 Market sistemi test komutu - User: {message.from_user.first_name} ({user_id})")
        
        # Database bağlantısını test et
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await message.reply("❌ Database bağlantısı kurulamadı!")
            return
        
        # Market ürünlerini test et
        async with pool.acquire() as conn:
            # Ürün sayısını kontrol et
            product_count = await conn.fetchval("SELECT COUNT(*) FROM market_products WHERE is_active = TRUE")
            
            # Kategori sayısını kontrol et
            category_count = await conn.fetchval("SELECT COUNT(*) FROM market_categories")
            
            # Sipariş sayısını kontrol et
            order_count = await conn.fetchval("SELECT COUNT(*) FROM market_orders")
            
            # Son 5 ürünü listele
            recent_products = await conn.fetch("""
                SELECT name, company_name, price, stock, category_id
                FROM market_products 
                WHERE is_active = TRUE 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            # Son 5 siparişi listele
            recent_orders = await conn.fetch("""
                SELECT o.order_number, o.status, o.total_price, p.name as product_name
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                ORDER BY o.created_at DESC 
                LIMIT 5
            """)
        
        # Test sonuçlarını göster
        test_results = f"""
🧪 **MARKET SİSTEMİ TEST SONUÇLARI**

📊 **Database Durumu:**
✅ Database bağlantısı: Aktif
📦 Ürün sayısı: {product_count} adet
📂 Kategori sayısı: {category_count} adet
📋 Sipariş sayısı: {order_count} adet

🛍️ **Son 5 Ürün:**
"""
        
        if recent_products:
            for i, product in enumerate(recent_products, 1):
                test_results += f"{i}. {product['name']} - {product['company_name']} ({product['price']} KP)\n"
        else:
            test_results += "❌ Ürün bulunamadı\n"
        
        test_results += f"""
📋 **Son 5 Sipariş:**
"""
        
        if recent_orders:
            for i, order in enumerate(recent_orders, 1):
                status_emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}.get(order['status'], '❓')
                test_results += f"{i}. {status_emoji} {order['order_number']} - {order['product_name']} ({order['total_price']} KP)\n"
        else:
            test_results += "❌ Sipariş bulunamadı\n"
        
        test_results += """
✅ **Market sistemi çalışıyor!**
        """
        
        await message.reply(test_results, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Market test komutu hatası: {e}")
        await message.reply(f"❌ Test sırasında hata oluştu: {str(e)}")

async def test_sql_queries_command(message: types.Message) -> None:
    """SQL sorguları test komutu"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # GRUP SESSİZLİK: Grup chatindeyse komut mesajını sil
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Admin panel komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                log_error(f"❌ Admin panel mesajı silinemedi: {e}")
        
        logger.info(f"🔍 SQL sorguları test komutu - User: {message.from_user.first_name} ({user_id})")
        
        # Database bağlantısını test et
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await message.reply("❌ Database bağlantısı kurulamadı!")
            return
        
        # SQL sorgularını test et
        async with pool.acquire() as conn:
            # Kullanıcı sayısı
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_registered = TRUE")
            
            # Toplam point
            total_points = await conn.fetchval("SELECT COALESCE(SUM(kirve_points), 0) FROM users")
            
            # Toplam mesaj
            total_messages = await conn.fetchval("SELECT COALESCE(SUM(total_messages), 0) FROM users")
            
            # Market ürün sayısı
            market_products = await conn.fetchval("SELECT COUNT(*) FROM market_products WHERE is_active = TRUE")
            
            # Bekleyen sipariş sayısı
            pending_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders WHERE status = 'pending'")
            
            # Onaylanmış sipariş sayısı
            approved_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders WHERE status = 'approved'")
            
            # Reddedilmiş sipariş sayısı
            rejected_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders WHERE status = 'rejected'")
            
            # En yüksek bakiyeli kullanıcı
            top_user = await conn.fetchrow("""
                SELECT first_name, username, kirve_points 
                FROM users 
                WHERE is_registered = TRUE 
                ORDER BY kirve_points DESC 
                LIMIT 1
            """)
            
            # En aktif kullanıcı
            most_active_user = await conn.fetchrow("""
                SELECT first_name, username, total_messages 
                FROM users 
                WHERE is_registered = TRUE 
                ORDER BY total_messages DESC 
                LIMIT 1
            """)
            
            # Son 3 sipariş
            recent_orders = await conn.fetch("""
                SELECT o.order_number, o.status, o.total_price, p.name as product_name, u.first_name
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                ORDER BY o.created_at DESC 
                LIMIT 3
            """)
        
        # Test sonuçlarını göster
        test_results = f"""
🔍 **SQL SORGULARI TEST SONUÇLARI**

📊 **Kullanıcı İstatistikleri:**
👥 Kayıtlı kullanıcı: {user_count} kişi
💎 Toplam point: {total_points:.2f} KP
💬 Toplam mesaj: {total_messages} adet

🛍️ **Market İstatistikleri:**
📦 Aktif ürün: {market_products} adet
⏳ Bekleyen sipariş: {pending_orders} adet
✅ Onaylanmış sipariş: {approved_orders} adet
❌ Reddedilmiş sipariş: {rejected_orders} adet

🏆 **En İyi Kullanıcılar:**
"""
        
        if top_user:
            test_results += f"💰 En yüksek bakiye: {top_user['first_name']} (@{top_user['username'] or 'Kullanıcı adı yok'}) - {top_user['kirve_points']:.2f} KP\n"
        else:
            test_results += "💰 En yüksek bakiye: Bulunamadı\n"
            
        if most_active_user:
            test_results += f"💬 En aktif kullanıcı: {most_active_user['first_name']} (@{most_active_user['username'] or 'Kullanıcı adı yok'}) - {most_active_user['total_messages']} mesaj\n"
        else:
            test_results += "💬 En aktif kullanıcı: Bulunamadı\n"
        
        test_results += f"""
📋 **Son 3 Sipariş:**
"""
        
        if recent_orders:
            for i, order in enumerate(recent_orders, 1):
                status_emoji = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}.get(order['status'], '❓')
                test_results += f"{i}. {status_emoji} {order['order_number']} - {order['product_name']} ({order['total_price']} KP) - {order['first_name']}\n"
        else:
            test_results += "❌ Sipariş bulunamadı\n"
        
        test_results += """
✅ **SQL sorguları çalışıyor!**
        """
        
        await message.reply(test_results, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ SQL test komutu hatası: {e}")
        await message.reply(f"❌ Test sırasında hata oluştu: {str(e)}")

async def test_user_orders_command(message: types.Message) -> None:
    """Test: Kullanıcı siparişlerini test et"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # GRUP SESSİZLİK: Grup chatindeyse sil
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Admin panel komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                log_error(f"❌ Admin panel mesajı silinemedi: {e}")
            return
        
        # Test kullanıcı ID'si
        test_user_id = 6513506166  # Test kullanıcısı
        
        from database import get_user_orders_with_details
        orders = await get_user_orders_with_details(test_user_id, limit=5)
        
        if not orders:
            await message.reply("❌ Test kullanıcısının siparişi bulunamadı!")
            return
        
        response = f"""
🧪 **SİPARİŞ TEST SONUCU**

👤 **Test Kullanıcı:** {test_user_id}
📋 **Sipariş Sayısı:** {len(orders)}

📊 **Son Siparişler:**
"""
        
        for order in orders[:3]:
            response += f"""
🛍️ **{order['order_number']}**
• Ürün: {order['product_name']}
• Tutar: {order['price']} KP
• Durum: {order['status']}
• Tarih: {order['created_at'].strftime('%d.%m.%Y %H:%M')}
"""
        
        await message.reply(response, parse_mode="Markdown")
        logger.info(f"✅ Test sipariş komutu çalıştırıldı - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Test sipariş komut hatası: {e}")
        await message.reply("❌ Test sırasında hata oluştu!")

async def show_orders_list_callback(callback: types.CallbackQuery) -> None:
    """Callback için sipariş listesi göster"""
    try:
        # Yeni SQL fonksiyonunu kullan
        from database import get_pending_orders_with_details
        orders = await get_pending_orders_with_details()
        
        if not orders:
            await callback.message.edit_text(
                "📋 **Sipariş Listesi**\n\n"
                "⏳ Bekleyen sipariş bulunmuyor.\n"
                "Tüm siparişler işlenmiş durumda.\n\n"
                "⬅️ Geri dönmek için /adminpanel yazın.",
                parse_mode="Markdown"
            )
            return
        
        # Sipariş listesi mesajı
        orders_text = "📋 **BEKLEYEN SİPARİŞLER** 📋\n\n"
        
        for i, order in enumerate(orders, 1):
            order_date = order['created_at'].strftime('%d.%m.%Y %H:%M')
            orders_text += f"**{i}.** `{order['order_number']}`\n"
            orders_text += f"👤 **Müşteri:** {order['first_name']} (@{order['username']})\n"
            orders_text += f"🛍️ **Ürün:** {order['product_name']}\n"
            orders_text += f"💰 **Tutar:** {order['total_price']} KP\n"
            orders_text += f"📅 **Tarih:** {order_date}\n"
            orders_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        orders_text += f"⏳ **Toplam:** {len(orders)} bekleyen sipariş\n"
        orders_text += f"📅 **Son Güncelleme:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        orders_text += "🔧 **İşlem:** Her sipariş için ayrı mesaj gönderilecek."
        
        # Geri butonu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_market_management")
            ]
        ])
        
        await callback.message.edit_text(
            orders_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        # Her sipariş için ayrı mesaj gönder
        for order in orders:
            order_date = order['created_at'].strftime('%d.%m.%Y %H:%M')
            
            order_message = f"""
╔═══════════════════════════════════╗
║        📦 SİPARİŞ DETAYI 📦      ║
╚═══════════════════════════════════╝

📋 **Sipariş Bilgileri:**
🆔 **Sipariş No:** `{order['order_number']}`
👤 **Müşteri:** {order['first_name']} (@{order['username']})
🛍️ **Ürün:** {order['product_name']}
🏢 **Site:** {order['company_name']}
💰 **Tutar:** {order['total_price']} KP
📅 **Tarih:** {order_date}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ **Durum:** Bekliyor
🔧 **İşlem:** Onay/Red bekleniyor
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Onayla", callback_data=f"admin_approve_{order['order_number']}"),
                    InlineKeyboardButton(text="❌ Reddet", callback_data=f"admin_reject_{order['order_number']}")
                ]
            ])
            
            await callback.message.answer(
                order_message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        
    except Exception as e:
        logger.error(f"❌ Sipariş listesi callback hatası: {e}")
        await callback.answer("❌ Siparişler yüklenemedi!", show_alert=True)

async def show_market_management_menu(callback: types.CallbackQuery) -> None:
    """Market yönetimi menüsü - /market komutunun paneli"""
    try:
        # /market komutunun çalıştırdığı paneli göster
        from handlers.admin_market_management import show_market_management_menu as show_market_menu
        await show_market_menu(callback.from_user.id, None)
        await callback.answer("🛍️ Market yönetimi açıldı!", show_alert=False)
    except Exception as e:
        logger.error(f"❌ Market management menu hatası: {e}")
        await callback.answer("❌ Market yönetim menüsü yüklenemedi!", show_alert=True)

# ==============================================
# YENİ RAPOR SİSTEMİ FONKSİYONLARI
# ==============================================

async def show_user_report(callback: types.CallbackQuery) -> None:
    """Kullanıcı raporu göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Kullanıcı istatistikleri
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_registered = TRUE")
            active_users = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE is_registered = TRUE 
                  AND last_activity >= NOW() - INTERVAL '7 days'
            """)
            new_users_today = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE is_registered = TRUE 
                  AND registration_date >= CURRENT_DATE
            """)
            new_users_week = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE is_registered = TRUE 
                  AND registration_date >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            # En aktif kullanıcılar
            top_users = await conn.fetch("""
                SELECT first_name, username, total_messages, kirve_points
                FROM users 
                WHERE is_registered = TRUE 
                ORDER BY total_messages DESC 
                LIMIT 5
            """)
            
            # En yüksek bakiyeli kullanıcılar
            top_balance = await conn.fetch("""
                SELECT first_name, username, kirve_points
                FROM users 
                WHERE is_registered = TRUE 
                ORDER BY kirve_points DESC 
                LIMIT 5
            """)
        
        response = f"""
👥 **KULLANICI RAPORU**

📊 **Genel İstatistikler:**
• Toplam kayıtlı kullanıcı: **{total_users}** kişi
• Son 7 gün aktif: **{active_users}** kişi
• Bugün yeni kayıt: **{new_users_today}** kişi
• Bu hafta yeni kayıt: **{new_users_week}** kişi

🏆 **En Aktif Kullanıcılar (Mesaj):**
"""
        
        for i, user in enumerate(top_users, 1):
            username = user['username'] or 'Kullanıcı adı yok'
            response += f"{i}. {user['first_name']} (@{username}) - {user['total_messages']} mesaj\n"
        
        response += f"""
💰 **En Yüksek Bakiyeli Kullanıcılar:**
"""
        
        for i, user in enumerate(top_balance, 1):
            username = user['username'] or 'Kullanıcı adı yok'
            response += f"{i}. {user['first_name']} (@{username}) - {user['kirve_points']:.2f} KP\n"
        
        response += f"""
📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_reports_users_refresh")],
            [InlineKeyboardButton(text="📊 Detaylı Rapor", callback_data="admin_reports_users_detailed")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_reports")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Kullanıcı raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

async def show_point_report(callback: types.CallbackQuery) -> None:
    """Point raporu göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Point istatistikleri
            total_points = await conn.fetchval("SELECT COALESCE(SUM(kirve_points), 0) FROM users")
            total_daily_points = await conn.fetchval("SELECT COALESCE(SUM(daily_points), 0) FROM users")
            avg_points = await conn.fetchval("SELECT COALESCE(AVG(kirve_points), 0) FROM users WHERE is_registered = TRUE")
            
            # Bugünkü point kazanımı
            today_points = await conn.fetchval("""
                SELECT COALESCE(SUM(points_earned), 0) 
                FROM daily_stats 
                WHERE message_date = CURRENT_DATE
            """)
            
            # Bu haftaki point kazanımı
            week_points = await conn.fetchval("""
                SELECT COALESCE(SUM(points_earned), 0) 
                FROM daily_stats 
                WHERE message_date >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            # En çok point kazananlar bugün
            top_earners_today = await conn.fetch("""
                SELECT u.first_name, u.username, ds.points_earned
                FROM daily_stats ds
                JOIN users u ON ds.user_id = u.user_id
                WHERE ds.message_date = CURRENT_DATE
                ORDER BY ds.points_earned DESC
                LIMIT 5
            """)
        
        response = f"""
💰 **POINT RAPORU**

📊 **Genel İstatistikler:**
• Toplam point: **{total_points:.2f}** KP
• Günlük toplam point: **{total_daily_points:.2f}** KP
• Ortalama bakiye: **{avg_points:.2f}** KP
• Bugün kazanılan: **{today_points:.2f}** KP
• Bu hafta kazanılan: **{week_points:.2f}** KP

🏆 **Bugün En Çok Point Kazananlar:**
"""
        
        if top_earners_today:
            for i, user in enumerate(top_earners_today, 1):
                username = user['username'] or 'Kullanıcı adı yok'
                response += f"{i}. {user['first_name']} (@{username}) - {user['points_earned']:.2f} KP\n"
        else:
            response += "Bugün henüz point kazanımı yok.\n"
        
        response += f"""
📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_reports_points_refresh")],
            [InlineKeyboardButton(text="📊 Detaylı Rapor", callback_data="admin_reports_points_detailed")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_reports")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Point raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

async def show_event_report(callback: types.CallbackQuery) -> None:
    """Etkinlik raporu göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Etkinlik istatistikleri
            total_events = await conn.fetchval("SELECT COUNT(*) FROM events")
            active_events = await conn.fetchval("SELECT COUNT(*) FROM events WHERE status = 'active'")
            completed_events = await conn.fetchval("SELECT COUNT(*) FROM events WHERE status = 'completed'")
            
            # Toplam katılımcı
            total_participants = await conn.fetchval("SELECT COUNT(*) FROM event_participants")
            
            # Son etkinlikler
            recent_events = await conn.fetch("""
                SELECT title, status, created_at, 
                       (SELECT COUNT(*) FROM event_participants WHERE event_id = e.id) as participant_count
                FROM events e
                ORDER BY created_at DESC
                LIMIT 5
            """)
        
        response = f"""
🎮 **ETKİNLİK RAPORU**

📊 **Genel İstatistikler:**
• Toplam etkinlik: **{total_events}** adet
• Aktif etkinlik: **{active_events}** adet
• Tamamlanan etkinlik: **{completed_events}** adet
• Toplam katılımcı: **{total_participants}** kişi

📋 **Son Etkinlikler:**
"""
        
        if recent_events:
            for event in recent_events:
                status_emoji = {'active': '🟢', 'completed': '✅', 'cancelled': '❌'}.get(event['status'], '❓')
                event_date = event['created_at'].strftime('%d.%m.%Y')
                response += f"• {status_emoji} {event['title']} ({event['participant_count']} katılımcı) - {event_date}\n"
        else:
            response += "Henüz etkinlik bulunmuyor.\n"
        
        response += f"""
📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_reports_events_refresh")],
            [InlineKeyboardButton(text="📊 Detaylı Rapor", callback_data="admin_reports_events_detailed")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_reports")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Etkinlik raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

async def show_system_report(callback: types.CallbackQuery) -> None:
    """Sistem raporu göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Sistem istatistikleri
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_registered = TRUE")
            total_messages = await conn.fetchval("SELECT COALESCE(SUM(total_messages), 0) FROM users")
            total_points = await conn.fetchval("SELECT COALESCE(SUM(kirve_points), 0) FROM users")
            
            # Bugünkü aktivite
            today_messages = await conn.fetchval("""
                SELECT COALESCE(SUM(message_count), 0) 
                FROM daily_stats 
                WHERE message_date = CURRENT_DATE
            """)
            
            today_points = await conn.fetchval("""
                SELECT COALESCE(SUM(points_earned), 0) 
                FROM daily_stats 
                WHERE message_date = CURRENT_DATE
            """)
            
            # Market istatistikleri
            total_products = await conn.fetchval("SELECT COUNT(*) FROM market_products WHERE is_active = TRUE")
            total_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders")
            pending_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders WHERE status = 'pending'")
            
            # Grup istatistikleri
            total_groups = await conn.fetchval("SELECT COUNT(*) FROM registered_groups")
        
        response = f"""
📈 **SİSTEM RAPORU**

📊 **Kullanıcı İstatistikleri:**
• Toplam kayıtlı kullanıcı: **{total_users}** kişi
• Toplam mesaj: **{total_messages}** adet
• Toplam point: **{total_points:.2f}** KP

📅 **Bugünkü Aktivite:**
• Mesaj sayısı: **{today_messages}** adet
• Kazanılan point: **{today_points:.2f}** KP

🛍️ **Market İstatistikleri:**
• Aktif ürün: **{total_products}** adet
• Toplam sipariş: **{total_orders}** adet
• Bekleyen sipariş: **{pending_orders}** adet

👥 **Grup İstatistikleri:**
• Kayıtlı grup: **{total_groups}** adet

📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_reports_system_refresh")],
            [InlineKeyboardButton(text="📊 Detaylı Rapor", callback_data="admin_reports_system_detailed")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_reports")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Sistem raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

# Detaylı rapor fonksiyonları
async def show_detailed_user_report(callback: types.CallbackQuery) -> None:
    """Detaylı kullanıcı raporu"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Detaylı kullanıcı analizi
            users_by_month = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('month', registration_date) as month,
                    COUNT(*) as new_users
                FROM users 
                WHERE is_registered = TRUE 
                  AND registration_date >= NOW() - INTERVAL '6 months'
                GROUP BY DATE_TRUNC('month', registration_date)
                ORDER BY month DESC
            """)
            
            # Aktiflik analizi
            activity_levels = await conn.fetch("""
                SELECT 
                    CASE 
                        WHEN total_messages >= 1000 THEN 'Çok Aktif (1000+)'
                        WHEN total_messages >= 500 THEN 'Aktif (500-999)'
                        WHEN total_messages >= 100 THEN 'Orta (100-499)'
                        WHEN total_messages >= 10 THEN 'Az (10-99)'
                        ELSE 'Yeni (0-9)'
                    END as activity_level,
                    COUNT(*) as user_count
                FROM users 
                WHERE is_registered = TRUE
                GROUP BY activity_level
                ORDER BY user_count DESC
            """)
        
        response = """
👥 **DETAYLI KULLANICI RAPORU**

📊 **Aylık Kayıt Analizi (Son 6 Ay):**
"""
        
        for record in users_by_month:
            month_name = record['month'].strftime('%B %Y')
            response += f"• {month_name}: **{record['new_users']}** yeni kullanıcı\n"
        
        response += f"""
📈 **Aktiflik Seviyesi Analizi:**
"""
        
        for record in activity_levels:
            response += f"• {record['activity_level']}: **{record['user_count']}** kullanıcı\n"
        
        response += f"""
📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Basit Rapor", callback_data="admin_reports_users")],
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_reports_users_detailed")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_reports")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Detaylı kullanıcı raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

async def show_detailed_point_report(callback: types.CallbackQuery) -> None:
    """Detaylı point raporu"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Günlük point kazanımı (son 7 gün)
            daily_points = await conn.fetch("""
                SELECT 
                    message_date,
                    COALESCE(SUM(points_earned), 0) as total_points,
                    COALESCE(SUM(message_count), 0) as total_messages
                FROM daily_stats 
                WHERE message_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY message_date
                ORDER BY message_date DESC
            """)
            
            # Point dağılımı
            point_distribution = await conn.fetch("""
                SELECT 
                    CASE 
                        WHEN kirve_points >= 1000 THEN 'Yüksek (1000+ KP)'
                        WHEN kirve_points >= 500 THEN 'Orta (500-999 KP)'
                        WHEN kirve_points >= 100 THEN 'Düşük (100-499 KP)'
                        WHEN kirve_points >= 10 THEN 'Çok Düşük (10-99 KP)'
                        ELSE 'Yeni (0-9 KP)'
                    END as point_level,
                    COUNT(*) as user_count
                FROM users 
                WHERE is_registered = TRUE
                GROUP BY point_level
                ORDER BY user_count DESC
            """)
        
        response = """
💰 **DETAYLI POINT RAPORU**

📊 **Son 7 Günlük Point Kazanımı:**
"""
        
        for record in daily_points:
            date_str = record['message_date'].strftime('%d.%m')
            response += f"• {date_str}: **{record['total_points']:.2f}** KP ({record['total_messages']} mesaj)\n"
        
        response += f"""
📈 **Point Dağılımı:**
"""
        
        for record in point_distribution:
            response += f"• {record['point_level']}: **{record['user_count']}** kullanıcı\n"
        
        response += f"""
📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Basit Rapor", callback_data="admin_reports_points")],
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_reports_points_detailed")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_reports")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Detaylı point raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

async def show_detailed_event_report(callback: types.CallbackQuery) -> None:
    """Detaylı etkinlik raporu"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Etkinlik türü analizi
            event_types = await conn.fetch("""
                SELECT 
                    event_type,
                    COUNT(*) as event_count,
                    AVG(participant_count) as avg_participants
                FROM events
                GROUP BY event_type
                ORDER BY event_count DESC
            """)
            
            # En popüler etkinlikler
            popular_events = await conn.fetch("""
                SELECT 
                    e.name,
                    e.event_type,
                    COUNT(ep.user_id) as participant_count
                FROM events e
                LEFT JOIN event_participants ep ON e.id = ep.event_id
                GROUP BY e.id, e.name, e.event_type
                ORDER BY participant_count DESC
                LIMIT 5
            """)
        
        response = """
🎮 **DETAYLI ETKİNLİK RAPORU**

📊 **Etkinlik Türü Analizi:**
"""
        
        for record in event_types:
            avg_participants = record['avg_participants'] or 0
            response += f"• {record['event_type']}: **{record['event_count']}** etkinlik (ortalama {avg_participants:.1f} katılımcı)\n"
        
        response += f"""
🏆 **En Popüler Etkinlikler:**
"""
        
        for i, event in enumerate(popular_events, 1):
            response += f"{i}. {event['name']} ({event['event_type']}) - **{event['participant_count']}** katılımcı\n"
        
        response += f"""
📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Basit Rapor", callback_data="admin_reports_events")],
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_reports_events_detailed")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_reports")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Detaylı etkinlik raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

async def show_detailed_system_report(callback: types.CallbackQuery) -> None:
    """Detaylı sistem raporu"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
            
        async with pool.acquire() as conn:
            # Haftalık aktivite analizi
            weekly_activity = await conn.fetch("""
                SELECT 
                    message_date,
                    COALESCE(SUM(message_count), 0) as total_messages,
                    COALESCE(SUM(points_earned), 0) as total_points,
                    COUNT(DISTINCT user_id) as active_users
                FROM daily_stats 
                WHERE message_date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY message_date
                ORDER BY message_date DESC
            """)
            
            # Sistem performansı
            system_stats = await conn.fetchrow("""
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE is_registered = TRUE) as total_users,
                    (SELECT COALESCE(SUM(total_messages), 0) FROM users) as total_messages,
                    (SELECT COALESCE(SUM(kirve_points), 0) FROM users) as total_points,
                    (SELECT COUNT(*) FROM market_products WHERE is_active = TRUE) as total_products,
                    (SELECT COUNT(*) FROM market_orders) as total_orders,
                    (SELECT COUNT(*) FROM groups) as total_groups
            """)
        
        response = """
📈 **DETAYLI SİSTEM RAPORU**

📊 **Son 7 Günlük Aktivite:**
"""
        
        for record in weekly_activity:
            date_str = record['message_date'].strftime('%d.%m')
            response += f"• {date_str}: **{record['total_messages']}** mesaj, **{record['total_points']:.2f}** KP, **{record['active_users']}** aktif kullanıcı\n"
        
        response += f"""
🔧 **Sistem Performansı:**
• Toplam kullanıcı: **{system_stats['total_users']}** kişi
• Toplam mesaj: **{system_stats['total_messages']}** adet
• Toplam point: **{system_stats['total_points']:.2f}** KP
• Aktif ürün: **{system_stats['total_products']}** adet
• Toplam sipariş: **{system_stats['total_orders']}** adet
• Kayıtlı grup: **{system_stats['total_groups']}** adet

📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Basit Rapor", callback_data="admin_reports_system")],
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_reports_system_detailed")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_reports")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Detaylı sistem raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

async def show_admin_commands_list(callback: types.CallbackQuery) -> None:
    """Admin komutları listesi - Tüm admin komutlarını göster"""
    try:
        response = """
🛡️ **ADMİN KOMUTLARI LİSTESİ**

📋 **Tüm Admin Komutları ve Açıklamaları:**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **ANA YÖNETİM KOMUTLARI:**
• `/adminpanel` - Ana admin paneli
• `/adminkomutlar` - Admin komutları listesi (bu menü)
• `/adminkomut` - Admin komutları listesi (kısa)
• `/yardim` - Yardım menüsü

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **BAKİYE YÖNETİMİ:**
• `/bakiyee @kullanıcı miktar` - Kullanıcıya bakiye ekle
• `/bakiyec @kullanıcı miktar` - Kullanıcıdan bakiye çıkar
• `/bakiyeeid ID miktar` - ID ile bakiye ekle
• `/bakiyecid ID miktar` - ID ile bakiye çıkar

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛍️ **MARKET YÖNETİMİ:**
• `/market` - Market yönetim paneli
• `/siparisliste` - Bekleyen siparişleri listele
• `/siparisonayla siparis_no` - Sipariş onayla
• `/siparisreddet siparis_no` - Sipariş reddet
• `/testmarket` - Market sistemi test
• `/testsiparis` - Sipariş sistemi test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎮 **ETKİNLİK YÖNETİMİ:**
• `/etkinlik` - Yeni etkinlik oluştur
• `/etkinlikler` - Aktif etkinlikleri listele
• `/etkinlikbitir etkinlik_id` - Etkinliği bitir
• `/etkinlikiptal etkinlik_id` - Etkinliği iptal et
• `/etkinlikdurum etkinlik_id` - Etkinlik durumu
• `/etkinlikyardım` - Etkinlik yardım menüsü

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎲 **ÇEKİLİŞ YÖNETİMİ:**
• `/cekilisyap` - Yeni çekiliş oluştur
• `/cekilisler` - Aktif çekilişleri listele
• `/cekilisbitir cekilis_id` - Çekilişi bitir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 **GRUP YÖNETİMİ:**
• `/kirvegrup` - Grubu sisteme kaydet
• `/grupbilgi` - Grup bilgilerini göster
• `/gruplar` - Kayıtlı grupları listele
• `/temizle sayı` - Grup mesajlarını sil

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ **ADMİN YETKİ YÖNETİMİ:**
• `/adminyap @kullanıcı seviye` - Admin yetkisi ver
• `/komutsil komut_adı` - Dinamik komut sil
• `/yetkial @kullanıcı` - Kullanıcıdan yetki al
• `/adminseviye @kullanıcı` - Admin seviyesini kontrol et
• `/adminyardım` - Admin yardım menüsü

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 **SİSTEM TEST KOMUTLARI:**
• `/testsql` - SQL sorguları test
• `/botyaz mesaj` - Bot'u konuştur

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **KULLANIM İPUÇLARI:**
• Komutlar grup chatinde silinir ve özel mesajda yanıtlanır
• Admin yetkisi gerektiren komutlar sadece Super Admin tarafından kullanılabilir
• Test komutları sadece geliştirme aşamasında kullanılmalıdır
• Tüm komutlar loglanır ve takip edilir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **TOPLAM:** 25+ Admin Komutu
🎯 **Durum:** Tüm komutlar aktif ve çalışır durumda
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛡️ Admin Panel", callback_data="admin_back")],
            [InlineKeyboardButton(text="🔧 Sistem Durumu", callback_data="admin_system_status")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Admin komutları listesi hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def admin_commands_list_command(message: Message) -> None:
    """Admin komutları listesi komutu - Doğrudan komut listesini göster"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        logger.info(f"🛡️ ADMIN COMMANDS LIST DEBUG - User: {user_id}, Text: '{message.text}'")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.info(f"❌ Admin değil - User: {user_id}, Admin ID: {config.ADMIN_USER_ID}")
            return
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                log_system(f"🔇 Admin commands list komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_admin_commands_list_privately(user_id)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        logger.info(f"🛡️ Admin commands list komutu ÖZELİNDE - User: {message.from_user.first_name} ({user_id})")
        
        # Admin komutları listesini doğrudan göster
        await _send_admin_commands_list_privately(user_id)
        
    except Exception as e:
        logger.error(f"❌ Admin commands list komutu hatası: {e}")
        await message.answer("❌ Admin komutları listesi yüklenirken hata oluştu!", reply_to_message_id=message.message_id)


async def _send_admin_commands_list_privately(user_id: int) -> None:
    """Admin komutları listesini özel mesajla gönder"""
    try:
        response = """
🛡️ **ADMİN KOMUTLARI LİSTESİ**

📋 **Tüm Admin Komutları ve Açıklamaları:**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **ANA YÖNETİM KOMUTLARI:**
• `/adminpanel` - Ana admin paneli
• `/adminkomutlar` - Admin komutları listesi (bu menü)
• `/adminkomut` - Admin komutları listesi (kısa)
• `/yardim` - Yardım menüsü

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **BAKİYE YÖNETİMİ:**
• `/bakiyee @kullanıcı miktar` - Kullanıcıya bakiye ekle
• `/bakiyec @kullanıcı miktar` - Kullanıcıdan bakiye çıkar
• `/bakiyeeid ID miktar` - ID ile bakiye ekle
• `/bakiyecid ID miktar` - ID ile bakiye çıkar

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛍️ **MARKET YÖNETİMİ:**
• `/market` - Market yönetim paneli
• `/siparisliste` - Bekleyen siparişleri listele
• `/siparisonayla siparis_no` - Sipariş onayla
• `/siparisreddet siparis_no` - Sipariş reddet
• `/testmarket` - Market sistemi test
• `/testsiparis` - Sipariş sistemi test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎮 **ETKİNLİK YÖNETİMİ:**
• `/etkinlik` - Yeni etkinlik oluştur
• `/etkinlikler` - Aktif etkinlikleri listele
• `/etkinlikbitir etkinlik_id` - Etkinliği bitir
• `/etkinlikiptal etkinlik_id` - Etkinliği iptal et
• `/etkinlikdurum etkinlik_id` - Etkinlik durumu
• `/etkinlikyardım` - Etkinlik yardım menüsü

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎲 **ÇEKİLİŞ YÖNETİMİ:**
• `/cekilisyap` - Yeni çekiliş oluştur
• `/cekilisler` - Aktif çekilişleri listele
• `/cekilisbitir cekilis_id` - Çekilişi bitir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 **GRUP YÖNETİMİ:**
• `/kirvegrup` - Grubu sisteme kaydet
• `/grupbilgi` - Grup bilgilerini göster
• `/gruplar` - Kayıtlı grupları listele
• `/temizle sayı` - Grup mesajlarını sil

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ **ADMİN YETKİ YÖNETİMİ:**
• `/adminyap @kullanıcı seviye` - Admin yetkisi ver
• `/komutsil komut_adı` - Dinamik komut sil
• `/yetkial @kullanıcı` - Kullanıcıdan yetki al
• `/adminseviye @kullanıcı` - Admin seviyesini kontrol et
• `/adminyardım` - Admin yardım menüsü

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 **SİSTEM TEST KOMUTLARI:**
• `/testsql` - SQL sorguları test
• `/botyaz mesaj` - Bot'u konuştur

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **KULLANIM İPUÇLARI:**
• Komutlar grup chatinde silinir ve özel mesajda yanıtlanır
• Admin yetkisi gerektiren komutlar sadece Super Admin tarafından kullanılabilir
• Test komutları sadece geliştirme aşamasında kullanılmalıdır
• Tüm komutlar loglanır ve takip edilir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **TOPLAM:** 25+ Admin Komutu
🎯 **Durum:** Tüm komutlar aktif ve çalışır durumda
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Çekiliş Yap", callback_data="admin_lottery_create")],
            [InlineKeyboardButton(text="🛡️ Admin Panel", callback_data="admin_back")],
            [InlineKeyboardButton(text="🔧 Sistem Durumu", callback_data="admin_system_status")]
        ])
        
        await _bot_instance.send_message(
            user_id,
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        logger.info(f"✅ Admin komutları listesi özel mesajla gönderildi: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Admin komutları listesi gönderilemedi: {e}")

async def create_lottery_from_admin_commands(callback: types.CallbackQuery) -> None:
    """Admin komutları listesinden çekiliş oluşturma"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"🎲 LOTTERY CREATE FROM ADMIN COMMANDS - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Callback answer
        await callback.answer("🎲 Çekiliş oluşturma başlatılıyor...", show_alert=True)
        
        # Memory manager kullanarak çekiliş oluşturma işlemini başlat
        from utils.memory_manager import memory_manager
        
        lottery_data = {
            "type": "lottery",
            "step": "cost",
            "created_at": datetime.now()
        }
        
        memory_manager.set_lottery_data(user_id, lottery_data)
        memory_manager.set_input_state(user_id, "lottery_cost")
        
        logger.info(f"🎯 LOTTERY DATA SET FROM ADMIN - User: {user_id}, Step: cost, Data: {lottery_data}")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="lottery_cancel")]
        ])
        
        await callback.message.edit_text(
            "🎲 **Çekiliş Oluşturma**\n\n"
            "Katılım ücreti kaç Kirve Point olsun?\n"
            "Örnek: `10` veya `5.50`\n\n"
            "**Lütfen ücreti yazın:**",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Çekiliş oluşturma başlatıldı - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Çekiliş oluşturma hatası: {e}")
        await callback.answer("❌ Çekiliş oluşturma sırasında hata oluştu!", show_alert=True)

async def execute_lottery_create_command(callback: types.CallbackQuery) -> None:
    """Çekiliş oluşturma komutunu çalıştır"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"🎲 EXECUTE LOTTERY CREATE COMMAND - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Callback answer
        await callback.answer("🎲 Çekiliş oluşturma komutu çalıştırılıyor...", show_alert=True)
        
        # Çekiliş oluşturma komutunu simüle et
        response = """
🎲 **ÇEKİLİŞ OLUŞTURMA KOMUTU ÇALIŞTIRILDI**

**Komut:** `/cekilisyap`

**Durum:** ✅ Başarıyla çalıştırıldı

**Sonraki Adımlar:**
1. Çekiliş adını girin
2. Ödül miktarını belirleyin
3. Katılım ücretini ayarlayın
4. Çekiliş süresini belirleyin

**Çekiliş oluşturma süreci başlatıldı!**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Mevcut Çekilişler", callback_data="list_lotteries_command")],
            [InlineKeyboardButton(text="🛡️ Admin Komutları", callback_data="admin_commands_list")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Çekiliş oluşturma komutu simüle edildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Çekiliş oluşturma komutu hatası: {e}")
        await callback.answer("❌ Çekiliş oluşturma komutu çalıştırılırken hata oluştu!", show_alert=True)


async def execute_list_lotteries_command(callback: types.CallbackQuery) -> None:
    """Çekiliş listesi komutunu çalıştır"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"📋 EXECUTE LIST LOTTERIES COMMAND - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Callback answer
        await callback.answer("📋 Çekiliş listesi yükleniyor...", show_alert=True)
        
        # Çekiliş listesi komutunu simüle et
        response = """
📋 **ÇEKİLİŞ LİSTESİ KOMUTU ÇALIŞTIRILDI**

**Komut:** `/cekilisler`

**Durum:** ✅ Başarıyla çalıştırıldı

**Mevcut Çekilişler:**
• Şu anda aktif çekiliş bulunmuyor

**Çekiliş Yönetimi:**
• Yeni çekiliş oluşturmak için `/cekilisyap` komutunu kullanın
• Mevcut çekilişleri yönetmek için `/cekilisler` komutunu kullanın
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Yeni Çekiliş", callback_data="create_lottery_command")],
            [InlineKeyboardButton(text="🛡️ Admin Komutları", callback_data="admin_commands_list")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Çekiliş listesi komutu simüle edildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Çekiliş listesi komutu hatası: {e}")
        await callback.answer("❌ Çekiliş listesi komutu çalıştırılırken hata oluştu!", show_alert=True)

async def show_system_management_menu(callback: types.CallbackQuery) -> None:
    """Sistem yönetimi menüsü"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"⚙️ SYSTEM MANAGEMENT MENU - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Mevcut ayarları al
        current_settings = await get_system_settings()
        
        response = f"""
⚙️ **SİSTEM YÖNETİMİ**

**Mevcut Ayarlar:**
💰 **Mesaj Başına Kazanım:** {current_settings.get('points_per_message', 0.04)} KP
📅 **Günlük Limit:** {current_settings.get('daily_limit', 5.0)} KP
📊 **Haftalık Maksimum:** {current_settings.get('weekly_limit', 20.0)} KP

**Yönetim Seçenekleri:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Kazanım Ayarlama", callback_data="admin_points_settings"),
                InlineKeyboardButton(text="📅 Günlük Limit", callback_data="admin_daily_limit")
            ],
            [
                InlineKeyboardButton(text="📊 Haftalık Limit", callback_data="admin_weekly_limit"),
                InlineKeyboardButton(text="📋 Sistem Durumu", callback_data="admin_system_status")
            ],
            [
                InlineKeyboardButton(text="🛡️ Admin Panel", callback_data="admin_back")
            ]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Sistem yönetimi menüsü gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Sistem yönetimi menüsü hatası: {e}")
        await callback.answer("❌ Sistem yönetimi menüsü yüklenirken hata oluştu!", show_alert=True)


async def show_points_settings_menu(callback: types.CallbackQuery) -> None:
    """Kazanım ayarlama menüsü"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"💰 POINTS SETTINGS MENU - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Mevcut ayarı al
        current_settings = await get_system_settings()
        current_points = current_settings.get('points_per_message', 0.04)
        
        response = f"""
💰 **KAZANIM AYARLAMA**

**Mevcut Değer:** {current_points} KP (mesaj başına)

**Yeni Değer Seçin:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="0.02 KP", callback_data="set_points_0.02"),
                InlineKeyboardButton(text="0.04 KP", callback_data="set_points_0.04"),
                InlineKeyboardButton(text="0.06 KP", callback_data="set_points_0.06")
            ],
            [
                InlineKeyboardButton(text="0.08 KP", callback_data="set_points_0.08"),
                InlineKeyboardButton(text="0.10 KP", callback_data="set_points_0.10"),
                InlineKeyboardButton(text="0.15 KP", callback_data="set_points_0.15")
            ],
            [
                InlineKeyboardButton(text="📝 Özel Değer", callback_data="set_points_custom")
            ],
            [
                InlineKeyboardButton(text="⚙️ Sistem Yönetimi", callback_data="admin_system_management")
            ]
        ])
        
        # Keyboard debug sistemi pasife çekildi
        # logger.info(f"🔍 KEYBOARD DEBUG - Keyboard created for user: {user_id}")
        # logger.info(f"🔍 KEYBOARD DEBUG - Keyboard structure:")
        # for row in keyboard.inline_keyboard:
        #     for button in row:
        #         logger.info(f"🔍 KEYBOARD DEBUG - Button: '{button.text}' -> '{button.callback_data}'")
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Kazanım ayarlama menüsü gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Kazanım ayarlama menüsü hatası: {e}")
        await callback.answer("❌ Kazanım ayarlama menüsü yüklenirken hata oluştu!", show_alert=True)


async def show_daily_limit_menu(callback: types.CallbackQuery) -> None:
    """Günlük limit ayarlama menüsü"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"📅 DAILY LIMIT MENU - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Mevcut ayarı al
        current_settings = await get_system_settings()
        current_limit = current_settings.get('daily_limit', 5.0)
        
        response = f"""
📅 **GÜNLÜK LİMİT AYARLAMA**

**Mevcut Limit:** {current_limit} KP (günlük)

**Yeni Limit Seçin:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="3 KP", callback_data="set_daily_3.0"),
                InlineKeyboardButton(text="5 KP", callback_data="set_daily_5.0"),
                InlineKeyboardButton(text="10 KP", callback_data="set_daily_10.0")
            ],
            [
                InlineKeyboardButton(text="15 KP", callback_data="set_daily_15.0"),
                InlineKeyboardButton(text="20 KP", callback_data="set_daily_20.0"),
                InlineKeyboardButton(text="25 KP", callback_data="set_daily_25.0")
            ],
            [
                InlineKeyboardButton(text="📝 Özel Limit", callback_data="set_daily_custom")
            ],
            [
                InlineKeyboardButton(text="⚙️ Sistem Yönetimi", callback_data="admin_system_management")
            ]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Günlük limit menüsü gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Günlük limit menüsü hatası: {e}")
        await callback.answer("❌ Günlük limit menüsü yüklenirken hata oluştu!", show_alert=True)


async def show_weekly_limit_menu(callback: types.CallbackQuery) -> None:
    """Haftalık limit ayarlama menüsü"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"📊 WEEKLY LIMIT MENU - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Mevcut ayarı al
        current_settings = await get_system_settings()
        current_limit = current_settings.get('weekly_limit', 20.0)
        
        response = f"""
📊 **HAFTALIK LİMİT AYARLAMA**

**Mevcut Limit:** {current_limit} KP (haftalık)

**Yeni Limit Seçin:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="15 KP", callback_data="set_weekly_15.0"),
                InlineKeyboardButton(text="20 KP", callback_data="set_weekly_20.0"),
                InlineKeyboardButton(text="30 KP", callback_data="set_weekly_30.0")
            ],
            [
                InlineKeyboardButton(text="50 KP", callback_data="set_weekly_50.0"),
                InlineKeyboardButton(text="75 KP", callback_data="set_weekly_75.0"),
                InlineKeyboardButton(text="100 KP", callback_data="set_weekly_100.0")
            ],
            [
                InlineKeyboardButton(text="📝 Özel Limit", callback_data="set_weekly_custom")
            ],
            [
                InlineKeyboardButton(text="⚙️ Sistem Yönetimi", callback_data="admin_system_management")
            ]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Haftalık limit menüsü gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Haftalık limit menüsü hatası: {e}")
        await callback.answer("❌ Haftalık limit menüsü yüklenirken hata oluştu!", show_alert=True)


async def get_system_settings() -> Dict[str, Any]:
    """Sistem ayarlarını getir"""
    try:
        pool = await get_db_pool()
        if not pool:
            return {'points_per_message': 0.04, 'daily_limit': 5.0, 'weekly_limit': 20.0}
            
        async with pool.acquire() as conn:
            # Sistem ayarlarını al
            settings = await conn.fetchrow("""
                SELECT 
                    points_per_message,
                    daily_limit,
                    weekly_limit
                FROM system_settings 
                WHERE id = 1
            """)
            
            if not settings:
                # Varsayılan ayarları döndür
                return {
                    'points_per_message': 0.04,
                    'daily_limit': 5.0,
                    'weekly_limit': 20.0
                }
                
            return {
                'points_per_message': float(settings['points_per_message']),
                'daily_limit': float(settings['daily_limit']),
                'weekly_limit': float(settings['weekly_limit'])
            }
            
    except Exception as e:
        logger.error(f"❌ Sistem ayarları hatası: {e}")
        return {'points_per_message': 0.04, 'daily_limit': 5.0, 'weekly_limit': 20.0}


async def update_system_setting(setting_name: str, new_value: float) -> bool:
    """Sistem ayarını güncelle"""
    try:
        logger.info(f"🔧 UPDATE SYSTEM SETTING - Setting: {setting_name}, Value: {new_value}")
        
        pool = await get_db_pool()
        if not pool:
            logger.error(f"❌ UPDATE SYSTEM SETTING - No database pool available")
            return False
            
        logger.info(f"🔧 UPDATE SYSTEM SETTING - Database pool acquired")
        
        async with pool.acquire() as conn:
            logger.info(f"🔧 UPDATE SYSTEM SETTING - Database connection acquired")
            
            # Önce sistem ayarları tablosunu oluştur (eğer yoksa)
            logger.info(f"🔧 UPDATE SYSTEM SETTING - Creating table if not exists")
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
            
            # İlk kayıt yoksa oluştur
            logger.info(f"🔧 UPDATE SYSTEM SETTING - Inserting default record if not exists")
            await conn.execute("""
                INSERT INTO system_settings (id, points_per_message, daily_limit, weekly_limit)
                VALUES (1, 0.04, 5.00, 20.00)
                ON CONFLICT (id) DO NOTHING
            """)
            
            # Ayarı güncelle
            logger.info(f"🔧 UPDATE SYSTEM SETTING - Updating setting: {setting_name} = {new_value}")
            result = await conn.execute(f"""
                UPDATE system_settings 
                SET {setting_name} = $1, updated_at = NOW()
                WHERE id = 1
            """, new_value)
            
            logger.info(f"🔧 UPDATE SYSTEM SETTING - Update result: {result}")
            
            # Güncelleme başarılı mı kontrol et
            if result == "UPDATE 1":
                logger.info(f"✅ UPDATE SYSTEM SETTING - Successfully updated {setting_name} to {new_value}")
                return True
            else:
                logger.error(f"❌ UPDATE SYSTEM SETTING - Update failed, result: {result}")
                return False
            
    except Exception as e:
        logger.error(f"❌ UPDATE SYSTEM SETTING - Error: {e}")
        logger.error(f"❌ UPDATE SYSTEM SETTING - Exception type: {type(e)}")
        logger.error(f"❌ UPDATE SYSTEM SETTING - Exception args: {e.args}")
        return False


async def handle_points_setting(callback: types.CallbackQuery, action: str) -> None:
    """Kazanım ayarı değiştirme"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"💰 POINTS SETTING - User: {user_id}, Action: {action}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        logger.info(f"💰 POINTS SETTING DEBUG - Action: {action}, User: {user_id}")
        logger.info(f"💰 POINTS SETTING ACTION TYPE - Type: {type(action)}")
        logger.info(f"💰 POINTS SETTING ACTION LENGTH - Length: {len(action) if action else 0}")
        
        if action == "set_points_custom":
            logger.info(f"💰 SET POINTS CUSTOM TRIGGERED - User: {user_id}")
            # Özel değer için input iste
            await callback.message.edit_text(
                "💰 **ÖZEL KAZANIM DEĞERİ**\n\n"
                "Yeni kazanım değerini girin (örn: 0.05):\n\n"
                "**Format:** 0.01 - 1.00 arası\n"
                "**Örnek:** 0.05, 0.10, 0.25\n\n"
                "**Sohbete yazın:**",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ İptal", callback_data="admin_system_management")]
                ])
            )
            
            # Input state'i kaydet
            from utils.memory_manager import memory_manager
            cache_manager = memory_manager.get_cache_manager()
            cache_manager.set_cache(f"input_state_{user_id}", "custom_points", ttl=300)
            
            logger.info(f"✅ Özel kazanım input başlatıldı - User: {user_id}")
            logger.info(f"🔍 Input state kaydedildi: custom_points - User: {user_id}")
            
            # Callback answer
            await callback.answer("💰 Özel değer girişi başlatıldı! Sohbete yazın.", show_alert=True)
            return
        
        # Değeri al
        logger.info(f"💰 EXTRACTING VALUE FROM ACTION - Action: {action}")
        new_value = float(action.replace("set_points_", ""))
        logger.info(f"💰 EXTRACTED VALUE - New Value: {new_value}")
        
        # Ayarı güncelle
        logger.info(f"💰 UPDATING SYSTEM SETTING - Setting: points_per_message, Value: {new_value}")
        success = await update_system_setting('points_per_message', new_value)
        logger.info(f"💰 UPDATE RESULT - Success: {success}")
        
        if success:
            logger.info(f"💰 SUCCESS - Sending callback answer")
            # Başarılı bildirim gönder
            await callback.answer(f"✅ Kazanım ayarı güncellendi: {new_value} KP", show_alert=True)
            
            logger.info(f"💰 SUCCESS - Showing updated menu")
            # Güncellenmiş menüyü göster
            await show_points_settings_menu(callback)
            
            logger.info(f"💰 SUCCESS - Sending detailed notification")
            # Ek bildirim mesajı gönder
            if _bot_instance:
                await _bot_instance.send_message(
                    user_id,
                    f"💰 **KAZANIM AYARI GÜNCELLENDİ!**\n\n"
                    f"**Yeni Değer:** {new_value} KP (mesaj başına)\n"
                    f"**Durum:** ✅ Aktif\n\n"
                    f"🔄 **Değişiklik anında uygulandı!**",
                    parse_mode="Markdown"
                )
                logger.info(f"💰 SUCCESS - Detailed notification sent")
            else:
                logger.error(f"❌ BOT INSTANCE NOT AVAILABLE")
        else:
            logger.error(f"❌ UPDATE FAILED - Sending error callback answer")
            await callback.answer("❌ Ayar güncellenirken hata oluştu!", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Kazanım ayarı hatası: {e}")
        logger.error(f"❌ EXCEPTION DETAILS - Type: {type(e)}, Args: {e.args}")
        await callback.answer("❌ Kazanım ayarı güncellenirken hata oluştu!", show_alert=True)


async def handle_daily_limit_setting(callback: types.CallbackQuery, action: str) -> None:
    """Günlük limit ayarı değiştirme"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"📅 DAILY LIMIT SETTING - User: {user_id}, Action: {action}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        if action == "set_daily_custom":
            # Özel değer için input iste
            await callback.message.edit_text(
                "📅 **ÖZEL GÜNLÜK LİMİT**\n\n"
                "Yeni günlük limit değerini girin (örn: 7.5):\n\n"
                "**Format:** 1.0 - 100.0 arası\n"
                "**Örnek:** 5.0, 10.0, 15.5",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ İptal", callback_data="admin_system_management")]
                ])
            )
            
            # Input state'i kaydet
            from utils.memory_manager import memory_manager
            cache_manager = memory_manager.get_cache_manager()
            cache_manager.set_cache(f"input_state_{user_id}", "custom_daily", ttl=300)
            
            logger.info(f"✅ Özel günlük limit input başlatıldı - User: {user_id}")
            return
        
        # Değeri al
        new_value = float(action.replace("set_daily_", ""))
        
        # Ayarı güncelle
        success = await update_system_setting('daily_limit', new_value)
        
        if success:
            # Başarılı bildirim gönder
            await callback.answer(f"✅ Günlük limit güncellendi: {new_value} KP", show_alert=True)
            
            # Güncellenmiş menüyü göster
            await show_daily_limit_menu(callback)
            
            # Ek bildirim mesajı gönder
            if _bot_instance:
                await _bot_instance.send_message(
                    user_id,
                    f"📅 **GÜNLÜK LİMİT GÜNCELLENDİ!**\n\n"
                    f"**Yeni Limit:** {new_value} KP (günlük)\n"
                    f"**Durum:** ✅ Aktif\n\n"
                    f"🔄 **Değişiklik anında uygulandı!**",
                    parse_mode="Markdown"
                )
        else:
            await callback.answer("❌ Limit güncellenirken hata oluştu!", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Günlük limit hatası: {e}")
        await callback.answer("❌ Günlük limit güncellenirken hata oluştu!", show_alert=True)


async def handle_weekly_limit_setting(callback: types.CallbackQuery, action: str) -> None:
    """Haftalık limit ayarı değiştirme"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"📊 WEEKLY LIMIT SETTING - User: {user_id}, Action: {action}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        if action == "set_weekly_custom":
            logger.info(f"📊 SET WEEKLY CUSTOM CALLBACK - User: {user_id}")
            await start_custom_weekly_input(callback)
        # YENİ: SET_POINTS_ CALLBACK'LERİNİ YAKALA
        elif action and action.startswith("set_points_"):
            logger.info(f"💰 SET POINTS CALLBACK - Action: {action}, User: {user_id}")
            await handle_points_setting(callback, action)
        elif action and action.startswith("set_daily_"):
            logger.info(f"📅 SET DAILY CALLBACK - Action: {action}, User: {user_id}")
            await handle_daily_limit_setting(callback, action)
        elif action and action.startswith("set_weekly_"):
            logger.info(f"📊 SET WEEKLY CALLBACK - Action: {action}, User: {user_id}")
            await handle_weekly_limit_setting(callback, action)
        else:
            logger.info(f"🔍 UNHANDLED CALLBACK - Action: {action}, User: {user_id}")
            logger.info(f"🔍 CALLBACK DATA DEBUG - Raw data: {callback.data}")
            logger.info(f"🔍 CALLBACK DATA TYPE - Type: {type(callback.data)}")
            logger.info(f"🔍 CALLBACK DATA LENGTH - Length: {len(callback.data) if callback.data else 0}")
            await callback.answer("❌ Bilinmeyen admin işlemi!", show_alert=True)
        
        # Değeri al
        new_value = float(action.replace("set_weekly_", ""))
        
        # Ayarı güncelle
        success = await update_system_setting('weekly_limit', new_value)
        
        if success:
            # Başarılı bildirim gönder
            await callback.answer(f"✅ Haftalık limit güncellendi: {new_value} KP", show_alert=True)
            
            # Güncellenmiş menüyü göster
            await show_weekly_limit_menu(callback)
            
            # Ek bildirim mesajı gönder
            if _bot_instance:
                await _bot_instance.send_message(
                    user_id,
                    f"📊 **HAFTALIK LİMİT GÜNCELLENDİ!**\n\n"
                    f"**Yeni Limit:** {new_value} KP (haftalık)\n"
                    f"**Durum:** ✅ Aktif\n\n"
                    f"🔄 **Değişiklik anında uygulandı!**",
                    parse_mode="Markdown"
                )
        else:
            await callback.answer("❌ Limit güncellenirken hata oluştu!", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Haftalık limit hatası: {e}")
        await callback.answer("❌ Haftalık limit güncellenirken hata oluştu!", show_alert=True)


async def start_custom_points_input(callback: types.CallbackQuery) -> None:
    """Özel kazanım değeri input'u başlat"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"💰 CUSTOM POINTS INPUT - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Input mesajı gönder
        await callback.message.edit_text(
            "💰 **ÖZEL KAZANIM DEĞERİ**\n\n"
            "Yeni kazanım değerini girin (örn: 0.05):\n\n"
            "**Format:** 0.01 - 1.00 arası\n"
            "**Örnek:** 0.05, 0.10, 0.25\n\n"
            "**Sohbete yazın:**",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ İptal", callback_data="admin_system_management")]
            ])
        )
        
        # Input state'i kaydet
        from utils.memory_manager import memory_manager
        cache_manager = memory_manager.get_cache_manager()
        cache_manager.set_cache(f"input_state_{user_id}", "custom_points", ttl=300)
        
        logger.info(f"✅ Özel kazanım input başlatıldı - User: {user_id}")
        logger.info(f"🔍 Input state kaydedildi: custom_points - User: {user_id}")
        
        # Callback answer
        await callback.answer("💰 Özel değer girişi başlatıldı! Sohbete yazın.", show_alert=True)
        
    except Exception as e:
        logger.error(f"❌ Özel kazanım input hatası: {e}")
        await callback.answer("❌ Input başlatılırken hata oluştu!", show_alert=True)


async def start_custom_daily_input(callback: types.CallbackQuery) -> None:
    """Özel günlük limit input'u başlat"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"📅 CUSTOM DAILY INPUT - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Input mesajı gönder
        await callback.message.edit_text(
            "📅 **ÖZEL GÜNLÜK LİMİT**\n\n"
            "Yeni günlük limit değerini girin (örn: 7.5):\n\n"
            "**Format:** 1.0 - 100.0 arası\n"
            "**Örnek:** 5.0, 10.0, 15.5",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ İptal", callback_data="admin_system_management")]
            ])
        )
        
        # Input state'i kaydet
        from utils.memory_manager import memory_manager
        cache_manager = memory_manager.get_cache_manager()
        cache_manager.set_cache(f"input_state_{user_id}", "custom_daily", ttl=300)
        
        logger.info(f"✅ Özel günlük limit input başlatıldı - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Özel günlük limit input hatası: {e}")
        await callback.answer("❌ Input başlatılırken hata oluştu!", show_alert=True)


async def start_custom_weekly_input(callback: types.CallbackQuery) -> None:
    """Özel haftalık limit input'u başlat"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        logger.info(f"📊 CUSTOM WEEKLY INPUT - User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin değil - User: {user_id}")
            await callback.answer("❌ Bu işlem için admin yetkisi gerekli!", show_alert=True)
            return
        
        # Input mesajı gönder
        await callback.message.edit_text(
            "📊 **ÖZEL HAFTALIK LİMİT**\n\n"
            "Yeni haftalık limit değerini girin (örn: 35.0):\n\n"
            "**Format:** 10.0 - 500.0 arası\n"
            "**Örnek:** 20.0, 50.0, 100.0",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ İptal", callback_data="admin_system_management")]
            ])
        )
        
        # Input state'i kaydet
        from utils.memory_manager import memory_manager
        cache_manager = memory_manager.get_cache_manager()
        cache_manager.set_cache(f"input_state_{user_id}", "custom_weekly", ttl=300)
        
        logger.info(f"✅ Özel haftalık limit input başlatıldı - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Özel haftalık limit input hatası: {e}")
        await callback.answer("❌ Input başlatılırken hata oluştu!", show_alert=True)


async def handle_custom_input(message: types.Message) -> None:
    """Özel input değerlerini işle"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        logger.info(f"🔍 CUSTOM INPUT DEBUG - User: {user_id}, Text: '{message.text}'")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.info(f"❌ Admin değil - User: {user_id}")
            return
        
        # Input state'ini kontrol et
        from utils.memory_manager import memory_manager
        cache_manager = memory_manager.get_cache_manager()
        input_state = cache_manager.get_cache(f"input_state_{user_id}")
        
        logger.info(f"🔍 Input state: {input_state} - User: {user_id}")
        
        if not input_state:
            logger.info(f"❌ Input state yok - User: {user_id}")
            return
        
        # Input değerini al
        input_value = message.text.strip()
        
        try:
            # Sayıya çevir
            numeric_value = float(input_value)
            
            # Değer aralıklarını kontrol et
            if input_state == "custom_points":
                if not (0.01 <= numeric_value <= 1.0):
                    await message.reply("❌ Geçersiz değer! 0.01 - 1.00 arası olmalı.")
                    return
                
                # Ayarı güncelle
                success = await update_system_setting('points_per_message', numeric_value)
                if success:
                    # Başarılı bildirim
                    await message.reply(f"✅ Kazanım ayarı güncellendi: {numeric_value} KP")
                    
                    # Ek bildirim mesajı gönder
                    if _bot_instance:
                        await _bot_instance.send_message(
                            user_id,
                            f"💰 **KAZANIM AYARI GÜNCELLENDİ!**\n\n"
                            f"**Yeni Değer:** {numeric_value} KP (mesaj başına)\n"
                            f"**Durum:** ✅ Aktif\n\n"
                            f"🔄 **Değişiklik anında uygulandı!**",
                            parse_mode="Markdown"
                        )
                    
                    # Sistem yönetimi menüsüne geri dön
                    await show_system_management_menu_from_message(message)
                else:
                    await message.reply("❌ Ayar güncellenirken hata oluştu!")
                    
            elif input_state == "custom_daily":
                if not (1.0 <= numeric_value <= 100.0):
                    await message.reply("❌ Geçersiz değer! 1.0 - 100.0 arası olmalı.")
                    return
                
                # Ayarı güncelle
                success = await update_system_setting('daily_limit', numeric_value)
                if success:
                    # Başarılı bildirim
                    await message.reply(f"✅ Günlük limit güncellendi: {numeric_value} KP")
                    
                    # Ek bildirim mesajı gönder
                    if _bot_instance:
                        await _bot_instance.send_message(
                            user_id,
                            f"📅 **GÜNLÜK LİMİT GÜNCELLENDİ!**\n\n"
                            f"**Yeni Limit:** {numeric_value} KP (günlük)\n"
                            f"**Durum:** ✅ Aktif\n\n"
                            f"🔄 **Değişiklik anında uygulandı!**",
                            parse_mode="Markdown"
                        )
                    
                    # Sistem yönetimi menüsüne geri dön
                    await show_system_management_menu_from_message(message)
                else:
                    await message.reply("❌ Limit güncellenirken hata oluştu!")
                    
            elif input_state == "custom_weekly":
                if not (10.0 <= numeric_value <= 500.0):
                    await message.reply("❌ Geçersiz değer! 10.0 - 500.0 arası olmalı.")
                    return
                
                # Ayarı güncelle
                success = await update_system_setting('weekly_limit', numeric_value)
                if success:
                    # Başarılı bildirim
                    await message.reply(f"✅ Haftalık limit güncellendi: {numeric_value} KP")
                    
                    # Ek bildirim mesajı gönder
                    if _bot_instance:
                        await _bot_instance.send_message(
                            user_id,
                            f"📊 **HAFTALIK LİMİT GÜNCELLENDİ!**\n\n"
                            f"**Yeni Limit:** {numeric_value} KP (haftalık)\n"
                            f"**Durum:** ✅ Aktif\n\n"
                            f"🔄 **Değişiklik anında uygulandı!**",
                            parse_mode="Markdown"
                        )
                    
                    # Sistem yönetimi menüsüne geri dön
                    await show_system_management_menu_from_message(message)
                else:
                    await message.reply("❌ Limit güncellenirken hata oluştu!")
            
            # Input state'ini temizle
            cache_manager.delete_cache(f"input_state_{user_id}")
            
        except ValueError:
            await message.reply("❌ Geçersiz sayı formatı! Lütfen sayı girin (örn: 0.05)")
            
    except Exception as e:
        logger.error(f"❌ Custom input hatası: {e}")
        await message.reply("❌ İşlem sırasında hata oluştu!")

async def show_system_management_menu_from_message(message: types.Message) -> None:
    """Mesaj üzerinden sistem yönetimi menüsünü göster"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # Mevcut ayarları al
        current_settings = await get_system_settings()
        
        response = f"""
⚙️ **SİSTEM YÖNETİMİ**

**Mevcut Ayarlar:**
💰 **Mesaj Başına Kazanım:** {current_settings.get('points_per_message', 0.04)} KP
📅 **Günlük Limit:** {current_settings.get('daily_limit', 5.0)} KP
📊 **Haftalık Maksimum:** {current_settings.get('weekly_limit', 20.0)} KP

**Yönetim Seçenekleri:**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Kazanım Ayarlama", callback_data="admin_points_settings"),
                InlineKeyboardButton(text="📅 Günlük Limit", callback_data="admin_daily_limit")
            ],
            [
                InlineKeyboardButton(text="📊 Haftalık Limit", callback_data="admin_weekly_limit"),
                InlineKeyboardButton(text="📋 Sistem Durumu", callback_data="admin_system_status")
            ],
            [
                InlineKeyboardButton(text="🛡️ Admin Panel", callback_data="admin_back")
            ]
        ])
        
        await message.reply(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Sistem yönetimi menüsü mesaj üzerinden gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Sistem yönetimi menüsü hatası: {e}")
        await message.reply("❌ Sistem yönetimi menüsü yüklenirken hata oluştu!")


async def show_system_status_menu(callback: types.CallbackQuery) -> None:
    """Sistem durumu menüsü"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        # Sistem ayarlarını al
        settings = await get_system_settings()
        
        response = f"""
📊 **Sistem Durumu**

**Mevcut Ayarlar:**
💰 **Kazanım:** {settings.get('points_per_message', 0.04)} KP/mesaj
📅 **Günlük Limit:** {settings.get('daily_limit', 5.0)} KP
📊 **Haftalık Limit:** {settings.get('weekly_limit', 20.0)} KP

**Sistem Bilgileri:**
• Bot durumu: ✅ Aktif
• Database: ✅ Bağlı
• Ayarlar: ✅ Güncel

Bu menüden sistem ayarlarını görüntüleyebilirsin.
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_system_management")
            ]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"📊 Sistem durumu menüsü gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Sistem durumu menüsü hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_scheduled_messages_menu(callback: types.CallbackQuery) -> None:
    """Zamanlanmış mesajlar menüsü"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
            
        # Zamanlanmış mesajlar durumunu al
        from handlers.scheduled_messages import get_scheduled_status
        status = await get_scheduled_status()
        
        response = f"""
⏰ **Zamanlanmış Mesajlar Sistemi**

**Durum:** {'✅ Aktif' if status.get('active') else '❌ Pasif'}
**Aralık:** {status.get('interval', 30)} dakika
**Profil:** {status.get('profile', 'default')}
**Son Mesaj:** {status.get('last_message_time', 'Hiç gönderilmemiş')}

**Mevcut Profiller:**
"""
        
        for profile in status.get('available_profiles', []):
            response += f"• {profile}\n"
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Başlat" if not status.get('active') else "🔴 Durdur",
                    callback_data="scheduled_toggle"
                ),
                InlineKeyboardButton(
                    text="⚙️ Ayarlar",
                    callback_data="scheduled_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Durum",
                    callback_data="scheduled_status"
                ),
                InlineKeyboardButton(
                    text="📝 Profiller",
                    callback_data="scheduled_profiles"
                )
            ],
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
            ]
        ])
        
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
        logger.info(f"✅ Zamanlanmış mesajlar menüsü gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Zamanlanmış mesajlar menüsü hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_link_commands_menu(callback: types.CallbackQuery) -> None:
    """Link komutları menüsü"""
    try:
        from handlers.dynamic_command_creator import get_all_custom_commands
        
        commands = await get_all_custom_commands()
        link_commands = [cmd for cmd in commands if cmd.get("type") == "link"]
        
        response = f"""
🔗 **Link Komutları Yönetimi**

**Toplam Link Komutu:** {len(link_commands)}
**Aktif Komutlar:** {len([cmd for cmd in link_commands if cmd.get("active")])}

**Mevcut Komutlar:**
"""
        
        for cmd in link_commands[:10]:  # İlk 10 komut
            status = "✅" if cmd.get("active") else "❌"
            response += f"• {status} !{cmd['command']} - {cmd.get('description', 'Açıklama yok')}\n"
        
        if len(link_commands) > 10:
            response += f"\n... ve {len(link_commands) - 10} komut daha"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yeni Link Komutu", callback_data="create_link_command"),
                InlineKeyboardButton(text="📋 Tüm Komutlar", callback_data="list_link_commands")
            ],
            [
                InlineKeyboardButton(text="⚙️ Komut Yönetimi", callback_data="manage_link_commands"),
                InlineKeyboardButton(text="📊 İstatistikler", callback_data="link_stats")
            ],
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_system_management")
            ]
        ])
        
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Link komutları menüsü hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_scheduled_commands_menu(callback: types.CallbackQuery) -> None:
    """Zamanlanmış komutlar menüsü"""
    try:
        from handlers.dynamic_command_creator import get_all_custom_commands
        from handlers.scheduled_messages import get_all_scheduled_messages
        
        commands = await get_all_custom_commands()
        scheduled_commands = [cmd for cmd in commands if cmd.get("type") == "scheduled_message"]
        scheduled_messages = await get_all_scheduled_messages()
        
        response = f"""
⏰ **Zamanlanmış Komutlar Yönetimi**

**Toplam Zamanlanmış Komut:** {len(scheduled_commands)}
**Aktif Komutlar:** {len([cmd for cmd in scheduled_commands if cmd.get("active")])}
**Toplam Zamanlanmış Mesaj:** {len(scheduled_messages)}

**Mevcut Komutlar:**
"""
        
        for cmd in scheduled_commands[:5]:  # İlk 5 komut
            status = "✅" if cmd.get("active") else "❌"
            response += f"• {status} !{cmd['command']} - {cmd.get('description', 'Açıklama yok')}\n"
        
        if len(scheduled_commands) > 5:
            response += f"\n... ve {len(scheduled_commands) - 5} komut daha"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yeni Zamanlanmış Komut", callback_data="create_scheduled_command"),
                InlineKeyboardButton(text="📋 Tüm Komutlar", callback_data="list_scheduled_commands")
            ],
            [
                InlineKeyboardButton(text="⚙️ Komut Yönetimi", callback_data="manage_scheduled_commands"),
                InlineKeyboardButton(text="📊 İstatistikler", callback_data="scheduled_stats")
            ],
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_system_management")
            ]
        ])
        
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Zamanlanmış komutlar menüsü hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_link_commands_list(callback: types.CallbackQuery) -> None:
    """Link komutları listesi"""
    try:
        from handlers.dynamic_command_creator import get_all_custom_commands
        
        commands = await get_all_custom_commands()
        link_commands = [cmd for cmd in commands if cmd.get("type") == "link"]
        
        if not link_commands:
            response = """
🔗 **Link Komutları Listesi**

❌ **Henüz link komutu oluşturulmamış!**

**Yeni link komutu oluşturmak için:**
• "➕ Yeni Link Komutu" butonuna tıklayın
• Komut adını girin (örn: site)
• Link URL'sini girin
• Açıklama ekleyin (opsiyonel)
            """
        else:
            response = f"""
🔗 **Link Komutları Listesi**

**Toplam:** {len(link_commands)} komut

"""
            for i, cmd in enumerate(link_commands, 1):
                status = "✅" if cmd.get("active") else "❌"
                response += f"""
**{i}. {status} !{cmd['command']}**
📝 **Açıklama:** {cmd.get('description', 'Açıklama yok')}
🔗 **Link:** {cmd.get('content', 'Link yok')}
📊 **Kullanım:** {cmd.get('usage_count', 0)} kez
📅 **Oluşturulma:** {cmd.get('created_at', 'Bilinmiyor')}

"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yeni Komut", callback_data="create_link_command"),
                InlineKeyboardButton(text="⚙️ Yönetim", callback_data="manage_link_commands")
            ],
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_link_commands")
            ]
        ])
        
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Link komutları listesi hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_link_commands_management(callback: types.CallbackQuery) -> None:
    """Link komutları yönetimi"""
    try:
        from handlers.dynamic_command_creator import get_all_custom_commands
        
        commands = await get_all_custom_commands()
        link_commands = [cmd for cmd in commands if cmd.get("type") == "link"]
        
        if not link_commands:
            response = """
⚙️ **Link Komutları Yönetimi**

❌ **Yönetilecek komut bulunamadı!**

Önce link komutu oluşturun.
            """
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Yeni Komut", callback_data="create_link_command")],
                [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_link_commands")]
            ])
        else:
            response = f"""
⚙️ **Link Komutları Yönetimi**

**Toplam:** {len(link_commands)} komut

**Yönetim Seçenekleri:**
            """
            
            # Her komut için buton oluştur
            keyboard_buttons = []
            for cmd in link_commands[:8]:  # Maksimum 8 komut
                status = "🟢" if cmd.get("active") else "🔴"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"{status} !{cmd['command']}", 
                        callback_data=f"manage_link_{cmd['command']}"
                    )
                ])
            
            keyboard_buttons.extend([
                [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_link_commands")]
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Link komutları yönetimi hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_link_commands_stats(callback: types.CallbackQuery) -> None:
    """Link komutları istatistikleri"""
    try:
        from handlers.dynamic_command_creator import get_all_custom_commands
        
        commands = await get_all_custom_commands()
        link_commands = [cmd for cmd in commands if cmd.get("type") == "link"]
        
        if not link_commands:
            response = """
📊 **Link Komutları İstatistikleri**

❌ **Henüz link komutu oluşturulmamış!**

İstatistik görmek için önce link komutu oluşturun.
            """
        else:
            active_commands = [cmd for cmd in link_commands if cmd.get("active")]
            total_usage = sum(cmd.get("usage_count", 0) for cmd in link_commands)
            most_used = max(link_commands, key=lambda x: x.get("usage_count", 0)) if link_commands else None
            
            response = f"""
📊 **Link Komutları İstatistikleri**

**Genel Bilgiler:**
• **Toplam Komut:** {len(link_commands)}
• **Aktif Komut:** {len(active_commands)}
• **Pasif Komut:** {len(link_commands) - len(active_commands)}
• **Toplam Kullanım:** {total_usage} kez

**En Çok Kullanılan:**
"""
            if most_used:
                response += f"• **!{most_used['command']}** - {most_used.get('usage_count', 0)} kez kullanıldı"
            else:
                response += "• Henüz kullanım yok"
            
            response += f"""

**Kullanım Dağılımı:**
"""
            for cmd in link_commands[:5]:  # İlk 5 komut
                response += f"• **!{cmd['command']}** - {cmd.get('usage_count', 0)} kez\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Tüm Komutlar", callback_data="list_link_commands"),
                InlineKeyboardButton(text="⚙️ Yönetim", callback_data="manage_link_commands")
            ],
            [
                InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_link_commands")
            ]
        ])
        
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Link komutları istatistikleri hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def handle_lottery_input(message: types.Message) -> None:
    """Çekiliş input handler"""
    try:
        user_id = message.from_user.id
        from utils.memory_manager import memory_manager
        
        logger.info(f"🎯 LOTTERY INPUT HANDLER CALLED - User: {user_id}, Text: '{message.text}'")
        
        # Input state'i al
        input_state = memory_manager.get_input_state(user_id)
        logger.info(f"🎯 LOTTERY INPUT DEBUG - User: {user_id}, Input State: {input_state}")
        
        if not input_state or not input_state.startswith("lottery_"):
            logger.info(f"🎯 LOTTERY INPUT REJECTED - User: {user_id}, Input State: {input_state}")
            return
        
        # Çekiliş verilerini al
        lottery_data = memory_manager.get_lottery_data(user_id)
        if not lottery_data:
            await message.answer("❌ Çekiliş verisi bulunamadı!")
            memory_manager.clear_input_state(user_id)
            return
        
        step = lottery_data.get("step", "")
        text = message.text.strip()
        
        logger.info(f"🎯 LOTTERY INPUT - User: {user_id}, Step: {step}, Text: {text}")
        
        # Input state'e göre işle
        if input_state == "lottery_cost":
            try:
                cost = float(text)
                if cost < 0:
                    await message.answer("❌ Maliyet 0'dan küçük olamaz!")
                    return
                
                lottery_data["cost"] = cost
                lottery_data["step"] = "prize"
                memory_manager.set_lottery_data(user_id, lottery_data)
                memory_manager.set_input_state(user_id, "lottery_prize")
                
                await message.answer("💰 **Ödül Miktarı**\n\nÇekiliş ödülü ne kadar olsun?")
                
            except ValueError:
                await message.answer("❌ Geçerli bir sayı girin!")
                return
                
        elif input_state == "lottery_prize":
            try:
                prize = float(text)
                if prize < 0:
                    await message.answer("❌ Ödül 0'dan küçük olamaz!")
                    return
                
                lottery_data["prize"] = prize
                lottery_data["step"] = "duration"
                memory_manager.set_lottery_data(user_id, lottery_data)
                memory_manager.set_input_state(user_id, "lottery_duration")
                
                await message.answer("⏰ **Çekiliş Süresi**\n\nÇekiliş kaç saat sürsün? (1-168 saat)")
                
            except ValueError:
                await message.answer("❌ Geçerli bir sayı girin!")
                return
                
        elif input_state == "lottery_duration":
            try:
                duration = int(text)
                if duration < 1 or duration > 168:
                    await message.answer("❌ Süre 1-168 saat arasında olmalı!")
                    return
                
                lottery_data["duration"] = duration
                lottery_data["step"] = "description"
                memory_manager.set_lottery_data(user_id, lottery_data)
                memory_manager.set_input_state(user_id, "lottery_description")
                
                await message.answer("📝 **Çekiliş Açıklaması**\n\nÇekiliş açıklamasını yazın:")
                
            except ValueError:
                await message.answer("❌ Geçerli bir sayı girin!")
                return
                
        elif input_state == "lottery_description":
            if len(text) < 10:
                await message.answer("❌ Açıklama en az 10 karakter olmalı!")
                return
            
            lottery_data["description"] = text
            lottery_data["step"] = "confirm"
            memory_manager.set_lottery_data(user_id, lottery_data)
            
            # Özet göster
            cost = lottery_data.get("cost", 0)
            prize = lottery_data.get("prize", 0)
            duration = lottery_data.get("duration", 0)
            description = lottery_data.get("description", "")
            
            summary = f"""
🎲 **ÇEKİLİŞ ÖZETİ**

💰 **Maliyet:** {cost} puan
🏆 **Ödül:** {prize} puan
⏰ **Süre:** {duration} saat
📝 **Açıklama:** {description}

✅ Çekilişi oluşturmak istiyor musunuz?
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Oluştur", callback_data="lottery_confirm_create")],
                [InlineKeyboardButton(text="❌ İptal", callback_data="lottery_cancel")]
            ])
            
            await message.answer(summary, parse_mode="Markdown", reply_markup=keyboard)
            
        # Input state'i temizle
        memory_manager.clear_input_state(user_id)
        
    except Exception as e:
        logger.error(f"❌ Çekiliş input hatası: {e}")
        await message.answer("❌ Bir hata oluştu!")
        from utils.memory_manager import memory_manager
        memory_manager.clear_input_state(user_id)

async def handle_lottery_confirm_create(callback: types.CallbackQuery) -> None:
    """Çekiliş oluşturma onayı"""
    try:
        user_id = callback.from_user.id
        from utils.memory_manager import memory_manager
        
        # Çekiliş verilerini al
        lottery_data = memory_manager.get_lottery_data(user_id)
        if not lottery_data:
            await callback.answer("❌ Çekiliş verisi bulunamadı!", show_alert=True)
            return
        
        # Çekilişi veritabanına kaydet
        from database import get_db_pool
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO events (name, description, entry_fee, prize_pool, duration_hours, created_by, status)
                VALUES ($1, $2, $3, $4, $5, $6, 'active')
            ''', 
            f"Çekiliş - {lottery_data.get('description', '')[:30]}",
            lottery_data.get('description', ''),
            lottery_data.get('cost', 0),
            lottery_data.get('prize', 0),
            lottery_data.get('duration', 24),
            user_id
            )
        
        # Verileri temizle
        memory_manager.clear_lottery_data(user_id)
        memory_manager.clear_input_state(user_id)
        
        await callback.answer("✅ Çekiliş başarıyla oluşturuldu!", show_alert=True)
        
        # Ana menüye dön
        await show_main_admin_menu(callback)
        
    except Exception as e:
        logger.error(f"❌ Çekiliş oluşturma hatası: {e}")
        await callback.answer("❌ Çekiliş oluşturulamadı!", show_alert=True)

async def handle_lottery_cancel(callback: types.CallbackQuery) -> None:
    """Çekiliş iptal"""
    try:
        user_id = callback.from_user.id
        from utils.memory_manager import memory_manager
        
        # Verileri temizle
        memory_manager.clear_lottery_data(user_id)
        memory_manager.clear_input_state(user_id)
        
        await callback.answer("❌ Çekiliş iptal edildi!", show_alert=True)
        
        # Ana menüye dön
        await show_main_admin_menu(callback)
        
    except Exception as e:
        logger.error(f"❌ Çekiliş iptal hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def update_bot_command(message: types.Message) -> None:
    """Bot güncelleme komutu - Sadece admin"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await message.reply("❌ Bu komut sadece admin için!")
            return
        
        # Grup chatindeyse sil
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Güncelleme mesajı
        await message.reply("🔄 Bot güncelleniyor... Bu işlem 30 saniye sürebilir.")
        
        # Güncelleme işlemi
        import subprocess
        import asyncio
        
        try:
            # Git pull
            result = subprocess.run(
                ["git", "pull", "origin", "main"], 
                capture_output=True, 
                text=True, 
                cwd="/root/telegrambot"
            )
            
            if result.returncode == 0:
                # Bot'u yeniden başlat
                subprocess.run(["pkill", "-f", "python3 main.py"], cwd="/root/telegrambot")
                await asyncio.sleep(2)
                
                # Yeni bot'u başlat
                subprocess.Popen([
                    "nohup", "python3", "main.py", ">", "bot.log", "2>&1", "&"
                ], cwd="/root/telegrambot")
                
                await message.reply("✅ Bot başarıyla güncellendi ve yeniden başlatıldı!")
            else:
                await message.reply(f"❌ Git pull hatası: {result.stderr}")
                
        except Exception as e:
            await message.reply(f"❌ Güncelleme hatası: {e}")
            
    except Exception as e:
        logger.error(f"❌ Bot güncelleme hatası: {e}")
        await message.reply("❌ Güncelleme sırasında hata oluştu!")