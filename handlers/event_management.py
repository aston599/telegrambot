"""
🏁 Çekiliş Yönetimi Sistemi - KirveHub Bot
/cekilisbitir komutu ve çekiliş sonlandırma işlemleri
"""

import logging
from datetime import datetime
from typing import Optional, Dict
from aiogram import Router, F, types
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
        target_group_id = None
        
        if len(args) >= 2:
            try:
                event_id = int(args[1])
                logger.info(f"🎯 ID ile çekiliş bitirme: {event_id}")
                
                # Eğer 3. parametre varsa grup ID'si
                if len(args) >= 3:
                    try:
                        target_group_id = int(args[2])
                        logger.info(f"🎯 Grup ID ile çekiliş bitirme: Event {event_id}, Group {target_group_id}")
                    except ValueError:
                        logger.warning(f"⚠️ Geçersiz grup ID: {args[2]}")
                        
            except ValueError:
                error_message = "❌ Geçersiz çekiliş ID! Örnek: `/cekilisbitir 123` veya `/cekilisbitir 123 456789`"
                if message.chat.type == "private":
                    await message.reply(error_message)
                else:
                    if _bot_instance:
                        await _bot_instance.send_message(message.from_user.id, error_message)
                return
        
        # ID yoksa reply kontrolü
        if not event_id:
            if message.reply_to_message:
                try:
                    # Reply'den event ID'sini çıkar
                    reply_text = message.reply_to_message.text
                    # Event ID'sini bul (örnek: "🎯 ID: 123" formatında)
                    import re
                    id_match = re.search(r'🎯\s*ID:\s*(\d+)', reply_text)
                    if id_match:
                        event_id = int(id_match.group(1))
                        logger.info(f"🎯 Reply'den çekiliş ID'si alındı: {event_id}")
                except Exception as e:
                    logger.error(f"❌ Reply'den ID çıkarma hatası: {e}")
            
            if not event_id:
                error_message = "❌ Çekiliş ID'si bulunamadı!\n\n" \
                               "**Kullanım:**\n" \
                               "• `/cekilisbitir 123` (ID ile)\n" \
                               "• `/cekilisbitir 123 456789` (ID ve Grup ID ile)\n" \
                               "• Çekiliş mesajına reply yapıp `/cekilisbitir`"
                if message.chat.type == "private":
                    await message.reply(error_message, parse_mode="Markdown")
                else:
                    if _bot_instance:
                        await _bot_instance.send_message(message.from_user.id, error_message, parse_mode="Markdown")
                return
        
        logger.info(f"🎯 Bitirilecek çekiliş ID: {event_id}, Hedef Grup: {target_group_id}")
        
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
        
        # Grup kontrolü - Eğer hedef grup belirtilmişse kontrol et
        if target_group_id:
            event_group_id = event_details.get('group_id')
            if event_group_id and event_group_id != target_group_id:
                error_message = f"❌ Bu çekiliş farklı bir grupta! (Event: {event_id}, Event Group: {event_group_id}, Target Group: {target_group_id})"
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
            winners = await get_event_winners(event_id, event_details.get('max_winners', 1))
            
            # Point havuzu hesapla
            total_pool = participant_count * event_details.get('entry_cost', 0)
            winner_share = total_pool / len(winners) if winners else 0
            
            # Kazananlara point ver
            if winners:
                from database import add_points_to_user
                for winner in winners:
                    try:
                        # Kazananlara point ver
                        await add_points_to_user(
                            winner['user_id'], 
                            winner_share,
                            group_id=event_details.get('group_id')
                        )
                        
                        # Kazananlara özel bildirim gönder
                        winner_message = f"""
🎉 **TEBRİKLER! ÇEKİLİŞ KAZANDINIZ!** 🎉

🏆 **Çekiliş:** {event_details.get('title', 'Çekiliş')}
💰 **Kazandığınız:** {winner_share:.2f} KP
👥 **Toplam Katılımcı:** {participant_count} kişi
🎯 **Çekiliş ID:** {event_id}

🎊 **İyi şanslar!**
                        """
                        
                        if _bot_instance:
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
                    winner_mentions.append("ID: {user_id}")
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
                # created_by kullanıcısının en son aktif olduğu grubu bul
                from database import get_registered_groups
                groups = await get_registered_groups()
                
                # Basit bir grup seçimi - ilk grubu kullan
                if groups and _bot_instance:
                    group_id = groups[0]['group_id']  # İlk grubu kullan
                    await _bot_instance.send_message(
                        group_id,
                        event_completion_message,
                        parse_mode="HTML"
                    )
                    logger.info(f"✅ Çekiliş sonucu gruba gönderildi: Group {group_id}")
                else:
                    logger.info("ℹ️ Grup bulunamadı, sadece özel mesajda gösterildi")
            except Exception as e:
                logger.error(f"❌ Grup mesajı gönderilemedi: {e}")
            
            logger.info(f"✅ Çekiliş başarıyla bitirildi: Event {event_id}, Winners: {len(winners)}")
            
        else:
            error_message = "❌ Çekiliş bitirilemedi! Sistem hatası."
            if message.chat.type == "private":
                await message.reply(error_message)
            else:
                if _bot_instance:
                    await _bot_instance.send_message(message.from_user.id, error_message)
            
    except Exception as e:
        logger.error(f"❌ Çekiliş bitirme hatası: {e}")
        error_message = "❌ Çekiliş bitirme sırasında hata oluştu!"
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