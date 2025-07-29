"""
💬 Sohbet Sistemi - KirveHub Bot
Bot'un grup sohbetlerinde doğal konuşabilmesi için
"""

import logging
import random
import re
from typing import List, Dict, Optional
from aiogram import Bot
from aiogram.types import Message

from database import is_user_registered, save_user_info
from config import get_config
from utils.cooldown_manager import cooldown_manager

logger = logging.getLogger(__name__)

# Sohbet sistemi durumu
chat_system_active = True
chat_probability = 0.5  # %50 ihtimalle cevap ver (cooldown manager ile kontrol edilecek)
min_message_length = 5  # Production için 5 harf minimum

# Selamlaşma kalıpları ve cevapları - Genişletilmiş ve samimi
GREETINGS = {
    "selam": [
        "Selam kirvem! Nasılsın? 😊",
        "Selam! Bugün nasıl gidiyor? 💎",
        "Selam! Sohbete katılığın için teşekkürler! 🎯",
        "Selam kirvem! Hoş geldin! 🚀",
        "Selam dostum! Nasıl gidiyor hayat? 😄",
        "Selam! Bugün keyfin nasıl? 💫",
        "Selam kirvem! Sohbete hoş geldin! 🌟",
        "Selam! Nasıl gidiyor hayat? 😊",
        "Selam dostum! Bugün nasıl? 💎",
        "Selam! Hoş geldin sohbete! 🎯"
    ],
    "merhaba": [
        "Merhaba! Nasılsın kirvem? 😊",
        "Merhaba! Bugün nasıl? 💎",
        "Merhaba! Sohbete hoş geldin! 🎯",
        "Merhaba kirvem! 🚀",
        "Merhaba dostum! Nasıl gidiyor? 😄",
        "Merhaba! Bugün keyfin nasıl? 💫",
        "Merhaba! Hoş geldin! 🌟",
        "Merhaba! Nasıl gidiyor hayat? 😊",
        "Merhaba dostum! Bugün nasıl? 💎",
        "Merhaba! Sohbete hoş geldin! 🎯"
    ],
    "sa": [
        "As kirvem! Nasılsın? 😊",
        "As! Bugün nasıl gidiyor? 💎",
        "As! Hoş geldin! 🎯",
        "As kirvem! 🚀",
        "As dostum! Nasıl gidiyor? 😄",
        "As! Bugün keyfin nasıl? 💫",
        "As! Hoş geldin sohbete! 🌟",
        "As! Nasıl gidiyor hayat? 😊",
        "As dostum! Bugün nasıl? 💎",
        "As! Sohbete hoş geldin! 🎯"
    ],
    "hey": [
        "Hey! Nasılsın? 😊",
        "Hey kirvem! Bugün nasıl? 💎",
        "Hey! Sohbete katılığın için teşekkürler! 🎯",
        "Hey! Hoş geldin! 🚀",
        "Hey dostum! Nasıl gidiyor? 😄",
        "Hey! Bugün keyfin nasıl? 💫",
        "Hey! Hoş geldin sohbete! 🌟",
        "Hey! Nasıl gidiyor hayat? 😊",
        "Hey dostum! Bugün nasıl? 💎",
        "Hey! Sohbete hoş geldin! 🎯"
    ],
    "hi": [
        "Hi! Nasılsın? 😊",
        "Hi kirvem! Bugün nasıl? 💎",
        "Hi! Sohbete hoş geldin! 🎯",
        "Hi! 🚀",
        "Hi dostum! Nasıl gidiyor? 😄",
        "Hi! Bugün keyfin nasıl? 💫",
        "Hi! Hoş geldin sohbete! 🌟",
        "Hi! Nasıl gidiyor hayat? 😊",
        "Hi dostum! Bugün nasıl? 💎",
        "Hi! Sohbete hoş geldin! 🎯"
    ],
    "günaydın": [
        "Günaydın kirvem! Nasılsın? 😊",
        "Günaydın! Bugün nasıl gidiyor? 💎",
        "Günaydın! Hoş geldin! 🎯",
        "Günaydın dostum! 🌟",
        "Günaydın! Bugün keyfin nasıl? 💫",
        "Günaydın kirvem! Hoş geldin! 😄",
        "Günaydın! Sohbete hoş geldin! 🚀",
        "Günaydın dostum! Nasıl gidiyor? 💎",
        "Günaydın! Bugün nasıl? 🎯",
        "Günaydın! Hoş geldin sohbete! 🌟"
    ],
    "iyi akşamlar": [
        "İyi akşamlar kirvem! Nasılsın? 😊",
        "İyi akşamlar! Bugün nasıl gidiyor? 💎",
        "İyi akşamlar! Hoş geldin! 🎯",
        "İyi akşamlar dostum! 🌟",
        "İyi akşamlar! Bugün keyfin nasıl? 💫",
        "İyi akşamlar kirvem! Hoş geldin! 😄",
        "İyi akşamlar! Sohbete hoş geldin! 🚀",
        "İyi akşamlar dostum! Nasıl gidiyor? 💎",
        "İyi akşamlar! Bugün nasıl? 🎯",
        "İyi akşamlar! Hoş geldin sohbete! 🌟"
    ],
    "iyi geceler": [
        "İyi geceler kirvem! Uyku tatlı olsun! 😊",
        "İyi geceler! Tatlı rüyalar! 💎",
        "İyi geceler! Hoşça kal! 🎯",
        "İyi geceler dostum! 🌟",
        "İyi geceler! Tatlı uykular! 💫",
        "İyi geceler kirvem! Hoşça kal! 😄",
        "İyi geceler! Sohbete hoş geldin! 🚀",
        "İyi geceler dostum! Tatlı rüyalar! 💎",
        "İyi geceler! Hoşça kal! 🎯",
        "İyi geceler! Tatlı uykular! 🌟"
    ]
}

