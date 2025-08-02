"""
📢 Toplu Mesaj Sistemi - KirveHub Bot
Router entegrasyonu ile tamamlanmış sistem
"""

import logging
from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import get_config
from database import get_db_pool
from utils.logger import logger

# Router tanımla
router = Router()

# FSM States
class BroadcastStates(StatesGroup):
    waiting_for_message = State()

# Bot instance
_bot_instance = None

def set_bot_instance(bot_instance):
    global _bot_instance
    _bot_instance = bot_instance

# Global FSM storage
broadcast_states = {}

# ==============================================
# ROUTER HANDLER'LARI
# ==============================================

@router.message(Command("broadcast"))
async def broadcast_command(message: Message):
    """Broadcast sistemi admin komutu"""
    try:
        # Admin kontrolü
        config = get_config()
        from config import is_admin
        if not is_admin(message.from_user.id):
            return

        # Grup chatindeyse komut mesajını sil
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Broadcast komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                logger.error(f"❌ Broadcast mesajı silinemedi: {e}")
            return

        # Broadcast durumunu göster
        status_message = f"""
📢 **BROADCAST SİSTEMİ**

🎯 **Mevcut Durum:** ✅ Aktif
📊 **Son Kullanım:** Manuel handler sistemi
🔄 **Router Durumu:** ✅ Entegre edildi

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **KULLANIM:**
• `/broadcast` - Bu menü
• Admin panelinden "📢 Toplu Mesaj Gönder" butonu
• Tüm medya türleri desteklenir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **Bilgi:** Sistem tüm kayıtlı kullanıcılara özelden mesaj gönderir.
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Toplu Mesaj Gönder", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📊 Broadcast İstatistikleri", callback_data="broadcast_stats")],
            [InlineKeyboardButton(text="❌ Kapat", callback_data="broadcast_close")]
        ])
        
        await message.reply(
            status_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Broadcast komut hatası: {e}")
        await message.reply("❌ Broadcast durumu yüklenemedi!")

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast_callback(callback: CallbackQuery):
    """Toplu mesaj gönderme sürecini başlat - Router versiyonu"""
    logger.info(f"🎯 BROADCAST CALLBACK YAKALANDI - User: {callback.from_user.id}, Data: {callback.data}")
    try:
        config = get_config()
        
        # Admin kontrolü
        from config import is_admin
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        # FSM state'i başlat
        broadcast_states[callback.from_user.id] = "waiting_for_message"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_broadcast_cancel")]
        ])
        
        await callback.message.edit_text(
            "✉️ **Toplu Medya Gönderimi**\n\n"
            "Göndermek istediğiniz medyayı gönderin:\n"
            "• 📝 Metin mesajı\n"
            "• 📸 Fotoğraf\n"
            "• 🎥 Video\n"
            "• 📄 Dosya\n"
            "• 🎵 Ses dosyası\n"
            "• 🎤 Ses mesajı\n"
            "• 📹 Video not\n\n"
            "Bu medya tüm kayıtlı kullanıcılara özelden gönderilecektir.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"📢 Toplu mesaj süreci başlatıldı - Admin: {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Toplu mesaj başlatma hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

@router.callback_query(F.data == "admin_broadcast_cancel")
async def cancel_broadcast_callback(callback: CallbackQuery):
    """Toplu mesaj gönderimini iptal et - Router versiyonu"""
    try:
        config = get_config()
        
        # Admin kontrolü
        from config import is_admin
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        await callback.message.edit_text("❌ **Toplu mesaj gönderimi iptal edildi.**", parse_mode="Markdown")
        
        # FSM state'i temizle
        if callback.from_user.id in broadcast_states:
            del broadcast_states[callback.from_user.id]
        
        logger.info(f"❌ Toplu mesaj iptal edildi - Admin: {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Toplu mesaj iptal hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

@router.callback_query(F.data == "broadcast_stats")
async def broadcast_stats_callback(callback: CallbackQuery):
    """Broadcast istatistiklerini göster"""
    try:
        config = get_config()
        
        # Admin kontrolü
        from config import is_admin
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        # Kullanıcı sayısını al
        pool = await get_db_pool()
        total_users = 0
        
        if pool:
            async with pool.acquire() as conn:
                total_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_registered = TRUE")
        
        stats_message = f"""
📊 **BROADCAST İSTATİSTİKLERİ**

