"""AuthService unit tests."""

import pytest
from services.auth_service import AuthService
from schemas.auth import UserCreate, UserInDB, UserTier


@pytest.fixture
def auth_service(mock_user_repo):
    return AuthService(repo=mock_user_repo)


# ─── Password hashing ────────────────────────────────────────────────────────


class TestPasswordHashing:
    def test_hash_and_verify_succeed(self, auth_service):
        plain = "SecurePass123!"
        hashed = auth_service.get_password_hash(plain)
        assert auth_service.verify_password(plain, hashed)

    def test_wrong_password_fails(self, auth_service):
        hashed = auth_service.get_password_hash("correct_password")
        assert not auth_service.verify_password("wrong_password", hashed)

    def test_two_hashes_of_same_password_differ(self, auth_service):
        """bcrypt uses a random salt each time."""
        pw = "SamePassword1!"
        assert auth_service.get_password_hash(pw) != auth_service.get_password_hash(pw)


# ─── Access token ─────────────────────────────────────────────────────────────


class TestAccessToken:
    def test_decode_returns_correct_user_id(self, auth_service):
        token = auth_service.create_access_token("user123", UserTier.PRO)
        data = auth_service.decode_token(token)
        assert data is not None
        assert data.user_id == "user123"
        assert data.tier == UserTier.PRO

    def test_superuser_flag_preserved(self, auth_service):
        token = auth_service.create_access_token(
            "admin1", UserTier.ELITE, is_superuser=True
        )
        data = auth_service.decode_token(token)
        assert data.is_superuser is True

    def test_tampered_token_returns_none(self, auth_service):
        token = auth_service.create_access_token("user123", UserTier.FREE)
        assert auth_service.decode_token(token + "x") is None

    def test_empty_string_returns_none(self, auth_service):
        assert auth_service.decode_token("") is None


# ─── Verification token ───────────────────────────────────────────────────────


class TestVerificationToken:
    def test_verification_token_contains_email(self, auth_service):
        import jwt as pyjwt
        from core.config import settings

        token = auth_service.create_verification_token("verify@example.com")
        payload = pyjwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload["sub"] == "verify@example.com"
        assert payload["type"] == "email_verify"


# ─── Register ─────────────────────────────────────────────────────────────────


class TestRegister:
    @pytest.mark.asyncio
    async def test_new_user_registered_successfully(
        self, auth_service, mock_user_repo, sample_user
    ):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = sample_user

        result = await auth_service.register_user(
            UserCreate(
                email="new@example.com",
                password="SecurePass123!",
                display_name="New User",
            )
        )
        assert result is not None
        mock_user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_none(
        self, auth_service, mock_user_repo, sample_user
    ):
        mock_user_repo.get_by_email.return_value = sample_user

        result = await auth_service.register_user(
            UserCreate(
                email="test@example.com", password="SecurePass123!", display_name="Dup"
            )
        )
        assert result is None
        mock_user_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_new_user_starts_as_free_tier(
        self, auth_service, mock_user_repo, sample_user
    ):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = sample_user

        await auth_service.register_user(
            UserCreate(
                email="new@example.com", password="SecurePass123!", display_name="New"
            )
        )
        created_user: UserInDB = mock_user_repo.create.call_args[0][0]
        assert created_user.tier == UserTier.FREE
        assert created_user.is_superuser is False
        assert created_user.is_verified is False


# ─── Password reset ───────────────────────────────────────────────────────────


class TestPasswordReset:
    def test_reset_token_has_correct_type(self, auth_service):
        import jwt as pyjwt
        from core.config import settings

        token = auth_service.create_password_reset_token("user@example.com")
        payload = pyjwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload["type"] == "password_reset"
        assert payload["sub"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_reset_password_updates_hash(
        self, auth_service, mock_user_repo, sample_user
    ):
        mock_user_repo.get_by_email.return_value = sample_user
        mock_user_repo.update_password.return_value = True

        token = auth_service.create_password_reset_token(sample_user.email)
        result = await auth_service.reset_password(token, "NewSecurePass456!")
        assert result is True
        mock_user_repo.update_password.assert_called_once()

    @pytest.mark.asyncio
    async def test_tampered_reset_token_returns_false(self, auth_service):
        result = await auth_service.reset_password("tampered.token.here", "NewPass123!")
        assert result is False

    @pytest.mark.asyncio
    async def test_reset_with_wrong_token_type_returns_false(self, auth_service):
        # email_verify token must not work as password reset
        token = auth_service.create_verification_token("user@example.com")
        result = await auth_service.reset_password(token, "NewPass123!")
        assert result is False
