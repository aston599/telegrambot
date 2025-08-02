"""
💬 Sohbet Sistemi - KirveHub Bot
Bot'un grup sohbetlerinde doğal konuşabilmesi için
"""

import random
import asyncio
import time
import re
from typing import Optional, Dict
from aiogram import Bot
from aiogram.types import Message
from utils.logger import logger
from utils.cooldown_manager import cooldown_manager
from database import is_user_registered
from config import get_config
from aiogram import types

# Bot başlangıç koruması
bot_startup_time = time.time() - 300  # 5 dakika önce başlat (koruma geçmiş olsun)
STARTUP_PROTECTION_DURATION = 60  # 1 dakika koruma

# Chat sistemi ayarları
chat_system_active = True
chat_probability = 0.15  # %15 ihtimalle cevap ver (daha seçici)
min_message_length = 3  # Minimum mesaj uzunluğu (3 harf)

# Kayıt olmayan kullanıcılar için teşvik sistemi
unregistered_users_last_message = {}  # {user_id: timestamp}
REGISTRATION_REMINDER_INTERVAL = 600  # 10 dakika (600 saniye)

# Selamlaşma kalıpları - Sadece gerçek selamlamalar
GREETINGS = {
    "selam": [
        "Selam! 😊",
        "Selam! 💎"
    ],
    "merhaba": [
        "Merhaba! 😊",
        "Merhaba! 💎"
    ],
    "sa": [
        "Aleyküm selam! 😊",
        "Selam! 💎"
    ],
    "günaydın": [
        "Günaydın! 😊",
        "Günaydın! 💎"
    ],
    "iyi akşamlar": [
        "İyi akşamlar! 😊",
        "İyi akşamlar! 💎"
    ],
    "iyi geceler": [
        "İyi geceler! 😊",
        "İyi geceler! 💎"
    ]
}

# Soru kalıpları - Sadece gerçek sorular
QUESTIONS = {
    "nasılsın": [
        "İyiyim, teşekkürler! Sen nasılsın? 😊",
        "İyiyim! Sen nasılsın? 💎"
    ],
    "ne yapıyorsun": [
        "Sohbete katılıyorum! Sen ne yapıyorsun? 😊",
        "Burada sohbet ediyorum! Sen ne yapıyorsun? 💎"
    ],
    "ne haber": [
        "İyi haber! Sen ne haber? 😊",
        "İyi! Sen ne haber? 💎"
    ],
    "naber": [
        "İyidir! Sen naber? 😊",
        "İyi haber! Sen naber? 💎"
    ],
    "nabıyon": [
        "İyidir! Sen nabıyon? 😊",
        "İyi haber! Sen nabıyon? 💎"
    ],
    "ne var ne yok": [
        "İyi haber! Sen ne var ne yok? 😊",
        "İyi! Sen ne var ne yok? 💎"
    ],
    "ne oluo": [
        "İyidir! Sen ne oluo? 😊",
        "İyi haber! Sen ne oluo? 💎"
    ],
    "ne oluyor": [
        "İyidir! Sen ne oluyor? 😊",
        "İyi haber! Sen ne oluyor? 💎"
    ],
    "nasıl gidiyor": [
        "İyi gidiyor! Sen nasıl? 😊",
        "Harika! Sen nasıl? 💎"
    ],
    "keyfin nasıl": [
        "Çok iyi! Sen nasıl? 😊",
        "Harika! Sen nasıl? 💎"
    ],
    "halin nasıl": [
        "İyidir! Sen nasılsın? 😊",
        "İyi! Sen nasılsın? 💎"
    ],
    "halin ne": [
        "İyidir! Sen nasılsın? 😊",
        "İyi! Sen nasılsın? 💎"
    ],
    "ne yapıyon": [
        "Sohbete katılıyorum! Sen ne yapıyon? 😊",
        "Burada sohbet ediyorum! Sen ne yapıyon? 💎"
    ],
    "ne yapıyorsun": [
        "Sohbete katılıyorum! Sen ne yapıyorsun? 😊",
        "Burada sohbet ediyorum! Sen ne yapıyorsun? 💎"
    ]
}

