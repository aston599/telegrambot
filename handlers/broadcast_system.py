"""
📢 Toplu Mesaj Sistemi - KirveHub Bot
Manuel handler sistemi
"""

import logging
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import get_config
from database import get_db_pool
from utils.logger import logger

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

async def start_broadcast(callback: types.CallbackQuery):
    """Toplu mesaj gönderme sürecini başlat"""
    logger.info(f"🎯 BROADCAST CALLBACK YAKALANDI - User: {callback.from_user.id}, Data: {callback.data}")
    try:
        config = get_config()
        
        # Admin kontrolü
        if callback.from_user.id != config.ADMIN_USER_ID:
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

async def process_broadcast_message(message: types.Message):
    """Admin mesajını al ve tüm kullanıcılara gönder"""
    # Text kontrolü - None olabilir (medya mesajları için)
    message_text = message.text or message.caption or "Metin yok"
    text_preview = message_text[:20] if message_text and len(message_text) > 20 else (message_text or "Metin yok")
    
    logger.info(f"🎯 BROADCAST MESSAGE HANDLER - User: {message.from_user.id}, Text: {text_preview}...")
    
    try:
        config = get_config()
        
        # Admin kontrolü
        if message.from_user.id != config.ADMIN_USER_ID:
            logger.info(f"❌ ADMIN DEĞİL - User: {message.from_user.id}")
            await message.answer("❌ Bu işlemi sadece admin yapabilir!")
            return
        
        # FSM state kontrolü
        if message.from_user.id not in broadcast_states or broadcast_states[message.from_user.id] != "waiting_for_message":
            logger.info(f"❌ BROADCAST STATE YOK - User: {message.from_user.id}, States: {broadcast_states}")
            return  # Bu handler'ı ignore et
        
        logger.info(f"✅ BROADCAST STATE BULUNDU - User: {message.from_user.id}, Processing message...")
        
        # Kullanıcı listesini çek
        pool = await get_db_pool()
        user_ids = []
        
        if pool:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT user_id FROM users WHERE is_registered = TRUE")
                user_ids = [row["user_id"] for row in rows]
        
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
        
        for uid in user_ids:
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

📢 **Gönderilen Medya:**
• 🎯 Tür: {message_type}
• 📝 İçerik: {message_text if message.text else "Medya içeriği"}
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

async def cancel_broadcast(callback: types.CallbackQuery):
    """Toplu mesaj gönderimini iptal et"""
    try:
        config = get_config()
        
        # Admin kontrolü
        if callback.from_user.id != config.ADMIN_USER_ID:
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