# Soru kalıpları ve cevapları - Genişletilmiş ve samimi
QUESTIONS = {
    "nasılsın": [
        "İyiyim kirvem, teşekkürler! Sen nasılsın? 😊",
        "Çok iyiyim! Sen nasılsın? 💎",
        "Harika! Sen nasılsın? 🎯",
        "İyiyim! Sen nasılsın? 🚀",
        "Çok iyiyim dostum! Sen nasılsın? 😄",
        "Harika gidiyor! Sen nasıl? 💫",
        "İyiyim! Sen nasılsın? 🌟",
        "Çok iyiyim! Sen nasıl? 😊",
        "Harika! Sen nasılsın? 💎",
        "İyiyim dostum! Sen nasıl? 🎯"
    ],
    "nasıl gidiyor": [
        "Harika gidiyor! Sen nasıl? 😊",
        "Çok iyi! Sen nasıl? 💎",
        "Mükemmel! Sen nasıl? 🎯",
        "İyi gidiyor! Sen nasıl? 🚀",
        "Harika dostum! Sen nasıl? 😄",
        "Çok iyi gidiyor! Sen nasıl? 💫",
        "Mükemmel! Sen nasıl? 🌟",
        "İyi gidiyor! Sen nasıl? 😊",
        "Harika! Sen nasıl? 💎",
        "Çok iyi dostum! Sen nasıl? 🎯"
    ],
    "ne yapıyorsun": [
        "Sohbete katılıyorum! Sen ne yapıyorsun? 😊",
        "Burada sohbet ediyorum! Sen ne yapıyorsun? 💎",
        "Sohbete katılıyorum! Sen ne yapıyorsun? 🎯",
        "Burada! Sen ne yapıyorsun? 🚀",
        "Sohbete katılıyorum dostum! Sen ne yapıyorsun? 😄",
        "Burada sohbet ediyorum! Sen ne yapıyorsun? 💫",
        "Sohbete katılıyorum! Sen ne yapıyorsun? 🌟",
        "Burada! Sen ne yapıyorsun? 😊",
        "Sohbete katılıyorum! Sen ne yapıyorsun? 💎",
        "Burada dostum! Sen ne yapıyorsun? 🎯"
    ],
    "ne haber": [
        "İyi haber! Sen ne haber? 😊",
        "Çok iyi! Sen ne haber? 💎",
        "Harika! Sen ne haber? 🎯",
        "İyi! Sen ne haber? 🚀",
        "İyi haber dostum! Sen ne haber? 😄",
        "Çok iyi! Sen ne haber? 💫",
        "Harika! Sen ne haber? 🌟",
        "İyi! Sen ne haber? 😊",
        "İyi haber! Sen ne haber? 💎",
        "Çok iyi dostum! Sen ne haber? 🎯"
    ],
    "ne yapıyorsun": [
        "Sohbete katılıyorum! Sen ne yapıyorsun? 😊",
        "Burada sohbet ediyorum! Sen ne yapıyorsun? 💎",
        "Sohbete katılıyorum! Sen ne yapıyorsun? 🎯",
        "Burada! Sen ne yapıyorsun? 🚀",
        "Sohbete katılıyorum dostum! Sen ne yapıyorsun? 😄",
        "Burada sohbet ediyorum! Sen ne yapıyorsun? 💫",
        "Sohbete katılıyorum! Sen ne yapıyorsun? 🌟",
        "Burada! Sen ne yapıyorsun? 😊",
        "Sohbete katılıyorum! Sen ne yapıyorsun? 💎",
        "Burada dostum! Sen ne yapıyorsun? 🎯"
    ],
    "nasıl gidiyor hayat": [
        "Harika gidiyor! Sen nasıl? 😊",
        "Çok iyi! Sen nasıl? 💎",
        "Mükemmel! Sen nasıl? 🎯",
        "İyi gidiyor! Sen nasıl? 🚀",
        "Harika dostum! Sen nasıl? 😄",
        "Çok iyi gidiyor! Sen nasıl? 💫",
        "Mükemmel! Sen nasıl? 🌟",
        "İyi gidiyor! Sen nasıl? 😊",
        "Harika! Sen nasıl? 💎",
        "Çok iyi dostum! Sen nasıl? 🎯"
    ],
    "keyfin nasıl": [
        "Çok iyi! Sen nasıl? 😊",
        "Harika! Sen nasıl? 💎",
        "Mükemmel! Sen nasıl? 🎯",
        "İyi! Sen nasıl? 🚀",
        "Çok iyi dostum! Sen nasıl? 😄",
        "Harika! Sen nasıl? 💫",
        "Mükemmel! Sen nasıl? 🌟",
        "İyi! Sen nasıl? 😊",
        "Çok iyi! Sen nasıl? 💎",
        "Harika dostum! Sen nasıl? 🎯"
    ]
}

