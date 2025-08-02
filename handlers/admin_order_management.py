"""
📋 Modern Admin Sipariş Yönetimi
Telegram uyumlu admin sipariş onay/red sistemi
"""

import logging
from datetime import datetime
from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import get_db_pool

logger = logging.getLogger(__name__)

# Router oluştur
router = Router()

# Admin sipariş durumları - Global olarak erişilebilir
admin_order_states = {}

def get_admin_order_states():
    """Global admin_order_states'e erişim"""
    return admin_order_states

# ==============================================
# KOMUT HANDLER'LARI
# ==============================================

@router.message(Command("siparisliste"))
async def siparis_liste_command(message: types.Message) -> None:
    """Sipariş listesi komutu"""
    try:
        # Admin kontrolü
        from config import get_config
        config = get_config()
        if message.from_user.id != config.ADMIN_USER_ID:
            return
        
        # Grup chatindeyse komut mesajını sil
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Sipariş listesi komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                logger.error(f"❌ Sipariş listesi mesajı silinemedi: {e}")
            return
        
        await show_orders_list_modern(message)
        
    except Exception as e:
        logger.error(f"❌ Sipariş listesi komutu hatası: {e}")
        await message.reply("❌ Sipariş listesi yüklenemedi!")

@router.message(Command("siparisonayla"))
async def siparis_onayla_command(message: types.Message) -> None:
    """Sipariş onaylama komutu"""
    try:
        # Admin kontrolü
        from config import get_config
        config = get_config()
        if message.from_user.id != config.ADMIN_USER_ID:
            return
        
        # Grup chatindeyse komut mesajını sil
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Sipariş onaylama komutu mesajı silindi - Group: {message.chat.id}")
            except Exception as e:
                logger.error(f"❌ Sipariş onaylama mesajı silinemedi: {e}")
            return
        
        # Sipariş listesini göster
        await show_orders_list_modern(message)
        
    except Exception as e:
        logger.error(f"❌ Sipariş onaylama komutu hatası: {e}")
        await message.reply("❌ Sipariş onaylama sistemi yüklenemedi!")

# ==============================================
# CALLBACK HANDLER'LARI
# ==============================================

@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_callback(callback: types.CallbackQuery) -> None:
    """Admin sipariş onaylama callback'i"""
    try:
        order_number = callback.data.replace("admin_approve_", "")
        await handle_admin_approve_order(callback, order_number)
    except Exception as e:
        logger.error(f"❌ Admin onay callback hatası: {e}")
        await callback.answer("❌ Onay işlemi başarısız!", show_alert=True)

@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_callback(callback: types.CallbackQuery) -> None:
    """Admin sipariş reddetme callback'i"""
    try:
        order_number = callback.data.replace("admin_reject_", "")
        await handle_admin_reject_order(callback, order_number)
    except Exception as e:
        logger.error(f"❌ Admin red callback hatası: {e}")
        await callback.answer("❌ Red işlemi başarısız!", show_alert=True)

@router.callback_query(F.data == "admin_orders_list")
async def admin_orders_list_callback(callback: types.CallbackQuery) -> None:
    """Admin sipariş listesi callback'i"""
    try:
        # Callback'i message'a çevir
        class MessageWrapper:
            def __init__(self, callback):
                self.callback = callback
                self.chat = callback.message.chat
                self.from_user = callback.from_user
                self.reply = callback.message.answer
                self.answer = callback.message.answer
                
        message_wrapper = MessageWrapper(callback)
        await show_orders_list_modern(message_wrapper)
        await callback.answer("📋 Sipariş listesi güncellendi!")
        
    except Exception as e:
        logger.error(f"❌ Admin sipariş listesi callback hatası: {e}")
        await callback.answer("❌ Sipariş listesi yüklenemedi!", show_alert=True)

# ==============================================
# MESAJ HANDLER'LARI
# ==============================================

@router.message(F.chat.type == "private")
async def admin_order_message_handler(message: types.Message) -> None:
    """Admin'in sipariş onay/red mesajını yakala"""
    try:
        await handle_admin_order_message(message)
    except Exception as e:
        logger.error(f"❌ Admin sipariş mesaj handler hatası: {e}")

# ==============================================
# MEVCUT FONKSİYONLAR
# ==============================================

