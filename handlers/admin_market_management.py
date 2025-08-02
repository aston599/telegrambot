"""
🛍️ Market Yönetim Sistemi - KirveHub Bot
Ürün ekleme, düzenleme, silme, stok yönetimi
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

from config import get_config
from database import get_db_pool
from utils.logger import logger

router = Router()

# Bot instance setter
_bot_instance = None

def set_bot_instance(bot_instance):
    global _bot_instance
    _bot_instance = bot_instance

# Bot instance'ınıı main.py'den al
def get_bot_instance():
    global _bot_instance
    if _bot_instance is None:
        # Main.py'den bot instance'ını al
        try:
            from main import _bot_instance as main_bot
            _bot_instance = main_bot
        except:
            pass
    return _bot_instance

# Ürün oluşturma durumu
product_creation_data = {}

# Ürün düzenleme durumu
product_edit_data = {}

# Ürün silme durumu
product_delete_data = {}

# ==============================================
# MARKET YÖNETİM KOMUTLARI
# ==============================================

# Sipariş yönetimi fonksiyonları (admin_market.py'den entegre edildi)
async def orders_list_command(message: Message) -> None:
    """
    /siparisliste komutu - Bekleyen siparişleri listele
    """
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        from config import is_admin
        if not is_admin(user_id):
            return
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Sipariş liste komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_orders_list_privately(user_id)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        logger.info(f"📋 Sipariş liste komutu ÖZELİNDE - User: {message.from_user.first_name} ({user_id})")
        
        # Sipariş listesini göster
        await send_orders_list(user_id, message.reply)
        
    except Exception as e:
        logger.error(f"❌ Sipariş liste komut hatası: {e}")
        if message.chat.type == "private":
            await message.reply("❌ Sipariş listesi yüklenemedi!")


async def approve_order_command(message: Message) -> None:
    """
    /siparisonayla ID komutu - Siparişi onayla
    """
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        from config import is_admin
        if not is_admin(user_id):
            return
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Sipariş onayla komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER - Parametreyi parse et
                try:
                    parts = message.text.split()
                    if len(parts) >= 2:
                        order_number = parts[1]
                        if _bot_instance:
                            await _send_approve_order_privately(user_id, order_number)
                    else:
                        if _bot_instance:
                            await _bot_instance.send_message(user_id, "❌ Kullanım: /siparisonayla [Sipariş ID]")
                except:
                    pass
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        # Parametreyi parse et
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("❌ Kullanım: /siparisonayla [Sipariş ID]\n\nÖrnek: /siparisonayla 123456")
            return
        
        order_number = parts[1]
        logger.info(f"✅ Sipariş onayla komutu ÖZELİNDE - User: {message.from_user.first_name} ({user_id}), Order: {order_number}")
        
        # Siparişi onayla
        await process_approve_order(user_id, order_number, message.reply)
        
    except Exception as e:
        logger.error(f"❌ Sipariş onayla komut hatası: {e}")
        if message.chat.type == "private":
            await message.reply("❌ Sipariş onaylama başarısız!")


async def reject_order_command(message: Message) -> None:
    """
    /siparisreddet ID komutu - Siparişi reddet
    """
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
                logger.info(f"🔇 Sipariş reddet komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER - Parametreyi parse et
                try:
                    parts = message.text.split()
                    if len(parts) >= 2:
                        order_number = parts[1]
                        if _bot_instance:
                            await _send_reject_order_privately(user_id, order_number)
                    else:
                        if _bot_instance:
                            await _bot_instance.send_message(user_id, "❌ Kullanım: /siparisreddet [Sipariş ID]")
                except:
                    pass
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        # Parametreyi parse et
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("❌ Kullanım: /siparisreddet [Sipariş ID]\n\nÖrnek: /siparisreddet 123456")
            return
        
        order_number = parts[1]
        logger.info(f"❌ Sipariş reddet komutu ÖZELİNDE - User: {message.from_user.first_name} ({user_id}), Order: {order_number}")
        
        # Siparişi reddet
        await process_reject_order(user_id, order_number, message.reply)
        
    except Exception as e:
        logger.error(f"❌ Sipariş reddet komut hatası: {e}")
        if message.chat.type == "private":
            await message.reply("❌ Sipariş reddetme başarısız!")


async def _send_orders_list_privately(user_id: int):
    """Sipariş listesini özel mesajla gönder"""
    try:
        await send_orders_list_direct(user_id)
        logger.info(f"✅ Sipariş listesi özel mesajla gönderildi: {user_id}")
    except Exception as e:
        logger.error(f"❌ Sipariş listesi gönderilemedi: {e}")


async def _send_approve_order_privately(user_id: int, order_number: str):
    """Sipariş onaylama işlemini özel mesajla gönder"""
    try:
        await process_approve_order_direct(user_id, order_number)
        logger.info(f"✅ Sipariş onaylama özel mesajla gönderildi: {user_id}, Order: {order_number}")
    except Exception as e:
        logger.error(f"❌ Sipariş onaylama gönderilemedi: {e}")


async def _send_reject_order_privately(user_id: int, order_number: str):
    """Sipariş reddetme işlemini özel mesajla gönder"""
    try:
        await process_reject_order_direct(user_id, order_number)
        logger.info(f"✅ Sipariş reddetme özel mesajla gönderildi: {user_id}, Order: {order_number}")
    except Exception as e:
        logger.error(f"❌ Sipariş reddetme gönderilemedi: {e}")


async def send_orders_list(user_id: int, reply_func) -> None:
    """Sipariş listesini göster"""
    try:
        pool = await get_db_pool()
        if not pool:
            await reply_func("❌ Database bağlantısı yok!")
            return
        
        async with pool.acquire() as conn:
            # Bekleyen siparişleri al
            orders_query = """
                SELECT o.id, o.order_number, o.user_id, o.product_id, o.quantity, 
                       o.total_amount, o.status, o.created_at, o.admin_notes,
                       p.name as product_name, p.price as product_price,
                       u.username, u.first_name
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.status = 'pending'
                ORDER BY o.created_at DESC
                LIMIT 20
            """
            orders = await conn.fetch(orders_query)
            
            if not orders:
                await reply_func("📋 **Bekleyen Sipariş Yok**\n\n✅ Tüm siparişler işlenmiş!")
                return
            
            # Sipariş listesini oluştur
            orders_text = f"📋 **Bekleyen Siparişler** ({len(orders)} adet)\n\n"
            
            for order in orders:
                username = order['username'] or order['first_name'] or "Anonim"
                created_date = order['created_at'].strftime('%d.%m %H:%M')
                total_amount = order['total_amount']
                product_name = order['product_name']
                quantity = order['quantity']
                
                orders_text += f"🆔 **Sipariş #{order['order_number']}**\n"
                orders_text += f"👤 **Müşteri:** @{username}\n"
                orders_text += f"📦 **Ürün:** {product_name}\n"
                orders_text += f"📊 **Adet:** {quantity}\n"
                orders_text += f"💰 **Tutar:** {total_amount:.2f} KP\n"
                orders_text += f"📅 **Tarih:** {created_date}\n"
                orders_text += f"📝 **Not:** {order.get('admin_notes', 'Yok')}\n\n"
            
            # Butonları oluştur
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            
            for order in orders:
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"✅ Onayla #{order['order_number']}", 
                        callback_data=f"admin_order_approve_{order['id']}"
                    ),
                    InlineKeyboardButton(
                        text=f"❌ Reddet #{order['order_number']}", 
                        callback_data=f"admin_order_reject_{order['id']}"
                    )
                ])
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_orders_refresh")
            ])
            
            await reply_func(orders_text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"❌ Sipariş listesi hatası: {e}")
        await reply_func("❌ Sipariş listesi yüklenemedi!")


async def send_orders_list_direct(user_id: int) -> None:
    """Sipariş listesini doğrudan kullanıcıya gönder"""
    try:
        if not _bot_instance:
            logger.error("❌ Bot instance yok!")
            return
        
        pool = await get_db_pool()
        if not pool:
            await _bot_instance.send_message(user_id, "❌ Database bağlantısı yok!")
            return
        
        async with pool.acquire() as conn:
            # Bekleyen siparişleri al
            orders_query = """
                SELECT o.id, o.order_number, o.user_id, o.product_id, o.quantity, 
                       o.total_amount, o.status, o.created_at, o.admin_notes,
                       p.name as product_name, p.price as product_price,
                       u.username, u.first_name
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.status = 'pending'
                ORDER BY o.created_at DESC
                LIMIT 20
            """
            orders = await conn.fetch(orders_query)
            
            if not orders:
                await _bot_instance.send_message(user_id, "📋 **Bekleyen Sipariş Yok**\n\n✅ Tüm siparişler işlenmiş!")
                return
            
            # Sipariş listesini oluştur
            orders_text = f"📋 **Bekleyen Siparişler** ({len(orders)} adet)\n\n"
            
            for order in orders:
                username = order['username'] or order['first_name'] or "Anonim"
                created_date = order['created_at'].strftime('%d.%m %H:%M')
                total_amount = order['total_amount']
                product_name = order['product_name']
                quantity = order['quantity']
                
                orders_text += f"🆔 **Sipariş #{order['order_number']}**\n"
                orders_text += f"👤 **Müşteri:** @{username}\n"
                orders_text += f"📦 **Ürün:** {product_name}\n"
                orders_text += f"📊 **Adet:** {quantity}\n"
                orders_text += f"💰 **Tutar:** {total_amount:.2f} KP\n"
                orders_text += f"📅 **Tarih:** {created_date}\n"
                orders_text += f"📝 **Not:** {order.get('admin_notes', 'Yok')}\n\n"
            
            # Butonları oluştur
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            
            for order in orders:
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"✅ Onayla #{order['order_number']}", 
                        callback_data=f"admin_order_approve_{order['id']}"
                    ),
                    InlineKeyboardButton(
                        text=f"❌ Reddet #{order['order_number']}", 
                        callback_data=f"admin_order_reject_{order['id']}"
                    )
                ])
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="🔄 Yenile", callback_data="admin_orders_refresh")
            ])
            
            await _bot_instance.send_message(user_id, orders_text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"❌ Sipariş listesi hatası: {e}")
        await _bot_instance.send_message(user_id, "❌ Sipariş listesi yüklenemedi!")


async def process_approve_order(user_id: int, order_number: str, reply_func) -> None:
    """Sipariş onaylama işlemi"""
    try:
        pool = await get_db_pool()
        if not pool:
            await reply_func("❌ Database bağlantısı yok!")
            return
        
        async with pool.acquire() as conn:
            # Sipariş ID'sini bul
            order_id = await get_order_id_by_number(order_number)
            if not order_id:
                await reply_func(f"❌ Sipariş bulunamadı: #{order_number}")
                return
            
            # Siparişi onayla
            update_query = """
                UPDATE market_orders 
                SET status = 'approved', 
                    approved_at = NOW(),
                    admin_id = $1,
                    admin_notes = 'Admin tarafından onaylandı'
                WHERE id = $2 AND status = 'pending'
            """
            result = await conn.execute(update_query, user_id, order_id)
            
            if result == "UPDATE 0":
                await reply_func(f"❌ Sipariş onaylanamadı: #{order_number}\n\nSipariş zaten işlenmiş veya mevcut değil!")
                return
            
            # Sipariş bilgilerini al
            order_query = """
                SELECT o.*, p.name as product_name, p.delivery_content,
                       u.username, u.first_name, u.kirve_points
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.id = $1
            """
            order = await conn.fetchrow(order_query, order_id)
            
            if not order:
                await reply_func("❌ Sipariş bilgileri alınamadı!")
                return
            
            # Müşteriye bildirim gönder
            delivery_content = order['delivery_content'] or "Ürün hazırlanıyor..."
            await notify_customer_order_approved(order, delivery_content)
            
            await reply_func(f"✅ **Sipariş Onaylandı!**\n\n🆔 **Sipariş:** #{order_number}\n👤 **Müşteri:** @{order['username'] or order['first_name']}\n📦 **Ürün:** {order['product_name']}\n💰 **Tutar:** {order['total_amount']:.2f} KP\n\n📝 **Teslimat:** {delivery_content}")
            
    except Exception as e:
        logger.error(f"❌ Sipariş onaylama hatası: {e}")
        await reply_func("❌ Sipariş onaylama başarısız!")


async def process_approve_order_direct(user_id: int, order_number: str) -> None:
    """Sipariş onaylama işlemi (doğrudan)"""
    try:
        if not _bot_instance:
            logger.error("❌ Bot instance yok!")
            return
        
        pool = await get_db_pool()
        if not pool:
            await _bot_instance.send_message(user_id, "❌ Database bağlantısı yok!")
            return
        
        async with pool.acquire() as conn:
            # Sipariş ID'sini bul
            order_id = await get_order_id_by_number(order_number)
            if not order_id:
                await _bot_instance.send_message(user_id, f"❌ Sipariş bulunamadı: #{order_number}")
                return
            
            # Siparişi onayla
            update_query = """
                UPDATE market_orders 
                SET status = 'approved', 
                    approved_at = NOW(),
                    admin_id = $1,
                    admin_notes = 'Admin tarafından onaylandı'
                WHERE id = $2 AND status = 'pending'
            """
            result = await conn.execute(update_query, user_id, order_id)
            
            if result == "UPDATE 0":
                await _bot_instance.send_message(user_id, f"❌ Sipariş onaylanamadı: #{order_number}\n\nSipariş zaten işlenmiş veya mevcut değil!")
                return
            
            # Sipariş bilgilerini al
            order_query = """
                SELECT o.*, p.name as product_name, p.delivery_content,
                       u.username, u.first_name, u.kirve_points
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.id = $1
            """
            order = await conn.fetchrow(order_query, order_id)
            
            if not order:
                await _bot_instance.send_message(user_id, "❌ Sipariş bilgileri alınamadı!")
                return
            
            # Müşteriye bildirim gönder
            delivery_content = order['delivery_content'] or "Ürün hazırlanıyor..."
            await notify_customer_order_approved(order, delivery_content)
            
            await _bot_instance.send_message(user_id, f"✅ **Sipariş Onaylandı!**\n\n🆔 **Sipariş:** #{order_number}\n👤 **Müşteri:** @{order['username'] or order['first_name']}\n📦 **Ürün:** {order['product_name']}\n💰 **Tutar:** {order['total_amount']:.2f} KP\n\n📝 **Teslimat:** {delivery_content}")
            
    except Exception as e:
        logger.error(f"❌ Sipariş onaylama hatası: {e}")
        await _bot_instance.send_message(user_id, "❌ Sipariş onaylama başarısız!")


async def process_reject_order(user_id: int, order_number: str, reply_func) -> None:
    """Sipariş reddetme işlemi"""
    try:
        pool = await get_db_pool()
        if not pool:
            await reply_func("❌ Database bağlantısı yok!")
            return
        
        async with pool.acquire() as conn:
            # Sipariş ID'sini bul
            order_id = await get_order_id_by_number(order_number)
            if not order_id:
                await reply_func(f"❌ Sipariş bulunamadı: #{order_number}")
                return
            
            # Sipariş bilgilerini al
            order_query = """
                SELECT o.*, p.name as product_name,
                       u.username, u.first_name, u.kirve_points
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.id = $1
            """
            order = await conn.fetchrow(order_query, order_id)
            
            if not order:
                await reply_func("❌ Sipariş bilgileri alınamadı!")
                return
            
            # Para iadesi yap
            refund_amount = order['total_amount']
            new_balance = order['kirve_points'] + refund_amount
            
            # Kullanıcı bakiyesini güncelle
            balance_query = "UPDATE users SET kirve_points = $1 WHERE user_id = $2"
            await conn.execute(balance_query, new_balance, order['user_id'])
            
            # Siparişi reddet
            reject_query = """
                UPDATE market_orders 
                SET status = 'rejected', 
                    rejected_at = NOW(),
                    admin_id = $1,
                    admin_notes = 'Admin tarafından reddedildi'
                WHERE id = $2 AND status = 'pending'
            """
            result = await conn.execute(reject_query, user_id, order_id)
            
            if result == "UPDATE 0":
                await reply_func(f"❌ Sipariş reddedilemedi: #{order_number}\n\nSipariş zaten işlenmiş veya mevcut değil!")
                return
            
            # Müşteriye bildirim gönder
            await notify_customer_order_rejected(order, refund_amount)
            
            await reply_func(f"❌ **Sipariş Reddedildi!**\n\n🆔 **Sipariş:** #{order_number}\n👤 **Müşteri:** @{order['username'] or order['first_name']}\n📦 **Ürün:** {order['product_name']}\n💰 **İade:** {refund_amount:.2f} KP\n\n💡 Para müşteri hesabına iade edildi!")
            
    except Exception as e:
        logger.error(f"❌ Sipariş reddetme hatası: {e}")
        await reply_func("❌ Sipariş reddetme başarısız!")


async def process_reject_order_direct(user_id: int, order_number: str) -> None:
    """Sipariş reddetme işlemi (doğrudan)"""
    try:
        if not _bot_instance:
            logger.error("❌ Bot instance yok!")
            return
        
        pool = await get_db_pool()
        if not pool:
            await _bot_instance.send_message(user_id, "❌ Database bağlantısı yok!")
            return
        
        async with pool.acquire() as conn:
            # Sipariş ID'sini bul
            order_id = await get_order_id_by_number(order_number)
            if not order_id:
                await _bot_instance.send_message(user_id, f"❌ Sipariş bulunamadı: #{order_number}")
                return
            
            # Sipariş bilgilerini al
            order_query = """
                SELECT o.*, p.name as product_name,
                       u.username, u.first_name, u.kirve_points
                FROM market_orders o
                JOIN market_products p ON o.product_id = p.id
                JOIN users u ON o.user_id = u.user_id
                WHERE o.id = $1
            """
            order = await conn.fetchrow(order_query, order_id)
            
            if not order:
                await _bot_instance.send_message(user_id, "❌ Sipariş bilgileri alınamadı!")
                return
            
            # Para iadesi yap
            refund_amount = order['total_amount']
            new_balance = order['kirve_points'] + refund_amount
            
            # Kullanıcı bakiyesini güncelle
            balance_query = "UPDATE users SET kirve_points = $1 WHERE user_id = $2"
            await conn.execute(balance_query, new_balance, order['user_id'])
            
            # Siparişi reddet
            reject_query = """
                UPDATE market_orders 
                SET status = 'rejected', 
                    rejected_at = NOW(),
                    admin_id = $1,
                    admin_notes = 'Admin tarafından reddedildi'
                WHERE id = $2 AND status = 'pending'
            """
            result = await conn.execute(reject_query, user_id, order_id)
            
            if result == "UPDATE 0":
                await _bot_instance.send_message(user_id, f"❌ Sipariş reddedilemedi: #{order_number}\n\nSipariş zaten işlenmiş veya mevcut değil!")
                return
            
            # Müşteriye bildirim gönder
            await notify_customer_order_rejected(order, refund_amount)
            
            await _bot_instance.send_message(user_id, f"❌ **Sipariş Reddedildi!**\n\n🆔 **Sipariş:** #{order_number}\n👤 **Müşteri:** @{order['username'] or order['first_name']}\n📦 **Ürün:** {order['product_name']}\n💰 **İade:** {refund_amount:.2f} KP\n\n💡 Para müşteri hesabına iade edildi!")
            
    except Exception as e:
        logger.error(f"❌ Sipariş reddetme hatası: {e}")
        await _bot_instance.send_message(user_id, "❌ Sipariş reddetme başarısız!")


async def get_order_id_by_number(order_number: str) -> Optional[int]:
    """Sipariş numarasından ID bul"""
    try:
        pool = await get_db_pool()
        if not pool:
            return None
        
        async with pool.acquire() as conn:
            query = "SELECT id FROM market_orders WHERE order_number = $1"
            result = await conn.fetchval(query, order_number)
            return result
            
    except Exception as e:
        logger.error(f"❌ Sipariş ID bulma hatası: {e}")
        return None


async def notify_customer_order_approved(order: Dict, delivery_content: str) -> None:
    """Müşteriye onay bildirimi gönder"""
    try:
        if not _bot_instance:
            return
        
        message = f"""
