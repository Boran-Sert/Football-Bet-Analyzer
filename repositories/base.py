"""Ortak CRUD islemleri icin Generic BaseRepository.

motor kullanimi SADECE repositories/ katmaninda yapilir (rules.md Madde 2).
Generic Type parametresi sayesinde her koleksiyon icin
tek satirda ozel repository turetmek mumkundur.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from motor.motor_asyncio import AsyncIOMotorDatabase

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Tum repository siniflari icin temel CRUD altyapisi.

    Args:
        db: Asenkron MongoDB veritabani nesnesi.
        collection_name: Hedef koleksiyon (tablo) adi.
    """

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str) -> None:
        self.collection = db[collection_name]

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Sorguya uyan ilk belgeyi dondurur."""
        return await self.collection.find_one(query)

    async def find_many(
        self,
        query: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        limit: int = 0,
    ) -> List[Dict[str, Any]]:
        """Sorguya uyan tum belgeleri liste olarak dondurur."""
        cursor = self.collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        if limit > 0:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=limit or None)

    async def insert_one(self, data: Dict[str, Any]) -> str:
        """Tek bir belge ekler. Eklenen belgenin ID'sini dondurur."""
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def insert_many(self, data: List[Dict[str, Any]]) -> int:
        """Birden fazla belge ekler. Eklenen belge sayisini dondurur."""
        if not data:
            return 0
        result = await self.collection.insert_many(data)
        return len(result.inserted_ids)

    async def update_one(
        self, query: Dict[str, Any], update: Dict[str, Any]
    ) -> int:
        """Sorguya uyan ilk belgeyi gunceller. Degisen belge sayisini dondurur."""
        result = await self.collection.update_one(query, {"$set": update})
        return result.modified_count

    async def delete_one(self, query: Dict[str, Any]) -> int:
        """Sorguya uyan ilk belgeyi siler. Silinen belge sayisini dondurur."""
        result = await self.collection.delete_one(query)
        return result.deleted_count

    async def count(self, query: Dict[str, Any] = None) -> int:
        """Sorguya uyan belge sayisini dondurur."""
        return await self.collection.count_documents(query or {})
