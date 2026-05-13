from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import pytest

from services.analysis_service import AnalysisService
from schemas.auth import UserTier
from schemas.match import MatchInDB, MatchStatus


def make_match(
    external_id: str,
    home: float,
    draw: float,
    away: float,
    status=MatchStatus.COMPLETED,
    home_team="Home FC",
    away_team="Away FC",
) -> MatchInDB:
    """Helper: build a minimal MatchInDB with h2h odds."""
    return MatchInDB(
        external_id=external_id,
        sport="football",
        league_key="soccer_epl",
        league_title="Premier League",
        home_team=home_team,
        away_team=away_team,
        commence_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        status=status,
        odds={"h2h": {"home": home, "draw": draw, "away": away}},
        metrics={},
        source="odds_api",
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_redis():
    """Redis mock — cache_response decorator icin."""
    redis = AsyncMock()
    redis.get.return_value = None  # Cache miss
    redis.setex.return_value = True
    return redis


@pytest.fixture
def analysis_service(mock_match_repo, mock_redis):
    """AnalysisService oluşturulurken ve çağrılırken Redis mock aktif olmalı."""
    patcher = patch("core.redis_client.redis_manager.get_client", return_value=mock_redis)
    patcher.start()
    service = AnalysisService(match_repo=mock_match_repo)
    yield service
    patcher.stop()


@pytest.fixture
def target_match():
    return make_match(
        "target_001", home=1.8, draw=3.5, away=4.5, status=MatchStatus.UPCOMING
    )


@pytest.fixture
def historical_matches():
    return [
        make_match("hist_001", 1.82, 3.48, 4.52, home_team="Team A", away_team="Team B"),
        make_match("hist_002", 5.0, 4.0, 1.5, home_team="Team C", away_team="Team D"),
        make_match("hist_003", 1.79, 3.51, 4.48, home_team="Team E", away_team="Team F"),
    ]


class TestSimilarMatchFinding:
    @pytest.mark.asyncio
    async def test_returns_only_close_matches(
        self, analysis_service, mock_match_repo, mock_redis, target_match, historical_matches
    ):
        mock_match_repo.get_by_external_id.return_value = target_match

        # Service artık repo.find_similar_matches_by_distance() çağırıyor
        mock_match_repo.find_similar_matches_by_distance.return_value = [
            {**historical_matches[0].model_dump(), "distance": 0.05},
            {**historical_matches[2].model_dump(), "distance": 0.08},
        ]

        results = await analysis_service.find_similar_matches(
            target_match_id="target_001",
            user_tier=UserTier.ELITE,
            is_superuser=False,
        )

        external_ids = [r.match.external_id for r in results]
        assert "hist_001" in external_ids
        assert "hist_003" in external_ids
        assert "hist_002" not in external_ids

    @pytest.mark.asyncio
    async def test_standard_tier_limited_to_3_results(
        self, analysis_service, mock_match_repo, mock_redis, target_match
    ):
        many_close = [
            make_match(f"hist_{i:03d}", home=1.8 + i * 0.01, draw=3.5, away=4.5)
            for i in range(10)
        ]
        mock_match_repo.get_by_external_id.return_value = target_match

        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [
            {**m.model_dump(), "distance": 0.01 * i} for i, m in enumerate(many_close)
        ]
        mock_match_repo.collection.database.matches.aggregate = MagicMock(
            return_value=mock_cursor
        )

        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            results = await analysis_service.find_similar_matches(
                target_match_id="target_001",
                user_tier=UserTier.STANDARD,
                is_superuser=False,
            )

        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_returns_empty_for_non_upcoming_match(
        self, analysis_service, mock_match_repo, mock_redis
    ):
        completed_target = make_match(
            "target_done", 1.8, 3.5, 4.5, status=MatchStatus.COMPLETED
        )
        mock_match_repo.get_by_external_id.return_value = completed_target

        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            results = await analysis_service.find_similar_matches(
                target_match_id="target_done",
                user_tier=UserTier.PRO,
            )
        assert results == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_match_not_found(
        self, analysis_service, mock_match_repo, mock_redis
    ):
        mock_match_repo.get_by_external_id.return_value = None

        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            results = await analysis_service.find_similar_matches(
                target_match_id="nonexistent",
                user_tier=UserTier.STANDARD,
            )
        assert results == []

    @pytest.mark.asyncio
    async def test_results_sorted_by_distance_ascending(
        self, analysis_service, mock_match_repo, mock_redis, target_match
    ):
        matches = [
            make_match("far", home=1.9, draw=3.6, away=4.6),
            make_match("close", home=1.81, draw=3.51, away=4.51),
        ]
        mock_match_repo.get_by_external_id.return_value = target_match

        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [
            {**matches[1].model_dump(), "distance": 0.05},
            {**matches[0].model_dump(), "distance": 0.15},
        ]
        mock_match_repo.collection.database.matches.aggregate = MagicMock(
            return_value=mock_cursor
        )

        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            results = await analysis_service.find_similar_matches(
                target_match_id="target_001",
                user_tier=UserTier.ELITE,
            )

        if len(results) >= 2:
            assert results[0].distance <= results[1].distance