# Emoji ve duygu kalıpları
EMOTIONS = {
    "😊": ["😊", "😄", "😁", "😆"],
    "😢": ["😢", "😭", "😔", "😞"],
    "😡": ["😡", "😠", "😤", "😾"],
    "😍": ["😍", "🥰", "😘", "😋"],
    "🤔": ["🤔", "🤨", "🧐", "🤓"],
    "😂": ["😂", "🤣", "😅", "😆"],
    "😎": ["😎", "😏", "😌", "😉"]
}

# Genel sohbet cevapları - Genişletilmiş ve samimi
GENERAL_RESPONSES = [
    "Evet kirvem! 😊",
    "Haklısın! 💎",
    "Aynen öyle! 🎯",
    "Kesinlikle! 🚀",
    "Doğru söylüyorsun! 😊",
    "Evet! 💎",
    "Haklısın kirvem! 🎯",
    "Aynen! 🚀",
    "Evet! 😊",
    "Doğru! 💎",
    "Evet dostum! 😄",
    "Haklısın! 💫",
    "Aynen öyle! 🌟",
    "Kesinlikle! 😊",
    "Doğru söylüyorsun! 💎",
    "Evet! 🎯",
    "Haklısın dostum! 🚀",
    "Aynen! 😄",
    "Evet! 💫",
    "Doğru! 🌟",
    "Evet kirvem! 😊",
    "Haklısın! 💎",
    "Aynen öyle! 🎯",
    "Kesinlikle! 🚀",
    "Doğru söylüyorsun! 😄",
    "Evet! 💫",
    "Haklısın kirvem! 🌟",
    "Aynen! 😊",
    "Evet! 💎",
    "Doğru! 🎯"
]

