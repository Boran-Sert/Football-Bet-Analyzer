"""Futbol veri adapter'i.

Odds API JSON ve Football-data.co.uk CSV verisini
standart MatchEntity formatina donusturur.
"""

import hashlib
import logging
from datetime import datetime
from typing import Any

from adapters.base_adapter import SportAdapter
from adapters.parsers.csv_parsers import CSVParserStrategy, CSVParserFactory
from adapters.name_mapping import (
    LEAGUE_CODE_TO_API_KEY,
    LEAGUE_TITLES,
    normalize_team_name,
)
from schemas.match import MatchEntity, MatchSource, MatchStatus

logger = logging.getLogger(__name__)


class FootballAdapter(SportAdapter):
    """Futbol verisi donusturucusu."""

    sport = "football"

    # ══════════════════════════════════════════
    #  Odds API JSON → MatchEntity
    # ══════════════════════════════════════════

    def normalize_upcoming(self, raw_events: list[dict]) -> list[MatchEntity]:
        """Odds API /odds yanitini MatchEntity listesine donusturur."""
        entities: list[MatchEntity] = []

        for event in raw_events:
            try:
                raw_home = event.get("home_team", "")
                raw_away = event.get("away_team", "")
                odds = self._extract_best_odds(
                    event.get("bookmakers", []), raw_home, raw_away
                )
                entity = MatchEntity(
                    external_id=event["id"],
                    sport=self.sport,
                    league_key=event.get("sport_key", ""),
                    league_title=LEAGUE_TITLES.get(event.get("sport_key", ""), ""),
                    home_team=normalize_team_name(raw_home),
                    away_team=normalize_team_name(raw_away),
                    commence_time=datetime.fromisoformat(
                        event["commence_time"].replace("Z", "+00:00")
                    ),
                    status=MatchStatus.UPCOMING,
                    odds=odds,
                    metrics={},
                    source=MatchSource.ODDS_API,
                    updated_at=datetime.utcnow(),
                )
                entities.append(entity)
            except (KeyError, ValueError) as exc:
                logger.warning(
                    "Odds API event parse hatasi: %s — %s", exc, event.get("id", "?")
                )
                continue

        logger.info(
            "FootballAdapter: %d upcoming event normalize edildi.", len(entities)
        )
        return entities

    def _extract_best_odds(
        self, bookmakers: list[dict], raw_home: str, raw_away: str
    ) -> dict:
        """Tum bahiscilerden en iyi oranlari cikarir."""
        market_data: dict[str, dict[tuple[str, float | None], list[float]]] = {}

        for bm in bookmakers:
            for market in bm.get("markets", []):
                mkey = market["key"]
                if mkey not in ("h2h", "totals", "btts"):
                    continue

                if mkey not in market_data:
                    market_data[mkey] = {}

                for outcome in market.get("outcomes", []):
                    name = outcome["name"]
                    price = outcome.get("price", 0.0)
                    point = outcome.get("point")

                    mapped_name = name.lower()
                    if name == raw_home:
                        mapped_name = "home"
                    elif name == raw_away:
                        mapped_name = "away"
                    elif name.lower() == "draw":
                        mapped_name = "draw"

                    key_tuple = (mapped_name, point)
                    if key_tuple not in market_data[mkey]:
                        market_data[mkey][key_tuple] = []
                    market_data[mkey][key_tuple].append(price)

        avg_data: dict[str, dict[tuple[str, float | None], float]] = {}
        for mkey, outcomes in market_data.items():
            avg_data[mkey] = {}
            for k, prices in outcomes.items():
                avg_data[mkey][k] = (
                    round(sum(prices) / len(prices), 2) if prices else 0.0
                )

        result: dict = {}
        if "h2h" in avg_data:
            d = avg_data["h2h"]
            h = d.get(("home", None))
            dr = d.get(("draw", None))
            a = d.get(("away", None))
            if h and dr and a:
                result["h2h"] = {"home": h, "draw": dr, "away": a}

        if "totals" in avg_data:
            totals_dict = {}
            for (name, point), price in avg_data["totals"].items():
                if point in [1.5, 2.5, 3.5]:
                    k = f"{name}_{str(point).replace('.', '_')}"
                    totals_dict[k] = price
            if totals_dict:
                result["totals"] = totals_dict

        if "btts" in avg_data:
            d = avg_data["btts"]
            y = d.get(("yes", None))
            n = d.get(("no", None))
            if y and n:
                result["btts"] = {"yes": y, "no": n}

        return result

    # ══════════════════════════════════════════
    #  CSV → MatchEntity
    # ══════════════════════════════════════════

    # ══════════════════════════════════════════
    #  CSV → MatchEntity
    # ══════════════════════════════════════════

    def normalize_historical(
        self, raw_rows: list[dict], league_code: str = ""
    ) -> list[MatchEntity]:
        """Football-data.co.uk CSV satirlarini MatchEntity listesine donusturur."""
        entities: list[MatchEntity] = []
        league_key = LEAGUE_CODE_TO_API_KEY.get(league_code, f"csv_{league_code}")

        # Strategy Selection (Faz 6 Fix: Strategy-Factory Pattern ile dinamik secim)
        if not raw_rows:
            return []
            
        try:
            parser = CSVParserFactory.get_parser(raw_rows[0])
        except ValueError as exc:
            logger.error(f"Parser secim hatasi: {exc}")
            return []

        for row in raw_rows:
            try:
                entity = self._parse_csv_row(row, league_key, league_code, parser)
                if entity:
                    entities.append(entity)
            except Exception as exc:
                logger.warning("CSV satir parse hatasi: %s — %s", exc, row)
                continue

        return entities

    def _parse_csv_row(
        self, row: dict, league_key: str, league_code: str, parser: CSVParserStrategy
    ) -> MatchEntity | None:
        """Tek bir CSV satirini MatchEntity'ye donusturur."""
        date_str = parser.get_date(row)
        home = parser.get_home_team(row)
        away = parser.get_away_team(row)

        if not date_str or not home or not away:
            return None

        commence_time = self._parse_date(date_str)
        if not commence_time:
            return None

        norm_date = commence_time.strftime("%Y-%m-%d")
        raw_id = f"{league_code}_{norm_date}_{home}_{away}"
        external_id = hashlib.md5(raw_id.encode()).hexdigest()

        # Oranlar ve Metrikler (Strategy üzerinden)
        odds = {}
        h2h = parser.get_h2h_odds(row)
        if h2h:
            odds["h2h"] = {"home": h2h[0], "draw": h2h[1], "away": h2h[2]}
            
        totals = parser.get_totals_odds(row)
        if totals:
            odds["totals"] = {"over_2_5": totals[0], "under_2_5": totals[1]}

        metrics = {}
        goals = parser.get_goals(row)
        if goals:
            metrics["home_goals"] = goals[0]
            metrics["away_goals"] = goals[1]
            metrics["total_goals"] = goals[0] + goals[1]

        # Diger metrikler icin opsiyonel alanlar (Ingilizce formatta varsa)
        if hasattr(parser, 'get_extra_metrics'):
             metrics.update(parser.get_extra_metrics(row))

        return MatchEntity(
            external_id=external_id,
            sport="football",
            league_key=league_key,
            league_title=LEAGUE_TITLES.get(league_key, league_code),
            home_team=normalize_team_name(home),
            away_team=normalize_team_name(away),
            commence_time=commence_time,
            status=MatchStatus.COMPLETED,
            odds=odds,
            metrics=metrics,
            source=MatchSource.FOOTBALL_DATA_CSV,
            updated_at=datetime.utcnow(),
        )

    def _parse_date(self, date_str: str) -> datetime | None:
        formats = ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _safe_float(val: str) -> float | None:
        try:
            return float(val.replace(",", ".")) if val else None
        except:
            return None

    @staticmethod
    def _safe_int(val: str) -> int | None:
        try:
            return int(float(val)) if val else None
        except:
            return None
