"""
🎉 Bakiye Etkinliği Handler - KirveHub Bot
"""

import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import get_config
from database import db_pool
from utils.logger import logger

router = Router()


class BalanceEventStates(StatesGroup):
    """Bakiye etkinliği state'leri"""
    waiting_for_amount = State()
    waiting_for_reason = State()
    waiting_for_confirmation = State()


@router.callback_query(lambda c: c.data and c.data.startswith("admin_balance_event_"))
async def balance_event_callback_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Bakiye etkinliği callback handler"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        action = callback.data
        
        if action == "admin_balance_event":
            await show_balance_event_menu(callback, state)
        elif action == "admin_balance_event_quick":
            await start_quick_balance_event(callback, state)
        elif action == "admin_balance_event_custom":
            await start_custom_balance_event(callback, state)
        else:
            await callback.answer("❌ Geçersiz işlem!")
            
    except Exception as e:
        logger.error(f"❌ Balance event callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def show_balance_event_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Bakiye etkinliği menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ Hızlı Etkinlik", callback_data="admin_balance_event_quick"),
            InlineKeyboardButton(text="🎁 Özel Etkinlik", callback_data="admin_balance_event_custom")
        ],
        [
            InlineKeyboardButton(text="📊 Etkinlik Geçmişi", callback_data="admin_balance_event_history"),
            InlineKeyboardButton(text="⚙️ Etkinlik Ayarları", callback_data="admin_balance_event_settings")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_balance")
        ]
    ])
    
    response = """
🎉 **Bakiye Etkinliği Sistemi**

**🎯 Özellikler:**
• **10 dakika aktif** kullanıcılara otomatik bakiye
• **Etkinlik** formatında dağıtım
• **Toplu duyuru** ile bildirim
• **Anlık etkinlik** başlatma

**📋 Seçenekler:**
• **Hızlı Etkinlik:** Hazır ayarlarla hızlı etkinlik
• **Özel Etkinlik:** Özel miktar ve sebep ile
• **Geçmiş:** Önceki etkinlikleri
• **Ayarlar:** Etkinlik ayarları

Hangi seçeneği kullanmak istiyorsun?
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def start_quick_balance_event(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Hızlı bakiye etkinliği başlat"""
    try:
        # Hızlı sürpriz için hazır ayarlar
        amount = 1.00  # 1 KP
        reason = "🎉 Sürpriz Etkinlik Bonusu!"
        
        # Aktif kullanıcıları bul ve bakiye ver
        result = await process_surprise_event(amount, reason, callback.from_user.id)
        
        if result["success"]:
            response = f"""
🎉 **Hızlı Sürpriz Etkinlik Başarılı!**

**💰 Dağıtılan Miktar:** {amount:.2f} KP
**👥 Etkilenen Kullanıcı:** {result["affected_users"]} kişi
**📝 Sebep:** {reason}
**⏰ Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

**🎯 Kriterler:**
• Son 10 dakika aktif olan kullanıcılar
• Kayıtlı üyeler
• Bot'u bloklamamış kullanıcılar

**✅ İşlem tamamlandı!**
            """
        else:
            response = f"""
❌ **Sürpriz Etkinlik Başarısız!**

**Hata:** {result["error"]}
**Etkilenen Kullanıcı:** {result["affected_users"]} kişi

**🔧 Çözüm:**
• Database bağlantısını kontrol edin
• Aktif kullanıcı sayısını kontrol edin
            """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yeni Sürpriz", callback_data="admin_surprise_event")],
            [InlineKeyboardButton(text="⬅️ Ana Menü", callback_data="admin_balance")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Quick surprise event hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def start_custom_balance_event(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Özel bakiye etkinliği başlat"""
    await state.set_state(BalanceEventStates.waiting_for_amount)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ İptal", callback_data="admin_surprise_event")]
    ])
    
    response = """
🎁 **Özel Sürpriz Etkinlik**

**📝 Dağıtılacak miktarı yazın:**

**Örnekler:**
• `5.00` (5 KP)
• `2.50` (2.50 KP)
• `0.25` (0.25 KP)

**🎯 Kriterler:**
• Son 10 dakika aktif olan kullanıcılar
• Kayıtlı üyeler
• Bot'u bloklamamış kullanıcılar

**⚠️ Dikkat:** Bu işlem geri alınamaz!
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@router.message(BalanceEventStates.waiting_for_amount)
async def handle_balance_event_amount(message: Message, state: FSMContext) -> None:
    """Sürpriz etkinlik miktar input handler"""
    try:
        amount_input = message.text.strip()
        
        # Miktarı parse et
        try:
            amount = float(amount_input)
            if amount <= 0:
                raise ValueError("Miktar pozitif olmalı!")
        except ValueError:
            await message.reply("❌ Geçersiz miktar! Pozitif bir sayı girin.")
            return
        
        # State'e miktarı kaydet
        await state.update_data(amount=amount)
        
        # Sebep girmesi için state'i değiştir
        await state.set_state(BalanceEventStates.waiting_for_reason)
        
        response = f"""
✅ **Miktar Kabul Edildi!**

**💰 Miktar:** {amount:.2f} KP
**👥 Hedef:** Son 10 dakika aktif kullanıcılar

**📝 Etkinlik sebebini yazın:**

**Örnekler:**
• `🎉 Sürpriz Bonus Etkinliği!`
• `🎁 Hafta Sonu Sürprizi`
• `⭐ Özel Etkinlik Ödülü`
• `🎊 Kutlama Bonusu`
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="admin_surprise_event")]
        ])
        
        await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Surprise amount handler hatası: {e}")
        await message.reply("❌ Bir hata oluştu!")


@router.message(BalanceEventStates.waiting_for_reason)
async def handle_balance_event_reason(message: Message, state: FSMContext) -> None:
    """Sürpriz etkinlik sebep input handler"""
    try:
        reason = message.text.strip()
        data = await state.get_data()
        amount = data.get("amount")
        
        # Onay için state'i değiştir
        await state.set_state(BalanceEventStates.waiting_for_confirmation)
        await state.update_data(reason=reason)
        
        # Aktif kullanıcı sayısını hesapla
        active_users_count = await get_active_users_count()
        
        response = f"""
🎉 **Sürpriz Etkinlik Onayı**

**💰 Dağıtılacak Miktar:** {amount:.2f} KP
**👥 Aktif Kullanıcı:** {active_users_count} kişi
**📝 Sebep:** {reason}
**⏰ Süre:** Son 10 dakika aktif

**💡 Tahmini Toplam:** {amount * active_users_count:.2f} KP

**⚠️ Bu işlem geri alınamaz!**

Onaylıyor musun?
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Onayla", callback_data="surprise_confirm"),
                InlineKeyboardButton(text="❌ İptal", callback_data="admin_surprise_event")
            ]
        ])
        
        await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"❌ Surprise reason handler hatası: {e}")
        await message.reply("❌ Bir hata oluştu!")


