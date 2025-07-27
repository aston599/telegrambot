"""
🛍️ Market Sistemi - Modern UI + Admin Bildirimleri
"""

import logging
from datetime import datetime
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user_points

logger = logging.getLogger(__name__)


async def show_product_details_modern(callback: types.CallbackQuery, data: str) -> None:
    """Modern ürün detay sayfası"""
    try:
        product_id = int(data.split("_")[-1])
        
        logger.info(f"🛍️ Ürün detayı isteniyor - Product ID: {product_id}")
        
        from database import get_product_by_id
        product = await get_product_by_id(product_id)
        
        logger.info(f"🛍️ get_product_by_id sonucu: {product}")
        
        if not product:
            logger.error(f"❌ Ürün bulunamadı - Product ID: {product_id}")
            await callback.answer("❌ Ürün bulunamadı!", show_alert=True)
            return
        
        # Kullanıcı bakiyesini kontrol et
        user_points = await get_user_points(callback.from_user.id)
        user_balance = float(user_points.get('kirve_points', 0))
        product_price = float(product['price'])
        
        logger.info(f"🛍️ Ürün detayı gösteriliyor - Product ID: {product_id}, Price: {product_price}, User Balance: {user_balance}")
        
        # Modern ürün detay mesajı
        detail_message = f"""
╔═══════════════════════════════════╗
║        📦 ÜRÜN DETAYI 📦          ║
╚═══════════════════════════════════╝

🛍️ **Ürün:** {product['name']}
🏢 **Site:** {product['company_name']}
💰 **Fiyat:** {product_price:.2f} KP
📊 **Stok:** {product['stock']} adet

📝 **Açıklama:**
{product['description'] or 'Açıklama bulunmuyor.'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Hesap Durumu:**
💎 **Bakiyeniz:** {user_balance:.2f} KP
{'✅ Yeterli bakiye' if user_balance >= product_price else '❌ Yetersiz bakiye'}

⚠️ **Önemli:**
• {product['company_name']} sitesine kayıt olmanız gerekiyor
• Satın alma işlemi geri alınamaz
• Admin onayından sonra kod/talimatlar gönderilecek
        """
        
        # Butonlar
        keyboard_buttons = []
        
        if user_balance >= product_price and product['stock'] > 0:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text="🛒 Satın Al", 
                    callback_data=f"buy_product_{product_id}"
                )
            ])
        else:
            if user_balance < product_price:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text="❌ Yetersiz Bakiye", 
                        callback_data="insufficient_balance"
                    )
                ])
            if product['stock'] <= 0:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text="❌ Stokta Yok", 
                        callback_data="out_of_stock"
                    )
                ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="⬅️ Geri", callback_data="profile_market")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            detail_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Ürün detay sayfası gösterildi - Product ID: {product_id}")
        
    except Exception as e:
        logger.error(f"❌ Ürün detay hatası: {e}")
        await callback.answer("❌ Ürün detayları yüklenemedi!", show_alert=True)


async def handle_buy_product_modern(callback: types.CallbackQuery, data: str) -> None:
    """Modern satın alma onay ekranı"""
    try:
        user_id = callback.from_user.id
        product_id = int(data.split("_")[-1])
        
        from database import get_product_by_id
        product = await get_product_by_id(product_id)
        
        if not product or product['stock'] <= 0:
            await callback.answer("❌ Ürün artık stokta yok!", show_alert=True)
            return
        
        user_points = await get_user_points(user_id)
        user_balance = float(user_points.get('kirve_points', 0))
        product_price = float(product['price'])
        
        if user_balance < product_price:
            await callback.answer("❌ Yetersiz bakiye!", show_alert=True)
            return
        
        # Modern onay mesajı
        confirm_message = f"""
╔═══════════════════════════════════╗
║      🛒 SATIN ALMA ONAYI 🛒       ║
╚═══════════════════════════════════╝

📋 **Sipariş Özeti:**
🛍️ **Ürün:** {product['name']}
🏢 **Site:** {product['company_name']}
💰 **Fiyat:** {product_price:.2f} KP
📊 **Stok:** {product['stock']} adet

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Hesap Bilgileri:**
💎 **Mevcut:** {user_balance:.2f} KP
💸 **Satın Alım Sonrası:** {user_balance - product_price:.2f} KP

⚠️ **Önemli Uyarılar:**
• {product['company_name']} sitesine kayıt olmanız gerekiyor
• Satın alma işlemi geri alınamaz
• Admin onayından sonra kod/talimatlar gönderilecek

✅ **Satın almayı onaylıyor musunuz?**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Evet, Satın Al", callback_data=f"confirm_buy_{product_id}"),
                InlineKeyboardButton(text="❌ İptal", callback_data=f"view_product_{product_id}")
            ]
        ])
        
        await callback.message.edit_text(
            confirm_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Satın alma onay hatası: {e}")
        await callback.answer("❌ Satın alma işlemi başarısız!", show_alert=True)


async def confirm_buy_product_modern(callback: types.CallbackQuery, data: str) -> None:
    """Modern satın alma işlemini tamamla"""
    try:
        user_id = callback.from_user.id
        product_id = int(data.split("_")[-1])
        
        from database import get_product_by_id, execute_query, execute_single_query
        product = await get_product_by_id(product_id)
        
        if not product or product['stock'] <= 0:
            await callback.answer("❌ Ürün artık stokta yok!", show_alert=True)
            return
        
        user_points = await get_user_points(user_id)
        user_balance = float(user_points.get('kirve_points', 0))
        product_price = float(product['price'])
        
        if user_balance < product_price:
            await callback.answer("❌ Yetersiz bakiye!", show_alert=True)
            return
        
        # Transaction işlemleri
        from database import execute_query, execute_single_query
        
        # 1. Kullanıcı bakiyesini düş
        await execute_query("""
            UPDATE users 
            SET kirve_points = kirve_points - $1 
            WHERE user_id = $2
        """, product_price, user_id)
        
        # 2. Ürün stoğunu azalt
        await execute_query("""
            UPDATE market_products 
            SET stock = stock - 1 
            WHERE id = $1 AND stock > 0
        """, product_id)
        
        # 3. Sipariş oluştur
        import uuid
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        await execute_query("""
            INSERT INTO market_orders (
                order_number, user_id, product_id, total_price, status, created_at
            ) VALUES ($1, $2, $3, $4, 'pending', NOW())
        """, order_number, user_id, product_id, product_price)
        
        # 4. Başarı mesajı
        success_message = f"""