# KirveHub ile ilgili cevaplar - Genişletilmiş
KIRVEHUB_RESPONSES = [
    "KirveHub harika bir yer! 💎",
    "Burada çok güzel sohbetler oluyor! 🎯",
    "KirveHub'da herkes çok iyi! 😊",
    "KirveHub gerçekten güzel bir topluluk! 🚀",
    "Burada çok samimi bir ortam var! 😄",
    "KirveHub'da herkes dostane! 💫",
    "Burada gerçekten harika insanlar var! 🌟",
    "KirveHub çok güzel bir yer! 😊",
    "Burada çok iyi sohbetler oluyor! 💎",
    "KirveHub'da herkes çok samimi! 🎯",
    "Burada gerçekten güzel bir topluluk var! 🚀",
    "KirveHub harika bir ortam! 😄",
    "Burada çok dostane bir atmosfer var! 💫",
    "KirveHub'da herkes çok iyi! 🌟",
    "Burada gerçekten harika insanlar var! 😊"
]

# Günlük hayat ile ilgili cevaplar
DAILY_LIFE_RESPONSES = [
    "Hayat gerçekten güzel! 😊",
    "Her gün yeni bir macera! 💎",
    "Hayat çok güzel dostum! 🎯",
    "Her gün yeni bir deneyim! 🚀",
    "Hayat gerçekten harika! 😄",
    "Her gün yeni bir fırsat! 💫",
    "Hayat çok güzel! 🌟",
    "Her gün yeni bir başlangıç! 😊",
    "Hayat gerçekten muhteşem! 💎",
    "Her gün yeni bir heyecan! 🎯",
    "Hayat çok güzel dostum! 🚀",
    "Her gün yeni bir deneyim! 😄",
    "Hayat gerçekten harika! 💫",
    "Her gün yeni bir fırsat! 🌟",
    "Hayat çok güzel! 😊"
]

# Motivasyon cevapları
MOTIVATION_RESPONSES = [
    "Sen de harikasın! 😊",
    "Sen de çok iyisin! 💎",
    "Sen de mükemmelsin! 🎯",
    "Sen de harika birisin! 🚀",
    "Sen de çok güzelsin! 😄",
    "Sen de muhteşemsin! 💫",
    "Sen de harika bir dostsun! 🌟",
    "Sen de çok iyisin! 😊",
    "Sen de mükemmelsin! 💎",
    "Sen de harika birisin! 🎯",
    "Sen de çok güzelsin! 🚀",
    "Sen de muhteşemsin! 😄",
    "Sen de harika bir dostsun! 💫",
    "Sen de çok iyisin! 🌟",
    "Sen de mükemmelsin! 😊"
]

