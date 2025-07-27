"""
🏛️ Grup Yönetimi Handler'ı
/kirvegrup komutu ve grup kayıt sistemi
"""

import logging
from aiogram import types
from aiogram.types import Message

from database import register_group, is_group_registered, has_permission, get_user_rank
from config import get_config

logger = logging.getLogger(__name__)


async def kirvegrup_command(message: Message) -> None:
    """
    /kirvegrup komutu - Grubu sisteme kayıt et
    Sadece Üst Yetkili - Admin 2 ve üstü kullanabilir
    """
    try:
        user = message.from_user
        chat = message.chat
        
        logger.info(f"🏛️ /kirvegrup komutu - User: {user.first_name} ({user.id}) - Chat: {chat.id}")
        
        # Chat tipi kontrolü - sadece grup/supergroup
        if chat.type not in ['group', 'supergroup']:
            # Private'daysa normal cevap ver
            await message.answer(
                "❌ Bu komut sadece gruplarda kullanılabilir!",
                reply_to_message_id=message.message_id
            )
            return
        
        # Yetki kontrolü - Üst Yetkili - Admin 2 veya üstü
        has_group_permission = await has_permission(user.id, "register_group")
        user_rank = await get_user_rank(user.id)
        
        if not has_group_permission:
            # YETKİ HATASI: Sadece özel mesajla bildir, grup chatinde hiçbir şey yazma
            try:
                from aiogram import Bot
                from config import get_config
                config = get_config()
                
                temp_bot = Bot(token=config.BOT_TOKEN)
                
                error_response = f"""
🚫 **Yetki Hatası - /kirvegrup**

Bu komutu **{chat.title}** grubunda kullanmaya çalıştınız ancak yetkiniz yok.

👤 **Mevcut Durumunuz:**
🎖️ Rütbe: {user_rank.get('rank_name', 'Üye')}
⭐ Seviye: {user_rank.get('rank_level', 1)}

⚠️ **Gerekli Yetki:**
👑 Üst Yetkili - Admin 2 (Seviye 3)
🛡️ Grup kayıt yetkisi

📝 **Grup Bilgileri:**
🏷️ Grup: {chat.title}
🆔 ID: `{chat.id}`

_Yetki talebi için Super Admin'le iletişime geçin._
                """
                
                await temp_bot.send_message(
                    chat_id=user.id,
                    text=error_response,
                    parse_mode="Markdown"
                )
                await temp_bot.session.close()
                
            except Exception as e:
                logger.error(f"❌ Yetki hatası mesajı gönderilemedi: {e}")
            
            return
        
        # Grup zaten kayıtlı mı kontrol et
        if await is_group_registered(chat.id):
            # ZATEN KAYITLI: Sadece özel mesajla bildir
            try:
                from aiogram import Bot
                from config import get_config
                config = get_config()
                
                temp_bot = Bot(token=config.BOT_TOKEN)
                
                already_registered_response = f"""
ℹ️ **Grup Durumu - /kirvegrup**

**{chat.title}** grubu zaten sistemde kayıtlı!

✅ **Mevcut Durum:**
💎 Kirve Point sistemi aktif
📈 Otomatik sistem çalışıyor
🎯 Güvenlik koruması aktif
💰 Sessiz mod aktif

📊 **Grup Bilgileri:**
🏷️ Ad: {chat.title}
🆔 ID: `{chat.id}`
📝 Username: @{chat.username if chat.username else 'Yok'}

_Grup zaten aktif durumda! 🚀_
                """
                
                await temp_bot.send_message(
                    chat_id=user.id,
                    text=already_registered_response,
                    parse_mode="Markdown"
                )
                await temp_bot.session.close()
                
            except Exception as e:
                logger.error(f"❌ Zaten kayıtlı mesajı gönderilemedi: {e}")
            
            return
        
        # Grubu kayıt et
        success = await register_group(
            group_id=chat.id,
            group_name=chat.title or "Bilinmeyen Grup",
            group_username=chat.username,
            registered_by=user.id
        )
        
        if success:
            # GRUP CHATİNDE: Hiçbir şey yazma - sadece sessizlik
            
            # ADMİN'E ÖZEL: Hem başarı hem grup kayıt detayları
            admin_response = f"""
🔐 **Admin Bildirimi - Grup Kayıt**

✅ **Grup başarıyla sisteme kayıt edildi!**

📊 *Grup Bilgileri:*
🏷️ **Ad:** {chat.title or 'Bilinmeyen'}
🆔 **ID:** `{chat.id}`
📝 **Username:** @{chat.username if chat.username else 'Yok'}
👥 **Tip:** {chat.type.title()}

👤 *İşlem Detayları:*
🎯 **Kayıt Eden:** {user.first_name} {user.last_name or ''}
🆔 **Admin ID:** `{user.id}`
👑 **Rütbe:** {user_rank.get('rank_name', 'Admin')} (Level {user_rank.get('rank_level', 0)})

💎 *Kirve Point Sistemi:*
✅ **Durum:** Aktif
🎯 **Sistem:** Otomatik çalışıyor
🛡️ **Güvenlik:** Spam koruması aktif
🔇 **Mod:** Sessiz çalışma

⚙️ *Sistem Özellikleri:*
🎮 Otomatik sistem çalışıyor
📊 Limit kontrolü aktif
🚫 Flood koruması (10sn interval)
📈 İstatistik takibi aktif
🔄 Auto-recruitment aktif
🔇 Grup sessizlik modu

_Grup artık sisteme kayıtlı! Bot sessizce çalışıyor._ 🛡️
            """
            
            # Admin'e özel mesaj gönder
            try:
                from aiogram import Bot
                from config import get_config
                config = get_config()
                
                # Bot instance oluştur (geçici)
                temp_bot = Bot(token=config.BOT_TOKEN)
                await temp_bot.send_message(
                    chat_id=user.id,
                    text=admin_response,
                    parse_mode="Markdown"
                )
                await temp_bot.session.close()
                
            except Exception as e:
                logger.error(f"❌ Admin'e özel mesaj gönderilemedi: {e}")
                # Grup chatinde hata bildirimi verme
            
            logger.info(f"✅ Grup kayıt edildi - Group: {chat.title} ({chat.id}) by User: {user.id}")
            
        else:
            # HATA DURUMU: Sadece özel mesajla bildir
            try:
                from aiogram import Bot
                from config import get_config
                config = get_config()
                
                temp_bot = Bot(token=config.BOT_TOKEN)
                
                error_response = f"""
❌ **Grup Kayıt Hatası**

**{chat.title}** grubu kayıt edilirken bir hata oluştu!

📊 **Denenen İşlem:**
🏷️ Grup: {chat.title}
🆔 ID: `{chat.id}`
👤 Admin: {user.first_name}

🔧 **Çözüm Önerileri:**
• Birkaç dakika bekleyip tekrar deneyin
• Bot'un grup yöneticisi olduğundan emin olun
• Database bağlantısı kontrol ediliyor

_Sorun devam ederse Super Admin'e bildirin._
                """
                
                await temp_bot.send_message(
                    chat_id=user.id,
                    text=error_response,
                    parse_mode="Markdown"
                )
                await temp_bot.session.close()
                
            except Exception as e:
                logger.error(f"❌ Hata mesajı gönderilemedi: {e}")
            
    except Exception as e:
        logger.error(f"❌ /kirvegrup handler hatası: {e}")
        
        # GENEL HATA: Sadece özel mesajla bildir
        try:
            from aiogram import Bot
            from config import get_config
            config = get_config()
            
            temp_bot = Bot(token=config.BOT_TOKEN)
            
            general_error = f"""
❌ **Sistem Hatası - /kirvegrup**

Beklenmeyen bir hata oluştu!

🔧 **Hata Detayları:**
📝 Komut: /kirvegrup
🏷️ Grup: {chat.title if 'chat' in locals() else 'Bilinmiyor'}
👤 Kullanıcı: {user.first_name}

⚠️ **Bu hata loglandı ve incelenecek.**

_Lütfen daha sonra tekrar deneyin veya Super Admin'e bildirin._
            """
            
            await temp_bot.send_message(
                chat_id=user.id,
                text=general_error,
                parse_mode="Markdown"
            )
            await temp_bot.session.close()
            
        except:
            pass  # Çifte hata durumunda sessiz kal