# Günlük konuşma kalıpları - Sadece gerçek tepkiler
DAILY_CHAT = {
    "evet": [
        "Evet! 😊",
        "Evet! 💎"
    ],
    "hayır": [
        "Hayır! 😊",
        "Hayır! 💎"
    ],
    "tamam": [
        "Tamam! 😊",
        "Tamam! 💎"
    ],
    "olur": [
        "Olur! 😊",
        "Olur! 💎"
    ],
    "yok": [
        "Yok! 😊",
        "Yok! 💎"
    ],
    "var": [
        "Var! 😊",
        "Var! 💎"
    ],
    "biliyorum": [
        "Biliyorum! 😊",
        "Evet, biliyorum! 💎"
    ],
    "bilmiyorum": [
        "Bilmiyorum! 😊",
        "Bilmiyorum, söyle! 💎"
    ],
    "anladım": [
        "Anladım! 😊",
        "Evet, anladım! 💎"
    ],
    "anlamadım": [
        "Anlamadım! 😊",
        "Anlamadım, açıkla! 💎"
    ],
    "güzel": [
        "Güzel! 😊",
        "Evet, güzel! 💎"
    ],
    "kötü": [
        "Kötü! 😊",
        "Evet, kötü! 💎"
    ],
    "iyi": [
        "İyi! 😊",
        "Evet, iyi! 💎"
    ],
    "harika": [
        "Harika! 😊",
        "Evet, harika! 💎"
    ],
    "mükemmel": [
        "Mükemmel! 😊",
        "Evet, mükemmel! 💎"
    ],
    "süper": [
        "Süper! 😊",
        "Evet, süper! 💎"
    ],
    "muhteşem": [
        "Muhteşem! 😊",
        "Evet, muhteşem! 💎"
    ],
    "berbat": [
        "Berbat! 😊",
        "Evet, berbat! 💎"
    ],
    "korkunç": [
        "Korkunç! 😊",
        "Evet, korkunç! 💎"
    ],
    "ah": [
        "Ah! 😊",
        "Ah, evet! 💎"
    ],
    "oh": [
        "Oh! 😊",
        "Oh, evet! 💎"
    ],
    "wow": [
        "Wow! 😊",
        "Wow, evet! 💎"
    ],
    "vay": [
        "Vay! 😊",
        "Vay, evet! 💎"
    ],
    "aferin": [
        "Aferin! 😊",
        "Evet, aferin! 💎"
    ],
    "bravo": [
        "Bravo! 😊",
        "Evet, bravo! 💎"
    ],
    "tebrikler": [
        "Tebrikler! 😊",
        "Evet, tebrikler! 💎"
    ]
}

# KirveHub ile ilgili cevaplar - Sadece gerçekten KirveHub hakkında konuşulduğunda
KIRVEHUB_RESPONSES = [
    "KirveHub harika bir yer! 💎",
    "Burada çok güzel sohbetler oluyor! 🎯",
    "KirveHub'da herkes çok iyi! 😊",
    "Burada gerçekten harika insanlar var! 🚀"
]

# Point sistemi ile ilgili cevaplar - Sadece point hakkında konuşulduğunda
POINT_RESPONSES = [
            "Point kazanmak çok kolay! Her 10 mesajda 0.02 point kazandırır! 💎",
    "Günlük 5 Kirve Point kazanabilirsin! 🎯",
    "Point sistemi harika! Her mesajın değeri var! 😊",
    "Point kazanmak için sadece sohbet et! 🚀"
]

# Kısaltma ve argo sözlüğü - Sadece gerçek kısaltmalar
SHORTCUTS = {
    "ab": ("abi", "Erkeklere hitap"),
    "abl": ("abla", "Kadınlara hitap"),
    "aeo": ("allah'a emanet ol", "Vedalaşma sözü"),
    "as": ("aleyküm selam", "Selamlaşmaya cevap"),
    "bknz": ("bakınız", "İmla/dalga geçme amaçlı"),
    "brn": ("ben", "Kısaltma"),
    "cnm": ("canım", "Hitap"),
    "cvp": ("cevap", "Genelde soru-cevapta"),
    "fln": ("falan", "Belirsizlik"),
    "grş": ("görüşürüz", "Veda"),
    "hşr": ("hoşçakal", "Vedalaşma"),
    "knk": ("kanka", "Arkadaşça hitap"),
    "krdş": ("kardeş", "Hitap"),
    "mrb": ("merhaba", "Selam"),
    "msl": ("mesela", "Örnek vermek için"),
    "nbr": ("ne haber", "Selamlaşma"),
    "sa": ("selamünaleyküm", "Selam"),
    "slm": ("selam", "Kısaca selam"),
    "tmm": ("tamam", "Onay"),
    "tşk": ("teşekkür", "Teşekkür etme"),
    "tşkrlr": ("teşekkürler", "Daha resmi"),
    "yk": ("yok", "Red cevabı")
}

