"""
🤖 Modern Telegram Bot - aiogram + Database
Modüler yapıda, Python 3.13 uyumlu
"""

import asyncio
import logging
import os
import psutil
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# Local imports
from config import get_config, validate_config
from database import init_database, close_database
from handlers import (
    start_command, kirvekayit_command, private_message_handler, 
    register_callback_handler, kayitsil_command, kirvegrup_command, 
    group_info_command, monitor_group_message, start_cleanup_task,
    menu_command, profile_callback_handler, yardim_command, komutlar_command,
    siparislerim_command, siralama_command, profil_command
)
from handlers.recruitment_system import (
    start_recruitment_background, handle_recruitment_response
)
from handlers.chat_system import (
    handle_chat_message, send_chat_response, bot_write_command
)
from handlers.admin_panel import router as admin_panel_router
from handlers.simple_events import router as simple_events_router, set_bot_instance as set_events_bot_instance
from handlers.unknown_commands import router as unknown_commands_router, set_bot_instance as set_unknown_bot_instance
from handlers.event_participation import router as event_participation_router, set_bot_instance as set_participation_bot_instance
from handlers.events_list import set_bot_instance as set_events_list_bot_instance
from handlers.system_notifications import send_maintenance_notification, send_startup_notification
from handlers.scheduled_messages import set_bot_instance as set_scheduled_bot, start_scheduled_messages
from handlers.balance_event import router as balance_event_router

from utils import setup_logger
from utils.logger import log_system, log_bot, log_error, log_info, log_warning
from utils.rate_limiter import rate_limiter, rate_limit
from utils.memory_manager import memory_manager, start_memory_cleanup, cleanup_all_resources

# Logger'ı kur
logger = setup_logger()

# Global bot instance kontrolü
_bot_instance = None
_bot_started = False
_bot_lock_file = "bot_running.lock"

