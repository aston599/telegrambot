"""
🛡️ Admin Komutları - KirveHub Bot
Yeni modüler yapıyı kullanır (admin_permission_manager.py)
"""

import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from typing import Optional

from config import get_config
from handlers.admin_permission_manager import (
    make_user_admin, remove_user_admin, get_user_admin_info, 
    get_admin_list, get_rank_name, get_rank_permissions,
    find_user_by_username_db, send_error_message, send_response_message
)
from utils.logger import logger

router = Router()

# Bot instance setter
_bot_instance = None

def set_bot_instance(bot_instance):
    global _bot_instance
    _bot_instance = bot_instance

async def delete_message_after_delay(message, delay=5):
    """Mesajı belirtilen süre sonra sil"""
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except:
        pass

# Admin seviye kontrolü fonksiyonları
def check_admin_permission(user_id: int, required_level: int) -> bool:
    """Kullanıcının admin seviyesini kontrol et"""
    try:
        config = get_config()
        # Super Admin her zaman erişebilir
        if user_id == config.ADMIN_USER_ID:
            return True
        
        # Diğer kullanıcılar için seviye kontrolü (gelecekte implement edilecek)
        # Şimdilik sadece Super Admin erişebilir
        return False
        
    except Exception as e:
        logger.error(f"❌ Admin permission check hatası: {e}")
        return False

def get_admin_level_name(level: int) -> str:
    """Admin seviye isimlerini getir"""
    levels = {
        1: "Üye",
        2: "Admin 1", 
        3: "Admin 2",
        4: "Super Admin"
    }
    return levels.get(level, "Bilinmiyor")

def get_admin_permissions(level: int) -> str:
    """Admin seviye yetkilerini getir"""
    permissions = {
        1: "Temel komutlar",
        2: "Grup yönetimi, mesaj silme",
        3: "Etkinlik yönetimi, market yönetimi", 
        4: "Tüm yetkiler"
    }
    return permissions.get(level, "Bilinmiyor")

@router.message(Command("adminyap"))
async def make_admin_command(message: Message) -> None:
    """Admin yetkisi verme: /adminyap @username SEVİYE veya reply ile /adminyap SEVİYE"""
    try:
        # Detaylı log
        from handlers.detailed_logging_system import log_command_execution, log_admin_action
        await log_command_execution(
            user_id=message.from_user.id,
            username=message.from_user.username or message.from_user.first_name,
            command="adminyap",
            chat_id=message.chat.id,
            chat_type=message.chat.type
        )
        
        # Admin seviye kontrolü (Admin 3+ gerekli)
        if not check_admin_permission(message.from_user.id, 3):
            await send_error_message(message, "❌ Bu komutu kullanmak için Admin 2+ seviyesi gerekli!")
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        user_id = None
        admin_level = None
        
        # 1. Reply ile kullanım: /adminyap SEVİYE
        if message.reply_to_message and len(parts) == 2:
            try:
                user_id = message.reply_to_message.from_user.id
                admin_level = int(parts[1])
            except ValueError:
                await send_error_message(message, "❌ Geçersiz seviye! Örnek: `/adminyap 2`")
                return
        
        # 2. Etiket ile kullanım: /adminyap @username SEVİYE
        elif len(parts) == 3 and parts[1].startswith('@'):
            try:
                username = parts[1][1:]  # @ işaretini kaldır
                admin_level = int(parts[2])
                
                # Username'den user_id bul
                result = await find_user_by_username_db(username)
                if not result["success"]:
                    await send_error_message(message, result["error"])
                    return
                    
                user_id = result["user"]["user_id"]
                    
            except ValueError:
                await send_error_message(message, "❌ Geçersiz seviye! Örnek: `/adminyap @username 2`")
                return
        
        else:
            await send_error_message(message, "❌ Kullanım:\n• `/adminyap SEVİYE` (reply ile)\n• `/adminyap @username SEVİYE` (etiket ile)")
            return
        
        if admin_level < 1 or admin_level > 4:
            await send_error_message(message, "❌ Seviye 1-4 arası olmalı!\n• 1: Üye\n• 2: Admin 1\n• 3: Admin 2\n• 4: Super Admin")
            return
        
        # Admin yetkisi ver (modüler yapıyı kullan)
        result = await make_user_admin(user_id, admin_level)
        
        if result["success"]:
            response = f"""
✅ **Admin Yetkisi Verildi!**

**👤 User ID:** {user_id}
**👤 İsim:** {result["user_name"]}
**🛡️ Eski Seviye:** {get_rank_name(result["old_rank"])}
**🛡️ Yeni Seviye:** {get_rank_name(admin_level)}
**👑 Yetki:** {get_rank_permissions(admin_level)}
            """
        else:
            response = f"❌ Hata: {result['error']}"
        
        await send_response_message(message, response)
        
    except Exception as e:
        logger.error(f"❌ Make admin hatası: {e}")
        await send_error_message(message, "❌ Bir hata oluştu!")