✅ <b>Siparişiniz Onaylandı!</b>

🆔 <b>Sipariş:</b> #{order['order_number']}
📦 <b>Ürün:</b> {order['product_name']}
📊 <b>Adet:</b> {order['quantity']}
💰 <b>Tutar:</b> {order['total_amount']:.2f} KP

📝 <b>Teslimat Bilgileri:</b>
{delivery_content}

🎉 <b>Siparişiniz başarıyla onaylandı!</b>
        """
        
        await _bot_instance.send_message(order['user_id'], message, parse_mode="HTML")
        logger.info(f"✅ Müşteri onay bildirimi gönderildi - User: {order['user_id']}")
        
    except Exception as e:
        logger.error(f"❌ Müşteri onay bildirim hatası: {e}")


async def notify_customer_order_rejected(order: Dict, refund_amount: float) -> None:
    """Müşteriye red bildirimi gönder"""
    try:
        if not _bot_instance:
            return
        
        message = f"""
❌ <b>Siparişiniz Reddedildi</b>

🆔 <b>Sipariş:</b> #{order['order_number']}
📦 <b>Ürün:</b> {order['product_name']}
📊 <b>Adet:</b> {order['quantity']}
💰 <b>Tutar:</b> {order['total_amount']:.2f} KP

💸 <b>İade Edilen:</b> {refund_amount:.2f} KP
• Paranız hesabınıza iade edildi

