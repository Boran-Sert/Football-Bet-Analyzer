"""Yaklasan maclari football-data.org'dan cekip MongoDB'ye yazan script.

Kullanim:
    python scripts/fetch_upcoming.py
"""

import asyncio
import os
import sys

# Proje kokunu path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import mongo
from tasks.fetch_data import fetch_daily_matches

async def main():
    await mongo.connect()
    print("✅ MongoDB baglantisi kuruldu.")
    
    print("🔄 Mac verileri football-data.org üzerinden cekiliyor...")
    await fetch_daily_matches()
    
    print("🏁 Islem tamamlandi.")
    await mongo.close()

if __name__ == "__main__":
    asyncio.run(main())
