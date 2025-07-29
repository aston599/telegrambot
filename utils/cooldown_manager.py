"""
⏱️ Cooldown Manager - Bot Mesaj Kısıtlamaları
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

class CooldownManager:
    """Bot mesaj cooldown yöneticisi"""
    
    def __init__(self):
        # Kullanıcı bazlı cooldown'lar
        self.user_last_message: Dict[int, datetime] = {}
        self.user_message_count: Dict[int, int] = defaultdict(int)
        
        # Global cooldown
        self.last_bot_message: Optional[datetime] = None
        self.global_cooldown = 60  # 1 dakika minimum
        
        # Ayarlar
        self.min_cooldown = 30  # 30 saniye minimum (1 dakikadan düşürüldü)
        self.max_cooldown = 60  # 1 dakika maksimum (2 dakikadan düşürüldü)
        self.response_probability = 0.7  # %70 ihtimalle cevap ver (50'den artırıldı)
        self.max_consecutive_messages = 2  # Aynı kişiye maksimum 2 mesaj (1'den artırıldı)
        
    async def can_respond_to_user(self, user_id: int) -> bool:
        """Kullanıcıya cevap verilebilir mi kontrol et"""
        try:
            now = datetime.now()
            
            # Kullanıcının son mesaj zamanını kontrol et
            if user_id in self.user_last_message:
                time_diff = (now - self.user_last_message[user_id]).total_seconds()
                
                # Minimum cooldown kontrolü
                if time_diff < self.min_cooldown:
                    return False
                    
                # Maksimum cooldown kontrolü
                if time_diff < self.max_cooldown:
                    # Rastgele cooldown (1-2 dakika arası)
                    random_cooldown = random.randint(self.min_cooldown, self.max_cooldown)
                    if time_diff < random_cooldown:
                        return False
            
            # Global cooldown kontrolü
            if self.last_bot_message:
                global_time_diff = (now - self.last_bot_message).total_seconds()
                if global_time_diff < 15:  # Global 15 saniye minimum (30'dan düşürüldü)
                    return False
            
            # Response probability kontrolü
            if random.random() > self.response_probability:
                return False
                
            # Kullanıcının mesaj sayısı kontrolü
            if self.user_message_count[user_id] >= self.max_consecutive_messages:
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Cooldown kontrol hatası: {e}")
            return False
    
    async def record_user_message(self, user_id: int):
        """Kullanıcı mesajını kaydet"""
        try:
            now = datetime.now()
            self.user_last_message[user_id] = now
            self.user_message_count[user_id] += 1
            self.last_bot_message = now
            
            # 5 dakika sonra mesaj sayısını sıfırla
            asyncio.create_task(self._reset_user_count(user_id))
            
        except Exception as e:
            print(f"❌ Mesaj kayıt hatası: {e}")
    
    async def _reset_user_count(self, user_id: int):
        """Kullanıcı mesaj sayısını sıfırla"""
        try:
            await asyncio.sleep(300)  # 5 dakika bekle
            self.user_message_count[user_id] = 0
        except Exception as e:
            print(f"❌ Mesaj sayısı sıfırlama hatası: {e}")
    
    async def check_user_registration(self, user_id: int) -> bool:
        """Kullanıcı kayıt durumunu kontrol et"""
        try:
            from database import is_user_registered
            return await is_user_registered(user_id)
        except Exception as e:
            print(f"❌ Kayıt kontrol hatası: {e}")
            return False
    
    async def should_redirect_to_registration(self, user_id: int) -> bool:
        """Kullanıcıyı kayıta yönlendir mi kontrol et"""
        try:
            is_registered = await self.check_user_registration(user_id)
            return not is_registered
        except Exception as e:
            print(f"❌ Kayıt yönlendirme hatası: {e}")
            return True
    
    def get_cooldown_status(self, user_id: int) -> Dict:
        """Cooldown durumunu getir"""
        try:
            now = datetime.now()
            last_message = self.user_last_message.get(user_id)
            
            if last_message:
                time_diff = (now - last_message).total_seconds()
                remaining = max(0, self.min_cooldown - time_diff)
            else:
                remaining = 0
                
            return {
                "can_respond": remaining <= 0,
                "remaining_seconds": remaining,
                "message_count": self.user_message_count[user_id],
                "is_registered": True  # Bu değer ayrıca kontrol edilmeli
            }
        except Exception as e:
            print(f"❌ Cooldown durum hatası: {e}")
            return {"can_respond": False, "remaining_seconds": 0, "message_count": 0, "is_registered": False}

# Global cooldown manager instance
cooldown_manager = CooldownManager()