❓ <b>İptal Sebebi:</b>
{order.get('admin_notes', 'Belirtilmedi')}

💡 <b>Başka ürünler için market'i tekrar ziyaret edebilirsiniz!</b>
        """
        
        await _bot_instance.send_message(order['user_id'], message, parse_mode="HTML")
        logger.info(f"❌ Müşteri red bildirimi gönderildi - User: {order['user_id']}")
        
    except Exception as e:
        logger.error(f"❌ Müşteri red bildirim hatası: {e}")


# ==============================================
# CALLBACK HANDLER'LARI
# ==============================================

@router.callback_query(lambda c: c.data.startswith("admin_order_"))
async def admin_order_callback_handler(callback: types.CallbackQuery) -> None:
    """Admin sipariş callback handler"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        action = callback.data
        
        if action == "admin_orders_refresh":
            await refresh_orders_list(callback)
        elif action.startswith("admin_order_approve_"):
            order_id = int(action.split("_")[-1])
            await approve_order_callback(callback, order_id)
        elif action.startswith("admin_order_reject_"):
            order_id = int(action.split("_")[-1])
            await reject_order_callback(callback, order_id)
        else:
            await callback.answer("❌ Bilinmeyen işlem!")
            
    except Exception as e:
        logger.error(f"❌ Admin order callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)


async def refresh_orders_list(callback: types.CallbackQuery) -> None:
    """Sipariş listesini yenile"""
    await callback.answer("🔄 Sipariş listesi yenileniyor...")
    await send_orders_list_direct(callback.from_user.id)
    await callback.message.delete()


async def approve_order_callback(callback: types.CallbackQuery, order_id: int) -> None:
    """Callback ile sipariş onayla"""
    try:
        from handlers.market_system import approve_order
        result = await approve_order(order_id, callback.from_user.id)
        
        if not result['success']:
            await callback.answer(f"❌ {result['error']}", show_alert=True)
            return
        
        await callback.answer("✅ Sipariş onaylandı!")
        
        # Müşteriye bildirim gönder
        await notify_customer_order_approved(result['order'], result['delivery_content'])
        
        # Listeleyi yenile
        await refresh_orders_list(callback)
        
    except Exception as e:
        logger.error(f"❌ Callback sipariş onaylama hatası: {e}")
        await callback.answer("❌ Onaylama hatası!", show_alert=True)


async def reject_order_callback(callback: types.CallbackQuery, order_id: int) -> None:
    """Callback ile sipariş reddet"""
    try:
        from handlers.market_system import reject_order
        result = await reject_order(order_id, callback.from_user.id, "Admin tarafından reddedildi")
        
        if not result['success']:
            await callback.answer(f"❌ {result['error']}", show_alert=True)
            return
        
        await callback.answer("❌ Sipariş reddedildi ve para iade edildi!")
        
        # Müşteriye bildirim gönder
        await notify_customer_order_rejected(result['order'], result['refund_amount'])
        
        # Listeyi yenile
        await refresh_orders_list(callback)
        
    except Exception as e:
        logger.error(f"❌ Callback sipariş reddetme hatası: {e}")
        await callback.answer("❌ Reddetme hatası!", show_alert=True)

# @router.message(Command("market"))  # MANUEL KAYITLI - ROUTER DEVRESİ DIŞI
async def market_management_command(message: Message) -> None:
    """Market yönetim komutu"""
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
                logger.info(f"🔇 Market yönetim komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_market_management_privately(user_id)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        logger.info(f"🛍️ Market yönetim komutu ÖZELİNDE - User: {message.from_user.first_name} ({user_id})")
        
        # Market yönetim menüsünü göster
        await show_market_management_menu(user_id, message.reply)
        
    except Exception as e:
        logger.error(f"❌ Market yönetim komut hatası: {e}")
        if message.chat.type == "private":
            await message.reply("❌ Market yönetim menüsü yüklenemedi!")

async def _send_market_management_privately(user_id: int):
    """Market yönetim menüsünü özel mesajla gönder"""
    try:
        # Bot instance'ını güvenli şekilde al
        bot = get_bot_instance()
        if bot:
            await show_market_management_menu(user_id, None)
            logger.info(f"✅ Market yönetim menüsü özel mesajla gönderildi: {user_id}")
        else:
            logger.error(f"❌ Bot instance bulunamadı - User: {user_id}")
    except Exception as e:
        logger.error(f"❌ Market yönetim menüsü gönderilemedi: {e}")

async def show_market_management_menu(user_id: int, reply_func=None):
    """Market yönetim ana menüsü"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Ürün Ekle", callback_data="market_add_product"),
            InlineKeyboardButton(text="📋 Ürün Listesi", callback_data="market_list_products")
        ],
        [
            InlineKeyboardButton(text="📦 Siparişler", callback_data="market_orders"),
            InlineKeyboardButton(text="✅ Onaylanan", callback_data="market_approved")
        ],
        [
            InlineKeyboardButton(text="❌ Reddedilen", callback_data="market_rejected"),
            InlineKeyboardButton(text="📊 Rapor", callback_data="market_report")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
🛍️ **Market Yönetim Sistemi**

**📋 Kullanılabilir İşlemler:**

➕ **Ürün Ekle:** Yeni ürün ekleme
📋 **Ürün Listesi:** Mevcut ürünleri görüntüleme
📦 **Siparişler:** Bekleyen siparişleri yönetme
✅ **Onaylanan:** Onaylanan siparişler
❌ **Reddedilen:** Reddedilen siparişler
📊 **Rapor:** Market istatistikleri

**💡 Hangi işlemi yapmak istiyorsun?**
    """
    
    if reply_func:
        await reply_func(response, parse_mode="Markdown", reply_markup=keyboard)
    else:
        # Bot instance'ını güvenli şekilde al
        bot = get_bot_instance()
        if bot:
            try:
                await bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=keyboard)
                logger.info(f"✅ Market yönetim menüsü gönderildi - User: {user_id}")
            except Exception as e:
                logger.error(f"❌ Market menü gönderme hatası: {e}")
        else:
            logger.error(f"❌ Bot instance bulunamadı - User: {user_id}")

# Callback'ten çağrıldığında mesajı güncellemek için yeni fonksiyon
async def show_market_management_menu_callback(callback: CallbackQuery):
    """Market yönetim menüsü - basit versiyon"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Ürün Ekle", callback_data="market_add_product"),
            InlineKeyboardButton(text="📋 Ürün Listesi", callback_data="market_list_products")
        ],
        [
            InlineKeyboardButton(text="📦 Siparişler", callback_data="market_orders"),
            InlineKeyboardButton(text="✅ Onaylanan", callback_data="market_approved")
        ],
        [
            InlineKeyboardButton(text="❌ Reddedilen", callback_data="market_rejected"),
            InlineKeyboardButton(text="📊 Rapor", callback_data="market_report")
        ],
        [
            InlineKeyboardButton(text="⬅️ Geri", callback_data="admin_back")
        ]
    ])
    
    response = """
🛍️ **Market Yönetim Sistemi**

**📋 Kullanılabilir İşlemler:**

➕ **Ürün Ekle:** Yeni ürün ekleme
📋 **Ürün Listesi:** Mevcut ürünleri görüntüleme
📦 **Siparişler:** Bekleyen siparişleri yönetme
✅ **Onaylanan:** Onaylanan siparişler
❌ **Reddedilen:** Reddedilen siparişler
📊 **Rapor:** Market istatistikleri

**💡 Hangi işlemi yapmak istiyorsun?**
    """
    
    await callback.message.edit_text(
        response,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ==============================================
# ÜRÜN EKLEME SİSTEMİ
# ==============================================

async def start_product_creation(callback: CallbackQuery):
    """Ürün ekleme sürecini başlat"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        # Ürün oluşturma verilerini başlat
        product_creation_data[user_id] = {
            "step": "name",
            "created_at": datetime.now()
        }
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_creation")]
        ])
        
        response = """
➕ **Yeni Ürün Ekleme**

**📝 Adım 1: Ürün Adı**

Lütfen ürün adını yazın:
Örnek: "Steam 50 TL Kartı", "Netflix 1 Aylık", "Spotify Premium"

**💡 İpucu:** Açık ve anlaşılır bir isim yazın.
        """
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Ürün ekleme başlatıldı - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ürün ekleme başlatma hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def handle_product_creation_input(message: Message):
    """Ürün oluşturma input handler'ı"""
    try:
        user_id = message.from_user.id
        
        logger.info(f"🔍 Product input handler çağrıldı - User: {user_id}, Text: {message.text}")
        
        # Admin kontrolü
        config = get_config()
        if user_id != config.ADMIN_USER_ID:
            logger.info(f"❌ Admin değil - User: {user_id}")
            return
        
        logger.info(f"🔍 Product creation data kontrolü - User: {user_id}, Data: {product_creation_data.get(user_id, 'YOK')}")
        
        # State kontrolü
        if user_id in product_creation_data:
            current_step = product_creation_data[user_id].get('step', 'BİLİNMİYOR')
            logger.info(f"🔍 Current step: {current_step} - User: {user_id}")
        else:
            logger.info(f"🔍 User not in product creation state - User: {user_id}")
        
        # Kullanıcının ürün oluşturma sürecinde olup olmadığını kontrol et
        if user_id in product_creation_data:
            logger.info(f"🛍️ Product creation input - User: {user_id}")
            product_info = product_creation_data[user_id]
            step = product_info.get("step")
            
            logger.info(f"🛍️ Product input - User: {user_id}, Step: {step}, Text: {message.text}")
            
            if step == "name":
                await handle_product_name_input(message, product_info)
            elif step == "description":
                await handle_product_description_input(message, product_info)
            elif step == "price":
                await handle_product_price_input(message, product_info)
            elif step == "stock":
                await handle_product_stock_input(message, product_info)
            elif step == "category":
                # Bu step callback ile çalışır, mesaj input'u kabul etme
                await message.reply("❌ Lütfen kategoriyi yukarıdaki butonlardan seçin!")
                return
            elif step == "site_name":
                await handle_product_site_name_input(message, product_info)
            elif step == "site_link":
                await handle_product_site_input(message, product_info)
            else:
                logger.info(f"❌ Bilinmeyen step: {step} - User: {user_id}")
            return
        
        # Ürün düzenleme sürecinde mi?
        if user_id in product_edit_data:
            logger.info(f"✏️ Product edit input - User: {user_id}")
            await handle_product_edit_input(message)
            return
        
        # Ürün silme sürecinde mi?
        if user_id in product_delete_data:
            logger.info(f"🗑️ Product delete input - User: {user_id}")
            await handle_product_delete_input(message)
            return
        
        logger.info(f"❌ Product input data yok - User: {user_id}")
        return  # Normal mesaj, bu handler'ı atla
        
    except Exception as e:
        logger.error(f"❌ Product input handler hatası: {e}")

