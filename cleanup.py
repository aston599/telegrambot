#!/usr/bin/env python3
"""
🧹 Bot Temizlik Script'i
Gereksiz dosyaları ve klasörleri temizler
"""

import os
import shutil
from pathlib import Path

def cleanup_files():
    """Gereksiz dosyaları temizle"""
    
    # Silinecek dosyalar
    files_to_remove = [
        "main_broken.py",
        "main.pyzw", 
        "test_simple.py",
        "ecosystem.config.js",
        "start_production.sh",
        "bot.log"
    ]
    
    print("🗑️ Gereksiz dosyalar temizleniyor...")
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ {file} silindi")
        else:
            print(f"ℹ️ {file} zaten yok")
    
    # __pycache__ klasörlerini temizle
    for root, dirs, files in os.walk("."):
        for dir in dirs:
            if dir == "__pycache__":
                cache_path = os.path.join(root, dir)
                shutil.rmtree(cache_path)
                print(f"✅ {cache_path} temizlendi")

def cleanup_empty_dirs():
    """Boş klasörleri temizle"""
    
    # Kontrol edilecek klasörler
    dirs_to_check = [
        "data",
        "logs", 
        "scripts",
        "database",
        "nginx",
        "backups",
        "ssl",
        "systemd",
        "models"
    ]
    
    print("\n📁 Boş klasörler kontrol ediliyor...")
    
    for dir in dirs_to_check:
        if os.path.exists(dir):
            if not os.listdir(dir):  # Boşsa
                os.rmdir(dir)
                print(f"✅ Boş klasör {dir} silindi")
            else:
                print(f"ℹ️ {dir} klasörü boş değil, bırakıldı")
        else:
            print(f"ℹ️ {dir} klasörü zaten yok")

def cleanup_main_py():
    """main.py'deki gereksiz yorumları temizle"""
    
    print("\n📝 main.py temizleniyor...")
    
    with open("main.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Gereksiz yorumları kaldır
    cleaned_lines = []
    for line in lines:
        if not line.strip().startswith("# KALDIRILDI") and not line.strip().startswith("# EKSİK"):
            cleaned_lines.append(line)
    
    with open("main.py", "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)
    
    print("✅ main.py temizlendi")

if __name__ == "__main__":
    print("🧹 KirveHub Bot Temizlik Başlatılıyor...")
    
    cleanup_files()
    cleanup_empty_dirs() 
    cleanup_main_py()
    
    print("\n🎉 Temizlik tamamlandı!")
    print("📊 Disk alanı kazanıldı!")