# Point sistemi ile ilgili cevaplar
POINT_RESPONSES = [
    "Point kazanmak çok kolay! Her mesajın point kazandırır! 💎",
    "Günlük 5 Kirve Point kazanabilirsin! 🎯",
    "Point sistemi harika! Her mesajın değeri var! 😊",
    "Point kazanmak için sadece sohbet et! 🚀",
    "Point sistemi çok adil! 💎",
    "Her mesajın point kazandırdığını biliyor muydun? 🎯",
    "Point kazanmak için aktif ol! 😊",
    "Point sistemi mükemmel! 🚀",
    "Point kazanmak çok eğlenceli! 💫",
    "Her mesajın point kazandırdığını unutma! 🌟",
    "Point sistemi gerçekten harika! 😄",
    "Point kazanmak için aktif ol dostum! 💎",
    "Point sistemi çok güzel! 🎯",
    "Her mesajın point kazandırdığını biliyor muydun? 😊",
    "Point kazanmak çok kolay! 🚀"
]

# Point sistemi ile ilgili cevaplar
POINT_RESPONSES = [
    "Point kazanmak çok kolay! Her mesajın point kazandırır! 💎",
    "Günlük 5 Kirve Point kazanabilirsin! 🎯",
    "Point sistemi harika! Her mesajın değeri var! 😊",
    "Point kazanmak için sadece sohbet et! 🚀",
    "Point sistemi çok adil! 💎",
    "Her mesajın point kazandırdığını biliyor muydun? 🎯",
    "Point kazanmak için aktif ol! 😊",
    "Point sistemi mükemmel! 🚀"
]

# Kısaltma ve argo sözlüğü
SHORTCUTS = {
    "ab": ("abi", "Erkeklere hitap"),
    "abl": ("abla", "Kadınlara hitap"),
    "aeo": ("allah'a emanet ol", "Vedalaşma sözü"),
    "aq": ("amk", "Küfür kısaltması"),
    "as": ("aleyküm selam", "Selamlaşmaya cevap"),
    "bknz": ("bakınız", "İmla/dalga geçme amaçlı"),
    "bı": ("biri", '"Biri şunu yapsın" gibi'),
    "brn": ("ben", "Kısaltma"),
    "bsl": ("başla", "Genellikle oyunlarda"),
    "byk": ("büyük", "Söyleniş kolaylığı"),
    "cnm": ("canım", "Hitap"),
    "cvp": ("cevap", "Genelde soru-cevapta"),
    "dşn": ("düşün", "Komut gibi kullanılır"),
    "dnz": ("deniz", "İsim yerine geçebilir"),
    "fln": ("falan", "Belirsizlik"),
    "grlz": ("görülez", '“Görülmedi” anlamında, mizahi'),
    "grş": ("görüşürüz", "Veda"),
    "hfd": ("haftada", "Zaman kısaltması"),
    "hşr": ("hoşçakal", "Vedalaşma"),
    "kbs": ("k.bakma sıkıntı yok", "Mizahi kullanılır"),
    "kdn": ("kanka dedin ne", "Mizah"),
    "knk": ("kanka", "Arkadaşça hitap"),
    "krdş": ("kardeş", "Hitap"),
    "lan": ("ulan", "Argo, hitap"),
    "lg": ("lol gibi", "İngilizce etkisi"),
    "lgs": ("lol gibi salaklık", "Şaka"),
    "mrb": ("merhaba", "Selam"),
    "msl": ("mesela", "Örnek vermek için"),
    "nbr": ("ne haber", "Selamlaşma"),
    "np": ("ne problem", '"Sıkıntı yok" anlamında'),
    "oç": ("orospu çocuğu", "Ağır küfür"),
    "pls": ("lütfen", "İngilizce etkisiyle"),
    "qlsn": ("konuşsun", "Mizahi"),
    "sa": ("selamünaleyküm", "Selam"),
    "slm": ("selam", "Kısaca selam"),
    "snn": ("senin", "Kısaltma"),
    "spo": ("spoiler", "Dizi/film ön bilgi uyarısı"),
    "sry": ("sorry", "Özür dilerim (İngilizce)"),
    "sş": ("sessiz", "Mizahi ya da komut"),
    "tmm": ("tamam", "Onay"),
    "tk": ("takıl", "Mizahi/davet"),
    "tnq": ("thank you", "İngilizce etkisi"),
    "trkr": ("tekrar", "Sıkça yazışmada geçer"),
    "tşk": ("teşekkür", "Teşekkür etme"),
    "tşkrlr": ("teşekkürler", "Daha resmi"),
    "üzdü": ("üzülme sebebi", "Kısa tepki"),
    "yb": ("yap bakalım", "Mizah"),
    "yk": ("yok", "Red cevabı"),
    "ykrm": ("yakarım", "Tehdit/şaka"),
    "ytd": ("yatırım tavsiyesi değildir", "Kripto sohbetlerinde")
}