async def handle_product_edit_input(message: Message):
    """Ürün düzenleme input handler'ı"""
    try:
        user_id = message.from_user.id
        
        # Debug: State kontrolü
        logger.info(f"🔍 Product edit input çağrıldı - User: {user_id}, Text: {message.text}")
        logger.info(f"🔍 Product edit data keys: {list(product_edit_data.keys())}")
        
        if user_id not in product_edit_data:
            logger.warning(f"⚠️ User {user_id} product_edit_data'da bulunamadı!")
            return
        
        edit_data = product_edit_data[user_id]
        step = edit_data.get("step")
        
        logger.info(f"✏️ Product edit input - User: {user_id}, Step: {step}, Text: {message.text}")
        
        if step == "waiting_for_product_id":
            await handle_edit_product_id_input(message, edit_data)
        elif step == "edit_name":
            await handle_edit_product_name_input(message, edit_data)
        elif step == "edit_description":
            await handle_edit_product_description_input(message, edit_data)
        elif step == "edit_price":
            await handle_edit_product_price_input(message, edit_data)
        elif step == "edit_stock":
            await handle_edit_product_stock_input(message, edit_data)
        elif step == "edit_site_name":
            await handle_edit_product_site_name_input(message, edit_data)
        elif step == "edit_site_link":
            await handle_edit_product_site_link_input(message, edit_data)
        else:
            logger.warning(f"⚠️ Bilinmeyen edit step: {step}")
            
    except Exception as e:
        logger.error(f"❌ Product edit input hatası: {e}")

async def handle_product_delete_input(message: Message):
    """Ürün silme input handler'ı"""
    try:
        user_id = message.from_user.id
        delete_data = product_delete_data[user_id]
        step = delete_data.get("step")
        
        logger.info(f"🗑️ Product delete input - User: {user_id}, Step: {step}, Text: {message.text}")
        
        if step == "waiting_for_product_id":
            await handle_delete_product_id_input(message, delete_data)
        else:
            logger.warning(f"⚠️ Bilinmeyen delete step: {step}")
            
    except Exception as e:
        logger.error(f"❌ Product delete input hatası: {e}")

async def handle_product_name_input(message: Message, product_info: Dict):
    """Ürün adı input handler'ı"""
    try:
        user_id = message.from_user.id
        logger.info(f"🔍 Product name input handler çağrıldı - User: {user_id}, Text: {message.text}")
        
        if len(message.text) < 3:
            await message.reply("❌ Ürün adı en az 3 karakter olmalı!")
            return
        
        product_info["name"] = message.text
        product_info["step"] = "description"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_creation")]
        ])
        
        await message.reply(
            "📝 **Adım 2: Ürün Açıklaması**\n\n"
            "Lütfen ürün açıklamasını yazın:\n"
            "Örnek: \"Steam hesabınıza yüklenebilir dijital kart\"\n\n"
            "**💡 İpucu:** Detaylı ve açıklayıcı bir açıklama yazın.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Product name input hatası: {e}")

async def handle_product_description_input(message: Message, product_info: Dict):
    """Ürün açıklaması input handler'ı"""
    try:
        user_id = message.from_user.id
        logger.info(f"🔍 Product description input handler çağrıldı - User: {user_id}, Text: {message.text}")
        
        if len(message.text) < 10:
            await message.reply("❌ Ürün açıklaması en az 10 karakter olmalı!")
            return
        
        product_info["description"] = message.text
        product_info["step"] = "price"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_creation")]
        ])
        
        await message.reply(
            "💰 **Adım 3: Ürün Fiyatı**\n\n"
            "Lütfen ürün fiyatını yazın (KP cinsinden):\n"
            "Örnek: 50, 25.5, 100\n\n"
            "**💡 İpucu:** Sadece sayı yazın, birim yazmayın.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Product description input hatası: {e}")

async def handle_product_price_input(message: Message, product_info: Dict):
    """Ürün fiyatı input handler'ı"""
    try:
        user_id = message.from_user.id
        logger.info(f"🔍 Product price input handler çağrıldı - User: {user_id}, Text: {message.text}")
        
        try:
            price = float(message.text.strip())
            if price <= 0:
                await message.reply("❌ Fiyat pozitif olmalı!")
                return
        except ValueError:
            await message.reply("❌ Geçersiz fiyat! Örnek: 50 veya 25.5")
            return
        
        product_info["price"] = price
        product_info["step"] = "stock"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_creation")]
        ])
        
        await message.reply(
            "📦 **Adım 4: Stok Miktarı**\n\n"
            "Lütfen stok miktarını yazın:\n"
            "Örnek: 10, 50, 100\n\n"
            "**💡 İpucu:** Sadece sayı yazın.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Product price input hatası: {e}")