@router.callback_query(lambda c: c.data == "surprise_confirm")
async def confirm_surprise_event(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Sürpriz etkinlik onayı"""
    try:
        data = await state.get_data()
        amount = data.get("amount")
        reason = data.get("reason")
        
        # Sürpriz etkinliği gerçekleştir
        result = await process_surprise_event(amount, reason, callback.from_user.id)
        
        if result["success"]:
            response = f"""
🎉 **Sürpriz Etkinlik Başarılı!**

**💰 Dağıtılan Miktar:** {amount:.2f} KP
**👥 Etkilenen Kullanıcı:** {result["affected_users"]} kişi
**📝 Sebep:** {reason}
**⏰ Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

**🎯 Kriterler:**
• Son 10 dakika aktif olan kullanıcılar
• Kayıtlı üyeler
• Bot'u bloklamamış kullanıcılar

**✅ İşlem tamamlandı!**
            """
        else:
            response = f"""
❌ **Sürpriz Etkinlik Başarısız!**

**Hata:** {result["error"]}
**Etkilenen Kullanıcı:** {result["affected_users"]} kişi

**🔧 Çözüm:**
• Database bağlantısını kontrol edin
• Aktif kullanıcı sayısını kontrol edin
            """
        
        # State'i temizle
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yeni Sürpriz", callback_data="admin_surprise_event")],
            [InlineKeyboardButton(text="⬅️ Ana Menü", callback_data="admin_balance")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Confirm surprise event hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


# Komut handler'ları
@router.message(Command("sürpriz"))
async def surprise_command(message: Message) -> None:
    """Sürpriz etkinlik komutu"""
    try:
        # Admin kontrolü
        config = get_config()
        if message.from_user.id != config.ADMIN_USER_ID:
            return
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Sürpriz komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_surprise_result_privately(message.from_user.id)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        # Hızlı sürpriz etkinlik başlat
        amount = 1.00  # 1 KP
        reason = "🎉 Sürpriz Etkinlik Bonusu!"
        
        result = await process_surprise_event(amount, reason, message.from_user.id)
        
        if result["success"]:
            response = f"""
🎉 **Sürpriz Etkinlik Başarılı!**

**💰 Dağıtılan Miktar:** {amount:.2f} KP
**👥 Etkilenen Kullanıcı:** {result["affected_users"]} kişi
**📝 Sebep:** {reason}
**⏰ Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

**✅ İşlem tamamlandı!**
            """
        else:
            response = f"""
❌ **Sürpriz Etkinlik Başarısız!**

**Hata:** {result["error"]}
**Etkilenen Kullanıcı:** {result["affected_users"]} kişi
            """
        
        await message.reply(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Surprise command hatası: {e}")
        await message.reply("❌ Bir hata oluştu!")

async def _send_surprise_result_privately(user_id: int):
    """Sürpriz sonucunu özel mesajla gönder"""
    try:
        if not _bot_instance:
            logger.error("❌ Bot instance bulunamadı!")
            return
        
        # Hızlı sürpriz etkinlik başlat
        amount = 1.00  # 1 KP
        reason = "🎉 Sürpriz Etkinlik Bonusu!"
        
        result = await process_surprise_event(amount, reason, user_id)
        
        if result["success"]:
            response = f"""
🎉 **Sürpriz Etkinlik Başarılı!**

**💰 Dağıtılan Miktar:** {amount:.2f} KP
**👥 Etkilenen Kullanıcı:** {result["affected_users"]} kişi
**📝 Sebep:** {reason}
**⏰ Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

**✅ İşlem tamamlandı!**
            """
        else:
            response = f"""
❌ **Sürpriz Etkinlik Başarısız!**

**Hata:** {result["error"]}
**Etkilenen Kullanıcı:** {result["affected_users"]} kişi
            """
        
        await _bot_instance.send_message(user_id, response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"❌ Private surprise result hatası: {e}")
        await _bot_instance.send_message(user_id, "❌ Sürpriz etkinlik hatası!")


# Yardımcı fonksiyonlar
async def get_active_users_count() -> int:
    """Son 10 dakika aktif kullanıcı sayısını al"""
    try:
        if not db_pool:
            return 0
        
        async with db_pool.acquire() as conn:
            # Son 10 dakika aktif olan kayıtlı kullanıcıları say
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE is_registered = TRUE 
                AND last_activity >= NOW() - INTERVAL '10 minutes'
            """)
            
            return count or 0
            
    except Exception as e:
        logger.error(f"❌ Get active users count hatası: {e}")
        return 0