# Küfür/argo kelimeler
BAD_WORDS = ["aq", "amk", "oç", "lan"]

# Veda kısaltmaları
FAREWELLS = ["aeo", "grş", "hşr"]

# Selamlaşma kısaltmaları
GREET_SHORTS = ["mrb", "slm", "sa", "nbr", "as"]

# Jargonlara özel hazır cevaplar - Günlük konuşma jargonları
JARGON_REPLIES = {
    "mrb": "Selam! Nasılsın?",
    "slm": "Selam! Nasılsın?",
    "sa": "Aleyküm selam! Hoş geldin!",
    "nbr": "İyiyim, sen nasılsın?",
    "as": "Aleyküm selam!",
    "aeo": "Allah'a emanet ol, kendine dikkat et! 👋",
    "grş": "Görüşürüz, kendine iyi bak!",
    "hşr": "Hoşçakal! Görüşmek üzere!",
    "tşk": "Rica ederim!",
    "tşkrlr": "Rica ederim, her zaman!",
    "cvp": "Cevap veriyorum!",
    "kdn": "Kanka dedin ne? 😂",
    "kbs": "K.bakma sıkıntı yok, devam!",
    "kanka": "Kanka! Buradayım, ne var ne yok?",
    "knk": "Kanka! Nasılsın?",
    "abi": "Abi, buyur dinliyorum!",
    "abla": "Abla, buradayım!",
    "krdş": "Kardeşim, ne var ne yok?",
    "cnm": "Canım, ne oldu?",
    "kirvem": "Kirvem! Her zaman buradayım!",
    "kirve": "Kirve! Ne var ne yok?",
    "yk": "Yok mu başka soru?",
    "naber": "İyidir! Sen naber?",
    "nabıyon": "İyidir! Sen nabıyon?",
    "ne var ne yok": "İyi haber! Sen ne var ne yok?",
    "ne oluo": "İyidir! Sen ne oluo?",
    "ne oluyor": "İyidir! Sen ne oluyor?",
    "nasıl gidiyor": "İyi gidiyor! Sen nasıl?",
    "keyfin nasıl": "Çok iyi! Sen nasıl?",
    "halin nasıl": "İyidir! Sen nasılsın?",
    "halin ne": "İyidir! Sen nasılsın?",
    "ne yapıyon": "Sohbete katılıyorum! Sen ne yapıyon?",
    "ne yapıyorsun": "Sohbete katılıyorum! Sen ne yapıyorsun?",
    "ne yapıyorsunuz": "Sohbete katılıyorum! Sen ne yapıyorsun?"
}

import re

def find_shortcuts(text):
    found = []
    for k in SHORTCUTS:
        # kelime olarak geçiyorsa
        if re.search(rf"\b{k}\b", text):
            found.append(k)
    return found

def find_jargon_reply(text):
    # En son geçen ve baskın jargon için cevap döndür
    found = []
    for k in JARGON_REPLIES:
        if re.search(rf"\b{k}\b", text):
            found.append(k)
    if found:
        # En son geçen jargonun cevabını döndür
        return JARGON_REPLIES[found[-1]]
    return None

def is_bot_startup_protection_active():
    """Bot başlangıç koruması aktif mi kontrol et"""
    return (time.time() - bot_startup_time) < STARTUP_PROTECTION_DURATION

