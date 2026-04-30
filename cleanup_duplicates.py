import asyncio
import os
import sys
from collections import defaultdict
from core.database import mongo

# Proje yolunu ekle
sys.path.append(os.getcwd())


async def cleanup_duplicates():
    await mongo.connect()
    db = mongo.get_db()

    print("[*] Mukerrer kayitlar temizleniyor...")

    # Tum tamamlanmis maclari cek
    cursor = db.matches.find({"status": "completed"})
    docs = await cursor.to_list(length=None)

    seen = {}
    to_delete = []

    for doc in docs:
        # Benzersiz anahtar: Tarih (gun), Ev Sahibi, Deplasman
        date_str = str(doc["commence_time"]).split()[0]
        key = (date_str, doc["home_team"], doc["away_team"])

        if key in seen:
            # Zaten gorduysek bunu silineceklere ekle
            to_delete.append(doc["_id"])
        else:
            seen[key] = doc["_id"]

    if to_delete:
        print(f"[!] {len(to_delete)} mukerrer kayit siliniyor...")
        result = await db.matches.delete_many({"_id": {"$in": to_delete}})
        print(f"[OK] {result.deleted_count} kayit silindi.")
    else:
        print("[+] Mukerrer kayit bulunmadi.")

    await mongo.close()


if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