async def handle_product_stock_input(message: Message, product_info: Dict):
    """Ürün stok input handler'ı"""
    try:
        user_id = message.from_user.id
        logger.info(f"🔍 Product stock input handler çağrıldı - User: {user_id}, Text: {message.text}")
        
        try:
            stock = int(message.text.strip())
            if stock < 0:
                await message.reply("❌ Stok sayısı negatif olamaz!")
                return
        except ValueError:
            await message.reply("❌ Geçersiz stok sayısı! Örnek: `10`")
            return
        
        product_info["stock"] = stock
        product_info["step"] = "category"  # Direkt kategori seçimine geç
        
        # Kategori seçim menüsü
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Freespinler", callback_data="market_category_freespin")],
            [InlineKeyboardButton(text="💰 Site Bakiyeleri", callback_data="market_category_balance")],
            [InlineKeyboardButton(text="🎁 Bonus Paketleri", callback_data="market_category_bonus")],
            [InlineKeyboardButton(text="👑 VIP Ürünler", callback_data="market_category_vip")],
            [InlineKeyboardButton(text="📦 Diğer Ürünler", callback_data="market_category_other")],
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_creation")]
        ])
        
        await message.reply(
            "📂 **Adım 5: Ürün Kategorisi**\n\n"
            "Lütfen ürün kategorisini seçin:\n\n"
            "**💡 Kategoriler:**\n"
            "• 🎰 Freespinler (Slot siteleri için)\n"
            "• 💰 Site Bakiyeleri (Casino siteleri için)\n"
            "• 🎁 Bonus Paketleri (Çeşitli siteler için)\n"
            "• 👑 VIP Ürünler (Özel ayrıcalıklar)\n"
            "• 📦 Diğer Ürünler (Genel ürünler)",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Product stock input hatası: {e}")

async def handle_product_site_name_input(message: Message, product_info: Dict):
    """Ürün site adı input handler'ı"""
    try:
        user_id = message.from_user.id
        logger.info(f"🔍 Product site name input handler çağrıldı - User: {user_id}, Text: {message.text}")
        
        if len(message.text) < 2:
            await message.reply("❌ Site adı en az 2 karakter olmalı!")
            return
        
        product_info["site_name"] = message.text
        product_info["step"] = "site_link"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_creation")]
        ])
        
        await message.reply(
            "🔗 **Adım 6: Site Linki**\n\n"
            "Lütfen ürünün satıldığı site linkini yazın:\n"
            "Örnek: https://www.steam.com, https://www.netflix.com\n\n"
            "**💡 İpucu:** Tam URL adresi yazın (http:// veya https:// ile başlamalı).",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Product site name input hatası: {e}")



async def handle_product_site_input(message: Message, product_info: Dict):
    """Ürün site linki input handler'ı"""
    try:
        user_id = message.from_user.id
        
        if len(message.text) < 5:
            await message.reply("❌ Site linki en az 5 karakter olmalı!")
            return
        
        # Basit URL kontrolü
        if not message.text.startswith(('http://', 'https://', 'www.')):
            await message.reply("❌ Geçersiz site linki! Örnek: https://example.com")
            return
        
        product_info["site_link"] = message.text
        product_info["step"] = "confirm"
        
        # Ürün bilgilerini göster ve onay iste
        response = f"""
✅ **Ürün Bilgileri Onayı**

**📋 Ürün Detayları:**
• **Ad:** {product_info.get('name', 'Bilinmiyor')}
• **Açıklama:** {product_info.get('description', 'Bilinmiyor')}
• **Fiyat:** {product_info.get('price', 0):.2f} KP
• **Stok:** {product_info.get('stock', 0)} adet
• **Site Adı:** {product_info.get('site_name', 'Bilinmiyor')}
• **Site Linki:** {product_info.get('site_link', 'Bilinmiyor')}

**💡 Ürünü oluşturmak için onaylayın.**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Onayla", callback_data="market_confirm_creation")],
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_creation")]
        ])
        
        await message.reply(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Product site input hatası: {e}")

async def handle_product_category_input(message: Message, product_info: Dict):
    """Ürün kategori input handler'ı - Bu callback ile çalışır"""
    pass  # Bu callback ile çalışacak

async def confirm_product_creation(callback: CallbackQuery):
    """Ürün oluşturmayı onayla"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        if user_id not in product_creation_data:
            await callback.answer("❌ Ürün oluşturma verisi bulunamadı!", show_alert=True)
            return
        
        product_info = product_creation_data[user_id]
        
        # Ürünü database'e kaydet
        success = await create_product_in_db(product_info, user_id)
        
        if success:
            # Başarı mesajı
            response = f"""
✅ **Ürün Başarıyla Oluşturuldu!**

**📋 Ürün Detayları:**
• **Ad:** {product_info.get('name', 'Bilinmiyor')}
• **Açıklama:** {product_info.get('description', 'Bilinmiyor')}
• **Fiyat:** {product_info.get('price', 0):.2f} KP
• **Stok:** {product_info.get('stock', 0)} adet
• **Kategori:** {product_info.get('category', 'Bilinmiyor')}

**💡 Ürün artık markette görünür durumda!**
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍️ Market Yönetimi", callback_data="market_management")]
            ])
            
            await callback.message.edit_text(
                response,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            logger.info(f"✅ Ürün başarıyla oluşturuldu: {product_info.get('name')}")
            
        else:
            await callback.message.edit_text(
                "❌ **Ürün oluşturulurken hata oluştu!**\n\n"
                "Lütfen tekrar deneyin veya sistem yöneticisi ile iletişime geçin.",
                parse_mode="Markdown"
            )
        
        # Geçici veriyi temizle
        del product_creation_data[user_id]
        
    except Exception as e:
        logger.error(f"❌ Product confirmation hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def create_product_in_db(product_info: Dict, admin_id: int) -> bool:
    """Ürünü database'e kaydet"""
    try:
        logger.info(f"🛍️ Product creation başlatılıyor: {product_info}")
        
        # Database pool'u güvenli şekilde al
        try:
            pool = await get_db_pool()
            if not pool:
                logger.error("❌ Database pool yok!")
                return False
        except Exception as e:
            logger.error(f"❌ Database import hatası: {e}")
            return False
        
        async with pool.acquire() as conn:
            # Kategori ID'sini al veya oluştur
            category_name = product_info.get('category', 'Diğer')
            category_emoji = {
                'freespin': '🎰',
                'balance': '💰',
                'bonus': '🎁',
                'vip': '👑',
                'other': '📦'
            }.get(category_name, '📦')
            
            # Kategoriyi kontrol et, yoksa oluştur
            category_id = await conn.fetchval("""
                SELECT id FROM market_categories WHERE name = $1
            """, category_name)
            
            if not category_id:
                category_id = await conn.fetchval("""
                    INSERT INTO market_categories (name, description, emoji) VALUES ($1, $2, $3) RETURNING id
                """, category_name, f"{category_name} kategorisi", category_emoji)
            
            # Ürünü ekle
            site_name = product_info.get('site_name')
            if not site_name or site_name == 'None':
                site_name = 'Bilinmiyor'
                
            await conn.execute("""
                INSERT INTO market_products (name, product_name, description, price, stock, category_id, is_active, company_name, site_link, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, product_info.get('name'), product_info.get('name'), product_info.get('description'), 
                 product_info.get('price'), product_info.get('stock'), 
                 category_id, True, site_name, product_info.get('site_link'), admin_id)
            
            logger.info(f"✅ Ürün başarıyla oluşturuldu: {product_info.get('name')}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Create product in db hatası: {e}")
        return False

# ==============================================
# CALLBACK HANDLER'LAR
# ==============================================

@router.callback_query(lambda c: c.data.startswith("market_"))
async def market_callback_handler(callback: CallbackQuery):
    """Market callback handler"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Debug log ekle
        logger.info(f"🔍 Market callback tetiklendi - Action: {callback.data}, User: {user_id}")
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            logger.warning(f"❌ Admin olmayan kullanıcı market callback'e erişmeye çalıştı: {user_id}")
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        action = callback.data
        logger.info(f"🎯 Market callback action: {action}")
        
        if action == "market_add_product":
            logger.info("➕ Ürün ekleme başlatılıyor...")
            await start_product_creation(callback)
        elif action == "market_list_products":
            logger.info("📋 Ürün listesi gösteriliyor...")
            await show_products_list(callback)
        elif action == "market_edit_product":
            logger.info("✏️ Ürün düzenleme menüsü açılıyor...")
            await show_edit_products_menu(callback)
        elif action == "market_delete_product":
            logger.info("🗑️ Ürün silme menüsü açılıyor...")
            await show_delete_products_menu(callback)
        elif action == "market_cancel_edit":
            logger.info("❌ Ürün düzenleme iptal ediliyor...")
            await cancel_product_edit(callback)
        elif action == "market_cancel_delete":
            logger.info("❌ Ürün silme iptal ediliyor...")
            await cancel_product_delete(callback)
        elif action == "market_orders":
            logger.info("📦 Sipariş yönetimi açılıyor...")
            await show_pending_orders(callback)
        elif action == "market_approved":
            logger.info("✅ Onaylanan siparişler gösteriliyor...")
            await show_approved_orders(callback)
        elif action == "market_rejected":
            logger.info("❌ Reddedilen siparişler gösteriliyor...")
            await show_rejected_orders(callback)
        elif action == "market_report":
            logger.info("📊 Market raporu gösteriliyor...")
            await show_market_report(callback)
        elif action == "market_report_refresh":
            logger.info("🔄 Market raporu yenileniyor...")
            await show_market_report(callback)
        # Onaylanan sipariş filtreleri
        elif action.startswith("market_approved_"):
            time_filter = action.replace("market_approved_", "")
            logger.info(f"✅ Onaylanan siparişler filtreleniyor: {time_filter}")
            await show_approved_orders_filtered(callback, time_filter)
        # Reddedilen sipariş filtreleri
        elif action.startswith("market_rejected_"):
            time_filter = action.replace("market_rejected_", "")
            logger.info(f"❌ Reddedilen siparişler filtreleniyor: {time_filter}")
            await show_rejected_orders_filtered(callback, time_filter)
        elif action == "market_cancel_creation":
            logger.info("❌ Ürün oluşturma iptal ediliyor...")
            await cancel_product_creation(callback)
        elif action == "market_management":
            logger.info("🛍️ Market yönetim menüsü açılıyor...")
            await show_market_management_menu_callback(callback)
        elif action == "admin_back":
            logger.info("⬅️ Admin panel'e geri dönülüyor...")
            # Admin panel'e geri dön
            from handlers.admin_panel import show_main_admin_menu
            await show_main_admin_menu(callback)
        elif action.startswith("market_category_"):
            logger.info(f"📂 Kategori seçimi: {action}")
            await handle_category_selection(callback, action)
        elif action.startswith("market_confirm_creation"):
            logger.info("✅ Ürün oluşturma onaylanıyor...")
            await confirm_product_creation(callback)
        elif action.startswith("market_delete_product_"):
            logger.info(f"🗑️ Ürün silme işlemi: {action}")
            await handle_delete_product(callback, action)
        elif action.startswith("order_approve_"):
            order_id = int(action.split("_")[2])
            logger.info(f"✅ Sipariş onaylanıyor: {order_id}")
            await approve_order(callback, order_id)
        elif action.startswith("order_reject_"):
            order_id = int(action.split("_")[2])
            logger.info(f"❌ Sipariş reddediliyor: {order_id}")
            await reject_order(callback, order_id)
        else:
            logger.warning(f"❌ Bilinmeyen market action: {action}")
            await callback.answer("❌ Bu özellik henüz aktif değil!", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Market callback hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def handle_category_selection(callback: CallbackQuery, action: str):
    """Kategori seçim handler'ı"""
    try:
        user_id = callback.from_user.id
        logger.info(f"🔍 Category selection handler çağrıldı - User: {user_id}, Action: {action}")
        
        if user_id not in product_creation_data:
            await callback.answer("❌ Ürün oluşturma sürecinde bulunamadı!", show_alert=True)
            return
        
        product_info = product_creation_data[user_id]
        
        # Kategori adını çıkar
        category_name = action.replace("market_category_", "")
        category_map = {
            'freespin': 'freespin',
            'balance': 'balance', 
            'bonus': 'bonus',
            'vip': 'vip',
            'other': 'other'
        }
        
        if category_name not in category_map:
            await callback.answer("❌ Geçersiz kategori!", show_alert=True)
            return
        
        product_info["category"] = category_name
        product_info["step"] = "site_name"
        
        logger.info(f"✅ Kategori seçildi: {category_name} - User: {user_id}")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_creation")]
        ])
        
        await callback.message.edit_text(
            "🏢 **Adım 6: Site Adı**\n\n"
            "Lütfen ürünün satıldığı site adını yazın:\n"
            "Örnek: `Steam`, `Netflix`, `Spotify`\n\n"
            "**💡 İpucu:** Site adını kısa ve net yazın.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Category selection hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def cancel_product_creation(callback: CallbackQuery):
    """Ürün oluşturmayı iptal et"""
    try:
        user_id = callback.from_user.id
        
        if user_id in product_creation_data:
            del product_creation_data[user_id]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")]
        ])
        
        await callback.message.edit_text(
            "❌ **Ürün oluşturma iptal edildi!**\n\n"
            "İşlem iptal edildi. Ana menüye dönmek için butona basın.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Cancel product creation hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)



async def handle_delete_product(callback: CallbackQuery, action: str):
    """Ürün silme handler'ı"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        product_id = int(action.split('_')[-1])
        
        # Ürünü veritabanından sil
        success = await delete_product_from_db(product_id, user_id)
        
        if success:
            await callback.answer("✅ Ürün başarıyla silindi!", show_alert=True)
            await show_products_list(callback) # Silme sonrası listeyi yeniden göster
        else:
            await callback.answer("❌ Ürün silinirken hata oluştu!", show_alert=True)
            
    except ValueError:
        await callback.answer("❌ Geçersiz ürün ID'si!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ Delete product hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def delete_product_from_db(product_id: int, admin_id: int) -> bool:
    """Ürünü veritabanından sil"""
    try:
        logger.info(f"🗑️ Ürün silme başlatılıyor: {product_id}")
        
        # Database pool'u güvenli şekilde al
        try:
            pool = await get_db_pool()
            if not pool:
                logger.error("❌ Database pool yok!")
                return False
        except Exception as e:
            logger.error(f"❌ Database import hatası: {e}")
            return False
        
        async with pool.acquire() as conn:
            # Ürünü kontrol et ve sil
            product = await conn.fetchrow("""
                SELECT id, is_active FROM market_products WHERE id = $1 AND created_by = $2
            """, product_id, admin_id)
            
            if not product:
                logger.warning(f"❌ Silinmek istenen ürün bulunamadı veya admin yetkisi yok: {product_id}")
                return False
            
            if product['is_active']:
                await conn.execute("""
                    UPDATE market_products SET is_active = FALSE WHERE id = $1
                """, product_id)
                logger.info(f"✅ Ürün pasif edildi: {product_id}")
                return True
            else:
                await conn.execute("""
                    DELETE FROM market_products WHERE id = $1
                """, product_id)
                logger.info(f"✅ Ürün silindi: {product_id}")
                return True
            
    except Exception as e:
        logger.error(f"❌ Delete product from db hatası: {e}")
        return False

# ==============================================
# DİĞER FONKSİYONLAR (PLACEHOLDER)
# ==============================================

async def show_products_list(callback: CallbackQuery):
    """Ürün listesini göster"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        # Database'den ürünleri al
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
        
        async with pool.acquire() as conn:
            products = await conn.fetch("""
                SELECT p.id, p.name, p.description, p.price, p.stock, p.company_link as site_link, p.company_name as site_name, 
                       p.is_active, p.created_at, p.category as category_name
                FROM market_products p
                ORDER BY p.created_at DESC
            """)
        
        if not products:
            await callback.message.edit_text(
                "📋 **Ürün Listesi**\n\n"
                "❌ Henüz hiç ürün eklenmemiş!\n\n"
                "➕ Yeni ürün eklemek için 'Ürün Ekle' butonunu kullanın.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")]
                ])
            )
            return
        
        # Ürün listesini oluştur
        response = "📋 **Mevcut Ürünler**\n\n"
        
        for product in products:
            product_id = product['id']
            name = product['name']
            price = product['price']
            stock = product['stock']
            category_name = product['category_name'] or "Kategorisiz"
            category_emoji = product['category_emoji'] or "📦"
            site_link = product['site_link']
            site_name = product['site_name']
            is_active = product['is_active']
            
            # Durum emoji
            status_emoji = "✅" if is_active else "❌"
            
            response += f"**{status_emoji} ID: {product_id}**\n"
            response += f"**{category_emoji} {name}**\n"
            response += f"**💰 Fiyat:** {price:.2f} KP\n"
            response += f"**📦 Stok:** {stock} adet\n"
            response += f"**{category_emoji} Kategori:** {category_name}\n"
            
            if site_name and site_name != 'Bilinmiyor' and site_name != 'None':
                response += f"**🌐 Site:** {site_name}\n"
            elif site_link and site_link != 'None':
                response += f"**🔗 Link:** {site_link}\n"
            
            response += f"**📅 Eklenme:** {product['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            response += "─" * 30 + "\n\n"
        
        # Sayfalama için butonlar
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Düzenle", callback_data="market_edit_product"),
                InlineKeyboardButton(text="🗑️ Sil", callback_data="market_delete_product")
            ],
            [
                InlineKeyboardButton(text="📦 Stok Yönetimi", callback_data="market_stock_management"),
                InlineKeyboardButton(text="💰 Fiyat Yönetimi", callback_data="market_price_management")
            ],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Show products list hatası: {e}")
        await callback.answer("❌ Ürün listesi yüklenirken hata oluştu!", show_alert=True)

