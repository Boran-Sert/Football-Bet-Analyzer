"""Shared pytest fixtures."""

import asyncio
import pytest
from unittest.mock import AsyncMock
from schemas.auth import UserInDB, UserTier


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_match_repo():
    return AsyncMock()


@pytest.fixture
def sample_user():
    return UserInDB(
        **{
            "_id": "64f1a2b3c4d5e6f7a8b9c0d1",
            "email": "test@example.com",
            "display_name": "Test User",
            "hashed_password": "$2b$12$placeholder",
            "tier": UserTier.FREE,
            "is_verified": True,
            "is_superuser": False,
        }
    )


@pytest.fixture
def pro_user():
    return UserInDB(
        **{
            "_id": "64f1a2b3c4d5e6f7a8b9c0d2",
            "email": "pro@example.com",
            "display_name": "Pro User",
            "hashed_password": "$2b$12$placeholder",
            "tier": UserTier.PRO,
            "is_verified": True,
            "is_superuser": False,
        }
    )