👥 **Hedef Kullanıcılar:**
• Toplam Kayıtlı: {total_users} kullanıcı
• Broadcast Kapsamı: Tüm kayıtlı kullanıcılar

📢 **Sistem Durumu:**
• ✅ Router Entegrasyonu: Aktif
• ✅ Medya Desteği: Tüm türler
• ✅ Admin Kontrolü: Aktif

🎯 **Desteklenen Medya Türleri:**
• 📝 Metin mesajları
• 📸 Fotoğraflar
• 🎥 Videolar
• 📄 Dosyalar
• 🎵 Ses dosyaları
• 🎤 Ses mesajları
• 📹 Video notlar

💡 **Not:** Sistem tüm kayıtlı kullanıcılara özelden mesaj gönderir.
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="broadcast_back")],
            [InlineKeyboardButton(text="❌ Kapat", callback_data="broadcast_close")]
        ])
        
        await callback.message.edit_text(
            stats_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Broadcast stats hatası: {e}")
        await callback.answer("❌ İstatistikler yüklenemedi!", show_alert=True)

@router.callback_query(F.data == "broadcast_back")
async def broadcast_back_callback(callback: CallbackQuery):
    """Broadcast ana menüsüne geri dön"""
    try:
        config = get_config()
        
        # Admin kontrolü
        from config import is_admin
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        # Broadcast durumunu göster
        status_message = f"""
📢 **BROADCAST SİSTEMİ**

🎯 **Mevcut Durum:** ✅ Aktif
📊 **Son Kullanım:** Manuel handler sistemi
🔄 **Router Durumu:** ✅ Entegre edildi

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **KULLANIM:**
• `/broadcast` - Bu menü
• Admin panelinden "📢 Toplu Mesaj Gönder" butonu
• Tüm medya türleri desteklenir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **Bilgi:** Sistem tüm kayıtlı kullanıcılara özelden mesaj gönderir.
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Toplu Mesaj Gönder", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📊 Broadcast İstatistikleri", callback_data="broadcast_stats")],
            [InlineKeyboardButton(text="❌ Kapat", callback_data="broadcast_close")]
        ])
        
        await callback.message.edit_text(
            status_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Broadcast back hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

@router.callback_query(F.data == "broadcast_close")
async def broadcast_close_callback(callback: CallbackQuery):
    """Broadcast mesajını kapat"""
    try:
        await callback.message.delete()
        await callback.answer("❌ Mesaj kapatıldı")
        
    except Exception as e:
        logger.error(f"❌ Broadcast close hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def process_broadcast_message_router(message: Message):
    """Admin mesajını al ve tüm kullanıcılara gönder - Router versiyonu"""
    # Text kontrolü - None olabilir (medya mesajları için)
    message_text = message.text or message.caption or "Metin yok"
    text_preview = message_text[:20] if message_text and len(message_text) > 20 else (message_text or "Metin yok")
    
    logger.info(f"🎯 BROADCAST MESSAGE HANDLER BAŞLADI - User: {message.from_user.id}, Text: {text_preview}...")
    logger.info(f"📊 BROADCAST STATES: {broadcast_states}")
    logger.info(f"🔍 CHAT TYPE: {message.chat.type}")
    # Admin kontrolü için import
    from config import is_admin
    logger.info(f"🔍 IS ADMIN: {is_admin(message.from_user.id)}")
    
    try:
        config = get_config()
        
        # Admin kontrolü - zaten import edildi
        if not is_admin(message.from_user.id):
            logger.info(f"❌ ADMIN DEĞİL - User: {message.from_user.id}")
            # Admin değilse diğer handler'lara bırak
            return False
        
        # FSM state kontrolü
        if message.from_user.id not in broadcast_states or broadcast_states[message.from_user.id] != "waiting_for_message":
            logger.info(f"❌ BROADCAST STATE YOK - User: {message.from_user.id}, States: {broadcast_states}")
            # Broadcast state yoksa diğer handler'lara bırak
            return False
        
        # REPLY KONTROLÜ KALDIRILDI - Direkt mesaj kabul edilir
        logger.info(f"✅ BROADCAST MESAJI KABUL EDİLDİ - User: {message.from_user.id}")
        
        logger.info(f"✅ BROADCAST STATE BULUNDU - User: {message.from_user.id}, Processing message...")
        
        # Kullanıcı listesini çek
        pool = await get_db_pool()
        user_ids = []
        
        if pool:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT user_id FROM users WHERE is_registered = TRUE")
                user_ids = [row["user_id"] for row in rows]
                logger.info(f"📊 TOPLAM KULLANICI SAYISI: {len(user_ids)}")
        else:
            logger.error("❌ Database pool bulunamadı!")
            return
        
        # Mesajı herkese gönder
        sent = 0
        failed = 0
        
        # Mesaj türü kontrolü - tüm medya türleri kabul edilir
        if not message.text and not message.photo and not message.video and not message.document and not message.audio and not message.voice and not message.video_note:
            await message.answer("❌ Geçerli bir mesaj türü değil! Metin, fotoğraf, video, dosya, ses gibi medya türleri gönderebilirsiniz.")
            # FSM state'i temizle
            if message.from_user.id in broadcast_states:
                del broadcast_states[message.from_user.id]
            return
        
        logger.info(f"🚀 MESAJ GÖNDERİMİ BAŞLIYOR - Toplam: {len(user_ids)} kullanıcı")
        
        for i, uid in enumerate(user_ids, 1):
            try:
                # Mesaj türüne göre gönderim
                if message.text:
                    # Metin mesajı
                    await message.bot.send_message(uid, message.text)
                elif message.photo:
                    # Fotoğraf
                    caption = message.caption or ""
                    await message.bot.send_photo(uid, message.photo[-1].file_id, caption=caption)
                elif message.video:
                    # Video
                    caption = message.caption or ""
                    await message.bot.send_video(uid, message.video.file_id, caption=caption)
                elif message.document:
                    # Dosya
                    caption = message.caption or ""
                    await message.bot.send_document(uid, message.document.file_id, caption=caption)
                elif message.audio:
                    # Ses dosyası
                    caption = message.caption or ""
                    await message.bot.send_audio(uid, message.audio.file_id, caption=caption)
                elif message.voice:
                    # Ses mesajı
                    await message.bot.send_voice(uid, message.voice.file_id)
                elif message.video_note:
                    # Video not
                    await message.bot.send_video_note(uid, message.video_note.file_id)
                else:
                    # Diğer medya türleri için genel kopyalama
                    await message.bot.copy_message(uid, message.chat.id, message.message_id)
                
                sent += 1
                if i % 10 == 0:  # Her 10 mesajda bir log
                    logger.info(f"📤 İLERLEME: {i}/{len(user_ids)} kullanıcıya gönderildi")
                    
            except Exception as e:
                logger.debug(f"❌ Mesaj gönderilemedi - User: {uid}, Error: {e}")
                failed += 1
        
        # Mesaj türünü belirle
        message_type = "Metin"
        if message.photo:
            message_type = "Fotoğraf"
        elif message.video:
            message_type = "Video"
        elif message.document:
            message_type = "Dosya"
        elif message.audio:
            message_type = "Ses Dosyası"
        elif message.voice:
            message_type = "Ses Mesajı"
        elif message.video_note:
            message_type = "Video Not"
        
        # Sonuç raporu
        result_message = f"""
✅ **Toplu Mesaj Gönderildi!**

📊 **Sonuçlar:**
• ✅ Başarılı: {sent} kullanıcı
• ❌ Başarısız: {failed} kullanıcı
• 📝 Toplam: {sent + failed} kullanıcı
• 📈 Başarı Oranı: %{(sent/(sent+failed)*100):.1f}

📢 **Gönderilen Medya:**
• 🎯 Tür: {message_type}
• 📝 İçerik: {message_text if message.text else "Medya içeriği"}

⏱️ **Süre:** {len(user_ids)} kullanıcıya gönderim tamamlandı
        """
        
        await message.answer(result_message, parse_mode="Markdown")
        
        # FSM state'i temizle
        if message.from_user.id in broadcast_states:
            del broadcast_states[message.from_user.id]
        
        logger.info(f"📢 Toplu mesaj tamamlandı - Admin: {message.from_user.id}, Başarılı: {sent}, Başarısız: {failed}")
        
    except Exception as e:
        logger.error(f"❌ Toplu mesaj işleme hatası: {e}")
        await message.answer("❌ Bir hata oluştu!")
        # FSM state'i temizle
        if message.from_user.id in broadcast_states:
            del broadcast_states[message.from_user.id] 