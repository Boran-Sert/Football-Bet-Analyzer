"""RateLimiter unit tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from middleware.rate_limiter import RateLimiter
from schemas.auth import UserTier


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    pipe = MagicMock()

    # Mock async context manager: async with redis.pipeline(...) as pipe
    cm = AsyncMock()
    cm.__aenter__.return_value = pipe
    cm.__aexit__ = AsyncMock(return_value=None)
    redis.pipeline.return_value = cm

    # pipe methods
    pipe.zremrangebyscore = MagicMock()
    pipe.zadd = MagicMock()
    pipe.zcard = MagicMock()
    pipe.expire = MagicMock()

    # pipe results: [zrem, zadd, zcard, expire]
    pipe.execute = AsyncMock(return_value=[0, 1, 1, True])

    redis.pipe = pipe  # Reference for tests
    return redis


@pytest.fixture
def free_request():
    req = MagicMock()
    req.state.user_tier = UserTier.FREE.value
    req.state.is_superuser = False
    req.state.user_id = "user_free"
    req.client.host = "127.0.0.1"
    req.headers = {}
    return req


@pytest.fixture
def pro_request():
    req = MagicMock()
    req.state.user_tier = UserTier.PRO.value
    req.state.is_superuser = False
    req.state.user_id = "user_pro"
    req.client.host = "127.0.0.2"
    req.headers = {}
    return req


@pytest.fixture
def admin_request():
    req = MagicMock()
    req.state.user_tier = UserTier.ELITE.value
    req.state.is_superuser = True
    req.state.user_id = "admin1"
    req.client.host = "127.0.0.3"
    req.headers = {}
    return req


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_superuser_bypasses_limit(self, admin_request, mock_redis):
        limiter = RateLimiter()
        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            await limiter(admin_request)
        mock_redis.pipeline.assert_not_called()

    @pytest.mark.asyncio
    async def test_under_limit_passes(self, free_request, mock_redis):
        # Current count = 5
        mock_redis.pipe.execute.return_value = [0, 1, 5, True]
        limiter = RateLimiter(requests_per_minute=60)
        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            await limiter(free_request)  # Must not raise

    @pytest.mark.asyncio
    async def test_over_limit_raises_429(self, free_request, mock_redis):
        # Current count = 61, limit = 60
        mock_redis.pipe.execute.return_value = [0, 1, 61, True]
        limiter = RateLimiter(requests_per_minute=60)
        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                await limiter(free_request)
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_pro_user_gets_higher_limit(self, pro_request, mock_redis):
        """PRO tier limit (200) should allow count=150 without raising."""
        mock_redis.pipe.execute.return_value = [0, 1, 150, True]
        limiter = RateLimiter()
        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            await limiter(pro_request)  # 150 < 200, must pass

    @pytest.mark.asyncio
    async def test_redis_failure_does_not_block_request(self, free_request, mock_redis):
        """If Redis is down, requests should still pass (fail-open)."""
        mock_redis.pipeline.side_effect = Exception("Redis connection error")
        limiter = RateLimiter(requests_per_minute=10)
        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            await limiter(free_request)  # Must not raise

    @pytest.mark.asyncio
    async def test_uses_x_forwarded_for_header(self, mock_redis):
        req = MagicMock()
        req.state.user_id = None
        req.state.is_superuser = False
        req.state.user_tier = UserTier.FREE.value
        req.headers = {"x-forwarded-for": "203.0.113.1, 10.0.0.1"}
        req.client.host = "10.0.0.1"
        mock_redis.pipe.execute.return_value = [0, 1, 1, True]

        limiter = RateLimiter(requests_per_minute=60)
        with patch("core.redis_client.redis_manager.get_client", return_value=mock_redis):
            await limiter(req)

        # check that zadd was called on the pipe with the correct identifier in the key
        # redis_key = f"rate_limit:sw:{identifier}"
        call_args_list = mock_redis.pipe.zadd.call_args_list
        found = False
        for args, kwargs in call_args_list:
            if "203.0.113.1" in args[0]:
                found = True
                break
        assert found, f"IP 203.0.113.1 not found in zadd calls: {call_args_list}"