@router.message(Command("adminçıkar"))
async def remove_admin_command(message: Message) -> None:
    """Admin yetkisi alma: /adminçıkar @username veya reply ile /adminçıkar"""
    try:
        # Admin seviye kontrolü (Admin 3+ gerekli)
        if not check_admin_permission(message.from_user.id, 3):
            await send_error_message(message, "❌ Bu komutu kullanmak için Admin 2+ seviyesi gerekli!")
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        user_id = None
        
        # 1. Reply ile kullanım: /adminçıkar
        if message.reply_to_message and len(parts) == 1:
            user_id = message.reply_to_message.from_user.id
        
        # 2. Etiket ile kullanım: /adminçıkar @username
        elif len(parts) == 2 and parts[1].startswith('@'):
            username = parts[1][1:]  # @ işaretini kaldır
            
            # Username'den user_id bul
            result = await find_user_by_username_db(username)
            if not result["success"]:
                await send_error_message(message, result["error"])
                return
                
            user_id = result["user"]["user_id"]
        
        else:
            await send_error_message(message, "❌ Kullanım:\n• `/adminçıkar` (reply ile)\n• `/adminçıkar @username` (etiket ile)")
            return
        
        # Kendini admin çıkarma kontrolü
        if user_id == message.from_user.id:
            await send_error_message(message, "❌ Kendinizi admin çıkaramazsınız!")
            return
        
        # Admin yetkisini al (modüler yapıyı kullan)
        result = await remove_user_admin(user_id)
        
        if result["success"]:
            response = f"""
❌ **Admin Yetkisi Alındı!**

**👤 User ID:** {user_id}
**👤 İsim:** {result["user_name"]}
**🛡️ Eski Seviye:** {get_rank_name(result["old_rank"])}
**🛡️ Yeni Seviye:** Üye
**👑 Yetki:** Temel komutlar
            """
        else:
            response = f"❌ Hata: {result['error']}"
        
        await send_response_message(message, response)
        
    except Exception as e:
        logger.error(f"❌ Remove admin hatası: {e}")
        await send_error_message(message, "❌ Bir hata oluştu!")

@router.message(Command("adminlist"))
async def list_admins_command(message: Message) -> None:
    """Admin listesi: /adminlist"""
    try:
        # Admin seviye kontrolü (Admin 2+ gerekli)
        if not check_admin_permission(message.from_user.id, 2):
            await send_error_message(message, "❌ Bu komutu kullanmak için Admin 1+ seviyesi gerekli!")
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Admin listesini al (modüler yapıyı kullan)
        result = await get_admin_list()
        
        if result["success"]:
            admin_list = "🛡️ **ADMİN LİSTESİ**\n\n"
            
            for admin in result["admins"]:
                level_name = get_rank_name(admin["rank_id"])
                username = admin['username'] or 'Kullanıcı adı yok'
                last_activity = admin['last_activity'].strftime('%d.%m.%Y %H:%M') if admin['last_activity'] else 'Bilinmiyor'
                
                admin_list += f"👤 **{admin['first_name']}** (@{username})\n"
                admin_list += f"🛡️ **Seviye:** {level_name}\n"
                admin_list += f"📅 **Son Aktivite:** {last_activity}\n\n"
            
            admin_list += f"📊 **Toplam Admin:** {len(result['admins'])} kişi"
            
            await send_response_message(message, admin_list)
        else:
            await send_error_message(message, f"❌ Hata: {result['error']}")
        
    except Exception as e:
        logger.error(f"❌ List admins hatası: {e}")
        await send_error_message(message, "❌ Bir hata oluştu!")