async def send_registration_reminder(user_id: int, user_name: str):
    """Kayıt olmayan kullanıcıya hatırlatma mesajı gönder"""
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Farklı teşvik mesajları
        reminder_messages = [
            f"""
🎯 **Hala Kayıt Olmadın!**

Merhaba {user_name}! 👋

❌ **Hala kayıtlı değilsin!**

💎 **Kayıt ol ve şunları kazan:**
• Her mesajın point kazandırır
• Günlük 5.00 KP limitin var
• Market'te freespin ve bakiye alabilirsin
• Çekilişlere ve etkinliklere katılabilirsin
• Sıralamada yer alabilirsin

⬇️ **Hemen kayıt ol ve sisteme katıl!**
            """,
            f"""
🚀 **Kayıt Olma Zamanı!**

{user_name}, hala kayıt olmadın! 😅

❌ **Şu anda kayıtlı değilsin!**

💎 **Kayıt olarak neler kazanacaksın:**
• Point kazanma sistemi
• Market alışverişi
• Etkinliklere katılma
• Profil ve istatistikler
• Topluluk özellikleri

⬇️ **Hemen kayıt ol ve sisteme katıl!**
            """,
            f"""
💡 **Son Fırsat!**

{user_name}, kayıt olmayı unuttun! 😊

❌ **Hala kayıtlı değilsin!**

💎 **Kayıt ol ve şunları yap:**
• Her mesajın point kazandırır
• Market'ten freespin alabilirsin
• Çekilişlere katılabilirsin
• Sıralamada yer alabilirsin
• Etkinliklerde ödüller kazanabilirsin

⬇️ **Hemen kayıt ol ve sisteme katıl!**
            """,
            f"""
🎯 **Kayıt Olma Vakti!**

{user_name}, hala bekliyoruz! 😄

❌ **Şu anda kayıtlı değilsin!**

💎 **Kayıt olarak neler yapabilirsin:**
• Point kazanma sistemi
• Market alışverişi
• Etkinliklere katılma
• Profil ve istatistikler
• Topluluk özellikleri

⬇️ **Hemen kayıt ol ve sisteme katıl!**
            """
        ]
        
        # Rastgele bir mesaj seç
        registration_message = random.choice(reminder_messages)
        
        # Kayıt butonu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 KAYIT OL", callback_data="register_user")],
            [InlineKeyboardButton(text="📋 Komutlar", callback_data="show_commands")],
            [InlineKeyboardButton(text="❌ Kapat", callback_data="close_message")]
        ])
        
        # Özelden gönder
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        await bot.send_message(
            chat_id=user_id,
            text=registration_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        await bot.session.close()
        logger.info(f"✅ Kayıt olmayan kullanıcıya hatırlatma mesajı gönderildi - User: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Hatırlatma mesajı gönderme hatası: {e}")

def should_send_registration_reminder(user_id: int) -> bool:
    """Kayıt olmayan kullanıcıya hatırlatma gönderilmeli mi kontrol et"""
    current_time = time.time()
    
    # Kullanıcının son mesaj zamanını kontrol et
    if user_id in unregistered_users_last_message:
        last_message_time = unregistered_users_last_message[user_id]
        # 10 dakika geçmişse hatırlatma gönder
        if current_time - last_message_time >= REGISTRATION_REMINDER_INTERVAL:
            unregistered_users_last_message[user_id] = current_time
            return True
    
    return False

def cleanup_unregistered_user(user_id: int):
    """Kullanıcı gruptan çıktığında veya kayıt olduğunda temizlik yap"""
    if user_id in unregistered_users_last_message:
        del unregistered_users_last_message[user_id]
        logger.info(f"🧹 Kayıt olmayan kullanıcı temizlendi - User: {user_id}")

def is_user_in_unregistered_list(user_id: int) -> bool:
    """Kullanıcı kayıt olmayan kullanıcılar listesinde mi kontrol et"""
    return user_id in unregistered_users_last_message
        
async def handle_chat_message(message: Message) -> Optional[str]:
    """
    Sohbet mesajını analiz et ve uygun cevabı döndür
    """
    try:
        user_id = message.from_user.id
        text = message.text.lower().strip()
        
        # Bot başlangıç koruması kontrolü
        if is_bot_startup_protection_active():
            logger.info(f"🛡️ Bot başlangıç koruması aktif - User: {user_id}")
            return None
        
        # Temel kontroller
        if not chat_system_active:
            logger.info("❌ Chat system inactive")
            return None
            
        if message.chat.type == "private":
            logger.info("❌ Private message, skipping")
            return None
            
        if not text or len(text) < min_message_length:
            logger.info("❌ Text too short or empty")
            return None
            
        # Cooldown kontrolü
        can_respond = await cooldown_manager.can_respond_to_user(user_id)
        if not can_respond:
            logger.info(f"❌ Cooldown aktif - User: {user_id}")
            return None
            
        # Rastgele cevap verme olasılığı kontrolü
        if random.random() > chat_probability:
            logger.info(f"❌ Rastgele cevap verme olasılığı düşük - User: {user_id}")
            return None
            
        # Kayıt kontrolü
        is_registered = await is_user_registered(user_id)
        
        # Kayıt olmayan kullanıcılar için hiçbir şey yapma (message_monitor.py'de hallediliyor)
        if not is_registered:
            return None
        
        # Mesajı kaydet
        await cooldown_manager.record_user_message(user_id)
        
        # Jargonlara özel cevap
        jargon_reply = find_jargon_reply(text)
        if jargon_reply:
            logger.info(f"✅ Jargon cevabı: {jargon_reply}")
            return jargon_reply

        # Kısaltma tespiti (diğerleri)
        found_shortcuts = find_shortcuts(text)
        if found_shortcuts:
            responses = []
            for sc in found_shortcuts:
                acilim, anlam = SHORTCUTS[sc]
                if sc in BAD_WORDS:
                    responses.append(f"⚠️ '{sc}' argo/küfürdür, dikkatli kullan! ({acilim})")
                elif sc in FAREWELLS:
                    responses.append(f"{acilim.capitalize()}! 👋 ({anlam})")
                elif sc in GREET_SHORTS:
                    responses.append(f"{acilim.capitalize()}! ({anlam})")
                else:
                    responses.append(f"'{sc}' = {acilim} ({anlam})")
            yanit = "\n".join(responses)
            logger.info(f"✅ Kısaltma cevabı: {yanit}")
            return yanit

        # Selamlaşma kontrolü - Sadece gerçek selamlamalar
        for greeting, responses in GREETINGS.items():
            if greeting in text:
                response = random.choice(responses)
                logger.info(f"✅ Selamlaşma cevabı: {response}")
                return response
                
        # Soru kontrolü - Sadece gerçek sorular
        for question, responses in QUESTIONS.items():
            if question in text:
                response = random.choice(responses)
                logger.info(f"✅ Soru cevabı: {response}")
                return response
                
        # Günlük konuşma kalıpları kontrolü - Sadece gerçek tepkiler
        for phrase, responses in DAILY_CHAT.items():
            if phrase in text:
                response = random.choice(responses)
                logger.info(f"✅ Günlük konuşma cevabı: {response}")
                return response
                
        # KirveHub kelimesi kontrolü - Sadece gerçekten KirveHub hakkında konuşulduğunda
        if "kirvehub" in text or "kirve hub" in text:
            response = random.choice(KIRVEHUB_RESPONSES)
            logger.info(f"✅ KirveHub cevabı: {response}")
            return response
            
        # Point kelimesi kontrolü - Sadece gerçekten point hakkında konuşulduğunda
        if "point" in text or "puan" in text or "kp" in text:
            response = random.choice(POINT_RESPONSES)
            logger.info(f"✅ Point cevabı: {response}")
            return response
            
        # Çok nadir genel cevaplar - Sadece çok pozitif mesajlarda
        if random.random() < 0.005:  # %0.5 ihtimalle (daha nadir)
            # Sadece çok pozitif mesajlarda cevap ver
            positive_words = ["güzel", "harika", "mükemmel", "süper", "muhteşem", "çok iyi"]
            if any(word in text for word in positive_words):
                response = random.choice([
                    "Evet, gerçekten güzel! 😊",
                    "Haklısın! 💎",
                    "Aynen öyle! 🎯",
                    "Kesinlikle! 🚀"
                ])
                logger.info(f"✅ Pozitif mesaj cevabı: {response}")
                return response
            
        logger.info("❌ Uygun cevap bulunamadı")
        return None
        
    except Exception as e:
        logger.error(f"❌ Chat message handler hatası: {e}")
        return None

async def send_chat_response(message: Message, response: str):
    """Sohbet cevabını gönder"""
    try:
        config = get_config()
        bot = Bot(token=config.BOT_TOKEN)
        
        # Kayıt kontrolü ve yönlendirme
        user_id = message.from_user.id
        is_registered = await is_user_registered(user_id)
        
        # Kayıt olmayan kullanıcılar için özel mesaj kontrolü
        if not is_registered and any(keyword in response.lower() for keyword in ["kayıt ol", "point kazan", "etkinliklere katıl"]):
            # Inline keyboard ile kayıt butonu
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎯 KAYIT OL", callback_data="register_user")]
            ])
            
            await bot.send_message(
                chat_id=message.chat.id,
                text=response,
                reply_to_message_id=message.message_id,
                reply_markup=keyboard
            )
        else:
            await bot.send_message(
                chat_id=message.chat.id,
                text=response,
                reply_to_message_id=message.message_id
            )
        
        await bot.session.close()
        logger.info(f"💬 Chat response gönderildi - User: {message.from_user.id}, Registered: {is_registered}")
        
    except Exception as e:
        logger.error(f"❌ Chat response hatası: {e}")

