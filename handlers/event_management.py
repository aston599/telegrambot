"""
🏁 Çekiliş Yönetimi Sistemi - KirveHub Bot
/cekilisbitir komutu ve çekiliş sonlandırma işlemleri
"""

import logging
from datetime import datetime
from typing import Optional, Dict
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from config import get_config
from database import db_pool, end_event, get_event_participant_count, get_event_winners, get_latest_active_event_in_group, get_event_info_for_end, cancel_event, get_event_status
from utils.logger import logger

router = Router()

# Bot instance setter
_bot_instance = None

def set_bot_instance(bot_instance):
    global _bot_instance
    _bot_instance = bot_instance

async def end_lottery_command(message: Message):
    """Çekiliş bitirme komutu - /cekilisbitir"""
    try:
        # Admin kontrolü
        config = get_config()
        if message.from_user.id != config.ADMIN_USER_ID:
            return
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Çekiliş bitir komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                # Silme başarısız olsa da devam et
        
        # ID kontrolü - Direkt komuttan
        args = message.text.split()
        event_id = None
        if len(args) == 2:
            try:
                event_id = int(args[1])
                logger.info(f"🎯 ID ile çekiliş bitirme: {event_id}")
            except ValueError:
                error_message = "❌ Geçersiz çekiliş ID! Örnek: `/cekilisbitir 123`"
                if message.chat.type == "private":
                    await message.reply(error_message)
                else:
                    if _bot_instance:
                        await _bot_instance.send_message(message.from_user.id, error_message)
                return
        
        # ID yoksa reply kontrolü
        if not event_id:
            if message.reply_to_message:
                # Reply edilen mesajdan etkinlik ID'si bulmaya çalış
                try:
                    # Callback data'dan ID bulma (inline keyboard'dan)
                    if message.reply_to_message.reply_markup:
                        for row in message.reply_to_message.reply_markup.inline_keyboard:
                            for button in row:
                                if button.callback_data and "join_event_" in button.callback_data:
                                    event_id = int(button.callback_data.split("_")[-1])
                                    logger.info(f"🎯 Reply callback'den çekiliş ID bulundu: {event_id}")
                                    break
                            if event_id:
                                break
                    
                    # Hala bulunamadıysa mesaj içeriğinden bul
                    if not event_id and message.reply_to_message.text:
                        import re
                        id_match = re.search(r'ID:\s*(\d+)', message.reply_to_message.text)
                        if id_match:
                            event_id = int(id_match.group(1))
                            logger.info(f"🎯 Reply text'ten çekiliş ID bulundu: {event_id}")
                    
                    # Son çare: grup içindeki en son aktif etkinliği bul
                    if not event_id:
                        event_id = await get_latest_active_event_in_group(message.chat.id)
                        if event_id:
                            logger.info(f"🎯 Grup'taki son aktif çekiliş ID bulundu: {event_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Reply'den ID çıkarma hatası: {e}")
            
            if not event_id:
                error_message = "❌ Çekiliş ID'si bulunamadı!\n\n" \
                               "**Kullanım:**\n" \
                               "• `/cekilisbitir 123` (ID ile)\n" \
                               "• Çekiliş mesajına reply yapıp `/cekilisbitir`"
                if message.chat.type == "private":
                    await message.reply(error_message, parse_mode="Markdown")
                else:
                    if _bot_instance:
                        await _bot_instance.send_message(message.from_user.id, error_message, parse_mode="Markdown")
                return
        
        logger.info(f"🎯 Bitirilecek çekiliş ID: {event_id} - Group: {message.chat.id}")
        
        # Çekiliş detaylarını al
        event_details = await get_event_info_for_end(event_id)
        if not event_details:
            error_message = "❌ Çekiliş bulunamadı veya zaten bitmiş!"
            if message.chat.type == "private":
                await message.reply(error_message)
            else:
                if _bot_instance:
                    await _bot_instance.send_message(message.from_user.id, error_message)
            return
        
        # Çekiliş bitirme işlemi - Sadece bitirme, kazanan işleme yok
        success = await end_event(event_id)
        
        if success:
            # Kazananları tekrar al (end_event'ten sonra)
            participant_count = await get_event_participant_count(event_id)
            max_winners = event_details.get('max_winners', 1)
            winners = await get_event_winners(event_id, max_winners)
            
            logger.info(f"🔍 Event {event_id} - end_lottery_command winners: {winners}")
            
            # Point hesaplamaları
            entry_cost = event_details.get('entry_cost', 0)
            total_pool = participant_count * entry_cost
            winner_share = total_pool / len(winners) if winners else 0
            
            # Kazananları kaydet ve point dağıt
            from database import get_db_pool, add_points_to_user
            pool = await get_db_pool()
            if pool:
                async with pool.acquire() as conn:
                    for winner in winners:
                        # Kazananı event_participations tablosunda kaydet
                        await conn.execute("""
                            UPDATE event_participations 
                            SET status = 'completed'
                            WHERE user_id = $1 AND event_id = $2
                        """, winner['user_id'], event_id)
                        
                        # Kazananı event_participants tablosunda da kaydet
                        await conn.execute("""
                            UPDATE event_participants 
                            SET status = 'completed', is_winner = TRUE
                            WHERE user_id = $1 AND event_id = $2
                        """, winner['user_id'], event_id)
                        
                        # Point dağıt
                        if winner_share > 0:
                            await add_points_to_user(winner['user_id'], winner_share, event_details.get('group_id'))
                            logger.info(f"🎉 Kazanan point dağıtıldı: User {winner['user_id']}, Amount: {winner_share:.2f}")
                        
                        # Kazananlara özel mesaj gönder
                        if _bot_instance:
                            try:
                                winner_message = f"""
🎉 **TEBRİKLER! ÇEKİLİŞİ KAZANDINIZ!** 🎉

🏆 **Çekiliş:** {event_details.get('title', 'Bilinmeyen Çekiliş')}
💰 **Kazandığınız:** {winner_share:.2f} KP
🎯 **Çekiliş ID:** {event_id}

✨ **Point'leriniz hesabınıza eklendi!**
📊 **Yeni bakiyenizi görmek için:** /menu

🎊 **İyi şanslar!**
                                """
                                await _bot_instance.send_message(
                                    winner['user_id'],
                                    winner_message,
                                    parse_mode="Markdown"
                                )
                                logger.info(f"🎉 Kazanan bildirimi gönderildi: User {winner['user_id']}")
                            except Exception as e:
                                logger.error(f"❌ Kazanan bildirimi gönderilemedi: User {winner['user_id']}, Error: {e}")
            
            # Kazanan listesi oluştur - DETAYLI
            winner_list = []
            winner_mentions = []
            logger.info(f"🔍 Event {event_id} - Winners processing: {winners}")
            
            for winner in winners:
                username = winner.get('username')
                user_id = winner.get('user_id')
                first_name = winner.get('first_name', '')
                last_name = winner.get('last_name', '')
                payment_amount = winner.get('payment_amount', 0)
                
                logger.info(f"🔍 Event {event_id} - Processing winner: username={username}, user_id={user_id}, first_name={first_name}, last_name={last_name}, payment_amount={payment_amount}")
                
                # Kullanıcı adı varsa
                if username:
                    winner_info = f"@{username}"
                    winner_mentions.append(f"@{username}")
                # Ad soyad varsa
                elif first_name or last_name:
                    full_name = f"{first_name} {last_name}".strip()
                    winner_info = f"<b>{full_name}</b>"
                    winner_mentions.append(full_name)
                # Sadece ID
                elif user_id:
                    winner_info = f"<b>ID: {user_id}</b>"
                    winner_mentions.append(f"ID: {user_id}")
                else:
                    winner_info = f"<b>Bilinmeyen Kullanıcı</b>"
                    winner_mentions.append("Bilinmeyen Kullanıcı")
                
                # Katılım miktarını da ekle
                winner_info += f" <code>({payment_amount:.2f} KP)</code>"
                winner_list.append(winner_info)
                logger.info(f"🔍 Event {event_id} - Winner info created: {winner_info}")
            
            logger.info(f"🔍 Event {event_id} - Winner list: {winner_list}")
            logger.info(f"🔍 Event {event_id} - Winner mentions: {winner_mentions}")
            
            if winner_list:
                winners_text = "\n".join([f"🏆 {winner}" for winner in winner_list])
            else:
                winners_text = "❌ <b>Kazanan bulunamadı</b>"
            
            # Çekiliş sonuç mesajı - DETAYLI
            event_completion_message = f"""
╔══════════════════════╗
║   🏁 <b>ÇEKİLİŞ SONUÇLANDI</b> 🏁   ║
╚══════════════════════╝

📊 <b>Çekiliş Detayları:</b>
• 🎯 ID: <code>{event_id}</code>
• 👥 Katılımcı: <code>{participant_count}</code> kişi
• 🏆 Kazanan: <code>{len(winners)}</code> kişi
• 📅 Bitiş: <code>{datetime.now().strftime('%d.%m.%Y %H:%M')}</code>

🎉 <b>KAZANANLAR:</b>
{winners_text}

💰 <b>Point Dağıtımı:</b>
• Toplam Havuz: <code>{total_pool:.2f} KP</code>
• Kazanan Başına: <code>{winner_share:.2f} KP</code>

╔══════════════════════╗
║   🎊 <b>ÇEKİLİŞ TAMAMLANDI</b> 🎊   ║
╚══════════════════════╝
            """
            
            # 1. KİRVEBOT SOHBETİNDE SONUÇ GÖSTER
            completion_msg = await message.answer(event_completion_message, parse_mode="HTML")
            
            # 2. ÇEKİLİŞİN OLDUĞU GRUPTA DA SONUÇ GÖSTER
            try:
                from database import get_db_pool
                pool = await get_db_pool()
                if pool:
                    async with pool.acquire() as conn:
                        event_data = await conn.fetchrow("SELECT message_id, group_id FROM events WHERE id = $1", event_id)
                    
                    if event_data and event_data['group_id']:
                        # Çekilişin olduğu grupta sonuç mesajı gönder
                        group_completion_msg = await _bot_instance.send_message(
                            event_data['group_id'],
                            event_completion_message,
                            parse_mode="HTML"
                        )
                        logger.info(f"✅ Çekiliş sonucu grupta gönderildi: {event_data['group_id']}")
                        
                        # Kazananları etiketle
                        if winner_mentions:
                            mention_text = " ".join(winner_mentions)
                            mention_message = f"🎉 **TEBRİKLER KAZANANLAR!** 🎉\n\n{mention_text}"
                            await _bot_instance.send_message(
                                event_data['group_id'],
                                mention_message,
                                parse_mode="Markdown"
                            )
                            logger.info(f"✅ Kazananlar etiketlendi: {event_data['group_id']}")
                        
                        # Orijinal çekiliş mesajını güncelle - "Çekiliş Sonuçlandı" butonu
                        if event_data['message_id']:
                            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(
                                    text="🏁 Çekiliş Sonuçlandı - Katılım Kapalı",
                                    callback_data="event_completed"
                                )]
                            ])
                            await _bot_instance.edit_message_reply_markup(
                                chat_id=event_data['group_id'],
                                message_id=event_data['message_id'],
                                reply_markup=keyboard
                            )
                            logger.info(f"✅ Orijinal çekiliş mesajı güncellendi: {event_data['message_id']}")
                else:
                    logger.warning("⚠️ Database pool yok - grup sonuç mesajı gönderilemedi")
                        
            except Exception as e:
                logger.error(f"❌ Grup sonuç mesajı gönderme hatası: {e}")
            
            # Admin'e özel mesajla sonuç bildir
            if _bot_instance and message.chat.type != "private":
                admin_message = f"""
╔═══════════════╗
║   ✅ <b>İŞLEM BAŞARILI</b> ✅   ║
╚═══════════════╝

📊 <b>Çekiliş Özeti:</b>
• 🎯 ID: <code>{event_id}</code>
• 👥 Katılımcı: <code>{participant_count}</code>
• 🏆 Kazanan: <code>{len(winners)}</code>

✨ <b>Çekiliş başarıyla sonuçlandırıldı!</b>
• ✅ KirveBot sohbetinde sonuç gösterildi
• ✅ Çekiliş grubunda sonuç gösterildi
• ✅ Orijinal mesaj güncellendi
                """
                await _bot_instance.send_message(
                    message.from_user.id,
                    admin_message,
                    parse_mode="HTML"
                )
        else:
            error_message = "❌ Çekiliş bitirilemedi! Çekiliş bulunamadı veya zaten bitmiş."
            if message.chat.type == "private":
                await message.reply(error_message)
            else:
                if _bot_instance:
                    await _bot_instance.send_message(message.from_user.id, error_message)
                    
    except Exception as e:
        logger.error(f"❌ End lottery command hatası: {e}")
        error_message = "❌ Çekiliş bitirme işlemi başarısız!"
        if message.chat.type == "private":
            await message.reply(error_message)
        else:
            if _bot_instance:
                await _bot_instance.send_message(message.from_user.id, error_message)