async def group_info_command(message: Message) -> None:
    """
    /grupbilgi komutu - Grup hakkında bilgi al
    """
    try:
        user = message.from_user
        chat = message.chat
        
        logger.info(f"ℹ️ /grupbilgi komutu - User: {user.first_name} ({user.id}) - Chat: {chat.id}")
        
        # Chat tipi kontrolü
        if chat.type not in ['group', 'supergroup']:
            # Private'daysa normal cevap ver
            await message.answer(
                "❌ Bu komut sadece gruplarda kullanılabilir!",
                reply_to_message_id=message.message_id
            )
            return
        
        # GRUP BİLGİLERİ: Sadece özel mesajla gönder
        try:
            from aiogram import Bot
            from config import get_config
            config = get_config()
            
            temp_bot = Bot(token=config.BOT_TOKEN)
            
            # Grup kayıtlı mı kontrol et
            is_registered = await is_group_registered(chat.id)
            
            if is_registered:
                response = f"""
ℹ️ **Grup Bilgileri - /grupbilgi**

🏷️ **Grup Adı:** {chat.title or 'Bilinmeyen'}
🆔 **Grup ID:** `{chat.id}`
👥 **Tip:** {chat.type.title()}
📝 **Username:** @{chat.username if chat.username else 'Yok'}

💎 **Kirve Point Sistemi:**
✅ **Durum:** Aktif
🎯 **Sistem:** Otomatik çalışıyor
🛡️ **Güvenlik:** Spam koruması aktif
🔇 **Mod:** Sessiz çalışma

📊 **Aktif Özellikler:**
🎮 Otomatik sistem
📈 İstatistik takibi  
🚫 Güvenlik koruması
🎯 Auto-recruitment sistemi
🔇 Grup sessizlik modu

⚙️ **Admin Özellikleri:**
• Dinamik ayarlar
• Limit kontrolü  
• Gerçek zamanlı monitoring

_Sistem otomatik olarak çalışıyor! 🚀_
                """
            else:
                response = f"""
ℹ️ **Grup Bilgileri - /grupbilgi**

🏷️ **Grup Adı:** {chat.title or 'Bilinmeyen'}
🆔 **Grup ID:** `{chat.id}`
👥 **Tip:** {chat.type.title()}
📝 **Username:** @{chat.username if chat.username else 'Yok'}

💎 **Kirve Point Sistemi:**
❌ **Durum:** Pasif

⚠️ **Point Kazanımı Mevcut Değil**
Bu grupta henüz point sistemi aktif değil.

🔧 **Grup Kayıt İçin:**
Üst Yetkili - Admin 2 rütbesindeki yöneticiler `/kirvegrup` komutunu kullanabilir.

🎯 **Kayıt Sonrası:**
• Otomatik sistem aktif olur
• Güvenlik koruması devreye girer
• Auto-recruitment sistemi çalışır
• Sessiz mod aktif olur

_Grup kayıt edilirse sistem aktif olur! 📈_
                """
                
            await temp_bot.send_message(
                chat_id=user.id,
                text=response,
                parse_mode="Markdown"
            )
            await temp_bot.session.close()
            
        except Exception as e:
            logger.error(f"❌ Grup bilgisi mesajı gönderilemedi: {e}")
        
    except Exception as e:
        logger.error(f"❌ /grupbilgi handler hatası: {e}")
        
        # GRUP BİLGİ HATASI: Sadece özel mesajla bildir
        try:
            from aiogram import Bot
            from config import get_config
            config = get_config()
            
            temp_bot = Bot(token=config.BOT_TOKEN)
            
            error_response = f"""
❌ **Sistem Hatası - /grupbilgi**

Grup bilgileri alınırken hata oluştu!

🔧 **Hata Detayları:**
📝 Komut: /grupbilgi
🏷️ Grup: {chat.title if 'chat' in locals() else 'Bilinmiyor'}
👤 Kullanıcı: {user.first_name}

⚠️ **Bu hata loglandı ve incelenecek.**

_Lütfen daha sonra tekrar deneyin._
            """
            
            await temp_bot.send_message(
                chat_id=user.id,
                text=error_response,
                parse_mode="Markdown"
            )
            await temp_bot.session.close()
            
        except:
            pass  # Çifte hata durumunda sessiz kal 