async def show_orders_list_modern(message: types.Message) -> None:
    """Modern sipariş listesi göster"""
    try:
        # Yeni SQL fonksiyonunu kullan
        from database import get_pending_orders_with_details
        orders = await get_pending_orders_with_details()
        
        if not orders:
            await message.reply(
                "📋 **Sipariş Listesi**\n\n"
                "⏳ Bekleyen sipariş bulunmuyor.\n"
                "Tüm siparişler işlenmiş durumda.",
                parse_mode="Markdown"
            )
            return
        
        # Her sipariş için ayrı mesaj
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
            
            await message.answer(
                order_message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        
        # Özet mesajı
        await message.reply(
            f"📋 **Sipariş Özeti**\n\n"
            f"⏳ **Bekleyen Sipariş:** {len(orders)} adet\n"
            f"📅 **Son Güncelleme:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Her sipariş için onay/red butonlarını kullanın.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ Sipariş listesi hatası: {e}")
        await message.reply("❌ Siparişler yüklenemedi!")


async def handle_admin_approve_order(callback: types.CallbackQuery, order_number: str) -> None:
    """Admin sipariş onaylama işlemi"""
    try:
        user_id = callback.from_user.id
        
        logger.info(f"✅ Admin onay butonu tıklandı - User: {user_id}, Order: {order_number}")
        
        # Admin kontrolü
        from config import get_config, is_admin
        config = get_config()
        if not is_admin(user_id):
            await callback.answer("❌ Yetkiniz yok!", show_alert=True)
            return
        
        # Admin'i sipariş durumuna al
        admin_order_states[user_id] = {
            'action': 'approve',
            'order_number': order_number,
            'timestamp': datetime.now()
        }
        
        logger.info(f"✅ Admin sipariş durumuna alındı - User: {user_id}, States: {admin_order_states}")
        
        # Onay mesajı formu
        approve_message = f"""
╔═══════════════════════════════════╗
║        ✅ SİPARİŞ ONAY FORMU ✅        ║
╚═══════════════════════════════════╝

📋 **Sipariş No:** `{order_number}`

📝 **Onay mesajınızı yazın:**
• Kod bilgileri
• Teslimat detayları
• Özel talimatlar
• Diğer bilgiler

💡 **Örnek:** "Kodunuz: ABC123, Siteye giriş yapıp kodu kullanın"

⚠️ **Önemli:** Mesajınız müşteriye gönderilecek
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        await callback.message.edit_text(
            approve_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        await callback.answer("📝 Onay mesajınızı yazın...")
        
    except Exception as e:
        logger.error(f"❌ Admin onay hatası: {e}")
        await callback.answer("❌ Onay işlemi başarısız!", show_alert=True)


async def handle_admin_reject_order(callback: types.CallbackQuery, order_number: str) -> None:
    """Admin sipariş reddetme işlemi"""
    try:
        user_id = callback.from_user.id
        
        logger.info(f"❌ Admin red butonu tıklandı - User: {user_id}, Order: {order_number}")
        
        # Admin kontrolü
        from config import get_config, is_admin
        config = get_config()
        if not is_admin(user_id):
            await callback.answer("❌ Yetkiniz yok!", show_alert=True)
            return
        
        # Admin'i sipariş durumuna al
        admin_order_states[user_id] = {
            'action': 'reject',
            'order_number': order_number,
            'timestamp': datetime.now()
        }
        
        logger.info(f"❌ Admin sipariş durumuna alındı - User: {user_id}, States: {admin_order_states}")
        
        # Red mesajı formu
        reject_message = f"""
╔═══════════════════════════════════╗
║        ❌ SİPARİŞ RED FORMU ❌        ║
╚═══════════════════════════════════╝

📋 **Sipariş No:** `{order_number}`

📝 **Red sebebini yazın:**
• Neden reddedildi
• Alternatif öneriler
• Tekrar sipariş bilgileri
• Diğer açıklamalar

💡 **Örnek:** "Site kayıt olmadığınız için reddedildi. Önce kayıt olun."

⚠️ **Önemli:** Mesajınız müşteriye gönderilecek
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        await callback.message.edit_text(
            reject_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        await callback.answer("📝 Red sebebini yazın...")
        
    except Exception as e:
        logger.error(f"❌ Admin red hatası: {e}")
        await callback.answer("❌ Red işlemi başarısız!", show_alert=True)


async def handle_admin_order_message(message: types.Message) -> None:
    """Admin'in sipariş onay/red mesajını işle"""
    try:
        user_id = message.from_user.id
        from config import get_config
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            return
        
        # Admin'in sipariş durumu var mı?
        if user_id not in admin_order_states:
            # Eğer admin sipariş durumunda değilse, diğer handler'lara geç
            logger.debug(f"❌ Admin sipariş durumunda değil - User: {user_id}")
            return
        
        # Debug log
        logger.info(f"📝 Admin sipariş mesajı alındı - User: {user_id}, Text: {message.text[:50]}...")
        logger.info(f"📝 Admin order states: {admin_order_states}")
        
        state = admin_order_states[user_id]
        action = state['action']
        order_number = state['order_number']
        admin_message = message.text
        
        # Mesajı işlemeden önce state'i temizle
        del admin_order_states[user_id]
        
        logger.info(f"📝 Sipariş işlemi başlatılıyor - Action: {action}, Order: {order_number}")
        
        pool = await get_db_pool()
        if not pool:
            await message.reply("❌ Sipariş işlemi başarısız!")
            return
        
        async with pool.acquire() as conn:
            # Sipariş bilgilerini al
            order_info = await conn.fetchrow("""
                SELECT o.user_id, o.total_price, o.status,
                       p.name as product_name, p.company_name,
                       u.first_name, u.username
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.order_number = $1
            """, order_number)
            
            if not order_info:
                await message.reply("❌ Sipariş bulunamadı!")
                return
            
            logger.info(f"📝 Sipariş bilgileri alındı - User: {order_info['user_id']}, Product: {order_info['product_name']}")
            
            if action == 'approve':
                # Siparişi onayla
                await conn.execute("""
                    UPDATE market_orders 
                    SET status = 'approved', admin_notes = $1, updated_at = NOW()
                    WHERE order_number = $2
                """, admin_message, order_number)
                
                logger.info(f"✅ Sipariş onaylandı - Order: {order_number}")
                
                # Müşteriye onay mesajı gönder
                customer_message = f"""
╔═══════════════════════════════════╗
║        ✅ SİPARİŞİNİZ ONAYLANDI ✅        ║
╚═══════════════════════════════════╝

📋 **Sipariş No:** `{order_number}`
🛍️ **Ürün:** {order_info['product_name']}
🏢 **Site:** {order_info['company_name']}
💰 **Tutar:** {order_info['total_price']} KP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 **Teslimat Bilgileri:**
{admin_message}

✅ **Siparişiniz onaylandı!**
                """
                
                from aiogram import Bot
                bot = Bot(token=config.BOT_TOKEN)
                
                await bot.send_message(
                    chat_id=order_info['user_id'],
                    text=customer_message,
                    parse_mode="Markdown"
                )
                
                logger.info(f"✅ Müşteriye onay mesajı gönderildi - User: {order_info['user_id']}")
                
                # Admin'e onay mesajı
                await message.reply("✅ Sipariş onaylandı ve müşteriye bildirim gönderildi!")
                
                # Log dosyasına kaydet
                with open("sipariskabullog.txt", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now()} - Sipariş onaylandı: {order_number} - Admin: {user_id} - Mesaj: {admin_message}\n")
                
            elif action == 'reject':
                # Siparişi reddet
                await conn.execute("""
                    UPDATE market_orders 
                    SET status = 'rejected', admin_notes = $1, updated_at = NOW()
                    WHERE order_number = $2
                """, admin_message, order_number)
                
                logger.info(f"❌ Sipariş reddedildi - Order: {order_number}")
                
                # BAKİYE İADE SİSTEMİ - Kullanıcının parasını geri ver
                refund_amount = order_info['total_price']
                await conn.execute("""
                    UPDATE users 
                    SET kirve_points = kirve_points + $1 
                    WHERE user_id = $2
                """, refund_amount, order_info['user_id'])
                
                logger.info(f"💰 Bakiye iade edildi - User: {order_info['user_id']}, Amount: {refund_amount} KP")
                
                # Müşteriye red mesajı gönder
                customer_message = f"""
╔═══════════════════════════════════╗
║        ❌ SİPARİŞİNİZ REDDEDİLDİ ❌        ║
╚═══════════════════════════════════╝

📋 **Sipariş No:** `{order_number}`
🛍️ **Ürün:** {order_info['product_name']}
🏢 **Site:** {order_info['company_name']}
💰 **Tutar:** {order_info['total_price']} KP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ **Red Sebebi:**
{admin_message}

💰 **Bakiye İadesi:**
✅ {refund_amount} KP hesabınıza iade edildi
💎 Yeni bakiyenizi `/menu` komutu ile kontrol edebilirsiniz

💡 **Öneriler:**
• Gerekli koşulları sağlayın
• Tekrar sipariş verebilirsiniz
• Sorularınız için destek alın

❌ **Siparişiniz reddedildi.**
                """
                
                from aiogram import Bot
                bot = Bot(token=config.BOT_TOKEN)
                
                await bot.send_message(
                    chat_id=order_info['user_id'],
                    text=customer_message,
                    parse_mode="Markdown"
                )
                
                logger.info(f"❌ Müşteriye red mesajı gönderildi - User: {order_info['user_id']}")
                
                # Admin'e red mesajı
                await message.reply(f"❌ Sipariş reddedildi ve müşteriye {refund_amount} KP iade edildi!")
                
                # Log dosyasına kaydet
                with open("siparisredlog.txt", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now()} - Sipariş reddedildi: {order_number} - Admin: {user_id} - Sebep: {admin_message} - İade: {refund_amount} KP\n")
        
    except Exception as e:
        logger.error(f"❌ Admin sipariş mesaj işleme hatası: {e}")
        await message.reply("❌ Sipariş işlemi başarısız!")


async def handle_admin_order_cancel(callback: types.CallbackQuery) -> None:
    """Admin sipariş işlemini iptal et"""
    try:
        user_id = callback.from_user.id
        
        # Admin kontrolü
        from config import get_config
        config = get_config()
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Yetkiniz yok!", show_alert=True)
            return
        
        # State'i temizle
        if user_id in admin_order_states:
            del admin_order_states[user_id]
        
        await callback.message.edit_text(
            "❌ **Sipariş İşlemi İptal Edildi**\n\n"
            "Sipariş işlemi iptal edildi.\n"
            "Yeni bir işlem başlatabilirsiniz.",
            parse_mode="Markdown"
        )
        
        await callback.answer("❌ İşlem iptal edildi!")
        
    except Exception as e:
        logger.error(f"❌ Admin iptal hatası: {e}")
        await callback.answer("❌ İptal işlemi başarısız!", show_alert=True) 