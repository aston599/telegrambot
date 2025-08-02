"""
🤖 Modern Telegram Bot - aiogram + Database
Modüler yapıda, Python 3.13 uyumlu
"""

import asyncio
import logging
import os
import psutil
import time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram import types

# Local imports
from config import get_config, validate_config
from database import init_database, close_database
from handlers import (
    start_command, kirvekayit_command, private_message_handler, 
    register_callback_handler, kayitsil_command, kirvegrup_command, 
    group_info_command, botlog_command, monitor_group_message, start_cleanup_task,
    menu_command, profile_callback_handler, yardim_command, komutlar_command,
    siparislerim_command, siralama_command, profil_command
)
from handlers.recruitment_system import (
    start_recruitment_background, handle_recruitment_response
)
from handlers.chat_system import (
    handle_chat_message, send_chat_response, bot_write_command, chat_callback_handler
)
from handlers.chat_message_handler import handle_chat_message as handle_chat_message_new, set_bot_instance as set_chat_message_bot_instance
from handlers.admin_panel import router as admin_panel_router
from handlers.simple_events import router as simple_events_router, set_bot_instance as set_events_bot_instance
from handlers.unknown_commands import router as unknown_commands_router, set_bot_instance as set_unknown_bot_instance
from handlers.event_participation import router as event_participation_router, set_bot_instance as set_participation_bot_instance
from handlers.events_list import router as events_list_router, set_bot_instance as set_events_list_bot_instance
from handlers.system_notifications import send_maintenance_notification, send_startup_notification
from handlers.scheduled_messages import set_bot_instance as set_scheduled_bot, start_scheduled_messages
from handlers.balance_event import router as balance_event_router
from handlers.detailed_logging_system import (
    log_system_startup, log_system_shutdown, log_error, 
    log_system_health_check, log_missing_data, log_deprecated_feature,
    log_conflict_resolution, log_invalid_input, log_overflow_protection,
    log_deadlock_detection, log_data_corruption, set_bot_instance as set_logging_bot_instance,
    router as detailed_logging_router
)

