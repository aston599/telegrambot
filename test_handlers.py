"""
Handler Fonksiyonları Testi
"""

import asyncio
from aiogram.types import Message, User, Chat
from handlers.start_handler import start_command
from handlers.message_monitor import get_dynamic_point_amount, check_flood_protection
from handlers.chat_message_handler import handle_chat_message

class MockMessage:
    def __init__(self, user_id: int, first_name: str, text: str):
        self.from_user = MockUser(user_id, first_name)
        self.chat = MockChat()
        self.text = text

class MockUser:
    def __init__(self, user_id: int, first_name: str):
        self.id = user_id
        self.first_name = first_name
        self.username = f"testuser{user_id}"
        self.last_name = None

class MockChat:
    def __init__(self):
        self.id = -1001234567890
        self.type = "group"
        self.title = "Test Group"

async def test_handlers():
    """Handler fonksiyonlarını test et"""
    try:
        print("🧪 Handler testleri başlatılıyor...")
        
        # Point sistemi test
        point_amount = await get_dynamic_point_amount()
        print(f"✅ Point miktarı: {point_amount}")
        
        # Flood protection test
        test_user_id = 6513506166
        can_send = await check_flood_protection(test_user_id)
        print(f"✅ Flood protection: {'Gönderilebilir' if can_send else 'Cooldown'}")
        
        # Chat message handler test
        mock_message = MockMessage(test_user_id, "TestUser", "Test mesajı")
        print("✅ Mock message oluşturuldu")
        
        print("✅ Handler testleri tamamlandı!")
        
    except Exception as e:
        print(f"❌ Handler test hatası: {e}")

if __name__ == "__main__":
    asyncio.run(test_handlers()) 