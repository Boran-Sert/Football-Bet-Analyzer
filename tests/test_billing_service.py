"""BillingService ve IyzicoProvider unit testleri."""

import pytest
from unittest.mock import AsyncMock
from services.billing_service import BillingService
from services.payment.iyzico_provider import IyzicoProvider
from schemas.auth import UserTier


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_provider():
    provider = AsyncMock()
    provider.create_checkout_session.return_value = "https://iyzico.com/pay"
    provider.validate_webhook.return_value = {
        "event": "payment.success",
        "user_id": "user123",
        "plan_id": "pro",
    }
    return provider


@pytest.fixture
def billing_service(mock_user_repo, mock_provider):
    return BillingService(user_repo=mock_user_repo, provider=mock_provider)


class TestBillingService:
    @pytest.mark.asyncio
    async def test_create_checkout_session_calls_provider(
        self, billing_service, mock_provider
    ):
        url = await billing_service.create_checkout_session(
            "user123", "test@example.com", "pro"
        )
        assert url == "https://iyzico.com/pay"
        mock_provider.create_checkout_session.assert_called_once_with(
            user_id="user123", user_email="test@example.com", plan_id="pro"
        )

    @pytest.mark.asyncio
    async def test_handle_webhook_updates_user_tier(
        self, billing_service, mock_user_repo, mock_provider
    ):
        mock_user_repo.update_tier.return_value = True

        success = await billing_service.handle_webhook({"token": "xyz"}, {})

        assert success is True
        mock_user_repo.update_tier.assert_called_once_with("user123", UserTier.PRO)

    @pytest.mark.asyncio
    async def test_handle_webhook_fails_on_invalid_event(
        self, billing_service, mock_provider
    ):
        mock_provider.validate_webhook.return_value = {"event": "payment.failed"}

        success = await billing_service.handle_webhook({}, {})

        assert success is False


class TestIyzicoProvider:
    @pytest.mark.asyncio
    async def test_create_checkout_session_raises_on_invalid_plan(self):
        provider = IyzicoProvider()
        with pytest.raises(ValueError, match="Gecersiz plan"):
            await provider.create_checkout_session("u1", "e1", "non_existent_plan")