@router.message(Command("admininfo"))
async def admin_info_command(message: Message) -> None:
    """Kullanıcı admin bilgisi: /admininfo @username veya reply ile /admininfo"""
    try:
        # Admin seviye kontrolü (Admin 2+ gerekli)
        if not check_admin_permission(message.from_user.id, 2):
            await send_error_message(message, "❌ Bu komutu kullanmak için Admin 1+ seviyesi gerekli!")
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        user_id = None
        
        # 1. Reply ile kullanım: /admininfo
        if message.reply_to_message and len(parts) == 1:
            user_id = message.reply_to_message.from_user.id
        
        # 2. Etiket ile kullanım: /admininfo @username
        elif len(parts) == 2 and parts[1].startswith('@'):
            username = parts[1][1:]  # @ işaretini kaldır
            
            # Username'den user_id bul
            result = await find_user_by_username_db(username)
            if not result["success"]:
                await send_error_message(message, result["error"])
                return
                
            user_id = result["user"]["user_id"]
        
        else:
            await send_error_message(message, "❌ Kullanım:\n• `/admininfo` (reply ile)\n• `/admininfo @username` (etiket ile)")
            return
        
        # Kullanıcı bilgilerini al (modüler yapıyı kullan)
        result = await get_user_admin_info(user_id)
        
        if result["success"]:
            user = result["user"]
            level_name = get_rank_name(user["rank_id"])
            permissions = get_rank_permissions(user["rank_id"])
            last_activity = user['last_activity'].strftime('%d.%m.%Y %H:%M') if user['last_activity'] else 'Bilinmiyor'
            username = user['username'] or 'Kullanıcı adı yok'
            
            response = f"""
👤 **KULLANICI BİLGİLERİ**

**🆔 User ID:** {user_id}
**👤 İsim:** {user['first_name']}
**🏷️ Username:** @{username}
**🛡️ Seviye:** {level_name}
**👑 Yetki:** {permissions}
**📅 Son Aktivite:** {last_activity}
**✅ Kayıtlı:** {'Evet' if user['is_registered'] else 'Hayır'}
            """
        else:
            response = f"❌ Hata: {result['error']}"
        
        await send_response_message(message, response)
        
    except Exception as e:
        logger.error(f"❌ Admin info hatası: {e}")
        await send_error_message(message, "❌ Bir hata oluştu!")

@router.message(Command("yetkiver"))
async def give_permission_command(message: Message) -> None:
    """Yetki verme: /yetkiver @username SEVİYE veya reply ile /yetkiver SEVİYE"""
    # /adminyap komutunun aynısı, sadece farklı isim
    await make_admin_command(message)