async def show_edit_products_menu(callback: CallbackQuery):
    """Ürün düzenleme menüsünü göster"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        # Database'den ürünleri al
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
        
        async with pool.acquire() as conn:
            products = await conn.fetch("""
                SELECT id, name, price, stock, is_active
                FROM market_products
                ORDER BY created_at DESC
                LIMIT 20
            """)
        
        if not products:
            await callback.message.edit_text(
                "✏️ **Ürün Düzenleme**\n\n"
                "❌ Düzenlenecek ürün bulunamadı!\n\n"
                "➕ Önce ürün ekleyin.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_list_products")]
                ])
            )
            return
        
        # Ürün listesini oluştur
        response = "✏️ **Ürün Düzenleme**\n\n"
        response += "📋 **Mevcut Ürünler:**\n\n"
        
        for product in products:
            product_id = product['id']
            name = product['name']
            price = product['price']
            stock = product['stock']
            is_active = product['is_active']
            
            # Durum emoji
            status_emoji = "✅" if is_active else "❌"
            
            response += f"**{status_emoji} ID: {product_id}**\n"
            response += f"**🛍️ {name}**\n"
            response += f"**💰 Fiyat:** {price:.2f} KP\n"
            response += f"**📦 Stok:** {stock} adet\n"
            response += "─" * 20 + "\n\n"
        
        response += "**Düzenlemek istediğiniz ürünün ID'sini yazın:**"
        
        # Düzenleme durumunu başlat
        product_edit_data[user_id] = {
            "step": "waiting_for_product_id",
            "data": {}
        }
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_edit")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✏️ Ürün düzenleme menüsü gösterildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Show edit products menu hatası: {e}")
        await callback.answer("❌ Ürün düzenleme menüsü yüklenirken hata oluştu!", show_alert=True)

async def show_delete_products_menu(callback: CallbackQuery):
    """Ürün silme menüsünü göster"""
    try:
        user_id = callback.from_user.id
        config = get_config()
        
        # Admin kontrolü
        if user_id != config.ADMIN_USER_ID:
            await callback.answer("❌ Bu işlemi sadece admin yapabilir!", show_alert=True)
            return
        
        # Database'den ürünleri al
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
        
        async with pool.acquire() as conn:
            products = await conn.fetch("""
                SELECT id, name, price, stock, is_active
                FROM market_products
                ORDER BY created_at DESC
                LIMIT 20
            """)
        
        if not products:
            await callback.message.edit_text(
                "🗑️ **Ürün Silme**\n\n"
                "❌ Silinecek ürün bulunamadı!\n\n"
                "➕ Önce ürün ekleyin.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_list_products")]
                ])
            )
            return
        
        # Ürün listesini oluştur
        response = "🗑️ **Ürün Silme**\n\n"
        response += "📋 **Mevcut Ürünler:**\n\n"
        
        for product in products:
            product_id = product['id']
            name = product['name']
            price = product['price']
            stock = product['stock']
            category_name = product['category_name'] or "Kategorisiz"
            
            button_text = f"🗑️ {name} ({price:.2f} KP)"
            keyboard_buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"market_delete_product_{product_id}")])
        
        # Geri butonu
        keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            "🗑️ **Ürün Silme**\n\n"
            "**⚠️ Dikkat:** Bu işlem geri alınamaz!\n\n"
            "**💡 Silmek istediğiniz ürünü seçin:**\n\n"
            "**📋 Toplam:** " + str(len(products)) + " aktif ürün",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Show delete products menu hatası: {e}")
        await callback.answer("❌ Ürün silme menüsü yüklenirken hata oluştu!", show_alert=True)

async def show_stock_management_menu(callback: CallbackQuery):
    """Stok yönetimi menüsünü göster"""
    await callback.answer("📦 Stok yönetimi yakında eklenecek!", show_alert=True)

async def show_price_management_menu(callback: CallbackQuery):
    """Fiyat yönetimi menüsünü göster"""
    await callback.answer("💰 Fiyat yönetimi yakında eklenecek!", show_alert=True)

async def show_market_report(callback: CallbackQuery):
    """Market raporunu göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı hatası!", show_alert=True)
            return
        
        async with pool.acquire() as conn:
            # Market istatistikleri
            total_products = await conn.fetchval("SELECT COUNT(*) FROM market_products WHERE is_active = TRUE")
            total_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders")
            pending_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders WHERE status = 'pending'")
            approved_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders WHERE status = 'approved'")
            rejected_orders = await conn.fetchval("SELECT COUNT(*) FROM market_orders WHERE status = 'rejected'")
            total_revenue = await conn.fetchval("SELECT COALESCE(SUM(total_price), 0) FROM market_orders WHERE status = 'approved'")
            
            # Bugünkü istatistikler
            today_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            today_revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(total_price), 0) FROM market_orders 
                WHERE status = 'approved' AND DATE(created_at) = CURRENT_DATE
            """)
        
        response = f"""
📊 **MARKET RAPORU**

🛍️ **Ürün İstatistikleri:**
• Toplam aktif ürün: **{total_products}** adet

📦 **Sipariş İstatistikleri:**
• Toplam sipariş: **{total_orders}** adet
• Bekleyen sipariş: **{pending_orders}** adet
• Onaylanan sipariş: **{approved_orders}** adet
• Reddedilen sipariş: **{rejected_orders}** adet

💰 **Gelir İstatistikleri:**
• Toplam gelir: **{total_revenue:.2f}** KP
• Bugünkü sipariş: **{today_orders}** adet
• Bugünkü gelir: **{today_revenue:.2f}** KP

📅 **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="market_report_refresh")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Market raporu hatası: {e}")
        await callback.answer("❌ Rapor yüklenemedi!", show_alert=True)

async def refresh_market_menu(callback: CallbackQuery):
    """Market menüsünü yenile"""
    try:
        user_id = callback.from_user.id
        
        # Market yönetim menüsünü yeniden göster
        await show_market_management_menu(user_id, None)
        
        await callback.answer("🔄 Market menüsü yenilendi!", show_alert=True)
        
    except Exception as e:
        logger.error(f"❌ Market menü yenileme hatası: {e}")
        await callback.answer("❌ Menü yenilenirken hata oluştu!", show_alert=True) 

