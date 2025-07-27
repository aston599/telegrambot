"""
🤖 Modern Telegram Bot - aiogram + Database
Modüler yapıda, Python 3.13 uyumlu

📁 Proje Yapısı:
- config.py: Bot konfigürasyonları
- database.py: Database işlemleri  
- handlers/: Komut handler'ları
- utils/: Yardımcı fonksiyonlar
- models/: Database modelleri (gelecek)
"""

import asyncio
import logging
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
    menu_command, profile_callback_handler, yardim_command
)
from handlers.recruitment_system import (
    start_recruitment_background, handle_recruitment_response
)
from handlers.chat_system import (
    handle_chat_message, send_chat_response, bot_write_command
)
from handlers.admin_panel import router as admin_panel_router, admin_commands_list_command
from handlers.simple_events import router as simple_events_router, set_bot_instance as set_events_bot_instance
from handlers.unknown_commands import router as unknown_commands_router, set_bot_instance as set_unknown_bot_instance
from handlers.event_participation import router as event_participation_router, set_bot_instance as set_participation_bot_instance
from handlers.events_list import set_bot_instance as set_events_list_bot_instance
from handlers.system_notifications import send_maintenance_notification, send_startup_notification
from handlers.scheduled_messages import scheduled_messages_command, scheduled_callback_handler
from utils import setup_logger
from utils.logger import setup_logger, log_important, log_system_error, log_performance
from utils.rate_limiter import rate_limiter, rate_limit
from utils.memory_manager import memory_manager, start_memory_cleanup, cleanup_all_resources

# Logger'ı kur
logger = setup_logger()

# Global bot instance kontrolü - Enhanced
_bot_instance = None
_bot_started = False
_bot_lock_file = "bot_running.lock"

import os
import psutil

