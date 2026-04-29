"""Soyut spor adapter sinifi.

Her spor icin bir adapter yazilir (FootballAdapter, BasketballAdapter, ...).
Adapter, dis kaynaktaki ham veriyi MatchEntity formatina donusturur.
"""

from abc import ABC, abstractmethod

from schemas.match import MatchEntity


class SportAdapter(ABC):
    """Soyut spor veri donusturucusu.

    Yeni bir spor eklemek icin:
    1. Bu sinifi miras al.
    2. normalize_upcoming() ve normalize_historical() metodlarini implement et.
    3. tasks/ingestion.py icerisinde adapter'i kaydet.
    """

    sport: str = ""  # Alt sinif tarafindan set edilir

    @abstractmethod
    def normalize_upcoming(self, raw_events: list[dict]) -> list[MatchEntity]:
        """Odds API ham verisini MatchEntity listesine donusturur.

        Args:
            raw_events: Odds API /odds endpoint'inden gelen ham JSON listesi.

        Returns:
            Normalize edilmis MatchEntity listesi.
        """
        ...

    @abstractmethod
    def normalize_historical(self, raw_rows: list[dict]) -> list[MatchEntity]:
        """CSV / tarihsel ham veriyi MatchEntity listesine donusturur.

        Args:
            raw_rows: CSV satirlarinin dict listesi.

        Returns:
            Normalize edilmis MatchEntity listesi.
        """
        ...