# Sipariş yönetimi fonksiyonları
async def show_pending_orders(callback: CallbackQuery):
    """Bekleyen siparişleri göster"""
    try:
        logger.info("📦 show_pending_orders fonksiyonu başlatıldı")
        
        # Database pool'u al
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool alınamadı")
            await callback.answer("❌ Database bağlantısı hatası!", show_alert=True)
            return
        
        logger.info("✅ Database pool başarıyla alındı")
        
        # Database'den bekleyen siparişleri al
        async with pool.acquire() as conn:
            logger.info("🔍 Bekleyen siparişler sorgulanıyor...")
            orders = await conn.fetch("""
                SELECT o.*, u.username, p.name as product_name 
                FROM market_orders o 
                JOIN users u ON o.user_id = u.user_id 
                JOIN market_products p ON o.product_id = p.id 
                WHERE o.status = 'pending' 
                ORDER BY o.created_at DESC
            """)
        
        logger.info(f"📊 {len(orders)} adet bekleyen sipariş bulundu")
        
        if not orders:
            logger.info("❌ Bekleyen sipariş bulunamadı")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")]
            ])
            
            await callback.message.edit_text(
                "📦 **Bekleyen Siparişler**\n\n❌ Bekleyen sipariş bulunamadı!",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            logger.info("✅ Boş sipariş mesajı gönderildi")
            return
        
        # İlk 5 siparişi göster
        logger.info("📝 Sipariş listesi hazırlanıyor...")
        response = "📦 **Bekleyen Siparişler**\n\n"
        keyboard_buttons = []
        
        for i, order in enumerate(orders[:5]):
            response += f"**{i+1}. {order['product_name']}**\n"
            response += f"👤 Kullanıcı: @{order['username']}\n"
            response += f"💰 Fiyat: {order['total_price']:.2f} KP\n"
            response += f"📅 Tarih: {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"✅ Onayla {i+1}", 
                    callback_data=f"order_approve_{order['id']}"
                ),
                InlineKeyboardButton(
                    text=f"❌ Reddet {i+1}", 
                    callback_data=f"order_reject_{order['id']}"
                )
            ])
        
        keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        logger.info("📤 Sipariş listesi gönderiliyor...")
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        logger.info("✅ Sipariş listesi başarıyla gönderildi")
        
    except Exception as e:
        logger.error(f"❌ Pending orders hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_approved_orders(callback: CallbackQuery):
    """Onaylanan siparişleri göster - Tarih filtreleri ile"""
    try:
        # Tarih filtreleri menüsü
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Bugün", callback_data="market_approved_today"),
                InlineKeyboardButton(text="📅 Bu Hafta", callback_data="market_approved_week")
            ],
            [
                InlineKeyboardButton(text="📅 Bu Ay", callback_data="market_approved_month"),
                InlineKeyboardButton(text="📅 Geçen Ay", callback_data="market_approved_last_month")
            ],
            [
                InlineKeyboardButton(text="📅 Bu Yıl", callback_data="market_approved_year"),
                InlineKeyboardButton(text="📅 Son 3 Ay", callback_data="market_approved_3months")
            ],
            [
                InlineKeyboardButton(text="📅 Tümü", callback_data="market_approved_all"),
                InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")
            ]
        ])
        
        response = """
✅ **Onaylanan Siparişler - Tarih Filtresi**

Hangi zaman aralığındaki onaylanan siparişleri görmek istiyorsun?

📅 **Seçenekler:**
• **Bugün:** Bugün onaylanan siparişler
• **Bu Hafta:** Bu hafta onaylanan siparişler  
• **Bu Ay:** Bu ay onaylanan siparişler
• **Geçen Ay:** Geçen ay onaylanan siparişler
• **Bu Yıl:** Bu yıl onaylanan siparişler
• **Son 3 Ay:** Son 3 ayda onaylanan siparişler
• **Tümü:** Tüm onaylanan siparişler
        """
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Approved orders menu hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_approved_orders_filtered(callback: CallbackQuery, time_filter: str):
    """Filtrelenmiş onaylanan siparişleri göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı hatası!", show_alert=True)
            return
        
        # Tarih filtresi SQL'i
        date_filter = {
            "today": "DATE(o.updated_at) = CURRENT_DATE",
            "week": "o.updated_at >= CURRENT_DATE - INTERVAL '7 days'",
            "month": "o.updated_at >= DATE_TRUNC('month', CURRENT_DATE)",
            "last_month": "o.updated_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND o.updated_at < DATE_TRUNC('month', CURRENT_DATE)",
            "year": "o.updated_at >= DATE_TRUNC('year', CURRENT_DATE)",
            "3months": "o.updated_at >= CURRENT_DATE - INTERVAL '3 months'",
            "all": "TRUE"
        }
        
        filter_name = {
            "today": "Bugün",
            "week": "Bu Hafta", 
            "month": "Bu Ay",
            "last_month": "Geçen Ay",
            "year": "Bu Yıl",
            "3months": "Son 3 Ay",
            "all": "Tümü"
        }
        
        async with pool.acquire() as conn:
            orders = await conn.fetch(f"""
                SELECT o.*, u.username, p.name as product_name 
                FROM market_orders o 
                JOIN users u ON o.user_id = u.user_id 
                JOIN market_products p ON o.product_id = p.id 
                WHERE o.status = 'approved' AND {date_filter[time_filter]}
                ORDER BY o.updated_at DESC
                LIMIT 20
            """)
        
        if not orders:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_approved")]
            ])
            
            await callback.message.edit_text(
                f"✅ **Onaylanan Siparişler - {filter_name[time_filter]}**\n\n❌ {filter_name[time_filter]} onaylanan sipariş bulunamadı!",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            return
        
        response = f"✅ **Onaylanan Siparişler - {filter_name[time_filter]}**\n\n"
        
        for i, order in enumerate(orders):
            response += f"**{i+1}. {order['product_name']}**\n"
            response += f"👤 Kullanıcı: @{order['username']}\n"
            response += f"💰 Fiyat: {order['total_price']:.2f} KP\n"
            response += f"📅 Onay: {order['updated_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_approved")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Filtered approved orders hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_rejected_orders(callback: CallbackQuery):
    """Reddedilen siparişleri göster - Tarih filtreleri ile"""
    try:
        # Tarih filtreleri menüsü
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Bugün", callback_data="market_rejected_today"),
                InlineKeyboardButton(text="📅 Bu Hafta", callback_data="market_rejected_week")
            ],
            [
                InlineKeyboardButton(text="📅 Bu Ay", callback_data="market_rejected_month"),
                InlineKeyboardButton(text="📅 Geçen Ay", callback_data="market_rejected_last_month")
            ],
            [
                InlineKeyboardButton(text="📅 Bu Yıl", callback_data="market_rejected_year"),
                InlineKeyboardButton(text="📅 Son 3 Ay", callback_data="market_rejected_3months")
            ],
            [
                InlineKeyboardButton(text="📅 Tümü", callback_data="market_rejected_all"),
                InlineKeyboardButton(text="⬅️ Geri", callback_data="market_management")
            ]
        ])
        
        response = """
❌ **Reddedilen Siparişler - Tarih Filtresi**

Hangi zaman aralığındaki reddedilen siparişleri görmek istiyorsun?