async def get_active_users() -> list:
    """Son 10 dakika aktif kullanıcıları al"""
    try:
        if not db_pool:
            return []
        
        async with db_pool.acquire() as conn:
            # Son 10 dakika aktif olan kayıtlı kullanıcıları al
            users = await conn.fetch("""
                SELECT user_id, first_name, username, kirve_points
                FROM users 
                WHERE is_registered = TRUE 
                AND last_activity >= NOW() - INTERVAL '10 minutes'
                ORDER BY last_activity DESC
            """)
            
            return [dict(user) for user in users]
            
    except Exception as e:
        logger.error(f"❌ Get active users hatası: {e}")
        return []


async def process_surprise_event(amount: float, reason: str, admin_id: int) -> dict:
    """Sürpriz etkinlik işlemini gerçekleştir"""
    try:
        if not db_pool:
            return {"success": False, "error": "Database bağlantısı yok", "affected_users": 0}
        
        # Aktif kullanıcıları al
        active_users = await get_active_users()
        
        if not active_users:
            return {"success": False, "error": "Aktif kullanıcı bulunamadı", "affected_users": 0}
        
        async with db_pool.acquire() as conn:
            success_count = 0
            
            for user in active_users:
                try:
                    # Mevcut bakiyeyi al
                    current_balance = await conn.fetchval("""
                        SELECT COALESCE(kirve_points, 0) FROM users WHERE user_id = $1
                    """, user["user_id"])
                    
                    if current_balance is None:
                        continue
                    
                    # Yeni bakiyeyi hesapla
                    new_balance = current_balance + amount
                    
                    # Bakiyeyi güncelle
                    await conn.execute("""
                        UPDATE users 
                        SET kirve_points = $1, last_activity = NOW()
                        WHERE user_id = $2
                    """, new_balance, user["user_id"])
                    
                    # İşlem logunu kaydet
                    await conn.execute("""
                        INSERT INTO balance_logs (user_id, admin_id, action, amount, reason, created_at)
                        VALUES ($1, $2, $3, $4, $5, NOW())
                    """, user["user_id"], admin_id, "add", amount, reason)
                    
                    # Kullanıcıya bildirim gönder
                    await send_surprise_notification(user["user_id"], amount, reason)
                    
                    # Admin'e sürpriz etkinlik bildirimi gönder (her kullanıcı için ayrı)
                    await send_admin_surprise_notification(
                        admin_id=admin_id,
                        user_info=user,
                        old_balance=current_balance,
                        new_balance=new_balance,
                        amount=amount,
                        reason=reason
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ User balance update hatası - User: {user['user_id']}, Error: {e}")
                    continue
            
            logger.info(f"🎉 Surprise event completed - Amount: {amount}, Users: {success_count}")
            
            return {
                "success": True,
                "affected_users": success_count,
                "total_amount": amount * success_count
            }
            
    except Exception as e:
        logger.error(f"❌ Process surprise event hatası: {e}")
        return {"success": False, "error": str(e), "affected_users": 0}


async def send_surprise_notification(user_id: int, amount: float, reason: str) -> None:
    """Kullanıcıya sürpriz bildirimi gönder"""
    try:
        from main import bot  # Bot instance'ını al
        
        response = f"""
🎉 **Sürpriz Etkinlik Bildirimi!**

**💰 Kazandığınız:** {amount:.2f} KP
**📝 Sebep:** {reason}
**⏰ Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

**🎯 Kriter:** Son 10 dakika aktif olan kullanıcılar

**💡 Bilgi:** Bu sürpriz etkinlik admin tarafından başlatıldı!
        """
        
        await bot.send_message(user_id, response, parse_mode="Markdown")
        logger.info(f"✅ Surprise notification sent - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Send surprise notification hatası: {e}")


async def send_admin_surprise_notification(admin_id: int, user_info: dict, old_balance: float, new_balance: float, amount: float, reason: str) -> None:
    """Admin'e sürpriz etkinlik bildirimi gönder"""
    try:
        from main import bot  # Bot instance'ını al
        
        change_amount = new_balance - old_balance
        
        response = f"""
🎉 **Sürpriz Etkinlik - Kullanıcı Bildirimi**

**👤 Kullanıcı:** {user_info["first_name"]}
**🆔 ID:** `{user_info["user_id"]}`
**💰 Eski Bakiye:** {old_balance:.2f} KP
**💰 Yeni Bakiye:** {new_balance:.2f} KP
**📈 Değişim:** +{change_amount:.2f} KP

**📝 Etkinlik:** {reason}
**⏰ Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

**✅ Sürpriz etkinlik kullanıcıya uygulandı!**
        """
        
        logger.info(f"✅ Surprise event completed - User: {user_info['user_id']}, Amount: {amount}, Reason: {reason}")
        
    except Exception as e:
        logger.error(f"❌ Send admin surprise notification hatası: {e}")


async def show_surprise_history(callback: types.CallbackQuery) -> None:
    """Sürpriz etkinlik geçmişi göster"""
    try:
        if not db_pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
        
        async with db_pool.acquire() as conn:
            # Son sürpriz etkinlikleri al
            events = await conn.fetch("""
                SELECT 
                    bl.created_at,
                    bl.amount,
                    bl.reason,
                    COUNT(bl.user_id) as affected_users,
                    SUM(bl.amount) as total_amount
                FROM balance_logs bl
                WHERE bl.action = 'add' 
                AND bl.reason LIKE '%sürpriz%' OR bl.reason LIKE '%etkinlik%'
                GROUP BY bl.created_at, bl.amount, bl.reason
                ORDER BY bl.created_at DESC
                LIMIT 10
            """)
            
            if not events:
                response = """
📊 **Sürpriz Etkinlik Geçmişi**

**📭 Henüz sürpriz etkinlik yapılmamış!**

**💡 İpucu:** İlk sürpriz etkinliği başlatmak için "Hızlı Sürpriz" butonunu kullanın!
                """
            else:
                response = """
📊 **Sürpriz Etkinlik Geçmişi**

**Son 10 Sürpriz Etkinlik:**
"""
                
                for i, event in enumerate(events, 1):
                    date_str = event["created_at"].strftime('%d.%m.%Y %H:%M')
                    response += f"""
**{i}. {date_str}**
• Miktar: {event["amount"]:.2f} KP
• Kullanıcı: {event["affected_users"]} kişi
• Toplam: {event["total_amount"]:.2f} KP
• Sebep: {event["reason"]}
"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_surprise_history")],
                [InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_surprise_event")]
            ])
            
            await callback.message.edit_text(
                response,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"❌ Surprise history hatası: {e}")
        await callback.answer("❌ Geçmiş yüklenemedi!", show_alert=True)


async def show_surprise_settings(callback: types.CallbackQuery) -> None:
    """Sürpriz etkinlik ayarları göster"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰ Aktiflik Süresi", callback_data="surprise_setting_time"),
            InlineKeyboardButton(text="💰 Varsayılan Miktar", callback_data="surprise_setting_amount")
        ],
        [
            InlineKeyboardButton(text="📢 Bildirim Ayarları", callback_data="surprise_setting_notifications"),
            InlineKeyboardButton(text="🔄 Otomatik Etkinlik", callback_data="surprise_setting_auto")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_surprise_event")
        ]
    ])
    
    response = """
⚙️ **Sürpriz Etkinlik Ayarları**

**Mevcut Ayarlar:**
• **Aktiflik Süresi:** 10 dakika
• **Varsayılan Miktar:** 1.00 KP
• **Bildirimler:** Aktif
• **Otomatik Etkinlik:** Kapalı

**🔧 Ayarları değiştirmek için butonları kullanın:**
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    ) 