# Admin panel fonksiyonları
def toggle_chat_system(enable: bool):
    """Sohbet sistemini aç/kapat"""
    global chat_system_active
    chat_system_active = enable
    
    status = "✅ Açıldı" if enable else "❌ Kapatıldı"
    logger.info(f"💬 Chat system {status}")
    
    return chat_system_active

def get_chat_status() -> bool:
    """Sohbet sistemi durumunu al"""
    return chat_system_active

def set_chat_probability(probability: float):
    """Sohbet cevap verme ihtimalini ayarla"""
    global chat_probability
    chat_probability = max(0.0, min(1.0, probability))
    logger.info(f"💬 Chat probability: {chat_probability}")

def set_min_message_length(length: int):
    """Minimum mesaj uzunluğunu ayarla"""
    global min_message_length
    min_message_length = max(1, length)
    logger.info(f"💬 Min message length: {min_message_length}")

# İstatistik fonksiyonları
def get_chat_stats() -> Dict:
    """Sohbet sistemi istatistiklerini al"""
    return {
        "active": chat_system_active,
        "probability": chat_probability,
        "min_length": min_message_length,
        "startup_protection_active": is_bot_startup_protection_active(),
        "startup_protection_remaining": max(0, STARTUP_PROTECTION_DURATION - (time.time() - bot_startup_time)),
        "greetings_count": len(GREETINGS),
        "questions_count": len(QUESTIONS),
        "daily_chat_count": len(DAILY_CHAT),
        "kirvehub_responses_count": len(KIRVEHUB_RESPONSES),
        "point_responses_count": len(POINT_RESPONSES)
    }

