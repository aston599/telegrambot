"""
Router Testleri
"""

from handlers.admin_panel import router as admin_router
from handlers.secret_commands import router as secret_router
from handlers.simple_events import router as events_router
from handlers.statistics_system import router as stats_router
from handlers.broadcast_system import router as broadcast_router
from handlers.scheduled_messages import router as scheduled_router
from handlers.balance_event import router as balance_router
from handlers.detailed_logging_system import router as logging_router

def test_routers():
    """Router'ları test et"""
    try:
        print("🧪 Router testleri başlatılıyor...")
        
        # Router'ları kontrol et
        routers = [
            ("Admin Panel", admin_router),
            ("Secret Commands", secret_router),
            ("Events", events_router),
            ("Statistics", stats_router),
            ("Broadcast", broadcast_router),
            ("Scheduled Messages", scheduled_router),
            ("Balance Event", balance_router),
            ("Detailed Logging", logging_router)
        ]
        
        for name, router in routers:
            if router and hasattr(router, 'routes'):
                print(f"✅ {name}: {len(router.routes)} route")
            else:
                print(f"❌ {name}: Router bulunamadı")
        
        print("✅ Router testleri tamamlandı!")
        
    except Exception as e:
        print(f"❌ Router test hatası: {e}")

if __name__ == "__main__":
    test_routers() 