def check_bot_running():
    """Bot'un zaten çalışıp çalışmadığını kontrol et"""
    try:
        # Lock file kontrolü
        if os.path.exists(_bot_lock_file):
            # Lock file'dan PID oku
            try:
                with open(_bot_lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Process kontrolü
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    if "python" in process.name().lower() and "main.py" in " ".join(process.cmdline()).lower():
                        log_important(f"⚠️ Bot zaten çalışıyor! PID: {pid}")
                        return True
            except:
                pass
        
        # Lock file'ı temizle (eski)
        if os.path.exists(_bot_lock_file):
            os.remove(_bot_lock_file)
            
        return False
    except Exception as e:
        log_important(f"⚠️ Bot kontrol hatası: {e}")
        return False

def create_bot_lock():
    """Bot lock file oluştur"""
    try:
        with open(_bot_lock_file, 'w') as f:
            f.write(str(os.getpid()))
        log_important(f"✅ Bot lock file oluşturuldu - PID: {os.getpid()}")
    except Exception as e:
        log_important(f"❌ Bot lock file oluşturulamadı: {e}")

def remove_bot_lock():
    """Bot lock file'ı kaldır"""
    try:
        if os.path.exists(_bot_lock_file):
            os.remove(_bot_lock_file)
            log_important("✅ Bot lock file kaldırıldı")
    except Exception as e:
        log_important(f"❌ Bot lock file kaldırılamadı: {e}")

async def cleanup_resources():
    """Temizlik işlemleri - Enhanced"""
    try:
        log_important("🧹 Temizlik işlemleri başlatılıyor...")
        
        # Database bağlantısını kapat
        await close_database()
        
        # Bot session'ını kapat
        if _bot_instance:
            await _bot_instance.session.close()
            log_important("🤖 Bot session kapatıldı.")
        
        # Lock file'ı kaldır
        remove_bot_lock()
        
        log_important("✅ Temizlik işlemleri tamamlandı!")
        
    except Exception as e:
        log_system_error(f"Cleanup hatası: {e}")
        # Hata durumunda da lock file'ı kaldırmaya çalış
        try:
            remove_bot_lock()
        except:
            pass

async def main():
    """Ana fonksiyon - Enhanced with instance control"""
    global _bot_instance, _bot_started
    
    import time
    start_time = time.time()
    
    # Bot instance kontrolü - Enhanced
    if check_bot_running():
        log_important("🚫 Bot zaten çalışıyor! Tek instance kontrolü aktif.")
        return
    
    if _bot_started:
        log_important("⚠️ Bot zaten başlatılmış! Global kontrol aktif.")
        return
    
    _bot_started = True
    create_bot_lock()  # Lock file oluştur
    
    try:
        log_important("=" * 60)
        log_important("MODERN TELEGRAM BOT BASLATILIYOR (aiogram)")
        log_important("=" * 60)
        
        # Konfigürasyonu doğrula
        config = get_config()
        validate_config()
        log_important("✅ Konfigürasyon doğrulandı!")
        log_important(f"🔧 Bot Token: {config.BOT_TOKEN[:20]}...")
        log_important(f"👤 Admin ID: {config.ADMIN_USER_ID}")
        log_important(f"🗄️ Database URL: {config.DATABASE_URL[:30]}...")
        
        # Database'i başlat
        log_important("🗄️ Database bağlantısı kuruluyor...")
        db_success = await init_database()
        if not db_success:
            log_important("⚠️ Database olmadan devam ediliyor!", "WARNING")
        else:
            log_important("✅ Database bağlantısı başarılı!")
            
        # Scheduled messages ayarlarını yükle
        log_important("📅 Scheduled messages ayarları yükleniyor...")
        try:
            from handlers.scheduled_messages import get_scheduled_settings, start_scheduled_messages, set_bot_instance as set_scheduled_bot_instance
            await get_scheduled_settings()
            set_scheduled_bot_instance(bot)  # Bot instance'ını set et
            await start_scheduled_messages(bot)  # Zamanlayıcıyı başlat
            log_important("✅ Scheduled messages sistemi başlatıldı!")
        except Exception as e:
            log_important(f"⚠️ Scheduled messages ayarları yüklenemedi: {e}", "WARNING")
        
        # Bot ve Dispatcher oluştur
        log_important("🤖 Bot instance oluşturuluyor...")
        bot = Bot(token=config.BOT_TOKEN)
        _bot_instance = bot  # Global instance'ı set et
        dp = Dispatcher()
        log_important("✅ Bot ve Dispatcher oluşturuldu!")
        
        # Bot instance'larını set et
        set_events_bot_instance(bot)
        set_events_list_bot_instance(bot)
        
        # Admin commands bot instance'ını set et
        from handlers.admin_commands import set_bot_instance as set_admin_bot_instance
        set_admin_bot_instance(bot)
        
        # TEK ADMİN PANELİ - Admin panel bot instance'ını set et
        from handlers.admin_panel import set_bot_instance as set_admin_panel_bot_instance
        set_admin_panel_bot_instance(bot)
        
        
        
        # Unknown commands bot instance'ını set et
        set_unknown_bot_instance(bot)
        
        # Event participation - MANUEL HANDLER kullanıyor
        from handlers.event_participation import set_bot_instance as set_participation_bot_instance
        set_participation_bot_instance(bot)
        
        # Event management - MANUEL HANDLER kullanıyor  
        from handlers.event_management import set_bot_instance as set_management_bot_instance
        set_management_bot_instance(bot)
        
        # Market yönetim sistemi - BOT INSTANCE SET ET
        from handlers.admin_market_management import set_bot_instance as set_market_bot_instance
        set_market_bot_instance(bot)
        
        # Broadcast system - BOT INSTANCE SET ET
        from handlers.broadcast_system import set_bot_instance as set_broadcast_bot_instance
        set_broadcast_bot_instance(bot)
        
        # Handler'ları kaydet
        log_important("🎯 Handler'lar kaydediliyor...")
        
        # 1. CALLBACK HANDLER'LARI (inline button'lar) - ÖNCE callback'leri kaydet
        dp.callback_query(F.data == "register_user")(register_callback_handler)
        dp.callback_query(F.data == "get_info")(register_callback_handler)
        
        # Etkinlik listesi callback'i
        from handlers.events_list import refresh_lotteries_list_callback
        dp.callback_query(F.data == "refresh_lotteries_list")(refresh_lotteries_list_callback)
        
        log_important("Callback handler'lar kaydedildi")
        
        # Profil callback'leri - EN BAŞTA KAYIT ET!
        from handlers.profile_handler import profile_callback_handler
        
        # Profil callback'leri - Basit filter
        dp.callback_query(F.data.startswith("profile_"))(profile_callback_handler)
        dp.callback_query(F.data.startswith("buy_product_"))(profile_callback_handler)
        dp.callback_query(F.data.startswith("confirm_buy_"))(profile_callback_handler)
        dp.callback_query(F.data.startswith("view_product_"))(profile_callback_handler)
        dp.callback_query(F.data == "product_sold_out")(profile_callback_handler)
        dp.callback_query(F.data == "my_orders")(profile_callback_handler)
        dp.callback_query(F.data == "profile_orders")(profile_callback_handler)
        dp.callback_query(F.data == "insufficient_balance")(profile_callback_handler)
        dp.callback_query(F.data == "out_of_stock")(profile_callback_handler)
        dp.callback_query(F.data == "profile_back")(profile_callback_handler)
        dp.callback_query(F.data == "profile_refresh")(profile_callback_handler)
        
        # Admin sipariş callback'leri - MANUEL KAYIT (ÖNCE - daha spesifik)
        from handlers.admin_market_management import orders_list_command, approve_order_command, reject_order_command
        from handlers.admin_order_management import handle_admin_approve_order, handle_admin_reject_order
        
        # Wrapper fonksiyonlar
        async def admin_approve_callback_wrapper(callback):
            order_number = callback.data.replace("admin_approve_", "")
            return await handle_admin_approve_order(callback, order_number)
        
        async def admin_reject_callback_wrapper(callback):
            order_number = callback.data.replace("admin_reject_", "")
            return await handle_admin_reject_order(callback, order_number)
        
        dp.callback_query(F.data.startswith("admin_approve_"))(admin_approve_callback_wrapper)
        dp.callback_query(F.data.startswith("admin_reject_"))(admin_reject_callback_wrapper)
        
        # Broadcast system callback'leri - MANUEL KAYIT (EN ÖNCE)
        from handlers.broadcast_system import start_broadcast, cancel_broadcast
        dp.callback_query(F.data == "admin_broadcast")(start_broadcast)
        dp.callback_query(F.data == "admin_broadcast_cancel")(cancel_broadcast)
        
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
        
        # 🔥 CRİTİK: MANUEL HANDLER KAYIT - GRUP SESSİZLİĞİ İÇİN (ROUTER'LAR YOK!)
        # TEK ADMİN PANELİ SİSTEMİ - Tüm admin komutları admin_panel.py'de
        from handlers.admin_panel import admin_panel_command, clean_messages_command, list_groups_command, help_command, approve_order_command
        from handlers.admin_order_management import show_orders_list_modern
        from handlers.events_list import list_active_lotteries as list_active_events, refresh_lotteries_list_callback
        from handlers.event_management import end_lottery_command as end_event_command
        
        # MANUEL HANDLER KAYITLARI
        dp.message(Command("adminpanel"))(admin_panel_command)  # Ana admin panel
        dp.message(Command("adminkomutlar"))(admin_panel_command)  # Admin komutları (alias)
        dp.message(Command("adminkomut"))(admin_commands_list_command)  # Admin komutları (doğrudan liste)
        dp.message(Command("temizle"))(clean_messages_command)   # Mesaj silme
        dp.message(Command("gruplar"))(list_groups_command)      # Grup listesi
        dp.message(Command("yardim"))(help_command)              # Yardım menüsü
        dp.message(Command("siparisliste"))(show_orders_list_modern) # Sipariş listesi
        dp.message(Command("siparisonayla"))(approve_order_command) # Sipariş onaylama
        dp.message(Command("siparisreddet"))(reject_order_command) # Sipariş reddetme
        

        dp.message(Command("etkinlikler"))(list_active_events)
        dp.message(Command("etkinlikbitir"))(end_event_command)
        
        # Admin komutları - MANUEL (admin_commands.py'den)
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
        
        log_important("Manuel handler'lar kayıtlandı - Router'lar YOK!")
        
        # Etkinlik katılım handler'ı için gerekli
        dp.include_router(event_participation_router)
        
        # Event management router'ını da ekle - end_event callback'i için
        from handlers.event_management import router as event_management_router
        dp.include_router(event_management_router)
        
        # Statistics system callback'leri
        from handlers.statistics_system import handle_stats_callback
        dp.callback_query(F.data.startswith("stats_"))(handle_stats_callback)
        
        # Zamanlanmış mesajlar sistemi
        dp.message(Command("zamanlanmismesaj"))(scheduled_messages_command)
        dp.callback_query(F.data.startswith("scheduled_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("toggle_bot_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("edit_bot_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("bot_toggle_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("edit_messages_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("edit_interval_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("edit_link_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("edit_image_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("edit_name_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("set_interval_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("remove_link_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("add_link_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("remove_image_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("add_image_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("create_bot_profile"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("edit_message_text_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("send_message_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("recreate_bot_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("delete_bot_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("create_bot_link_yes_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("create_bot_link_no_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("select_bot_group_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("recreate_bot_link_yes_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("recreate_bot_link_no_"))(scheduled_callback_handler)
        dp.callback_query(F.data.startswith("select_recreate_group_"))(scheduled_callback_handler)
        dp.callback_query(F.data == "admin_scheduled_messages")(scheduled_callback_handler)
        
        # Dynamic command creator router'ını dahil et
        from handlers.dynamic_command_creator import router as dynamic_command_router
        dp.include_router(dynamic_command_router)
        
        # Admin permission manager router'ını dahil et
        from handlers.admin_permission_manager import router as admin_permission_router
        dp.include_router(admin_permission_router)

        # Admin panel router'ını dahil et (FSM handler'ları için)
        dp.include_router(admin_panel_router)
        
        # Simple events router'ını dahil et
        dp.include_router(simple_events_router)
        
        # Unknown commands router'ını dahil et
        dp.include_router(unknown_commands_router)
        
        # 3. GRUP MESAJ MONITOR (Point kazanımı için)
        dp.message(F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"))(monitor_group_message)
        
        # 🔧 DYNAMIC COMMAND HANDLER - GRUP MESAJLARI İÇİN
        from handlers.dynamic_command_creator import handle_custom_command as handle_custom_command_group
        dp.message(F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"))(handle_custom_command_group)
        
        # 3.5. SOHBET SİSTEMLER - Grup sohbetlerinde doğal konuşma
        dp.message(F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"))(handle_group_chat)
        
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
        async def handle_all_chat_inputs(message: Message) -> None:
            """Tüm chat input'larını işle"""
            try:
                user_id = message.from_user.id
                config = get_config()
                
                # Bakım modu kontrolü
                if config.MAINTENANCE_MODE and user_id != config.ADMIN_USER_ID:
                    await message.answer("🔧 **Bot şu anda bakım modunda!**\n\nLütfen daha sonra tekrar deneyin.")
                    return
                
                from utils.memory_manager import memory_manager
                input_state = memory_manager.get_input_state(user_id)
                
                if not input_state:
                    return
                    
                # 1. Market input kontrolü
                if input_state.startswith("market_"):
                    from handlers.admin_market_management import handle_market_input
                    await handle_market_input(message)
                    return
                    
                # 2. Broadcast input kontrolü
                if input_state.startswith("broadcast_"):
                    from handlers.broadcast_system import handle_broadcast_input
                    await handle_broadcast_input(message)
                    return
                    
                # 3. Event input kontrolü
                if input_state.startswith("event_"):
                    from handlers.simple_events import handle_event_input
                    await handle_event_input(message)
                    return
                    
                # 4. Bot oluşturma input kontrolü
                if input_state.startswith("create_bot_"):
                    from handlers.scheduled_messages import handle_scheduled_input
                    await handle_scheduled_input(message)
                    return
                # 5.2. Bot yeniden kurulum input kontrolü
                elif input_state.startswith("recreate_bot_"):
                    from handlers.scheduled_messages import handle_scheduled_input
                    await handle_scheduled_input(message)
                    return
                    
            except Exception as e:
                logger.error(f"❌ Chat input handler hatası: {e}")

        # Özel mesaj handler'ını kaydet
        dp.message(F.chat.type == "private", ~F.text.startswith("/"))(handle_all_chat_inputs)
        
        # Grup mesajları için komut oluşturucu handler'ı
        async def handle_group_command_creation(message: Message):
            """Grup mesajlarında komut oluşturucu"""
            try:
                user_id = message.from_user.id
                
                # Komut mesajlarını atla
                if message.text.startswith("/"):
                    return
                
                # Komut oluşturma sistemi kontrolü
                from handlers.dynamic_command_creator import command_creation_states
                if user_id in command_creation_states:
                    from handlers.dynamic_command_creator import handle_command_creation_input
                    await handle_command_creation_input(message)
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
                    
            except Exception as e:
                logger.error(f"❌ Grup komut oluşturucu hatası: {e}")
        
        # Grup komut oluşturucu handler'ını kaydet
        dp.message(F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"))(handle_group_command_creation)
        
        # Recruitment callback handler - MANUEL
        from handlers.recruitment_system import handle_recruitment_callback
        dp.callback_query(F.data == "register_user")(handle_recruitment_callback)
        dp.callback_query(F.data.startswith("recruitment_"))(handle_recruitment_callback)
        dp.callback_query(F.data == "show_commands")(handle_recruitment_callback)
        dp.callback_query(F.data == "close_recruitment")(handle_recruitment_callback)
        dp.callback_query(F.data == "recruitment_back")(handle_recruitment_callback)
        
        # Admin panel callback'leri - MANUEL KAYIT (EN SON - genel)
        from handlers.admin_panel import admin_panel_callback
        dp.callback_query(F.data.startswith("admin_"))(admin_panel_callback)
        dp.callback_query(F.data.startswith("set_"))(admin_panel_callback)
        
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
        
        # 🔥 MANUEL HANDLER KAYIT - ÇEKİLİŞ MESAJ HANDLER'ı (AKTİF)
        # Not: handle_all_chat_inputs içinde zaten kontrol ediliyor
        
        log_important("Tüm handler'lar kaydedildi!")

        
        # Background task'ları başlat
        asyncio.create_task(start_cleanup_task())
        asyncio.create_task(start_memory_cleanup())  # Memory cleanup
        asyncio.create_task(start_recruitment_background())  # Kayıt teşvik sistemi
        log_important("Background cleanup task başlatıldı!")
        log_important("🎯 Kayıt teşvik sistemi başlatıldı!")
        
        # Memory cache güncelleme task'ı kaldırıldı
        
        # Bot bilgilerini al
        log_important("🔍 Bot bilgileri alınıyor...")
        bot_info = await bot.get_me()
        log_important(f"🤖 Bot: @{bot_info.username} - {bot_info.first_name}")
        log_important(f"👤 Admin ID: {config.ADMIN_USER_ID}")
        
        log_important("🚀 Bot başarıyla çalışmaya başladı!")
        log_important("⏹️ Durdurmak için Ctrl+C")
        
        # STARTUP BİLDİRİMİ: Database pool hazır olduktan sonra gönder
        log_important("📢 Startup bildirimi hazırlanıyor...")
        
        # Background'da çalıştır - database pool kontrolü ile
        async def delayed_startup_notification():
            from database import db_pool
            
            # Database pool'u bekle (maksimum 30 saniye)
            for attempt in range(30):
                if db_pool is not None:
                    log_important(f"Database pool hazır, startup bildirimi gönderiliyor (attempt {attempt + 1})")
                    break
                await asyncio.sleep(1)
            else:
                log_important("Database pool 30 saniye sonra hala hazır değil, startup bildirimini atlıyoruz", "WARNING")
                return
            
            try:
                await send_startup_notification()
            except Exception as e:
                log_system_error(f"Startup bildirimi hatası: {e}")
        
        # Background'da çalıştır
        asyncio.create_task(delayed_startup_notification())
        
        # Bot'u başlat
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        log_important("Bot kullanıcı tarafından durduruldu!")
        
        # SHUTDOWN BİLDİRİMİ: Tüm aktif kullanıcılara bakım modu mesajı gönder
        log_important("Shutdown bildirimi gönderiliyor...")
        try:
            # Önce bildirim gönder
            await send_maintenance_notification()
            log_important("Shutdown bildirimi başarıyla gönderildi!")
            
            # Bildirim gönderildikten sonra 2 saniye bekle
            await asyncio.sleep(2)
            
            # Sonra temiz kapanış
            await cleanup_resources()
            
        except Exception as e:
            log_system_error(f"Shutdown bildirimi hatası: {e}")
            await cleanup_resources()
            
    except Exception as e:
        log_system_error(f"Bot başlatma hatası: {e}")
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
        logger.error(f"❌ Group chat handler hatası: {e}")

async def handle_group_command_silently(message: Message):
    """Grup chatindeki komutları yakala ve özelde çalıştır"""
    try:
        user_id = message.from_user.id
        command = message.text.split()[0]  # İlk kelimeyi al (komut)
        
        logger.info(f"🔇 Grup komutu yakalandı - User: {user_id}, Command: {command}, Group: {message.chat.id}")
        
        # Mesajı sil
        try:
            await message.delete()
            logger.debug(f"✅ Grup komut mesajı silindi - Command: {command}")
        except Exception as e:
            logger.error(f"❌ Grup komut mesajı silinemedi: {e}")
        
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
                await admin_panel_command(message)  # admin_panel_command kullanılıyor
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

🔔 **Not:** Komutlar grup chatinde silinir ve özel mesajda yanıtlanır.
                """
                
                await temp_bot.send_message(
                    user_id,
                    unknown_command_message,
                    parse_mode="Markdown"
                )
            
            await temp_bot.session.close()
            logger.info(f"✅ Grup komutu özelde çalıştırıldı - Command: {command}")
            
        except Exception as e:
            logger.error(f"❌ Grup komut işleme hatası: {e}")
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
                logger.error(f"❌ Hata mesajı gönderilemedi: {send_error}")
        
    except Exception as e:
        logger.error(f"❌ Grup komut handler hatası: {e}")


if __name__ == "__main__":
    """
    Bot'u çalıştır
    
    Kullanım:
    python main.py
    """
    asyncio.run(main()) 