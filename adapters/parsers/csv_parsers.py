from abc import ABC, abstractmethod
from typing import Any

class CSVParserStrategy(ABC):
    """CSV parserlar icin strateji arayuzu."""
    
    @staticmethod
    @abstractmethod
    def can_handle(first_row: dict) -> bool:
        """Bu parser verilen satiri isleyebilir mi?"""
        pass

    @abstractmethod
    def get_date(self, row: dict) -> str | None:
        pass

    @abstractmethod
    def get_home_team(self, row: dict) -> str | None:
        pass

    @abstractmethod
    def get_away_team(self, row: dict) -> str | None:
        pass

    @abstractmethod
    def get_h2h_odds(self, row: dict) -> tuple[float, float, float] | None:
        pass

    @abstractmethod
    def get_totals_odds(self, row: dict) -> tuple[float, float] | None:
        pass

    @abstractmethod
    def get_goals(self, row: dict) -> tuple[int, int] | None:
        pass

class EnglishCSVParser(CSVParserStrategy):
    """Football-data.co.uk standart Ingilizce formatı."""
    
    @staticmethod
    def can_handle(first_row: dict) -> bool:
        return "B365H" in first_row or "HomeTeam" in first_row

    def get_date(self, row: dict) -> str | None:
        return row.get("Date")

    def get_home_team(self, row: dict) -> str | None:
        return row.get("HomeTeam")

    def get_away_team(self, row: dict) -> str | None:
        return row.get("AwayTeam")

    def get_h2h_odds(self, row: dict) -> tuple[float, float, float] | None:
        h = row.get("B365H") or row.get("PSH")
        d = row.get("B365D") or row.get("PSD")
        a = row.get("B365A") or row.get("PSA")
        try:
            return float(h), float(d), float(a)
        except (TypeError, ValueError):
            return None

    def get_totals_odds(self, row: dict) -> tuple[float, float] | None:
        over = row.get("B365>2.5") or row.get("P>2.5")
        under = row.get("B365<2.5") or row.get("P<2.5")
        try:
            return float(over), float(under)
        except (TypeError, ValueError):
            return None

    def get_goals(self, row: dict) -> tuple[int, int] | None:
        hg = row.get("FTHG")
        ag = row.get("FTAG")
        try:
            return int(hg), int(ag)
        except (TypeError, ValueError):
            return None

class TurkishCSVParser(CSVParserStrategy):
    """Ozel Turkce baslikli CSV formatı."""
    
    @staticmethod
    def can_handle(first_row: dict) -> bool:
        return "MS 1" in first_row or "Ev Sahibi" in first_row

    def get_date(self, row: dict) -> str | None:
        return row.get("Tarih")

    def get_home_team(self, row: dict) -> str | None:
        return row.get("Ev Sahibi")

    def get_away_team(self, row: dict) -> str | None:
        return row.get("Deplasman")

    def get_h2h_odds(self, row: dict) -> tuple[float, float, float] | None:
        h = row.get("MS 1")
        d = row.get("MS 0")
        a = row.get("MS 2")
        try:
            return float(h.replace(",", ".")), float(d.replace(",", ".")), float(a.replace(",", "."))
        except (AttributeError, TypeError, ValueError):
            return None

    def get_totals_odds(self, row: dict) -> tuple[float, float] | None:
        over = row.get("2.5 Ust")
        under = row.get("2.5 Alt")
        try:
            return float(over.replace(",", ".")), float(under.replace(",", "."))
        except (AttributeError, TypeError, ValueError):
            return None

    def get_goals(self, row: dict) -> tuple[int, int] | None:
        hg = row.get("Ev Sahibi Gol")
        ag = row.get("Deplasman Gol")
        try:
            return int(hg), int(ag)
        except (TypeError, ValueError):
            return None

class CSVParserFactory:
    """Uygun parser'i dinamik olarak secer (Faz 6 Fix: Strategy-Factory Pattern)."""
    
    _parsers = [EnglishCSVParser, TurkishCSVParser]

    @classmethod
    def get_parser(cls, first_row: dict) -> CSVParserStrategy:
        for parser_cls in cls._parsers:
            if parser_cls.can_handle(first_row):
                return parser_cls()
        
        # Default veya hata
        raise ValueError("Bu CSV formatı için uygun bir parser bulunamadı.")