╔═══════════════════════════════════╗
║      ✅ SİPARİŞ TAMAMLANDI ✅      ║
╚═══════════════════════════════════╝

📋 **Sipariş Bilgileri:**
🆔 **Sipariş No:** `{order_number}`
🛍️ **Ürün:** {product['name']}
🏢 **Site:** {product['company_name']}
💰 **Tutar:** {product_price:.2f} KP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ **Durum:** Admin onayı bekleniyor
📝 **Sonraki Adım:** Admin onayından sonra kod/talimatlar gönderilecek

✅ **Siparişiniz başarıyla oluşturuldu!**
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Siparişlerim", callback_data="profile_orders")],
            [InlineKeyboardButton(text="🛍️ Market", callback_data="profile_market")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="profile_refresh")]
        ])
        
        await callback.message.edit_text(
            success_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        # Admin'e bildirim gönder
        await notify_admin_new_order_modern(user_id, product, order_number)
        
        # Log kaydı
        from utils.logger import log_market_purchase
        log_market_purchase(order_number, user_id, product['name'], product_price)
        
    except Exception as e:
        logger.error(f"❌ Satın alma işlemi hatası: {e}")
        await callback.answer("❌ Satın alma işlemi başarısız!", show_alert=True)


async def notify_admin_new_order_modern(user_id: int, product: dict, order_number: str) -> None:
    """Modern admin bildirimi gönder"""
    try:
        from config import get_config
        config = get_config()
        
        # Kullanıcı bilgilerini al
        from database import execute_single_query
        user_info = await execute_single_query("""
            SELECT first_name, username 
            FROM users 
            WHERE user_id = $1
        """, user_id)
        
        if not user_info:
            return
        
        # Modern admin bildirimi
        admin_message = f"""
╔═══════════════════════════════════╗
║        📦 YENİ SİPARİŞ 📦        ║
╚═══════════════════════════════════╝

📋 **Sipariş Detayları:**
🆔 **Sipariş No:** `{order_number}`
👤 **Müşteri:** {user_info['first_name']} (@{user_info['username']})
🛍️ **Ürün:** {product['name']}
🏢 **Site:** {product['company_name']}
💰 **Tutar:** {product['price']} KP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ **Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

🔧 **İşlemler:**
• Siparişi inceleyin
• Uygunluğunu kontrol edin
• Onay/red kararı verin
• Müşteriye bildirim gönderin
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Onayla", callback_data=f"admin_approve_{order_number}"),
                InlineKeyboardButton(text="❌ Reddet", callback_data=f"admin_reject_{order_number}")
            ],
            [InlineKeyboardButton(text="📋 Tüm Siparişler", callback_data="admin_orders_list")]
        ])
        
        from aiogram import Bot
        bot = Bot(token=config.BOT_TOKEN)
        
        await bot.send_message(
            chat_id=config.ADMIN_USER_ID,
            text=admin_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Admin bildirimi gönderildi - Order: {order_number}")
        
    except Exception as e:
        logger.error(f"❌ Admin bildirimi hatası: {e}")


async def show_my_orders(callback: types.CallbackQuery) -> None:
    """Kullanıcının siparişlerini göster"""
    try:
        user_id = callback.from_user.id
        
        # Yeni SQL fonksiyonunu kullan
        from database import get_user_orders_with_details
        orders = await get_user_orders_with_details(user_id, 10)
        
        if not orders:
            await callback.message.edit_text(
                "📋 **Siparişlerim**\n\n"
                "Henüz sipariş vermediniz.\n"
                "Market'ten ürün satın alarak siparişlerinizi burada görebilirsiniz.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🛍️ Market'e Git", callback_data="profile_market")],
                    [InlineKeyboardButton(text="⬅️ Geri", callback_data="profile_refresh")]
                ])
            )
            return
        
        # Sipariş listesi
        orders_text = "📋 **Siparişlerim**\n\n"
        
        for order in orders:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌',
                'delivered': '📦'
            }.get(order['status'], '❓')
            
            status_text = {
                'pending': 'Bekliyor',
                'approved': 'Onaylandı',
                'rejected': 'Reddedildi',
                'delivered': 'Teslim Edildi'
            }.get(order['status'], 'Bilinmiyor')
            
            order_date = order['created_at'].strftime('%d.%m.%Y %H:%M')
            
            orders_text += f"""
{status_emoji} **{order['order_number']}**
🛍️ {order['product_name']}
🏢 {order['company_name']}
💰 {order['total_price']} KP
📅 {order_date}
📊 **Durum:** {status_text}

"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍️ Market'e Git", callback_data="profile_market")],
            [InlineKeyboardButton(text="⬅️ Geri", callback_data="profile_refresh")]
        ])
        
        await callback.message.edit_text(
            orders_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Sipariş listesi hatası: {e}")
        await callback.answer("❌ Siparişler yüklenemedi!", show_alert=True) 


async def send_admin_notification(order_number: str, user_id: int, product_name: str, amount: float):
    """Admin'e sipariş bildirimi gönder - Session düzeltmesi"""
    try:
        import aiohttp
        from config import get_config
        
        config = get_config()
        admin_id = config.ADMIN_USER_ID
        
        # Session'ı düzgün kapat
        async with aiohttp.ClientSession() as session:
            # Admin'e bildirim gönder
            notification_text = f"""
🛍️ **YENİ SİPARİŞ ALINDI!**

📋 **Sipariş No:** `{order_number}`
👤 **Müşteri ID:** {user_id}
🛍️ **Ürün:** {product_name}
💰 **Tutar:** {amount} KP

⏰ **Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

✅ **Onaylamak için:** Sipariş listesini kontrol edin
❌ **Reddetmek için:** Sipariş listesini kontrol edin
            """
            
            # Admin'e mesaj gönder
            from handlers.admin_panel import _bot_instance
            if _bot_instance:
                await _bot_instance.send_message(
                    admin_id,
                    notification_text,
                    parse_mode="Markdown"
                )
                
                # Onay/Red butonları
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Onayla", callback_data=f"admin_approve_{order_number}"),
                        InlineKeyboardButton(text="❌ Reddet", callback_data=f"admin_reject_{order_number}")
                    ]
                ])
                
                await _bot_instance.send_message(
                    admin_id,
                    f"📋 **Sipariş İşlemleri**\n\nSipariş No: `{order_number}`",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                logger.info(f"✅ Admin bildirimi gönderildi - Order: {order_number}")
            else:
                logger.error("❌ Bot instance bulunamadı!")
                
    except Exception as e:
        logger.error(f"❌ Admin bildirimi hatası: {e}") 


async def get_user_market_history(user_id: int) -> dict:
    """Kullanıcının market geçmişini getir"""
    try:
        from database import get_db_pool
        
        pool = await get_db_pool()
        if not pool:
            return {}
        
        async with pool.acquire() as conn:
            # Toplam sipariş sayısı
            total_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders WHERE user_id = $1
            """, user_id)
            
            # Toplam harcama
            total_spent = await conn.fetchval("""
                SELECT COALESCE(SUM(total_price), 0) FROM market_orders WHERE user_id = $1
            """, user_id)
            
            # Onaylanan sipariş sayısı
            approved_orders = await conn.fetchval("""
                SELECT COUNT(*) FROM market_orders 
                WHERE user_id = $1 AND status = 'approved'
            """, user_id)
            
            # Son sipariş tarihi
            last_order = await conn.fetchval("""
                SELECT created_at FROM market_orders 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT 1
            """, user_id)
            
            # Son sipariş tarihini formatla
            last_order_date = "Hiç sipariş yok"
            if last_order:
                last_order_date = last_order.strftime('%d.%m.%Y %H:%M')
            
            return {
                'total_orders': total_orders,
                'total_spent': float(total_spent) if total_spent else 0.0,
                'approved_orders': approved_orders,
                'last_order_date': last_order_date
            }
            
    except Exception as e:
        logger.error(f"❌ Kullanıcı market geçmişi getirme hatası: {e}")
        return {} 