@router.message(Command("yetkial"))
async def take_permission_command(message: Message) -> None:
    """Yetki alma: /yetkial @username veya reply ile /yetkial"""
    try:
        # Admin seviye kontrolü (Admin 3+ gerekli)
        if not check_admin_permission(message.from_user.id, 3):
            await send_error_message(message, "❌ Bu komutu kullanmak için Admin 2+ seviyesi gerekli!")
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        user_id = None
        
        # 1. Reply ile kullanım: /yetkial
        if message.reply_to_message and len(parts) == 1:
            user_id = message.reply_to_message.from_user.id
        
        # 2. Etiket ile kullanım: /yetkial @username
        elif len(parts) == 2 and parts[1].startswith('@'):
            username = parts[1][1:]  # @ işaretini kaldır
            
            # Username'den user_id bul
            result = await find_user_by_username_db(username)
            if not result["success"]:
                await send_error_message(message, result["error"])
                return
                
            user_id = result["user"]["user_id"]
        
        else:
            await send_error_message(message, "❌ Kullanım:\n• `/yetkial` (reply ile)\n• `/yetkial @username` (etiket ile)")
            return
        
        # Kendini yetki alma kontrolü
        if user_id == message.from_user.id:
            await send_error_message(message, "❌ Kendinizden yetki alamazsınız!")
            return
        
        # Yetkiyi al (modüler yapıyı kullan)
        result = await remove_user_admin(user_id)
        
        if result["success"]:
            response = f"""
❌ **Yetki Alındı!**

**👤 User ID:** {user_id}
**👤 İsim:** {result["user_name"]}
**🛡️ Eski Seviye:** {get_rank_name(result["old_rank"])}
**🛡️ Yeni Seviye:** Üye
**👑 Yetki:** Temel komutlar
            """
        else:
            response = f"❌ Hata: {result['error']}"
        
        await send_response_message(message, response)
        
    except Exception as e:
        logger.error(f"❌ Take permission hatası: {e}")
        await send_error_message(message, "❌ Bir hata oluştu!")

@router.message(Command("komutsil"))
async def delete_command_command(message: Message) -> None:
    """Komut silme: /komutsil veya /komutsil ID"""
    try:
        # Admin seviye kontrolü (Admin 4+ gerekli - Super Admin)
        if not check_admin_permission(message.from_user.id, 4):
            await send_error_message(message, "❌ Bu komutu kullanmak için Super Admin seviyesi gerekli!")
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        # Sadece /komutsil yazıldıysa - kullanım bilgisi ve komut listesi göster
        if len(parts) == 1:
            from database import list_custom_commands
            
            commands = await list_custom_commands()
            
            if not commands:
                await message.reply("❌ Hiç komut yok!")
                return
            
            response = "🗑️ **KOMUT SİLME**\n\n"
            response += "**Kullanım:** `/komutsil ID`\n"
            response += "**Örnek:** `/komutsil 1`\n\n"
            response += "**📋 Mevcut Komutlar:**\n"
            
            for cmd in commands[:10]:  # İlk 10 komut
                response += f"**ID: {cmd['id']}** `{cmd['command_name']}`\n"
                response += f"   📝 {cmd['reply_text'][:30]}...\n\n"
            
            if len(commands) > 10:
                response += f"... ve {len(commands) - 10} komut daha\n\n"
            
            response += "**Silmek için ID yazın:** `/komutsil ID`"
            
            await message.reply(response, parse_mode="Markdown")
            return
        
        # /komutsil ID yazıldıysa - komutu sil
        if len(parts) == 2:
            try:
                command_id = int(parts[1])
            except ValueError:
                await message.reply("❌ Geçersiz ID! Sayı olmalı.")
                return
            
            # Komutu sil
            from database import delete_custom_command_by_id
            
            success = await delete_custom_command_by_id(command_id)
            
            if success:
                await message.reply(f"✅ Komut başarıyla silindi! ID: {command_id}")
            else:
                await message.reply(f"❌ Komut silinemedi! ID: {command_id}")
            
            return
        
        # Yanlış kullanım
        await message.reply("❌ Kullanım:\n• `/komutsil` - Komut listesi\n• `/komutsil ID` - Komut sil")
        
    except Exception as e:
        logger.error(f"❌ Komut silme hatası: {e}")
        await message.reply("❌ Bir hata oluştu!")