# Bot yazma komutu
async def bot_write_command(message: Message):
    """Bot'un ağzından yazı yazma komutu"""
    try:
        user_id = message.from_user.id
        config = get_config()
        
        # Admin kontrolü
        from config import is_admin
        if not is_admin(user_id):
            await message.reply("❌ Bu komutu sadece admin kullanabilir!")
            return
        
        # 🔥 GRUP SESSİZLİK: Grup chatindeyse sil ve özel mesajla yanıt ver
        if message.chat.type != "private":
            try:
                await message.delete()
                logger.info(f"🔇 Botyaz komutu mesajı silindi - Group: {message.chat.id}")
                
                # ÖZELİNDE YANIT VER
                if _bot_instance:
                    await _send_bot_write_privately(user_id, message.text)
                return
                
            except Exception as e:
                logger.error(f"❌ Komut mesajı silinemedi: {e}")
                return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split(' ', 2)  # En fazla 2 parçaya böl
        
        if len(parts) < 3:
            await message.reply("❌ Kullanım: `/botyaz <grup_id> <mesaj>`\nÖrnek: `/botyaz -1001234567890 Merhaba kirvem!`")
            return
        
        try:
            group_id = int(parts[1])
            bot_message = parts[2]
        except ValueError:
            await message.reply("❌ Geçersiz grup ID! Örnek: `/botyaz -1001234567890 Merhaba kirvem!`")
            return
        
        # Bot instance'ını al
        bot = Bot(token=config.BOT_TOKEN)
        
        try:
            # Mesajı gönder
            await bot.send_message(chat_id=group_id, text=bot_message)
            
            # Başarı mesajı
            await message.reply(f"✅ Bot mesajı gönderildi!\n\n**Grup ID:** {group_id}\n**Mesaj:** {bot_message}")
            
            logger.info(f"🤖 Bot mesajı gönderildi - Group: {group_id}, Message: {bot_message[:50]}...")
            
        except Exception as e:
            await message.reply(f"❌ Mesaj gönderilemedi: {str(e)}")
            logger.error(f"❌ Bot mesaj gönderme hatası: {e}")
            
        finally:
            await bot.session.close()
            
    except Exception as e:
        logger.error(f"❌ Bot write command hatası: {e}")
        await message.reply("❌ Bir hata oluştu!")

