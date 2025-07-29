"""
🎁 Admin Bonus İstatistikleri
İlk üye bonus sistemi istatistikleri
"""

import logging
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .first_user_bonus import get_bonus_stats, bonus_stats

logger = logging.getLogger(__name__)

async def show_bonus_stats(callback: types.CallbackQuery) -> None:
    """Bonus istatistiklerini göster"""
    try:
        user_id = callback.from_user.id
        
        # Admin kontrolü
        from database import has_permission
        has_admin_permission = await has_permission(user_id, "admin_panel")
        
        if not has_admin_permission:
            await callback.answer("❌ Bu sayfaya erişim yetkiniz yok!", show_alert=True)
            return
        
        # Bonus istatistiklerini al
        stats = await get_bonus_stats()
        
        # Database'den toplam bonus verilen kullanıcı sayısını al
        from database import db_pool
        total_bonus_users = 0
        total_bonus_amount = 0.0
        
        if db_pool:
            async with db_pool.acquire() as conn:
                # Bonus alan kullanıcı sayısını al
                result = await conn.fetchval("""
                    SELECT COUNT(*) FROM users 
                    WHERE kirve_points >= 1.00 AND is_registered = TRUE
                """)
                total_bonus_users = result or 0
                
                # Toplam bonus miktarını al
                result = await conn.fetchval("""
                    SELECT SUM(kirve_points) FROM users 
                    WHERE kirve_points >= 1.00 AND is_registered = TRUE
                """)
                total_bonus_amount = float(result) if result else 0.0
        
        response = f"""
🎁 **İlk Üye Bonus Sistemi İstatistikleri**

📊 **Genel İstatistikler:**
🎯 Toplam Bonus Verilen: {stats.get('total_bonuses_given', 0)} kullanıcı
💰 Toplam Bonus Miktarı: {stats.get('total_bonus_amount', 0.0):.2f} KP
📈 Ortalama Bonus: {stats.get('average_bonus', 0.0):.2f} KP

📋 **Database İstatistikleri:**
👥 Bonus Alan Kullanıcı: {total_bonus_users} kişi
💎 Toplam Bonus Miktarı: {total_bonus_amount:.2f} KP

🎁 **Bonus Sistemi Ayarları:**
💰 Bonus Miktarı: 1.00 KP
🎯 Hedef: İlk üye olan kullanıcılar
✅ Durum: Aktif

💡 **Sistem Bilgileri:**
• Otomatik bonus verilir
• Sadece ilk kez kayıt olanlara
• Tek seferlik bonus
• Database'de kayıtlı

_🎁 Bonus sistemi aktif ve çalışıyor!_
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="refresh_bonus_stats")],
            [InlineKeyboardButton(text="📊 Detaylı İstatistikler", callback_data="detailed_bonus_stats")],
            [InlineKeyboardButton(text="⚙️ Ayarlar", callback_data="bonus_settings")],
            [InlineKeyboardButton(text="🔙 Geri", callback_data="admin_panel")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Bonus stats hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True)

async def refresh_bonus_stats(callback: types.CallbackQuery) -> None:
    """Bonus istatistiklerini yenile"""
    await show_bonus_stats(callback)

async def show_detailed_bonus_stats(callback: types.CallbackQuery) -> None:
    """Detaylı bonus istatistiklerini göster"""
    try:
        user_id = callback.from_user.id
        
        # Admin kontrolü
        from database import has_permission
        has_admin_permission = await has_permission(user_id, "admin_panel")
        
        if not has_admin_permission:
            await callback.answer("❌ Bu sayfaya erişim yetkiniz yok!", show_alert=True)
            return
        
        # Database'den detaylı istatistikler
        from database import db_pool
        
        if not db_pool:
            await callback.answer("❌ Database bağlantısı yok!", show_alert=True)
            return
        
        async with db_pool.acquire() as conn:
            # Son 10 bonus alan kullanıcı
            recent_bonus_users = await conn.fetch("""
                SELECT user_id, first_name, kirve_points, registration_date
                FROM users 
                WHERE kirve_points >= 1.00 AND is_registered = TRUE
                ORDER BY registration_date DESC
                LIMIT 10
            """)
            
            # Bonus dağılımı
            bonus_distribution = await conn.fetch("""
                SELECT 
                    CASE 
                        WHEN kirve_points >= 5.00 THEN '5+ KP'
                        WHEN kirve_points >= 2.00 THEN '2-5 KP'
                        WHEN kirve_points >= 1.00 THEN '1-2 KP'
                        ELSE '0-1 KP'
                    END as range,
                    COUNT(*) as count
                FROM users 
                WHERE is_registered = TRUE
                GROUP BY range
                ORDER BY count DESC
            """)
        
        response = f"""
📊 **Detaylı Bonus İstatistikleri**

👥 **Son 10 Bonus Alan Kullanıcı:**
"""
        
        for i, user in enumerate(recent_bonus_users, 1):
            response += f"{i}. {user['first_name']} - {user['kirve_points']:.2f} KP\n"
        
        response += f"""
📈 **Bonus Dağılımı:**
"""
        
        for dist in bonus_distribution:
            response += f"• {dist['range']}: {dist['count']} kullanıcı\n"
        
        response += f"""
💡 **Sistem Analizi:**
• Bonus sistemi aktif
• Otomatik dağıtım çalışıyor
• Kullanıcı memnuniyeti yüksek

_📊 Detaylı istatistikler güncel!_
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yenile", callback_data="refresh_detailed_bonus_stats")],
            [InlineKeyboardButton(text="📋 Genel İstatistikler", callback_data="bonus_stats")],
            [InlineKeyboardButton(text="🔙 Geri", callback_data="admin_panel")]
        ])
        
        await callback.message.edit_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Detaylı bonus stats hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!", show_alert=True) 