📅 **Seçenekler:**
• **Bugün:** Bugün reddedilen siparişler
• **Bu Hafta:** Bu hafta reddedilen siparişler  
• **Bu Ay:** Bu ay reddedilen siparişler
• **Geçen Ay:** Geçen ay reddedilen siparişler
• **Bu Yıl:** Bu yıl reddedilen siparişler
• **Son 3 Ay:** Son 3 ayda reddedilen siparişler
• **Tümü:** Tüm reddedilen siparişler
        """
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Rejected orders menu hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def show_rejected_orders_filtered(callback: CallbackQuery, time_filter: str):
    """Filtrelenmiş reddedilen siparişleri göster"""
    try:
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı hatası!", show_alert=True)
            return
        
        # Tarih filtresi SQL'i
        date_filter = {
            "today": "DATE(o.updated_at) = CURRENT_DATE",
            "week": "o.updated_at >= CURRENT_DATE - INTERVAL '7 days'",
            "month": "o.updated_at >= DATE_TRUNC('month', CURRENT_DATE)",
            "last_month": "o.updated_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND o.updated_at < DATE_TRUNC('month', CURRENT_DATE)",
            "year": "o.updated_at >= DATE_TRUNC('year', CURRENT_DATE)",
            "3months": "o.updated_at >= CURRENT_DATE - INTERVAL '3 months'",
            "all": "TRUE"
        }
        
        filter_name = {
            "today": "Bugün",
            "week": "Bu Hafta", 
            "month": "Bu Ay",
            "last_month": "Geçen Ay",
            "year": "Bu Yıl",
            "3months": "Son 3 Ay",
            "all": "Tümü"
        }
        
        async with pool.acquire() as conn:
            orders = await conn.fetch(f"""
                SELECT o.*, u.username, p.name as product_name 
                FROM market_orders o 
                JOIN users u ON o.user_id = u.user_id 
                JOIN market_products p ON o.product_id = p.id 
                WHERE o.status = 'rejected' AND {date_filter[time_filter]}
                ORDER BY o.updated_at DESC
                LIMIT 20
            """)
        
        if not orders:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_rejected")]
            ])
            
            await callback.message.edit_text(
                f"❌ **Reddedilen Siparişler - {filter_name[time_filter]}**\n\n❌ {filter_name[time_filter]} reddedilen sipariş bulunamadı!",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            return
        
        response = f"❌ **Reddedilen Siparişler - {filter_name[time_filter]}**\n\n"
        
        for i, order in enumerate(orders):
            response += f"**{i+1}. {order['product_name']}**\n"
            response += f"👤 Kullanıcı: @{order['username']}\n"
            response += f"💰 Fiyat: {order['total_price']:.2f} KP\n"
            response += f"📅 Red: {order['updated_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="market_rejected")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Filtered rejected orders hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

# Sipariş onaylama/reddetme fonksiyonları
async def approve_order(callback: CallbackQuery, order_id: int):
    """Siparişi onayla"""
    try:
        # Database pool'u al
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı hatası!", show_alert=True)
            return
        
        async with pool.acquire() as conn:
            # Siparişi onayla
            await conn.execute("""
                UPDATE market_orders 
                SET status = 'approved', updated_at = NOW() 
                WHERE id = $1
            """, order_id)
            
            # Kullanıcıya bildirim gönder
            order_info = await conn.fetchrow("""
                SELECT o.*, u.user_id, p.name as product_name 
                FROM market_orders o 
                JOIN users u ON o.user_id = u.user_id 
                JOIN market_products p ON o.product_id = p.id 
                WHERE o.id = $1
            """, order_id)
            
            if order_info:
                bot = get_bot_instance()
                if bot:
                    await bot.send_message(
                        order_info['user_id'],
                        f"✅ **Siparişiniz Onaylandı!**\n\n"
                        f"**Ürün:** {order_info['product_name']}\n"
                        f"**Fiyat:** {order_info['total_price']:.2f} KP\n"
                        f"**Durum:** Onaylandı ✅\n\n"
                        f"En kısa sürede size ulaşacağız!"
                    )
        
        await callback.answer("✅ Sipariş onaylandı!", show_alert=True)
        await show_pending_orders(callback)
        
    except Exception as e:
        logger.error(f"❌ Approve order hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def reject_order(callback: CallbackQuery, order_id: int):
    """Siparişi reddet"""
    try:
        # Database pool'u al
        from database import get_db_pool
        pool = await get_db_pool()
        if not pool:
            await callback.answer("❌ Database bağlantısı hatası!", show_alert=True)
            return
        
        async with pool.acquire() as conn:
            # Siparişi reddet
            await conn.execute("""
                UPDATE market_orders 
                SET status = 'rejected', updated_at = NOW() 
                WHERE id = $1
            """, order_id)
            
            # Kullanıcıya bildirim gönder
            order_info = await conn.fetchrow("""
                SELECT o.*, u.user_id, p.name as product_name 
                FROM market_orders o 
                JOIN users u ON o.user_id = u.user_id 
                JOIN market_products p ON o.product_id = p.id 
                WHERE o.id = $1
            """, order_id)
            
            if order_info:
                bot = get_bot_instance()
                if bot:
                    await bot.send_message(
                        order_info['user_id'],
                        f"❌ **Siparişiniz Reddedildi**\n\n"
                        f"**Ürün:** {order_info['product_name']}\n"
                        f"**Fiyat:** {order_info['total_price']:.2f} KP\n"
                        f"**Durum:** Reddedildi ❌\n\n"
                        f"Pointleriniz iade edildi."
                    )
        
        await callback.answer("❌ Sipariş reddedildi!", show_alert=True)
        await show_pending_orders(callback)
        
    except Exception as e:
        logger.error(f"❌ Reject order hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

# ==============================================
# ÜRÜN DÜZENLEME HANDLER'LARI
# ==============================================

async def handle_edit_product_id_input(message: Message, edit_data: Dict):
    """Ürün ID girişi - düzenleme"""
    try:
        user_id = message.from_user.id
        
        logger.info(f"🔍 Edit product ID input çağrıldı - User: {user_id}, Text: {message.text}")
        
        try:
            product_id = int(message.text.strip())
            logger.info(f"✅ Product ID parse edildi: {product_id}")
        except ValueError:
            logger.warning(f"❌ Geçersiz ID formatı: {message.text}")
            await message.reply("❌ Geçersiz ID! Lütfen sayısal bir ID girin.")
            return
        
        # Database'den ürünü kontrol et
        pool = await get_db_pool()
        if not pool:
            logger.error("❌ Database pool bulunamadı!")
            await message.reply("❌ Database bağlantısı hatası!")
            return
        
        logger.info(f"🔍 Database'den ürün aranıyor - Product ID: {product_id}")
        
        async with pool.acquire() as conn:
            product = await conn.fetchrow("""
                SELECT * FROM market_products WHERE id = $1
            """, product_id)
        
        if not product:
            logger.warning(f"❌ Ürün bulunamadı - Product ID: {product_id}")
            await message.reply("❌ Bu ID'ye sahip ürün bulunamadı!")
            return
        
        logger.info(f"✅ Ürün bulundu - Product ID: {product_id}, Name: {product['name']}")
        
        # Ürün bilgilerini edit_data'ya kaydet
        edit_data["product_id"] = product_id
        edit_data["original_product"] = dict(product)
        edit_data["step"] = "edit_name"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_edit")]
        ])
        
        await message.reply(
            f"✏️ **Ürün Düzenleme - {product['name']}**\n\n"
            f"**Mevcut ad:** {product['name']}\n\n"
            "**Yeni ürün adını yazın:**",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✏️ Ürün düzenleme başlatıldı - Product ID: {product_id}, User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Edit product ID input hatası: {e}")

async def handle_edit_product_name_input(message: Message, edit_data: Dict):
    """Ürün adı düzenleme"""
    try:
        user_id = message.from_user.id
        
        if len(message.text) < 3:
            await message.reply("❌ Ürün adı en az 3 karakter olmalı!")
            return
        
        edit_data["new_name"] = message.text
        edit_data["step"] = "edit_description"
        
        original_product = edit_data["original_product"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_edit")]
        ])
        
        await message.reply(
            f"✏️ **Ürün Düzenleme**\n\n"
            f"**Mevcut açıklama:** {original_product['description']}\n\n"
            "**Yeni ürün açıklamasını yazın:**",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Edit product name input hatası: {e}")

async def handle_edit_product_description_input(message: Message, edit_data: Dict):
    """Ürün açıklaması düzenleme"""
    try:
        user_id = message.from_user.id
        
        if len(message.text) < 10:
            await message.reply("❌ Ürün açıklaması en az 10 karakter olmalı!")
            return
        
        edit_data["new_description"] = message.text
        edit_data["step"] = "edit_price"
        
        original_product = edit_data["original_product"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_edit")]
        ])
        
        await message.reply(
            f"✏️ **Ürün Düzenleme**\n\n"
            f"**Mevcut fiyat:** {original_product['price']:.2f} KP\n\n"
            "**Yeni fiyatı yazın (KP):**",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Edit product description input hatası: {e}")

async def handle_edit_product_price_input(message: Message, edit_data: Dict):
    """Ürün fiyatı düzenleme"""
    try:
        user_id = message.from_user.id
        
        try:
            price = float(message.text.strip())
            if price <= 0:
                await message.reply("❌ Fiyat 0'dan büyük olmalı!")
                return
        except ValueError:
            await message.reply("❌ Geçersiz fiyat! Lütfen sayısal bir değer girin.")
            return
        
        edit_data["new_price"] = price
        edit_data["step"] = "edit_stock"
        
        original_product = edit_data["original_product"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_edit")]
        ])
        
        await message.reply(
            f"✏️ **Ürün Düzenleme**\n\n"
            f"**Mevcut stok:** {original_product['stock']} adet\n\n"
            "**Yeni stok miktarını yazın:**",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Edit product price input hatası: {e}")

async def handle_edit_product_stock_input(message: Message, edit_data: Dict):
    """Ürün stok düzenleme"""
    try:
        user_id = message.from_user.id
        
        try:
            stock = int(message.text.strip())
            if stock < 0:
                await message.reply("❌ Stok 0'dan küçük olamaz!")
                return
        except ValueError:
            await message.reply("❌ Geçersiz stok! Lütfen sayısal bir değer girin.")
            return
        
        edit_data["new_stock"] = stock
        edit_data["step"] = "edit_site_name"
        
        original_product = edit_data["original_product"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_edit")]
        ])
        
        await message.reply(
            f"✏️ **Ürün Düzenleme**\n\n"
            f"**Mevcut site adı:** {original_product['site_name'] or 'Belirtilmemiş'}\n\n"
            "**Yeni site adını yazın (veya 'geç' yazın):**",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Edit product stock input hatası: {e}")

async def handle_edit_product_site_name_input(message: Message, edit_data: Dict):
    """Ürün site adı düzenleme"""
    try:
        user_id = message.from_user.id
        
        if message.text.lower() == "geç":
            edit_data["new_site_name"] = None
        else:
            edit_data["new_site_name"] = message.text
        
        edit_data["step"] = "edit_site_link"
        
        original_product = edit_data["original_product"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ İptal", callback_data="market_cancel_edit")]
        ])
        
        await message.reply(
            f"✏️ **Ürün Düzenleme**\n\n"
            f"**Mevcut site linki:** {original_product['site_link'] or 'Belirtilmemiş'}\n\n"
            "**Yeni site linkini yazın (veya 'geç' yazın):**",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Edit product site name input hatası: {e}")

async def handle_edit_product_site_link_input(message: Message, edit_data: Dict):
    """Ürün site linki düzenleme"""
    try:
        user_id = message.from_user.id
        
        if message.text.lower() == "geç":
            edit_data["new_site_link"] = None
        else:
            edit_data["new_site_link"] = message.text
        
        # Ürünü database'de güncelle
        success = await update_product_in_db(edit_data, user_id)
        
        if success:
            await message.reply(
                "✅ **Ürün başarıyla güncellendi!**\n\n"
                "Ürün bilgileri güncellendi ve market'te aktif.",
                parse_mode="Markdown"
            )
            
            # Edit state'ini temizle
            if user_id in product_edit_data:
                del product_edit_data[user_id]
        else:
            await message.reply("❌ Ürün güncellenirken hata oluştu!")
        
    except Exception as e:
        logger.error(f"❌ Edit product site link input hatası: {e}")

async def update_product_in_db(edit_data: Dict, admin_id: int) -> bool:
    """Ürünü database'de güncelle"""
    try:
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE market_products 
                SET name = $1, description = $2, price = $3, stock = $4, 
                    site_name = $5, site_link = $6, updated_at = NOW()
                WHERE id = $7
            """, 
            edit_data["new_name"],
            edit_data["new_description"],
            edit_data["new_price"],
            edit_data["new_stock"],
            edit_data["new_site_name"],
            edit_data["new_site_link"],
            edit_data["product_id"]
            )
        
        logger.info(f"✅ Ürün güncellendi - Product ID: {edit_data['product_id']}, Admin: {admin_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Update product in db hatası: {e}")
        return False

# ==============================================
# ÜRÜN SİLME HANDLER'LARI
# ==============================================

async def handle_delete_product_id_input(message: Message, delete_data: Dict):
    """Ürün ID girişi - silme"""
    try:
        user_id = message.from_user.id
        
        try:
            product_id = int(message.text.strip())
        except ValueError:
            await message.reply("❌ Geçersiz ID! Lütfen sayısal bir ID girin.")
            return
        
        # Database'den ürünü kontrol et
        pool = await get_db_pool()
        if not pool:
            await message.reply("❌ Database bağlantısı hatası!")
            return
        
        async with pool.acquire() as conn:
            product = await conn.fetchrow("""
                SELECT * FROM market_products WHERE id = $1
            """, product_id)
        
        if not product:
            await message.reply("❌ Bu ID'ye sahip ürün bulunamadı!")
            return
        
        # Ürünü sil
        success = await delete_product_from_db(product_id, user_id)
        
        if success:
            await message.reply(
                f"✅ **Ürün başarıyla silindi!**\n\n"
                f"**Silinen ürün:** {product['name']}\n"
                f"**ID:** {product_id}",
                parse_mode="Markdown"
            )
            
            # Delete state'ini temizle
            if user_id in product_delete_data:
                del product_delete_data[user_id]
        else:
            await message.reply("❌ Ürün silinirken hata oluştu!")
        
    except Exception as e:
        logger.error(f"❌ Delete product ID input hatası: {e}")

# ==============================================
# CANCEL HANDLER'LARI
# ==============================================

async def cancel_product_edit(callback: CallbackQuery):
    """Ürün düzenlemeyi iptal et"""
    try:
        user_id = callback.from_user.id
        
        if user_id in product_edit_data:
            del product_edit_data[user_id]
        
        await callback.answer("❌ Ürün düzenleme iptal edildi!", show_alert=True)
        
        # Market yönetim menüsüne geri dön
        await show_market_management_menu_callback(callback)
        
    except Exception as e:
        logger.error(f"❌ Cancel product edit hatası: {e}")

async def cancel_product_delete(callback: CallbackQuery):
    """Ürün silmeyi iptal et"""
    try:
        user_id = callback.from_user.id
        
        if user_id in product_delete_data:
            del product_delete_data[user_id]
        
        await callback.answer("❌ Ürün silme iptal edildi!", show_alert=True)
        
        # Market yönetim menüsüne geri dön
        await show_market_management_menu_callback(callback)
        
    except Exception as e:
        logger.error(f"❌ Cancel product delete hatası: {e}") 