@router.message(Command("adminseviye"))
async def check_admin_level_command(message: Message) -> None:
    """Admin seviye kontrolü: /adminseviye @username veya reply ile /adminseviye"""
    try:
        # Admin seviye kontrolü (Admin 2+ gerekli)
        if not check_admin_permission(message.from_user.id, 2):
            await send_error_message(message, "❌ Bu komutu kullanmak için Admin 1+ seviyesi gerekli!")
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        # Komut metnini parse et
        command_text = message.text.strip()
        parts = command_text.split()
        
        user_id = None
        
        # 1. Reply ile kullanım: /adminseviye
        if message.reply_to_message and len(parts) == 1:
            user_id = message.reply_to_message.from_user.id
        
        # 2. Etiket ile kullanım: /adminseviye @username
        elif len(parts) == 2 and parts[1].startswith('@'):
            username = parts[1][1:]  # @ işaretini kaldır
            
            # Username'den user_id bul
            result = await find_user_by_username_db(username)
            if not result["success"]:
                await send_error_message(message, result["error"])
                return
                
            user_id = result["user"]["user_id"]
        
        else:
            await send_error_message(message, "❌ Kullanım:\n• `/adminseviye` (reply ile)\n• `/adminseviye @username` (etiket ile)")
            return
        
        # Kullanıcı bilgilerini al
        result = await get_user_admin_info(user_id)
        
        if result["success"]:
            user = result["user"]
            level_name = get_rank_name(user["rank_id"])
            permissions = get_rank_permissions(user["rank_id"])
            last_activity = user['last_activity'].strftime('%d.%m.%Y %H:%M') if user['last_activity'] else 'Bilinmiyor'
            username = user['username'] or 'Kullanıcı adı yok'
            
            response = f"""
🛡️ **ADMİN SEVİYE KONTROLÜ**

**👤 User ID:** {user_id}
**👤 İsim:** {user['first_name']}
**🏷️ Username:** @{username}
**🛡️ Seviye:** {level_name}
**👑 Yetki:** {permissions}
**📅 Son Aktivite:** {last_activity}
**✅ Kayıtlı:** {'Evet' if user['is_registered'] else 'Hayır'}
            """
        else:
            response = f"❌ Hata: {result['error']}"
        
        await send_response_message(message, response)
        
    except Exception as e:
        logger.error(f"❌ Admin seviye kontrol hatası: {e}")
        await send_error_message(message, "❌ Bir hata oluştu!")

@router.message(Command("adminyardım"))
async def admin_help_command(message: Message) -> None:
    """Admin komutları yardım: /adminyardım"""
    try:
        # Admin seviye kontrolü (Admin 1+ gerekli)
        if not check_admin_permission(message.from_user.id, 1):
            await send_error_message(message, "❌ Bu komutu kullanmak için Admin seviyesi gerekli!")
            return
        
        # Grup chatindeyse komut mesajını sil ve sessiz çalış
        if message.chat.type != "private":
            try:
                await message.delete()
            except:
                pass
            return
        
        response = """
🛡️ **ADMİN KOMUTLARI YARDIM**

**👥 Kullanıcı Yönetimi:**
• `/adminyap SEVİYE` (reply ile) - Admin yetkisi ver
• `/adminyap @username SEVİYE` (etiket ile) - Admin yetkisi ver
• `/adminçıkar` (reply ile) - Admin yetkisi al
• `/adminçıkar @username` (etiket ile) - Admin yetkisi al
• `/yetkiver` - Yetki verme (alias)
• `/yetkial` - Yetki alma (alias)

**📋 Bilgi Komutları:**
• `/adminlist` - Tüm adminleri listele
• `/admininfo` (reply ile) - Kullanıcı bilgisi
• `/admininfo @username` (etiket ile) - Kullanıcı bilgisi
• `/adminseviye` (reply ile) - Admin seviye kontrolü
• `/adminseviye @username` (etiket ile) - Admin seviye kontrolü

**🔧 Sistem Komutları:**
• `/komutsil` - Komut listesi
• `/komutsil ID` - Komut sil
• `/adminyardım` - Bu yardım mesajı

**🛡️ Admin Seviyeleri:**
• 1: Üye (Temel komutlar)
• 2: Admin 1 (Grup yönetimi)
• 3: Admin 2 (Etkinlik yönetimi)
• 4: Super Admin (Tüm yetkiler)

**📝 Kullanım Örnekleri:**
• `/adminyap 2` (reply ile)
• `/adminyap @username 3`
• `/adminçıkar @username`
• `/admininfo @username`
        """
        
        await send_response_message(message, response)
        
    except Exception as e:
        logger.error(f"❌ Admin yardım hatası: {e}")
        await send_error_message(message, "❌ Bir hata oluştu!")

# Diğer admin komutları buraya eklenebilir 