@router.message(Command("etkinlikiptal"))
async def cancel_event_command(message: Message):
    """Etkinlik iptal etme komutu - /etkinlikiptal ID"""
    try:
        # Admin kontrolü
        config = get_config()
        if message.from_user.id != config.ADMIN_USER_ID:
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        if len(parts) != 2:
            await message.reply("❌ Kullanım: `/etkinlikiptal ID`")
            return
        
        try:
            event_id = int(parts[1])
        except ValueError:
            await message.reply("❌ Geçersiz ID! Sayı olmalı.")
            return
        
        # Etkinliği iptal et
        success = await cancel_event(event_id)
        
        if success:
            await message.reply(f"✅ Etkinlik başarıyla iptal edildi! ID: {event_id}")
        else:
            await message.reply(f"❌ Etkinlik iptal edilemedi! ID: {event_id}")
        
    except Exception as e:
        logger.error(f"❌ Etkinlik iptal hatası: {e}")
        await message.reply("❌ Bir hata oluştu!")

@router.message(Command("etkinlikdurum"))
async def event_status_command(message: Message):
    """Etkinlik durumu komutu - /etkinlikdurum ID"""
    try:
        # Admin kontrolü
        config = get_config()
        if message.from_user.id != config.ADMIN_USER_ID:
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        if len(parts) != 2:
            await message.reply("❌ Kullanım: `/etkinlikdurum ID`")
            return
        
        try:
            event_id = int(parts[1])
        except ValueError:
            await message.reply("❌ Geçersiz ID! Sayı olmalı.")
            return
        
        # Etkinlik durumunu getir
        event_info = await get_event_status(event_id)
        
        if event_info:
            response = f"""
📊 **ETKİNLİK DURUMU**

🎯 **ID:** {event_id}
📝 **Başlık:** {event_info['title']}
💰 **Katılım:** {event_info['entry_cost']:.2f} KP
🏆 **Kazanan:** {event_info['max_winners']} kişi
👥 **Katılımcı:** {event_info['participant_count']} kişi
📅 **Durum:** {event_info['status']}
⏰ **Oluşturulma:** {event_info['created_at']}
            """
        else:
            response = f"❌ Etkinlik bulunamadı! ID: {event_id}"
        
        await message.reply(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Etkinlik durum hatası: {e}")
        await message.reply("❌ Bir hata oluştu!") 

@router.message(Command("etkinlikyardım"))
async def event_help_command(message: Message):
    """Etkinlik komutları yardım: /etkinlikyardım"""
    try:
        # Admin kontrolü
        config = get_config()
        if message.from_user.id != config.ADMIN_USER_ID:
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        response = """
🎯 **ETKİNLİK SİSTEMİ YARDIM**

**🎲 Etkinlik Oluşturma:**
• `/etkinlik` - Yeni etkinlik oluştur
• `/cekilisyap` - Çekiliş oluştur (alias)

**🏁 Etkinlik Yönetimi:**
• `/cekilisbitir ID` - Çekiliş bitir ve kazananları seç
• `/etkinlikiptal ID` - Etkinlik iptal et (point geri ver)
• `/etkinlikdurum ID` - Etkinlik durumu görüntüle

**📋 Etkinlik Listesi:**
• `/etkinlikler` - Aktif etkinlikleri listele
• `/cekilisler` - Aktif çekilişleri listele (alias)

**👥 Katılım Sistemi:**
• Etkinlik mesajlarındaki butonlarla katılım
• Point kontrolü otomatik
• Çifte katılım önleme aktif

**🎉 Kazanan Seçimi:**
• Katılım miktarına göre ağırlıklı seçim
• Point dağıtımı otomatik
• Sonuç bildirimi otomatik

**📝 Kullanım Örnekleri:**
• `/cekilisbitir 123` - ID 123'lü çekilişi bitir
• `/etkinlikiptal 123` - ID 123'lü etkinliği iptal et
• `/etkinlikdurum 123` - ID 123'lü etkinlik durumu
        """
        
        await message.reply(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Etkinlik yardım hatası: {e}")
        await message.reply("❌ Bir hata oluştu!") 