# Küfür/argo kelimeler
BAD_WORDS = ["aq", "amk", "oç", "lan"]

# Veda kısaltmaları
FAREWELLS = ["aeo", "grş", "hşr"]

# Selamlaşma kısaltmaları
GREET_SHORTS = ["mrb", "slm", "sa", "nbr", "as"]

# Jargonlara özel hazır cevaplar
JARGON_REPLIES = {
    "mrb": "Selam knk! Nasılsın?",
    "slm": "Selam! Nasılsın?",
    "sa": "Aleyküm selam! Hoş geldin!",
    "nbr": "İyiyim knk, sen nasılsın?",
    "as": "Aleyküm selam!",
    "aeo": "Allah'a emanet ol, kendine dikkat et! 👋",
    "grş": "Görüşürüz, kendine iyi bak!",
    "hşr": "Hoşçakal! Görüşmek üzere!",
    "tşk": "Rica ederim knk!",
    "tşkrlr": "Rica ederim, her zaman!",
    "pls": "Tabii, hemen hallediyorum!",
    "cvp": "Cevap veriyorum knk!",
    "kdn": "Kanka dedin ne? 😂",
    "kbs": "K.bakma sıkıntı yok, devam!",
    "yb": "Yap bakalım, görelim 😎",
    "qlsn": "Biri konuşsun mu dedin? Ben buradayım!",
    "tk": "Takıl kafana göre knk!",
    "byk": "Büyük düşün, büyük yaşa!",
    "brn": "Ben de buradayım!",
    "bsl": "Başla bakalım, izliyorum!",
    "trkr": "Tekrar tekrar denemekten vazgeçme!",
    "spo": "Spoiler verme knk, izlemeyen var!",
    "sry": "Sorun yok, canın sağ olsun!",
    "tnq": "Thank you too!",
    "msl": "Mesela? Devam et!",
    "fln": "Falan filan işte...",
    "hfd": "Haftada bir görüşelim knk!",
    "dşn": "Düşün bakalım, belki güzel bir fikir çıkar!",
    "sş": "Sessiz mod açıldı...",
    "oç": "Knk, ağır oldu bu! Biraz sakin 😅",
    "aq": "Knk, biraz yavaş olalım 😅",
    "amk": "Knk, argo fazla oldu!", 
    "lan": "Lan demesek daha iyi olur knk!",
    "kanka": "Kanka! Buradayım, ne var ne yok?",
    "knk": "Kanka! Nasılsın?",
    "abi": "Abi, buyur dinliyorum!",
    "abla": "Abla, buradayım!",
    "krdş": "Kardeşim, ne var ne yok?",
    "cnm": "Canım, ne oldu?",
    "kirvem": "Kirvem! Her zaman buradayım!",
    "kirve": "Kirve! Ne var ne yok?",
    "üzdü": "Üzülme knk, her şey yoluna girer!",
    "yk": "Yok mu başka soru?",
    "ykrm": "Yakarım buraları şaka şaka! 😂",
    "ytd": "Yatırım tavsiyesi değildir, kriptoya dikkat!",
}

import re

def find_shortcuts(text):
    found = []
    for k in SHORTCUTS:
        # kelime olarak geçiyorsa
        if re.search(rf"\\b{k}\\b", text):
            found.append(k)
    return found