from utils import setup_logger
from utils.logger import log_system, log_bot, log_error, log_info, log_warning
from utils.universal_logger import get_universal_logger, log_everything, log_command_attempt
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
                    cmdline = " ".join(process.cmdline()).lower()
                    if "python" in process.name().lower() and "main.py" in cmdline:
                        # Process'in gerçekten bot olup olmadığını daha detaylı kontrol et
                        try:
                            # Process'in çalışma süresini kontrol et (çok kısa süre çalışıyorsa eski process olabilir)
                            if process.create_time() < time.time() - 60:  # 1 dakikadan eski process'ler
                                log_system(f"⚠️ Eski bot process bulundu, PID: {pid}")
                                os.remove(_bot_lock_file)
                                return False
                            else:
                                log_system(f"⚠️ Bot zaten çalışıyor! PID: {pid}")
                                return True
                        except:
                            # Process bilgisi alınamıyorsa lock dosyasını sil
                            os.remove(_bot_lock_file)
                            return False
            except Exception as e:
                log_system(f"⚠️ Lock dosyası okuma hatası: {e}")
                # Hata durumunda lock dosyasını sil
                if os.path.exists(_bot_lock_file):
                    os.remove(_bot_lock_file)
        
        return False
    except Exception as e:
        log_system(f"⚠️ Bot kontrol hatası: {e}")
        # Hata durumunda lock dosyasını sil
        try:
            if os.path.exists(_bot_lock_file):
                os.remove(_bot_lock_file)
        except:
            pass
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
        print("🔍 Bot başlatma süreci başlatılıyor...")
        
        # Bot lock kontrolü
        print("🔒 Bot lock kontrolü yapılıyor...")
        if check_bot_running():
            print("❌ Bot zaten çalışıyor!")
            log_system("Bot zaten çalışıyor!")
            return
        
        print("✅ Bot lock kontrolü geçildi")
        
        # Lock file oluştur
        print("📝 Lock file oluşturuluyor...")
        create_bot_lock()
        print("✅ Lock file oluşturuldu")
        
        print("🚀 Bot başlatılıyor...")
        log_system("Bot başlatılıyor...")
        
        # Konfigürasyon kontrolü
        print("⚙️ Konfigürasyon kontrol ediliyor...")
        config = get_config()
        print("✅ Konfigürasyon yüklendi")
        log_system("Konfigürasyon doğrulandı")
        
        # Database bağlantısı
        print("🗄️ Database bağlantısı kuruluyor...")
        log_system("Database bağlantısı kuruluyor...")
        db_success = await init_database()
        if not db_success:
            print("⚠️ Database bağlantısı başarısız!")
            log_warning("⚠️ Database olmadan devam ediliyor!")
        else:
            print("✅ Database bağlantısı başarılı!")
            log_system("✅ Database bağlantısı başarılı!")
        
        # Bot instance oluştur
        print("🤖 Bot instance oluşturuluyor...")
        log_system("Bot instance oluşturuluyor...")
        bot = Bot(token=config.BOT_TOKEN)
        print("✅ Bot instance oluşturuldu")
        _bot_instance = bot  # Global instance'ı set et
        
        # Bot instance'ını handler'lara aktar
        print("🔗 Bot instance handler'lara aktarılıyor...")
        log_system("Bot instance handler'lara aktarılıyor...")
        set_events_bot_instance(bot)
        set_unknown_bot_instance(bot)
        set_participation_bot_instance(bot)
        set_events_list_bot_instance(bot)
        set_scheduled_bot(bot)
        set_logging_bot_instance(bot)  # Log sistemi için bot instance
        
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
        
        # Chat sistemi callback'leri
        dp.callback_query(F.data == "register_user")(chat_callback_handler)
        dp.callback_query(F.data == "show_commands")(chat_callback_handler)
        dp.callback_query(F.data == "close_message")(chat_callback_handler)
        
        # Etkinlik listesi callback'i
        from handlers.events_list import refresh_lotteries_list_callback
        dp.callback_query(F.data == "refresh_lotteries_list")(refresh_lotteries_list_callback)
        
        log_system("Callback handler'lar kaydedildi")
        
        # Profil callback'leri - EN BAŞTA KAYIT ET!
        from handlers.profile_handler import profile_callback_handler, set_bot_instance as set_profile_bot_instance
        set_profile_bot_instance(bot)
        
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
        
        # Ranking callback'leri - Ayrı kayıt
        dp.callback_query(F.data == "ranking_top_kp")(profile_callback_handler)
        dp.callback_query(F.data == "ranking_top_messages")(profile_callback_handler)
        
        # Admin sipariş yönetimi router'ı - YENİ!
        from handlers.admin_order_management import router as admin_order_router
        dp.include_router(admin_order_router)
        
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
        
        # Çekiliş callback'leri - Router'da tanımlı olduğu için kaldırıldı
        
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
        
        # 💎 MESAJ MONITOR - Point sistemi ve mesaj kayıt (ÖNCE)
        # Sadece point sistemi için, dinamik komutları engellemeyecek
        dp.message(F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"), ~F.text.startswith("!"))(monitor_group_message)
        
        # 💬 CHAT MESAJ HANDLER - Kayıtlı kullanıcıları menu'ye yönlendir (SONRA)
        # Sadece chat sistemi için, dinamik komutları engellemeyecek
        dp.message(F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"), ~F.text.startswith("!"))(handle_chat_message_new)
        dp.message(Command("kirvekayit"))(kirvekayit_command)
        dp.message(Command("kayitsil"))(kayitsil_command)
        # Grup komutları handle_group_command_silently'de işleniyor
        dp.message(Command("kirvegrup"))(kirvegrup_command)
        dp.message(Command("botlog"))(botlog_command)
        dp.message(Command("grupbilgi"))(group_info_command)
        dp.message(Command("menu"))(menu_command)
        dp.message(Command("menü"))(menu_command)  # Türkçe karakter desteği
        dp.message(Command("komutlar"))(komutlar_command)
        dp.message(Command("siparislerim"))(siparislerim_command)
        dp.message(Command("siralama"))(siralama_command)
        dp.message(Command("profil"))(profil_command)
        
        # Admin komutları artık router'larda
        
        # Etkinlik komutları kaldırıldı
        
        # Admin komutları - Router'da tanımlı olduğu için kaldırıldı
        
        # Market yönetim sistemi
        from handlers.admin_market_management import market_management_command, handle_product_creation_input
        
        # Market komutuna log ekle
        async def market_command_with_log(message: types.Message):
            # Detaylı log
            from handlers.detailed_logging_system import log_command_execution
            await log_command_execution(
                user_id=message.from_user.id,
                username=message.from_user.username or message.from_user.first_name,
                command="market",
                chat_id=message.chat.id,
                chat_type=message.chat.type
            )
            await market_management_command(message)
        
        dp.message(Command("market"))(market_command_with_log)
        
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
        from handlers.admin_panel import admin_panel_command, clean_messages_command, list_groups_command, help_command, approve_order_command, test_market_system_command, test_sql_queries_command, test_user_orders_command, update_bot_command, delete_group_command
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
        dp.message(Command("grupsil"))(delete_group_command)     # Grup silme
        dp.message(Command("yardim"))(help_command)              # Yardım menüsü
        dp.message(Command("siparisliste"))(show_orders_list_modern) # Sipariş listesi
        dp.message(Command("siparisonayla"))(approve_order_command) # Sipariş onaylama
        
        # Test komutları
        dp.message(Command("testmarket"))(test_market_system_command) # Market test
        dp.message(Command("testsql"))(test_sql_queries_command) # SQL test
        dp.message(Command("testsiparis"))(test_user_orders_command) # Sipariş test
        dp.message(Command("etkinlikler"))(list_active_events)
        dp.message(Command("etkinlikbitir"))(end_event_command)
        
        # Admin komutları - Manuel handler kayıtları
        from handlers.admin_commands import delete_command_command
        dp.message(Command("komutsil"))(delete_command_command)
        
        # Etkinlik oluşturma komutu - MANUEL
        from handlers.simple_events import create_lottery_command as create_event_command
        dp.message(Command("etkinlik"))(create_event_command)
        # Lottery handler'ı geçici olarak devre dışı
        # dp.message()(handle_lottery_input)  # Etkinlik input handler'ı
        
        # Etkinlik yönetimi komutları - Router'da tanımlı olduğu için kaldırıldı
        
        # Çekiliş komutları - Router'da tanımlı olduğu için kaldırıldı
        
        # 🔐 GİZLİ KOMUTLAR - Sadece bot sahibi için
        from handlers.secret_commands import router as secret_commands_router
        dp.include_router(secret_commands_router)
        
        # 💬 CHAT MESAJ HANDLER - Kayıtlı kullanıcıları menu'ye yönlendir
        set_chat_message_bot_instance(bot)
        
        # 🔥 YENİ EKSİK SİSTEMLER - MANUEL KOMUTLAR
        # Zamanlanmış mesajlar sistemi router'ını dahil et
        from handlers.scheduled_messages import router as scheduled_messages_router
        dp.include_router(scheduled_messages_router)
        
        # Bakiye etkinlikleri sistemi komutları - EKSİK FONKSIYONLAR, KALDIRILDI
        # from handlers.balance_event import create_balance_event_command, list_balance_events_command
        # dp.message(Command("bakiyeetkinlik"))(create_balance_event_command)
        # dp.message(Command("bakiyeetkinlikler"))(list_balance_events_command)
        
        # Admin izin yöneticisi komutları - EKSİK FONKSIYONLAR, KALDIRILDI
        # from handlers.admin_permission_manager import admin_permission_command, set_admin_level_command
        # dp.message(Command("adminyetki"))(admin_permission_command)
        # dp.message(Command("adminseviyeayarla"))(set_admin_level_command)
        
        # 📊 İstatistikler Sistemi - ROUTER ENTEGRASYONU
        from handlers.statistics_system import router as statistics_router
        from handlers.recruitment_system import router as recruitment_router
        from handlers.broadcast_system import router as broadcast_router
        from handlers.admin_permission_manager import router as admin_permission_router
        from handlers.admin_commands import router as admin_commands_router
        
        # 📢 BROADCAST ROUTER - EN ÖNCE (Mesaj handler'ı için)
        dp.include_router(broadcast_router) # Yayın sistemi router'ı
        
        dp.include_router(statistics_router)  # İstatistikler sistemi router'ı
        dp.include_router(recruitment_router) # Kayıt teşvik sistemi router'ı
        dp.include_router(admin_permission_router) # Admin izin yöneticisi router'ı
        dp.include_router(admin_commands_router) # Admin komutları router'ı
        dp.include_router(balance_event_router) # Bakiye etkinlikleri sistemi
        
        log_system("Router'lar kayıtlandı!")
        
        # Etkinlik katılım handler'ı için gerekli
        dp.include_router(event_participation_router)  # GERİ EKLENDİ - Katılım handler için
        
        # Event management router'ını da ekle - end_event callback'i için
        from handlers.event_management import router as event_management_router
        dp.include_router(event_management_router)  # End event callback için
        
        # Dynamic command creator router'ını dahil et - EN ÖNCE!
        from handlers.dynamic_command_creator import router as dynamic_command_router
        dp.include_router(dynamic_command_router)  # Dinamik komut oluşturucu için
        
        # Eksik router'ları ekle
        dp.include_router(simple_events_router)  # Simple events router'ı
        dp.include_router(unknown_commands_router)  # Unknown commands router'ı
        dp.include_router(events_list_router)  # Events list router'ı
        
        # Detaylı log sistemi router'ı
        dp.include_router(detailed_logging_router)  # Detaylı log sistemi
        
        # 📢 Broadcast Sistemi - ROUTER ENTEGRASYONU
        from handlers.broadcast_system import set_bot_instance as set_broadcast_bot_instance
        set_broadcast_bot_instance(bot)
        
        # Manuel handler'lar - ROUTER SİSTEMİNE GEÇİLDİ
        # from handlers.broadcast_system import start_broadcast, cancel_broadcast
        # dp.register_callback_query_handler(start_broadcast, lambda c: c.data == "admin_broadcast")
        # dp.register_callback_query_handler(cancel_broadcast, lambda c: c.data == "admin_broadcast_cancel")
        
        # Manuel mesaj handler'ı - ROUTER SİSTEMİNE GEÇİLDİ
        # from handlers.broadcast_system import process_broadcast_message
        # from handlers.broadcast_system import broadcast_states
        # dp.register_message_handler(process_broadcast_message, lambda m: m.from_user and m.from_user.id == config.ADMIN_USER_ID and m.from_user.id in broadcast_states and broadcast_states[m.from_user.id] == "waiting_for_message")
        
        # Admin commands router'ını dahil et - ZATEN DAHİL EDİLDİ (YUKARIDA)
        # from handlers.admin_commands import router as admin_commands_router
        # dp.include_router(admin_commands_router)  # Admin yetki komutları için
        
        # Admin panel router'ını dahil et (FSM handler'ları için)
        dp.include_router(admin_panel_router)
        
        # Bot yazma komutu
        dp.message(Command("botyaz"))(bot_write_command)
        
        # 4. PRIVATE MESSAGE HANDLER - Market ürün ekleme + admin sipariş mesajları (EN SON!)
        from handlers.admin_panel import handle_product_step_input
        from handlers.admin_order_management import handle_admin_order_message
        from handlers.admin_market_management import handle_product_creation_input
        
        # BROADCAST MESSAGE HANDLER - KALDIRILDI - handle_all_chat_inputs içinde işleniyor
        # from handlers.broadcast_system import process_broadcast_message_router
        # dp.message(F.chat.type == "private")(process_broadcast_message_router)
        
        # BROADCAST CALLBACK HANDLER'LARI - MANUEL KAYIT
        from handlers.broadcast_system import start_broadcast_callback, cancel_broadcast_callback, broadcast_stats_callback, broadcast_back_callback, broadcast_close_callback
        dp.callback_query(lambda c: c.data == "admin_broadcast")(start_broadcast_callback)
        dp.callback_query(lambda c: c.data == "admin_broadcast_cancel")(cancel_broadcast_callback)
        dp.callback_query(lambda c: c.data == "broadcast_stats")(broadcast_stats_callback)
        dp.callback_query(lambda c: c.data == "broadcast_back")(broadcast_back_callback)
        dp.callback_query(lambda c: c.data == "broadcast_close")(broadcast_close_callback)
        
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
                
                # 0. BROADCAST SİSTEMİ KONTROLÜ - GERİ EKLENDİ
                from handlers.broadcast_system import broadcast_states
                if user_id in broadcast_states and broadcast_states[user_id] == "waiting_for_message":
                    log_system(f"📢 BROADCAST STATE BULUNDU - User: {user_id}")
                    # Broadcast mesajını işle
                    from handlers.broadcast_system import process_broadcast_message_router
                    await process_broadcast_message_router(message)
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
                
                # 6. Recruitment response kontrolü - sadece recruitment callback'lerinde çalışır
                # Burada çağrılmaz, sadece callback'lerde çalışır
                
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
                
                # 10. Özelden menü gösterme sistemi - Kayıtlı kullanıcılar için
                if message.chat.type == "private":
                    from database import is_user_registered, add_points_to_user, get_user_points_cached
                    is_registered = await is_user_registered(user_id)
                    
                    if is_registered:
                        # Özelden yeni point sistemi - Her 10 mesajda 0.02 point
                        current_balance = await get_user_points_cached(user_id)
                        total_messages = current_balance.get('total_messages', 0) if current_balance else 0
                        
                        # Yeni mesaj sayısı
                        new_total_messages = total_messages + 1
                        
                        # Her 10 mesajda bir point kazanılır
                        if new_total_messages % 10 == 0:
                            old_balance = current_balance.get('kirve_points', 0.0) if current_balance else 0.0
                            
                            # Point ekle (özel chat için group_id = 0)
                            await add_points_to_user(user_id, 0.02, 0)
                            
                            # Yeni bakiyeyi hesapla
                            new_balance = old_balance + 0.02
                            
                            log_system(f"💎 Özelden point eklendi - User: {user_id}, Points: +0.02, New Balance: {new_balance:.2f}, Mesaj: {new_total_messages}")
                        else:
                            log_system(f"📝 Özelden mesaj sayısı artırıldı - User: {user_id}, Mesaj: {new_total_messages}/10")
                        
                        # Özelden menü cooldown kontrolü
                        import time
                        current_time = time.time()
                        private_menu_cooldown_duration = 60  # 1 dakika
                        
                        # Cooldown kontrolü için global değişken
                        if not hasattr(handle_all_chat_inputs, 'private_menu_cooldowns'):
                            handle_all_chat_inputs.private_menu_cooldowns = {}
                        
                        # Kullanıcının son menü zamanını kontrol et
                        if user_id in handle_all_chat_inputs.private_menu_cooldowns:
                            last_menu_time = handle_all_chat_inputs.private_menu_cooldowns[user_id]
                            if current_time - last_menu_time < private_menu_cooldown_duration:
                                # Cooldown aktif, menü gösterme
                                log_system(f"⏰ Özelden menü cooldown'da - User: {user_id}")
                                return
                        
                        # Cooldown geçmişse veya ilk mesajsa
                        handle_all_chat_inputs.private_menu_cooldowns[user_id] = current_time
                        
                        # Kayıtlı kullanıcı - Menü göster
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                        
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🎮 Ana Menü", callback_data="menu_command")]
                        ])
                        
                        response_text = f"""
**Merhaba {message.from_user.first_name}!** 👋

**KirveHub**'ta aktifsin! Hemen menu'ye git ve özellikleri keşfet:

**Ne yapabilirsin:**
• 💎 **Point kazan** - Her mesajın point kazandırır
• 🛍️ **Market alışverişi** - Point'lerini freespinler, bakiyeler için kullan
• 🎯 **Etkinliklere katıl** - Point'lerinle çekilişlere, bonus hunt'lara katıl
• 📊 **Profilini gör** - İstatistiklerin ve sıralaman
• 🏆 **Yarış** - En aktif üyeler arasında yer al

**Hemen başla:**
💎 **Point kazanmaya devam et!**
🛍️ **Market'ten alışveriş yap!**
🎯 **Etkinliklere katıl!**


_🎯 Market'te point'lerini freespinler için kullanabilirsin!_
_🏆 Etkinliklerde point'lerinle özel ödüller kazanabilirsin!_
                        """
                        
                        await message.reply(
                            response_text,
                            parse_mode="Markdown",
                            reply_markup=keyboard
                        )
                        
                        log_system(f"💬 Özelden menü gösterildi - User: {user_id}")
                
            except Exception as e:
                log_error(f"❌ Chat input handler hatası: {e}")

        # BASİT HANDLER - TÜM ÖZEL MESAJLAR İÇİN
        @dp.message()
        async def simple_message_handler(message: Message):
            """Basit mesaj handler - Sadece özel mesajlar için"""
            try:
                user_id = message.from_user.id
                username = message.from_user.username or "Unknown"
                
                # KESİN LOG - Bu satır görünüyorsa handler çalışıyor
                print(f"🔍 HANDLER ÇALIŞIYOR - User: {user_id}, Text: {message.text}")
                log_system(f"📨 Özel mesaj alındı - User: {user_id} (@{username})")
                
                # Komut değilse handle_all_chat_inputs'u çağır
                if not message.text.startswith("/"):
                    await handle_all_chat_inputs(message)
                    log_system(f"✅ Özel mesaj işlendi - User: {user_id}")
                else:
                    # Komut logu
                    command = message.text.split()[0] if message.text else "Unknown"
                    log_system(f"⚡ Komut alındı: {command} - User: {user_id} (@{username})")
                    
                    # Komutları doğrudan işle
                    if command == "/testsql":
                        from handlers.admin_panel import test_sql_queries_command
                        await test_sql_queries_command(message)
                    elif command == "/start":
                        from handlers.start_handler import start_command
                        await start_command(message)
                    elif command == "/menu":
                        from handlers.profile_handler import menu_command
                        await menu_command(message)
                    elif command == "/cekilisler":
                        from handlers.event_participation import list_active_events
                        await list_active_events(message)
                    elif command == "/cekilisyap":
                        from handlers.simple_events import create_lottery_command
                        await create_lottery_command(message)
                    else:
                        # Diğer komutlar için normal handler'lara bırak
                        log_system(f"🔄 Komut router'lara yönlendiriliyor: {command} - User: {user_id}")
                        return
                    
            except Exception as e:
                log_error(f"❌ Private message handler hatası: {e}")
                print(f"HANDLER HATASI: {e}")
        
        # Eski karmaşık kayıt - iptal
        # dp.message(F.chat.type == "private", ~F.text.startswith("/"))(handle_all_chat_inputs)
        
        # Grup mesajları için tek handler - hem dinamik komutlar hem chat sistemi
        async def handle_group_command_creation(message: Message):
            """Grup mesajlarında hem dinamik komutlar hem chat sistemi"""
            try:
                user_id = message.from_user.id
                username = message.from_user.username or "Unknown"
                group_id = message.chat.id
                group_title = message.chat.title or "Unknown Group"
                
                # Detaylı log
                log_system(f"📨 Grup mesajı alındı - User: {user_id} (@{username}) - Group: {group_title} ({group_id}) - Text: {message.text}")
                
                # Komut mesajlarını atla
                if message.text and message.text.startswith("/"):
                    return
                
                # Dinamik komut handler'ı önce çağır - ! ile başlayan komutlar için
                if message.text and message.text.startswith('!'):
                    log_system(f"🔍 Dinamik komut tespit edildi - Text: {message.text}")
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
                from handlers.chat_system import handle_chat_message, send_chat_response
                
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
                    log_warning(f"⚠️ Cooldown nedeniyle yanıt verilmedi - User: {message.from_user.id}")
                    
            except Exception as e:
                log_error(f"❌ Grup komut oluşturucu hatası: {e}")
        
        # Grup mesajları için tek handler - hem dinamik komutlar hem chat sistemi
        dp.message(F.chat.type.in_(["group", "supergroup"]), ~F.text.startswith("/"))(handle_group_command_creation)
        
        # Grup komut handler'ını kaydet (silent komutlar için)
        dp.message(F.chat.type.in_(["group", "supergroup"]), F.text.startswith("/"))(handle_group_command_silently)
        
        # Recruitment callback handler - Router'da tanımlı olduğu için kaldırıldı
        
        # Admin panel callback'leri - SADECE admin panel prefix'leri (event_ prefix'i YOK!)
        from handlers.admin_panel import admin_panel_callback
        dp.callback_query(
            F.data.startswith("admin_") |
            F.data.startswith("category_") |
            F.data.startswith("price_") |
            F.data.startswith("admin_order_") |
            F.data.startswith("set_points_") |
            F.data.startswith("set_daily_") |
            F.data.startswith("set_weekly_") |
            F.data.startswith("balance_") |
            F.data.startswith("system_")
        )(admin_panel_callback)
        
        # Admin panel komutunu manuel olarak kaydet
        from handlers.admin_panel import admin_panel_command
        dp.message(Command("adminpanel"))(admin_panel_command)
        
        # Start menü callback handler'ları
        async def start_menu_callback(callback: types.CallbackQuery):
            """Start menü callback'lerini işle"""
            try:
                user_id = callback.from_user.id
                data = callback.data
                
                if data == "menu_command":
                    from handlers.profile_handler import menu_command
                    await menu_command(callback.message)
                elif data == "market_command":
                    # Market komutu için doğrudan market callback'i çağır
                    from handlers.profile_handler import profile_callback_handler
                    callback.data = "profile_market"
                    await profile_callback_handler(callback)
                elif data == "events_command":
                    # Etkinlikler komutu için doğrudan events callback'i çağır
                    from handlers.profile_handler import profile_callback_handler
                    callback.data = "profile_events"
                    await profile_callback_handler(callback)
                elif data == "profile_command":
                    # Profil komutu için doğrudan profile callback'i çağır
                    from handlers.profile_handler import profile_callback_handler
                    callback.data = "profile_main"
                    await profile_callback_handler(callback)
                elif data == "ranking_command":
                    # Sıralama komutu için doğrudan ranking callback'i çağır
                    from handlers.profile_handler import profile_callback_handler
                    callback.data = "profile_ranking"
                    await profile_callback_handler(callback)
                elif data == "help_command":
                    from handlers.register_handler import yardim_command
                    await yardim_command(callback.message)
                elif data == "start_command":
                    # Start komutunu çağır
                    from handlers.start_handler import start_command
                    await start_command(callback.message)

                
                await callback.answer("✅ Komut çalıştırıldı!")
                
            except Exception as e:
                log_error(f"❌ Start menü callback hatası: {e}")
                await callback.answer("❌ Hata oluştu!")
        
        # Start menü callback'lerini kaydet
        dp.callback_query(F.data.in_(["menu_command", "market_command", "events_command", "profile_command", "ranking_command", "help_command", "start_command"]))(start_menu_callback)
        
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
        
        # Bakiye etkinlikleri sistemi callback'leri - Router'da tanımlı olduğu için kaldırıldı
        
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
        
        # Detaylı log sistemi başlatma
        from utils.logging_utils import set_logging_system
        from handlers.detailed_logging_system import logging_system
        set_logging_system(logging_system)
        
        # Telegram logger'ı kur (sadece etkinse)
        if config.DETAILED_LOGGING_ENABLED:
            try:
                from utils.telegram_logger import setup_telegram_logger
                setup_telegram_logger(bot, config.LOG_GROUP_ID)
                log_system("📱 Telegram logger başarıyla kuruldu")
            except Exception as e:
                log_error(f"Telegram logger kurulum hatası: {e}")
        else:
            log_system("📱 Telegram logger devre dışı - DETAILED_LOGGING_ENABLED=False")
        
        await log_system_startup()
        
        # STARTUP BİLDİRİMİ: DEVRE DIŞI BIRAKILDI
        # STARTUP BİLDİRİMİ: Admin'lere bot başlatma bildirimi
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
                log_warning("Database pool 30 saniye sonra hala hazır değil, startup bildirimini atlıyoruz")
                return
            
            try:
                await send_startup_notification()
            except Exception as e:
                log_error(f"Startup bildirimi hatası: {e}")
        
        # Background'da çalıştır
        asyncio.create_task(delayed_startup_notification())
        
        # Bot'u başlat
        print("🚀 Bot polling başlatılıyor...")
        log_system("🚀 Bot polling başlatılıyor...")
        print("✅ Bot başarıyla çalışıyor! Komutlar hazır.")
        log_system("✅ Bot başarıyla çalışıyor! Komutlar hazır.")
        
        # Periyodik log gönderimi için background task - DEVRE DIŞI BIRAKILDI
        # async def periodic_logging():
        #     while True:
        #         try:
        #             await asyncio.sleep(60)  # Her 60 saniyede bir
        #             log_system("🔄 Bot aktif çalışıyor - Periyodik log")
        #             
        #             # Database durumunu kontrol et
        #             from database import db_pool
        #             if db_pool:
        #                 log_system("✅ Database bağlantısı aktif")
        #             else:
        #                 log_warning("⚠️ Database bağlantısı yok")
        #                 
        #         except Exception as e:
        #             log_error(f"Periyodik log hatası: {e}")
        # 
        # # Background task'i başlat
        # print("🔄 Periyodik log task'i başlatılıyor...")
        # asyncio.create_task(periodic_logging())
        # print("✅ Periyodik log task'i başlatıldı")
        
        print("🎯 Bot polling başlatılıyor...")
        await dp.start_polling(bot, timeout=60, request_timeout=60)
        
    except KeyboardInterrupt:
        log_system("Bot kullanıcı tarafından durduruldu!")
        
        # Detaylı log sistemi kapatma
        await log_system_shutdown()
        
        # SHUTDOWN BİLDİRİMİ: DEVRE DIŞI BIRAKILDI
        # log_system("Shutdown bildirimi gönderiliyor...")
        # try:
        #     # Önce bildirim gönder
        #     await send_maintenance_notification()
        #     log_system("Shutdown bildirimi başarıyla gönderildi!")
        #     
        #     # Bildirim gönderildikten sonra 2 saniye bekle
        #     await asyncio.sleep(2)
        #     
        #     # Sonra temiz kapanış
        #     await cleanup_resources()
        #     
        # except Exception as e:
        #     log_error(f"Shutdown bildirimi hatası: {e}")
        #     await cleanup_resources()
        
        # Temiz kapanış
        await cleanup_resources()
            
    except Exception as e:
        log_error(f"Bot başlatma hatası: {e}")
        
        # Detaylı log
        try:
            from handlers.detailed_logging_system import log_error as detailed_log_error
            await detailed_log_error(e, "Bot başlatma hatası")
        except:
            pass
        
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
        
        # Detaylı log
        try:
            from handlers.detailed_logging_system import log_error as detailed_log_error
            await detailed_log_error(e, "Group chat handler hatası")
        except:
            pass

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
            
            # Detaylı log
            try:
                from handlers.detailed_logging_system import log_error as detailed_log_error
                await detailed_log_error(e, "Grup komut mesajı silme hatası")
            except:
                pass
        
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
            from handlers.admin_panel import clean_messages_command, list_groups_command, help_command, delete_group_command
            from handlers.group_handler import kirvegrup_command, botlog_command, group_info_command
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
                from config import is_admin
                is_admin_user = is_admin(user_id)
                
                if is_admin_user:
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
            elif command == "/grupsil":
                await delete_group_command(message)
            elif command == "/kirvegrup":
                from handlers.group_handler import kirvegrup_command
                await kirvegrup_command(message)
            elif command == "/botlog":
                await botlog_command(message)
            elif command == "/grupbilgi":
                await group_info_command(message)
            elif command == "/yardim":
                await yardim_command(message)
            elif command == "/siparisliste":
                await show_orders_list_modern(message)
            elif command == "/etkinlikler":
                await list_active_events(message)
            elif command == "/cekilisbitir":
                await end_lottery_command(message)
            elif command == "/adminyap":
                from handlers.admin_permission_manager import make_admin_command
                await make_admin_command(message)
            elif command == "/adminçıkar":
                from handlers.admin_permission_manager import remove_admin_command
                await remove_admin_command(message)
            elif command == "/adminlist":
                from handlers.admin_permission_manager import list_admins_command
                await list_admins_command(message)
            elif command == "/admininfo":
                from handlers.admin_permission_manager import admin_info_command
                await admin_info_command(message)
            elif command == "/yetkiver":
                from handlers.admin_permission_manager import give_permission_command
                await give_permission_command(message)
            elif command == "/yetkial":
                from handlers.admin_permission_manager import take_permission_command
                await take_permission_command(message)
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
            elif command == "/testsql":
                from handlers.admin_panel import test_sql_queries_command
                await test_sql_queries_command(message)
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
• `/kirvegrup` - Grup kayıt sistemi
• `/grupbilgi` - Grup bilgileri
• `/botlog` - Log grubu ayarlama
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
    # Logging'i CMD'ye yönlendir
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # CMD'ye yazdır
            logging.FileHandler('bot.log', encoding='utf-8')  # Dosyaya da yazdır
        ]
    )
    
    print("🚀 Bot başlatılıyor...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹️ Bot kullanıcı tarafından durduruldu!")
    except Exception as e:
        print(f"❌ Bot hatası: {e}")
        import traceback
        traceback.print_exc() 