# Callback handler'ları
async def chat_callback_handler(callback: types.CallbackQuery):
    """Chat sistemi callback handler'ı"""
    try:
        user_id = callback.from_user.id
        data = callback.data
        
        logger.info(f"🔍 Chat callback alındı - User: {user_id} - Data: {data}")
        
        if data == "register_user":
            # Kayıt işlemi başlat
            from handlers.register_handler import register_user_command
            await register_user_command(callback.message)
            
            # Kayıt olmayan kullanıcılar listesinden temizle
            cleanup_unregistered_user(user_id)
            
            await callback.answer("🎯 Kayıt işlemi başlatıldı!")
            
        elif data == "show_commands":
            # Komut listesi göster
            from handlers.register_handler import komutlar_command
            await komutlar_command(callback.message)
            await callback.answer("📋 Komutlar gösterildi!")
            
        elif data == "close_message":
            # Mesajı sil
            try:
                await callback.message.delete()
                await callback.answer("❌ Mesaj kapatıldı!")
            except Exception as e:
                logger.error(f"❌ Mesaj silme hatası: {e}")
                await callback.answer("❌ Mesaj silinemedi!")
                
    except Exception as e:
        logger.error(f"❌ Chat callback handler hatası: {e}")
        await callback.answer("❌ Bir hata oluştu!")

async def _send_bot_write_privately(user_id: int, command_text: str):
    """Botyaz mesajını özel mesajla gönder"""
    try:
        if not _bot_instance:
            logger.error("❌ Bot instance bulunamadı!")
            return
        
        # Admin kontrolü
        from config import get_config, is_admin
        config = get_config()
        if not is_admin(user_id):
            await _bot_instance.send_message(user_id, "❌ Bu komutu sadece admin kullanabilir!")
            return
        
        # Komut metnini parse et
        parts = command_text.strip().split(' ', 2)  # En fazla 2 parçaya böl
        
        if len(parts) < 3:
            await _bot_instance.send_message(
                user_id,
                "❌ Kullanım: `/botyaz <grup_id> <mesaj>`\nÖrnek: `/botyaz -1001234567890 Merhaba kirvem!`"
            )
            return
        
        try:
            group_id = int(parts[1])
            bot_message = parts[2]
        except ValueError:
            await _bot_instance.send_message(
                user_id,
                "❌ Geçersiz grup ID! Örnek: `/botyaz -1001234567890 Merhaba kirvem!`"
            )
            return
        
        # Bot instance'ını al
        bot = Bot(token=config.BOT_TOKEN)
        
        try:
            # Mesajı gönder
            await bot.send_message(chat_id=group_id, text=bot_message)
            
            # Başarı mesajı
            await _bot_instance.send_message(
                user_id,
                f"✅ Bot mesajı gönderildi!\n\n**Grup ID:** {group_id}\n**Mesaj:** {bot_message}"
            )
            
            logger.info(f"🤖 Bot mesajı gönderildi - Group: {group_id}, Message: {bot_message[:50]}...")
            
        except Exception as e:
            await _bot_instance.send_message(user_id, f"❌ Mesaj gönderilemedi: {str(e)}")
            logger.error(f"❌ Bot mesaj gönderme hatası: {e}")
            
        finally:
            await bot.session.close()
            
    except Exception as e:
        logger.error(f"❌ Private bot write hatası: {e}")
        await _bot_instance.send_message(user_id, "❌ Bot yazma mesajı gönderilemedi!") 