def find_jargon_reply(text):
    # En son geçen ve baskın jargon için cevap döndür
    found = []
    for k in JARGON_REPLIES:
        if re.search(rf"\\b{k}\\b", text):
            found.append(k)
    if found:
        # En son geçen jargonun cevabını döndür
        return JARGON_REPLIES[found[-1]]
        return None
        
async def handle_chat_message(message: Message) -> Optional[str]:
    """
    Sohbet mesajını analiz et ve uygun cevabı döndür
    """
    try:
        user_id = message.from_user.id
        text = message.text.lower().strip()
        
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
            
        # Kayıt kontrolü - Kayıtlı olmayan kullanıcılar için de cevap ver
        is_registered = await is_user_registered(user_id)
        
        # Mesajı kaydet
        await cooldown_manager.record_user_message(user_id)
        
        # Jargonlara özel cevap
        jargon_reply = find_jargon_reply(text)
        if jargon_reply:
            yanit = jargon_reply
            logger.info(f"✅ Jargon cevabı: {yanit}")
            return yanit

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

        # Selamlaşma kontrolü
        for greeting, responses in GREETINGS.items():
            if greeting in text:
                response = random.choice(responses)
                logger.info(f"✅ Selamlaşma cevabı: {response}")
                return response
                
        # Soru kontrolü
        for question, responses in QUESTIONS.items():
            if question in text:
                response = random.choice(responses)
                logger.info(f"✅ Soru cevabı: {response}")
                return response
                
        # Emoji kontrolü
        for emoji in EMOTIONS:
            if emoji in text:
                response_emoji = random.choice(EMOTIONS[emoji])
                response = f"{response_emoji}"
                logger.info(f"✅ Emoji cevabı: {response}")
                return response
                
        # KirveHub kelimesi kontrolü
        if "kirve" in text or "kirvehub" in text:
            response = random.choice(KIRVEHUB_RESPONSES)
            logger.info(f"✅ KirveHub cevabı: {response}")
            return response
            
        # Point kelimesi kontrolü
        if "point" in text or "puan" in text or "kp" in text:
            response = random.choice(POINT_RESPONSES)
            logger.info(f"✅ Point cevabı: {response}")
            return response
            
        # Günlük hayat kelimeleri kontrolü
        if any(word in text for word in ["hayat", "gün", "yaşam", "dünya"]):
            response = random.choice(DAILY_LIFE_RESPONSES)
            logger.info(f"✅ Günlük hayat cevabı: {response}")
            return response
            
        # Motivasyon kelimeleri kontrolü
        if any(word in text for word in ["güzel", "harika", "mükemmel", "süper", "muhteşem"]):
            response = random.choice(MOTIVATION_RESPONSES)
            logger.info(f"✅ Motivasyon cevabı: {response}")
            return response
            
        # Genel cevaplar (düşük ihtimalle)
        if random.random() < 0.1:
            response = random.choice(GENERAL_RESPONSES)
            logger.info(f"✅ Genel cevap: {response}")
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
        
        if not is_registered:
            # Kayıtlı olmayan kullanıcıya kayıt yönlendirmesi
            response += "\n\n💡 İpucu: Kayıt olarak point kazanabilirsin!"
        
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
        "greetings_count": len(GREETINGS),
        "questions_count": len(QUESTIONS),
        "general_responses_count": len(GENERAL_RESPONSES),
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
        if user_id != config.ADMIN_USER_ID:
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

async def _send_bot_write_privately(user_id: int, command_text: str):
    """Botyaz mesajını özel mesajla gönder"""
    try:
        if not _bot_instance:
            logger.error("❌ Bot instance bulunamadı!")
            return
        
        # Admin kontrolü
        from config import get_config
        config = get_config()
        if user_id != config.ADMIN_USER_ID:
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