def check_bot_running():
    """Bot'un zaten çalışıp çalışmadığını kontrol et"""
    try:
        if os.path.exists(_bot_lock_file):
            try:
                with open(_bot_lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    if "python" in process.name().lower() and "main.py" in " ".join(process.cmdline()).lower():
                        log_system(f"⚠️ Bot zaten çalışıyor! PID: {pid}")
                        return True
            except:
                pass
        
        if os.path.exists(_bot_lock_file):
            os.remove(_bot_lock_file)
            
        return False
    except Exception as e:
        log_system(f"⚠️ Bot kontrol hatası: {e}")
        return False

def create_bot_lock():
    """Bot lock file oluştur"""
    try:
        with open(_bot_lock_file, 'w') as f:
            f.write(str(os.getpid()))
        log_system(f"✅ Bot lock file oluşturuldu - PID: {os.getpid()}")
    except Exception as e:
        log_system(f"❌ Bot lock file oluşturulamadı: {e}")

def remove_bot_lock():
    """Bot lock file'ı kaldır"""
    try:
        if os.path.exists(_bot_lock_file):
            os.remove(_bot_lock_file)
            log_system("✅ Bot lock file kaldırıldı")
    except Exception as e:
        log_system(f"❌ Bot lock file kaldırılamadı: {e}")

async def cleanup_resources():
    """Temizlik işlemleri - Enhanced"""
    try:
        log_system("🧹 Temizlik işlemleri başlatılıyor...")
        
        # Database bağlantısını kapat
        await close_database()
        
        # Bot session'ını kapat
        if _bot_instance:
            await _bot_instance.session.close()
            log_system("🤖 Bot session kapatıldı.")
        
        # Lock file'ı kaldır
        remove_bot_lock()
        
        log_system("✅ Temizlik işlemleri tamamlandı!")
        
    except Exception as e:
        log_error(f"Cleanup hatası: {e}")
        # Hata durumunda da lock file'ı kaldırmaya çalış
        try:
            remove_bot_lock()
        except:
            pass

async def main():
    """Ana bot fonksiyonu"""
    try:
        # Bot lock kontrolü
        if check_bot_running():
            log_system("Bot zaten çalışıyor!")
            return
        
        # Lock file oluştur
        create_bot_lock()
        log_system("Bot başlatılıyor...")
        
        # Konfigürasyon kontrolü
        config = get_config()
        log_system("Konfigürasyon doğrulandı")
        
        # Database bağlantısı
        log_system("Database bağlantısı kuruluyor...")
        db_success = await init_database()
        if not db_success:
            log_warning("⚠️ Database olmadan devam ediliyor!", "WARNING")
        else:
            log_system("✅ Database bağlantısı başarılı!")
        
        # Bot instance oluştur
        log_system("Bot instance oluşturuluyor...")
        bot = Bot(token=config.BOT_TOKEN)
        _bot_instance = bot  # Global instance'ı set et
        
        # Bot instance'ını handler'lara aktar
        log_system("Bot instance handler'lara aktarılıyor...")
        set_events_bot_instance(bot)
        set_unknown_bot_instance(bot)
        set_participation_bot_instance(bot)
        set_events_list_bot_instance(bot)
        set_scheduled_bot(bot)
        
        # Admin panel bot instance'ını set et
        from handlers.admin_panel import set_bot_instance as set_admin_panel_bot_instance
        set_admin_panel_bot_instance(bot)
        
        # Diğer handler'lar için bot instance'ını set et
        from handlers.statistics_system import set_bot_instance as set_statistics_bot_instance
        from handlers.event_management import set_bot_instance as set_event_management_bot_instance
        from handlers.dynamic_command_creator import set_bot_instance as set_dynamic_command_bot_instance
        from handlers.broadcast_system import set_bot_instance as set_broadcast_bot_instance
        from handlers.balance_management import set_bot_instance as set_balance_bot_instance
        from handlers.admin_permission_manager import set_bot_instance as set_admin_permission_bot_instance
        from handlers.admin_market_management import set_bot_instance as set_admin_market_bot_instance
        from handlers.admin_commands import set_bot_instance as set_admin_commands_bot_instance
        
        set_statistics_bot_instance(bot)
        set_event_management_bot_instance(bot)
        set_dynamic_command_bot_instance(bot)
        set_broadcast_bot_instance(bot)
        set_balance_bot_instance(bot)
        set_admin_permission_bot_instance(bot)
        set_admin_market_bot_instance(bot)
        set_admin_commands_bot_instance(bot)
        
        # Group handler bot instance'ını set et
        from handlers.group_handler import set_bot_instance as set_group_handler_bot_instance
        set_group_handler_bot_instance(bot)
        
        log_system("✅ Bot instance tüm handler'lara aktarıldı!")
        
        dp = Dispatcher()
        
        # Handler'ları kaydet
        log_system("Handler'lar kaydediliyor...")
        
        # 1. CALLBACK HANDLER'LARI (inline button'lar) - ÖNCE callback'leri kaydet
        dp.callback_query(F.data == "register_user")(register_callback_handler)
        dp.callback_query(F.data == "get_info")(register_callback_handler)
        
        # Etkinlik listesi callback'i
        from handlers.events_list import refresh_lotteries_list_callback
        dp.callback_query(F.data == "refresh_lotteries_list")(refresh_lotteries_list_callback)
        
        log_system("Callback handler'lar kaydedildi")
        
        # Profil callback'leri - EN BAŞTA KAYIT ET!
        from handlers.profile_handler import profile_callback_handler
        
        # Profil callback'leri - Basit filter
        dp.callback_query(lambda c: c.data and c.data.startswith("profile_"))(profile_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("buy_product_"))(profile_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("confirm_buy_"))(profile_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("view_product_"))(profile_callback_handler)
        dp.callback_query(F.data == "product_sold_out")(profile_callback_handler)
        dp.callback_query(F.data == "my_orders")(profile_callback_handler)
        dp.callback_query(F.data == "profile_orders")(profile_callback_handler)
        dp.callback_query(F.data == "insufficient_balance")(profile_callback_handler)
        dp.callback_query(F.data == "out_of_stock")(profile_callback_handler)
        dp.callback_query(F.data == "profile_back")(profile_callback_handler)
        dp.callback_query(F.data == "profile_refresh")(profile_callback_handler)
        
        # Admin sipariş callback'leri - MANUEL KAYIT (ÖNCE - daha spesifik)
        from handlers.admin_order_management import handle_admin_approve_order, handle_admin_reject_order
        
        # Wrapper fonksiyonlar
        async def admin_approve_callback_wrapper(callback):
            order_number = callback.data.replace("admin_approve_", "")
            return await handle_admin_approve_order(callback, order_number)
        
        async def admin_reject_callback_wrapper(callback):
            order_number = callback.data.replace("admin_reject_", "")
            return await handle_admin_reject_order(callback, order_number)
        
        dp.callback_query(lambda c: c.data and c.data.startswith("admin_approve_"))(admin_approve_callback_wrapper)
        dp.callback_query(lambda c: c.data and c.data.startswith("admin_reject_"))(admin_reject_callback_wrapper)
        
        # Broadcast system callback'leri - KALDIRILDI (admin_panel_callback'te yönetiliyor)
        # from handlers.broadcast_system import start_broadcast, cancel_broadcast
        # dp.callback_query(F.data == "admin_broadcast")(start_broadcast)
        # dp.callback_query(F.data == "admin_broadcast_cancel")(cancel_broadcast)
        
        # Kategori ve fiyat callback'leri - MANUEL KAYIT
        from handlers.admin_panel import handle_category_callback, handle_price_callback
        
        # Wrapper fonksiyonlar
        async def category_callback_wrapper(callback):
            return await handle_category_callback(callback, callback.data)
        
        async def price_callback_wrapper(callback):
            return await handle_price_callback(callback, callback.data)
        
        dp.callback_query(F.data.startswith("category_"))(category_callback_wrapper)
        dp.callback_query(F.data.startswith("price_"))(price_callback_wrapper)
        
        # Admin sipariş callback'leri - admin_panel.py içinde handle ediliyor
        
        # Admin commands list callback'leri - KALDIRILDI
        # from handlers.admin_commands_list import admin_commands_callback
        # dp.callback_query(F.data.startswith("admin_commands_"))(admin_commands_callback)
        # admin_commands_back router tarafından yönetiliyor
        
        # Etkinlik listesi callback'i
        from handlers.events_list import refresh_lotteries_list_callback
        dp.callback_query(F.data == "refresh_lotteries_list")(refresh_lotteries_list_callback)
        
        # Çekiliş callback'leri - MANUEL KAYIT
        from handlers.simple_events import (
            select_lottery_type, select_bonus_type, show_lottery_list, 
            cancel_lottery_creation, back_to_lottery_menu, handle_lottery_input,
            select_group_for_event, confirm_lottery_creation, create_lottery_callback
        )
        
        dp.callback_query(F.data == "lottery_type_lottery")(select_lottery_type)
        dp.callback_query(F.data == "lottery_type_bonus")(select_bonus_type)
        dp.callback_query(F.data == "lottery_list")(show_lottery_list)
        dp.callback_query(F.data == "lottery_cancel")(cancel_lottery_creation)
        dp.callback_query(F.data == "lottery_back_to_menu")(back_to_lottery_menu)
        dp.callback_query(F.data.startswith("select_group_"))(select_group_for_event)
        dp.callback_query(F.data == "lottery_confirm_create")(confirm_lottery_creation)
        dp.callback_query(F.data == "create_lottery_command")(create_lottery_callback)
        
        # Debug handler'ı kaldırıldı - callback çakışmasına neden oluyordu
        
        # Bakiye komutları - MANUEL KAYIT
        from handlers.balance_management import add_balance_command, remove_balance_command, add_balance_id_command, remove_balance_id_command
        dp.message(Command("bakiyee"))(add_balance_command)
        dp.message(Command("bakiyec"))(remove_balance_command)
        dp.message(Command("bakiyeeid"))(add_balance_id_command)
        dp.message(Command("bakiyecid"))(remove_balance_id_command)
        
        # 1. GRUP SESSİZLİK SİSTEMİ - EN ÖNCE KAYIT ET!
        # Grup chatindeki tüm komutları yakala ve özelde çalıştır
        dp.message(F.chat.type.in_(["group", "supergroup"]), F.text.startswith("/"))(handle_group_command_silently)
        
        # 2. KOMUT HANDLER'LARI
        dp.message(CommandStart())(start_command)
        dp.message(Command("kirvekayit"))(kirvekayit_command)
        dp.message(Command("kayitsil"))(kayitsil_command)
        dp.message(Command("kirvegrup"))(kirvegrup_command)
        dp.message(Command("grupbilgi"))(group_info_command)
        dp.message(Command("menu"))(menu_command)
        dp.message(Command("komutlar"))(komutlar_command)
        dp.message(Command("siparislerim"))(siparislerim_command)
        dp.message(Command("siralama"))(siralama_command)
        dp.message(Command("profil"))(profil_command)
        
        # Admin komutları artık router'larda
        
        # Etkinlik komutları kaldırıldı
        
        # Admin komutları
        from handlers.admin_commands import make_admin_command
        dp.message(Command("adminyap"))(make_admin_command)
        
        # Market yönetim sistemi
        from handlers.admin_market_management import market_management_command, handle_product_creation_input
        dp.message(Command("market"))(market_management_command)
        
        # Market callback handler
        from handlers.admin_market_management import router as market_router
        dp.include_router(market_router)
        
        # Admin commands list router - KALDIRILDI
        # from handlers.admin_commands_list import router as admin_commands_router
        # dp.include_router(admin_commands_router)
        
        # Reports router'ları - ZATEN YUKARIDA İMPORT EDİLDİ
        # from handlers.reports.user_report import router as user_report_router
        # from handlers.reports.point_report import router as point_report_router
        # from handlers.reports.event_report import router as event_report_router
        # from handlers.reports.system_report import router as system_report_router
            # Reports router'ları kaldırıldı - admin_panel_callback'te import ediliyor
        
        # 🔥 CRİTİK: MANUEL HANDLER KAYIT - GRUP SESSİZLİĞİ İÇİN (ROUTER'LAR YOK!)
        # TEK ADMİN PANELİ SİSTEMİ - admin_commands_list.py kaldırıldı
        from handlers.admin_panel import admin_panel_command, clean_messages_command, list_groups_command, help_command, approve_order_command, test_market_system_command, test_sql_queries_command, test_user_orders_command, update_bot_command
        from handlers.admin_order_management import show_orders_list_modern
        # from handlers.admin_commands_list import admin_commands_list  # KALDIRILDI
        from handlers.events_list import list_active_lotteries as list_active_events, refresh_lotteries_list_callback
        from handlers.event_management import end_lottery_command as end_event_command
        
        # MANUEL HANDLER KAYITLARI - TEK ADMİN PANELİ
        dp.message(Command("adminpanel"))(admin_panel_command)  # Ana admin panel
        dp.message(Command("updatebot"))(update_bot_command)  # Bot güncelleme komutu
        dp.message(Command("adminkomutlar"))(admin_panel_command)  # Admin komutları (alias)
        # dp.message(Command("adminkomut"))(admin_commands_list)  # Admin komutları listesi - KALDIRILDI
        dp.message(Command("temizle"))(clean_messages_command)   # Mesaj silme
        dp.message(Command("gruplar"))(list_groups_command)      # Grup listesi
        dp.message(Command("yardim"))(help_command)              # Yardım menüsü
        dp.message(Command("siparisliste"))(show_orders_list_modern) # Sipariş listesi
        dp.message(Command("siparisonayla"))(approve_order_command) # Sipariş onaylama
        
        # Test komutları
        dp.message(Command("testmarket"))(test_market_system_command) # Market test
        dp.message(Command("testsql"))(test_sql_queries_command) # SQL test
        dp.message(Command("testsiparis"))(test_user_orders_command) # Sipariş test
        dp.message(Command("etkinlikler"))(list_active_events)
        dp.message(Command("etkinlikbitir"))(end_event_command)
        
        # Admin komutları - MANUEL
        from handlers.admin_commands import (
            delete_command_command, take_permission_command, 
            check_admin_level_command, admin_help_command
        )
        dp.message(Command("komutsil"))(delete_command_command)  # Komut silme
        dp.message(Command("yetkial"))(take_permission_command)  # Yetki alma
        dp.message(Command("adminseviye"))(check_admin_level_command)  # Admin seviye kontrolü
        dp.message(Command("adminyardım"))(admin_help_command)  # Admin yardım
        
        # Etkinlik oluşturma komutu - MANUEL
        from handlers.simple_events import create_lottery_command as create_event_command
        dp.message(Command("etkinlik"))(create_event_command)
        # Lottery handler'ı geçici olarak devre dışı
        # dp.message()(handle_lottery_input)  # Etkinlik input handler'ı
        
        # Etkinlik yönetimi komutları - MANUEL
        from handlers.event_management import cancel_event_command, event_status_command, event_help_command
        dp.message(Command("etkinlikiptal"))(cancel_event_command)  # Etkinlik iptal
        dp.message(Command("etkinlikdurum"))(event_status_command)  # Etkinlik durum
        dp.message(Command("etkinlikyardım"))(event_help_command)  # Etkinlik yardım
        
        # Çekiliş komutları - MANUEL
        from handlers.simple_events import create_lottery_command
        from handlers.events_list import list_active_lotteries
        from handlers.event_management import end_lottery_command
        
        dp.message(Command("cekilisyap"))(create_lottery_command)
        dp.message(Command("cekilisler"))(list_active_lotteries)
        dp.message(Command("cekilisbitir"))(end_lottery_command)
        
        # 🔥 YENİ EKSİK SİSTEMLER - MANUEL KOMUTLAR
        # Zamanlanmış mesajlar sistemi komutları - EKSİK FONKSIYONLAR, KALDIRILDI
        # from handlers.scheduled_messages import create_scheduled_bot_command, list_scheduled_bots_command, edit_scheduled_bot_command, delete_scheduled_bot_command
        # dp.message(Command("zamanlanmesmesaj"))(create_scheduled_bot_command)
        # dp.message(Command("zamanlimesajlar"))(list_scheduled_bots_command)
        # dp.message(Command("zamanlimesajduzenle"))(edit_scheduled_bot_command)
        # dp.message(Command("zamanlimesajsil"))(delete_scheduled_bot_command)
        
        # Bakiye etkinlikleri sistemi komutları - EKSİK FONKSIYONLAR, KALDIRILDI
        # from handlers.balance_event import create_balance_event_command, list_balance_events_command
        # dp.message(Command("bakiyeetkinlik"))(create_balance_event_command)
        # dp.message(Command("bakiyeetkinlikler"))(list_balance_events_command)
        
        # Admin izin yöneticisi komutları - EKSİK FONKSIYONLAR, KALDIRILDI
        # from handlers.admin_permission_manager import admin_permission_command, set_admin_level_command
        # dp.message(Command("adminyetki"))(admin_permission_command)
        # dp.message(Command("adminseviyeayarla"))(set_admin_level_command)
        
        # 📊 İstatistikler Sistemi komutları - YENİ!
        from handlers.statistics_system import admin_stats_command, system_stats_command
        dp.message(Command("adminstats"))(admin_stats_command)
        dp.message(Command("sistemistatistik"))(system_stats_command)
        
        log_system("Manuel handler'lar kayıtlandı - Router'lar YOK!")
        
        # Etkinlik katılım handler'ı için gerekli
        dp.include_router(event_participation_router)  # GERİ EKLENDİ - Katılım handler için
        
        # Event management router'ını da ekle - end_event callback'i için
        from handlers.event_management import router as event_management_router
        dp.include_router(event_management_router)  # End event callback için
        
        # Statistics system callback'leri - MANUEL KAYIT
        from handlers.statistics_system import handle_stats_callback
        dp.callback_query(F.data.startswith("stats_"))(handle_stats_callback)
        
        # Dynamic command creator router'ını dahil et - EN ÖNCE!
        from handlers.dynamic_command_creator import router as dynamic_command_router
        dp.include_router(dynamic_command_router)  # Dinamik komut oluşturucu için
        
        # BROADCAST SYSTEM ROUTER (FSM için EN ÖNCE)
        # dp.include_router(broadcast_system_router) # Kaldırıldı
        
        # Admin commands router'ını dahil et - ZATEN DAHİL EDİLDİ (YUKARIDA)
        # from handlers.admin_commands import router as admin_commands_router
        # dp.include_router(admin_commands_router)  # Admin yetki komutları için
        
        # Admin permission manager router'ını dahil et
        from handlers.admin_permission_manager import router as admin_permission_router
        dp.include_router(admin_permission_router)  # Admin yetki yönetimi için

        # Admin panel router'ını dahil et (FSM handler'ları için)
        dp.include_router(admin_panel_router)
        
        # 🔥 YENİ EKSİK SİSTEMLER - ROUTER'LAR
        dp.include_router(balance_event_router)  # Bakiye etkinlikleri sistemi
        
        # 📊 İstatistikler Sistemi - ROUTER
        from handlers.statistics_system import router as statistics_router
        dp.include_router(statistics_router)  # İstatistikler sistemi
        
        # Bot yazma komutu
        dp.message(Command("botyaz"))(bot_write_command)
        
        # 4. PRIVATE MESSAGE HANDLER - Market ürün ekleme + admin sipariş mesajları (EN SON!)
        from handlers.admin_panel import handle_product_step_input
        from handlers.admin_order_management import handle_admin_order_message
        from handlers.admin_market_management import handle_product_creation_input
        
        # BROADCAST MESSAGE HANDLER - handle_all_chat_inputs İÇİNDE KONTROL EDİLİYOR
        from handlers.broadcast_system import process_broadcast_message
        # dp.message(F.chat.type == "private", ~F.text.startswith("/"))(process_broadcast_message)
        
        # 🔧 CHAT-BASED SİSTEMLER - TEK HANDLER İLE YÖNETİM
        async def handle_all_chat_inputs(message: Message):
            """Tüm chat-based input sistemlerini tek handler'da yönet"""
            try:
                user_id = message.from_user.id
                
                # DEBUG: Input handler başlatıldı
                # logger.info(f"🔧 INPUT HANDLER BAŞLATILDI - User: {user_id}, Text: '{message.text}'")
                
                # Komut mesajlarını atla
                if message.text.startswith("/"):
                    log_system(f"⏭️ Komut mesajı atlandı - User: {user_id}")
                    return
                
                # 0. BROADCAST SİSTEMİ KONTROLÜ - EN ÖNCE
                from handlers.broadcast_system import broadcast_states
                if user_id in broadcast_states and broadcast_states[user_id] == "waiting_for_message":
                    from handlers.broadcast_system import process_broadcast_message
                    await process_broadcast_message(message)
                    return
                
                # 1. Komut oluşturma sistemi kontrolü
                from handlers.dynamic_command_creator import command_creation_states
                if user_id in command_creation_states:
                    from handlers.dynamic_command_creator import handle_command_creation_input
                    await handle_command_creation_input(message)
                    return
                
                # 2. Market ürün ekleme sistemi kontrolü
                from handlers.admin_market_management import product_creation_data
                if user_id in product_creation_data:
                    from handlers.admin_market_management import handle_product_creation_input
                    await handle_product_creation_input(message)
                    return
                
                # 2.1. Market ürün düzenleme sistemi kontrolü
                from handlers.admin_market_management import product_edit_data
                if user_id in product_edit_data:
                    from handlers.admin_market_management import handle_product_edit_input
                    await handle_product_edit_input(message)
                    return
                
                # 2.2. Market ürün silme sistemi kontrolü
                from handlers.admin_market_management import product_delete_data
                if user_id in product_delete_data:
                    from handlers.admin_market_management import handle_product_delete_input
                    await handle_product_delete_input(message)
                    return
                
                # 3. Admin panel ürün adım sistemi kontrolü
                from handlers.admin_panel import product_data_storage
                if user_id in product_data_storage:
                    from handlers.admin_panel import handle_product_step_input
                    await handle_product_step_input(message)
                    return
                
                # 4. Admin sipariş mesajları kontrolü
                from handlers.admin_order_management import admin_order_states
                if user_id in admin_order_states:
                    from handlers.admin_order_management import handle_admin_order_message
                    await handle_admin_order_message(message)
                    return
                
                # 5. Custom input kontrolü - Sistem ayarları için
                from utils.memory_manager import memory_manager
                cache_manager = memory_manager.get_cache_manager()
                input_state = cache_manager.get_cache(f"input_state_{user_id}")
                if input_state and input_state in ["custom_points", "custom_daily", "custom_weekly"]:
                    log_system(f"💰 CUSTOM INPUT BULUNDU - User: {user_id}, State: {input_state}")
                    from handlers.admin_panel import handle_custom_input
                    await handle_custom_input(message)
                    return
                
                # 6. Recruitment response kontrolü - kendi kontrolünü yapar
                from handlers.recruitment_system import handle_recruitment_response
                await handle_recruitment_response(message)
                
                # 7. Çekiliş input kontrolü - çekiliş oluşturma sürecinde
                lottery_data = memory_manager.get_lottery_data(user_id)
                # logger.info(f"🎯 ÇEKİLİŞ KONTROL - User: {user_id}, lottery_data: {lottery_data}")
                if lottery_data:
                    log_system(f"🎯 ÇEKİLİŞ INPUT BULUNDU - User: {user_id}, Data: {lottery_data}")
                    from handlers.simple_events import handle_lottery_input
                    await handle_lottery_input(message)
                    return
                else:
                    # logger.info(f"🎯 ÇEKİLİŞ DATA YOK - User: {user_id}")
                    pass
                
                # 8. Scheduled Messages input kontrolü
                input_state = memory_manager.get_input_state(user_id)
                if input_state and (input_state.startswith("create_bot_") or input_state.startswith("recreate_bot_") or input_state.startswith("add_link_")):
                    log_system(f"🔍 SCHEDULED INPUT BULUNDU - User: {user_id}, State: {input_state}")
                    from handlers.scheduled_messages import handle_scheduled_input
                    await handle_scheduled_input(message)
                    return
                
                # 9. Dinamik komut çalıştırma kontrolü - en son
                from handlers.dynamic_command_creator import handle_custom_command
                await handle_custom_command(message)
                
            except Exception as e:
                log_error(f"❌ Chat input handler hatası: {e}")

        # ESKİ KARMAŞIK HANDLER YERİNE BASİT HANDLER
        @dp.message(F.chat.type == "private")
        async def simple_message_handler(message: Message):
            """Basit mesaj handler - Sadece özel mesajlar için"""
            try:
                user_id = message.from_user.id
                # print(f"MESAJ ALINDI: '{message.text}' - User: {user_id}")
                
                # Komut değilse handle_all_chat_inputs'u çağır
                if not message.text.startswith("/"):
                    await handle_all_chat_inputs(message)
                    
            except Exception as e:
                print(f"HANDLER HATASI: {e}")
        
        # Eski karmaşık kayıt - iptal
        # dp.message(F.chat.type == "private", ~F.text.startswith("/"))(handle_all_chat_inputs)
        
        # Grup mesajları için tek handler - hem dinamik komutlar hem chat sistemi
        async def handle_group_command_creation(message: Message):
            """Grup mesajlarında hem dinamik komutlar hem chat sistemi"""
            try:
                user_id = message.from_user.id
                
                # Komut mesajlarını atla
                if message.text.startswith("/"):
                    return
                
                # Dinamik komut handler'ı önce çağır - ! ile başlayan komutlar için
                if message.text.startswith('!'):
                    from handlers.dynamic_command_creator import handle_custom_command
                    await handle_custom_command(message)
                    return
                
                # Komut oluşturma sistemi kontrolü
                from handlers.dynamic_command_creator import command_creation_states
                if user_id in command_creation_states:
                    from handlers.dynamic_command_creator import handle_command_creation_input
                    await handle_command_creation_input(message)
                    return
                
                # Zamanlanmış mesajlar sistemi kontrolü - GRUP İÇİN DE
                from utils.memory_manager import memory_manager
                input_state = memory_manager.get_input_state(user_id)
                if input_state and (input_state.startswith("create_bot_") or input_state.startswith("recreate_bot_") or input_state.startswith("add_link_")):
                    from handlers.scheduled_messages import handle_scheduled_input
                    await handle_scheduled_input(message)
                    return
                
                # Market ürün düzenleme sistemi kontrolü
                from handlers.admin_market_management import product_edit_data
                if user_id in product_edit_data:
                    from handlers.admin_market_management import handle_product_edit_input
                    await handle_product_edit_input(message)
                    return
                
                # Market ürün silme sistemi kontrolü
                from handlers.admin_market_management import product_delete_data
                if user_id in product_delete_data:
                    from handlers.admin_market_management import handle_product_delete_input
                    await handle_product_delete_input(message)
                    return
                
                # Chat sistemi kontrolü - Eğer yukarıdaki hiçbiri çalışmadıysa
                from utils.cooldown_manager import cooldown_manager
                
                # Cooldown kontrolü
                can_respond = await cooldown_manager.can_respond_to_user(message.from_user.id)
                if can_respond:
                    response = await handle_chat_message(message)
                    if response:
                        await send_chat_response(message, response)
                        # Mesajı kaydet
                        await cooldown_manager.record_user_message(message.from_user.id)
                else:
                    log_system(f"⏱️ Cooldown aktif - User: {message.from_user.id}")
                    
            except Exception as e:
                log_error(f"❌ Grup komut oluşturucu hatası: {e}")
        
        # Grup mesajları için tek handler - hem dinamik komutlar hem chat sistemi
        dp.message(F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"))(handle_group_command_creation)
        
        # Grup komut handler'ını kaydet (silent komutlar için)
        dp.message(F.chat.type.in_(["group", "supergroup"]), F.text.startswith("/"))(handle_group_command_silently)
        
        # Recruitment callback handler - MANUEL
        from handlers.recruitment_system import handle_recruitment_callback
        dp.callback_query(F.data == "register_user")(handle_recruitment_callback)
        dp.callback_query(F.data.startswith("recruitment_"))(handle_recruitment_callback)
        dp.callback_query(F.data == "show_commands")(handle_recruitment_callback)
        dp.callback_query(F.data == "close_recruitment")(handle_recruitment_callback)
        dp.callback_query(F.data == "recruitment_back")(handle_recruitment_callback)
        
        # Admin panel callback'leri - MANUEL KAYIT (EN SON - genel)
        from handlers.admin_panel import admin_panel_callback
        dp.callback_query(F.data.startswith("admin_") | F.data.startswith("category_") | F.data.startswith("price_") | F.data.startswith("event_") | F.data.startswith("admin_order_") | F.data.startswith("set_points_") | F.data.startswith("set_daily_") | F.data.startswith("set_weekly_") | F.data.startswith("balance_") | F.data.startswith("system_"))(admin_panel_callback)
        
        # Dinamik komut oluşturucu callback'leri - MANUEL KAYIT
        from handlers.dynamic_command_creator import (
            start_command_creation, cancel_command_creation, 
            handle_skip_button_text, handle_skip_button_url,
            list_custom_commands_handler, delete_custom_command_handler
        )
        dp.callback_query(F.data == "admin_command_creator")(start_command_creation)
        dp.callback_query(F.data == "cancel_command_creation")(cancel_command_creation)
        dp.callback_query(F.data == "skip_button_text")(handle_skip_button_text)
        dp.callback_query(F.data == "skip_button_url")(handle_skip_button_url)
        dp.callback_query(F.data == "list_custom_commands")(list_custom_commands_handler)
        dp.callback_query(F.data == "delete_custom_command")(delete_custom_command_handler)
        
        # 🔥 YENİ EKSİK SİSTEMLER - CALLBACK HANDLER'LAR
        # Zamanlanmış mesajlar sistemi callback'leri - EKSİK FONKSIYONLAR, KALDIRILDI
        # from handlers.scheduled_messages import (
        #     scheduled_bot_callback, start_scheduled_bot_creation, 
        #     cancel_scheduled_bot_creation, edit_scheduled_bot_callback,
        #     delete_scheduled_bot_callback, confirm_scheduled_bot_delete
        # )
        # dp.callback_query(F.data == "admin_scheduled_messages")(scheduled_bot_callback)
        # dp.callback_query(F.data == "create_scheduled_bot")(start_scheduled_bot_creation)
        # dp.callback_query(F.data == "cancel_scheduled_bot")(cancel_scheduled_bot_creation)
        # dp.callback_query(F.data.startswith("edit_scheduled_"))(edit_scheduled_bot_callback)
        # dp.callback_query(F.data.startswith("delete_scheduled_"))(delete_scheduled_bot_callback)
        # dp.callback_query(F.data.startswith("confirm_delete_scheduled_"))(confirm_scheduled_bot_delete)
        
        # Bakiye etkinlikleri sistemi callback'leri
        from handlers.balance_event import balance_event_callback_handler
        dp.callback_query(lambda c: c.data and c.data.startswith("admin_balance_event"))(balance_event_callback_handler)
        
        # Scheduled Messages callback'leri
        from handlers.scheduled_messages import scheduled_callback_handler
        dp.callback_query(lambda c: c.data and c.data.startswith("scheduled_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("toggle_bot_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("edit_bot_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("bot_toggle_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("edit_messages_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("edit_interval_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("edit_link_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("edit_image_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("edit_name_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("set_interval_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("remove_link_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("add_link_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("remove_image_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("add_image_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("create_bot_profile"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("edit_message_text_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("send_message_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("recreate_bot_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("delete_bot_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("create_bot_link_yes_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("create_bot_link_no_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("select_bot_group_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("recreate_bot_link_yes_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("recreate_bot_link_no_"))(scheduled_callback_handler)
        dp.callback_query(lambda c: c.data and c.data.startswith("select_recreate_group_"))(scheduled_callback_handler)

        
        # 🔥 MANUEL HANDLER KAYIT - ÇEKİLİŞ MESAJ HANDLER'ı (AKTİF)
        # Not: handle_all_chat_inputs içinde zaten kontrol ediliyor
        
        log_system("Tüm handler'lar kaydedildi!")
        # dp.include_router(balance_management_router)  # KALDIRILDI
        # dp.include_router(balance_event_router)  # KALDIRILDI
        # dp.include_router(event_participation_router)  # KALDIRILDI
        # dp.include_router(admin_panel_router)  # KALDIRILDI
        # dp.include_router(unknown_commands_router)  # KALDIRILDI
        
        # Background task'ları başlat
        asyncio.create_task(start_cleanup_task())
        asyncio.create_task(start_memory_cleanup())  # Memory cleanup
        asyncio.create_task(start_recruitment_background())  # Kayıt teşvik sistemi
        asyncio.create_task(start_scheduled_messages(bot))  # Zamanlanmış mesajlar
        log_system("Background cleanup task başlatıldı!")
        log_system("🎯 Kayıt teşvik sistemi başlatıldı!")
        
        # Memory cache güncelleme task'ı kaldırıldı
        
        # Bot bilgilerini al
        log_system("🔍 Bot bilgileri alınıyor...")
        bot_info = await bot.get_me()
        log_system(f"🤖 Bot: @{bot_info.username} - {bot_info.first_name}")
        log_system(f"👤 Admin ID: {config.ADMIN_USER_ID}")
        
        log_system("🚀 Bot başarıyla çalışmaya başladı!")
        log_system("⏹️ Durdurmak için Ctrl+C")
        
        # STARTUP BİLDİRİMİ: Database pool hazır olduktan sonra gönder
        log_system("📢 Startup bildirimi hazırlanıyor...")
        
        # Background'da çalıştır - database pool kontrolü ile
        async def delayed_startup_notification():
            from database import db_pool
            
            # Database pool'u bekle (maksimum 30 saniye)
            for attempt in range(30):
                if db_pool is not None:
                    log_system(f"Database pool hazır, startup bildirimi gönderiliyor (attempt {attempt + 1})")
                    break
                await asyncio.sleep(1)
            else:
                log_warning("Database pool 30 saniye sonra hala hazır değil, startup bildirimini atlıyoruz", "WARNING")
                return
            
            try:
                await send_startup_notification()
            except Exception as e:
                log_error(f"Startup bildirimi hatası: {e}")
        
        # Background'da çalıştır
        asyncio.create_task(delayed_startup_notification())
        
        # Bot'u başlat
        log_system("🚀 Bot polling başlatılıyor...")
        log_system("✅ Bot başarıyla çalışıyor! Komutlar hazır.")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        log_system("Bot kullanıcı tarafından durduruldu!")
        
        # SHUTDOWN BİLDİRİMİ: Tüm aktif kullanıcılara bakım modu mesajı gönder
        log_system("Shutdown bildirimi gönderiliyor...")
        try:
            # Önce bildirim gönder
            await send_maintenance_notification()
            log_system("Shutdown bildirimi başarıyla gönderildi!")
            
            # Bildirim gönderildikten sonra 2 saniye bekle
            await asyncio.sleep(2)
            
            # Sonra temiz kapanış
            await cleanup_resources()
            
        except Exception as e:
            log_error(f"Shutdown bildirimi hatası: {e}")
            await cleanup_resources()
            
    except Exception as e:
        log_error(f"Bot başlatma hatası: {e}")
    finally:
        await cleanup_resources()

async def handle_group_chat(message: Message):
    """Grup sohbetlerinde bot yanıtları"""
    try:
        # Sadece metin mesajları
        if not message.text:
            return
            
        # Bot mesajlarını ignore et
        if message.from_user.is_bot:
            return
            
        # Sohbet cevabı al
        response = await handle_chat_message(message)
        if response:
            await send_chat_response(message, response)
            
    except Exception as e:
        log_error(f"❌ Group chat handler hatası: {e}")

async def handle_group_command_silently(message: Message):
    """Grup chatindeki komutları yakala ve özelde çalıştır"""
    try:
        user_id = message.from_user.id
        command = message.text.split()[0]  # İlk kelimeyi al (komut)
        
        log_system(f"🔇 Grup komutu yakalandı - User: {user_id}, Command: {command}, Group: {message.chat.id}")
        
        # Mesajı sil
        try:
            await message.delete()
            log_system(f"✅ Grup komut mesajı silindi - Command: {command}")
        except Exception as e:
            log_error(f"❌ Grup komut mesajı silinemedi: {e}")
        
        # Komutu özelde çalıştır
        try:
            # Bot instance'ını al
            from config import get_config
            config = get_config()
            from aiogram import Bot
            temp_bot = Bot(token=config.BOT_TOKEN)
            
            # Import'ları burada yap
            from handlers.start_handler import start_command
            from handlers.register_handler import kirvekayit_command
            from handlers.profile_handler import menu_command
            from handlers.events_list import list_active_lotteries, send_lotteries_list_privately, send_group_lotteries_list
            from handlers.simple_events import create_lottery_command
            from handlers.admin_panel import admin_panel_command
            # from handlers.admin_commands_list import admin_commands_list
            from handlers.admin_panel import clean_messages_command, list_groups_command, help_command
            from handlers.admin_order_management import show_orders_list_modern
            from handlers.events_list import list_active_lotteries as list_active_events
            from handlers.event_management import end_lottery_command
            
            # Komut türüne göre işle
            if command == "/start":
                await start_command(message)
            elif command == "/kirvekayit":
                await kirvekayit_command(message)
            elif command == "/menu":
                await menu_command(message)
            elif command == "/cekilisler":
                # Admin kontrolü
                config = get_config()
                is_admin = user_id == config.ADMIN_USER_ID
                
                if is_admin:
                    # Admin için özel çekiliş listesi (bitirme butonu ile)
                    await send_lotteries_list_privately(user_id, is_admin=True)
                else:
                    # Normal kullanıcı için grup çekiliş listesi (sadece katılım)
                    await send_group_lotteries_list(user_id)
            elif command == "/cekilisyap":
                await create_lottery_command(message)
            elif command == "/adminpanel":
                await admin_panel_command(message)
            elif command == "/adminkomutlar":
                await admin_panel_command(message)  # admin_commands_list yerine admin_panel_command
            elif command == "/temizle":
                await clean_messages_command(message)
            elif command == "/gruplar":
                await list_groups_command(message)
            elif command == "/yardim":
                await yardim_command(message)
            elif command == "/siparisliste":
                await show_orders_list_modern(message)
            elif command == "/etkinlikler":
                await list_active_events(message)
            elif command == "/cekilisbitir":
                await end_lottery_command(message)
            elif command == "/bakiyeetkinlik":
                # from handlers.balance_event import create_balance_event_command
                # await create_balance_event_command(message)
                pass # Eski komutu kaldır
            elif command == "/bakiyeetkinlikler":
                # from handlers.balance_event import list_balance_events_command
                pass # Eski komutu kaldır
            elif command == "/adminstats":
                from handlers.statistics_system import admin_stats_command
                await admin_stats_command(message)
            elif command == "/sistemistatistik":
                from handlers.statistics_system import system_stats_command
                await system_stats_command(message)
            else:
                # Bilinmeyen komut için uyarı
                unknown_command_message = f"""
⚠️ **Bilinmeyen Komut**

**Komut:** `{command}`
**Grup:** {message.chat.title}

❌ **Bu komut henüz tanımlanmamış veya kullanılamıyor.**

💡 **Kullanılabilir Komutlar:**
• `/start` - Ana menü
• `/menu` - Profil menüsü
• `/kirvekayit` - Kayıt sistemi
• `/cekilisler` - Aktif çekilişler
• `/cekilisyap` - Çekiliş oluştur (Admin)
• `/adminpanel` - Admin paneli (Admin)
• `/adminstats` - Admin istatistikleri (Admin)
• `/sistemistatistik` - Sistem istatistikleri (Admin)

🔔 **Not:** Komutlar grup chatinde silinir ve özel mesajda yanıtlanır.
                """
                
                await temp_bot.send_message(
                    user_id,
                    unknown_command_message,
                    parse_mode="Markdown"
                )
            
            await temp_bot.session.close()
            log_system(f"✅ Grup komutu özelde çalıştırıldı - Command: {command}")
            
        except Exception as e:
            log_error(f"❌ Grup komut işleme hatası: {e}")
            # Hata durumunda kullanıcıya bildir
            try:
                error_message = f"""
❌ **Komut İşleme Hatası**

**Komut:** `{command}`
**Hata:** Sistem hatası oluştu

🔧 **Çözüm:** Birkaç dakika bekleyip tekrar deneyin.
                """
                
                from aiogram import Bot
                from config import get_config
                config = get_config()
                temp_bot = Bot(token=config.BOT_TOKEN)
                await temp_bot.send_message(user_id, error_message, parse_mode="Markdown")
                await temp_bot.session.close()
                
            except Exception as send_error:
                log_error(f"❌ Hata mesajı gönderilemedi: {send_error}")
        
    except Exception as e:
        log_error(f"❌ Grup komut handler hatası: {e}")


if __name__ == "__main__":
    """
    Bot'u çalıştır
    
    Kullanım:
    python main.py
    """
    asyncio.run(main()) 