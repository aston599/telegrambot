#!/usr/bin/env python3
"""
Bonus Sistemi Test Scripti
"""

import asyncio
import sys
import os

# Proje dizinini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database, get_user_info, is_user_registered, get_user_points
from handlers.first_user_bonus import is_first_time_user, get_bonus_stats

async def test_bonus_system():
    """Bonus sistemini test et"""
    try:
        await init_database()
        
        print("🎁 **Bonus Sistemi Test**")
        print("=" * 50)
        
        # Test kullanıcı ID'leri
        test_users = [
            {"id": 8154732274, "name": "KirveHub Media"},
            {"id": 123456789, "name": "Test User 1"},
            {"id": 987654321, "name": "Test User 2"}
        ]
        
        for user in test_users:
            user_id = user["id"]
            user_name = user["name"]
            
            print(f"\n🔍 **Kullanıcı: {user_name}**")
            print(f"🆔 ID: {user_id}")
            
            # Kullanıcı bilgilerini kontrol et
            user_info = await get_user_info(user_id)
            if user_info:
                print(f"✅ Kullanıcı bilgileri mevcut")
                print(f"📝 Ad: {user_info.get('first_name', 'Bilinmiyor')}")
                print(f"📅 Kayıt Tarihi: {user_info.get('registration_date', 'Bilinmiyor')}")
            else:
                print(f"❌ Kullanıcı bilgileri yok")
            
            # Kayıt durumunu kontrol et
            is_registered = await is_user_registered(user_id)
            print(f"📊 Kayıtlı: {'✅ Evet' if is_registered else '❌ Hayır'}")
            
            # İlk kez kullanıcı mı kontrol et
            is_first_time = await is_first_time_user(user_id)
            print(f"🎁 İlk Kez: {'✅ Evet' if is_first_time else '❌ Hayır'}")
            
            # Point bilgilerini al
            points_info = await get_user_points(user_id)
            if points_info:
                print(f"💰 Point: {points_info.get('kirve_points', 0.0):.2f} KP")
            else:
                print(f"💰 Point: 0.00 KP")
        
        # Bonus istatistiklerini al
        print(f"\n📊 **Bonus Sistemi İstatistikleri**")
        stats = await get_bonus_stats()
        print(f"🎯 Toplam Bonus Verilen: {stats.get('total_bonuses_given', 0)}")
        print(f"💰 Toplam Bonus Miktarı: {stats.get('total_bonus_amount', 0.0):.2f} KP")
        print(f"📈 Ortalama Bonus: {stats.get('average_bonus', 0.0):.2f} KP")
        
        print(f"\n✅ **Bonus sistemi test tamamlandı!**")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bonus_system()) 