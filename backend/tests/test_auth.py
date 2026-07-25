"""
Tests for app/services/auth.py — authentication service.

Covers:
  ✓ Password hashing and verification (including bcrypt 72-byte fix)
  ✓ _pre_hash determinism and output length
  ✓ JWT access/refresh token creation and decoding
  ✓ Token blacklisting
  ✓ register_user flow (success + conflict cases)
  ✓ login_user flow (success + invalid credentials + disabled account)
  ✓ refresh_tokens flow (success + revoked + wrong type)
  ✓ update_password_by_email flow (success + not found)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from app.core.exceptions import AuthenticationError, ConflictError
from app.schemas.user import TokenResponse, UserCreate
from app.services.auth import (
    ALGORITHM,
    _pre_hash,
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_token_blacklisted,
    login_user,
    refresh_tokens,
    register_user,
    update_password_by_email,
    verify_password,
)


# ─── _pre_hash Tests ─────────────────────────────────────────────


class TestPreHash:
    """Tests for the SHA-256 pre-hashing function."""

    def test_output_is_deterministic(self):
        """Same password should always produce the same pre-hash."""
        result1 = _pre_hash("mysecretpassword")
        result2 = _pre_hash("mysecretpassword")
        assert result1 == result2

    def test_different_passwords_produce_different_hashes(self):
        """Different passwords must produce different pre-hashes."""
        assert _pre_hash("password1") != _pre_hash("password2")

    def test_output_length_is_under_72_bytes(self):
        """Pre-hash output must always be under bcrypt's 72-byte limit."""
        # Even with a very long input, output is a fixed 44-char base64 string
        long_password = "a" * 1000
        result = _pre_hash(long_password)
        assert len(result) <= 72
        # SHA-256 digest is 32 bytes, base64 of 32 bytes = 44 bytes
        assert len(result) == 44

    def test_unicode_password(self):
        """Unicode passwords should be handled correctly."""
        result = _pre_hash("密码很安全🔐")
        assert len(result) == 44
        assert isinstance(result, bytes)

    def test_return_type_is_bytes(self):
        """_pre_hash must return bytes (base64-encoded), not str."""
        result = _pre_hash("anypassword")
        assert isinstance(result, bytes)

    def test_empty_string(self):
        """Empty string should still produce a valid pre-hash."""
        result = _pre_hash("")
        assert len(result) == 44


# ─── Password Hashing Tests ──────────────────────────────────────


class TestPasswordHashing:
    """Tests for hash_password and verify_password."""

    def test_hash_returns_bcrypt_string(self):
        """hash_password should return a bcrypt hash string."""
        hashed = hash_password("testpassword123")
        assert hashed.startswith("$2b$")

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses random salt, so two hashes of same password should differ."""
        h1 = hash_password("testpassword123")
        h2 = hash_password("testpassword123")
        assert h1 != h2

    def test_verify_correct_password(self):
        """Correct password should verify successfully."""
        password = "mysecurepassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Wrong password should fail verification."""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_long_password_no_error(self):
        """Passwords longer than 72 bytes must NOT raise ValueError (the original bug)."""
        long_password = "a" * 200  # 200 bytes, well over bcrypt's 72-byte limit
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed) is True

    def test_exactly_72_byte_password(self):
        """Boundary: exactly 72 bytes should work."""
        password = "x" * 72
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_73_byte_password(self):
        """Boundary: 73 bytes (one over the limit) should work after the fix."""
        password = "x" * 73
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_unicode_multibyte_long_password(self):
        """Multi-byte unicode characters that exceed 72 bytes when encoded."""
        # Each emoji is 4 bytes in UTF-8, so 20 emojis = 80 bytes
        password = "🔑" * 20
        assert len(password.encode("utf-8")) > 72
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_128_char_password_max_schema_length(self):
        """The schema allows up to 128 chars — this must work."""
        password = "P@ssw0rd!" * 15  # 135 chars, trimmed to 128 for realism
        password = password[:128]
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


# ─── JWT Token Tests ─────────────────────────────────────────────


class TestJWTTokens:
    """Tests for JWT creation and decoding."""

    def test_create_access_token_is_valid_jwt(self):
        """create_access_token should return a decodable JWT."""
        token = create_access_token("user-abc-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-abc-123"
        assert payload["type"] == "access"

    def test_create_refresh_token_is_valid_jwt(self):
        """create_refresh_token should return a decodable JWT."""
        token = create_refresh_token("user-abc-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-abc-123"
        assert payload["type"] == "refresh"

    def test_access_token_has_expiration(self):
        """Access token payload must include an 'exp' claim."""
        token = create_access_token("user-1")
        payload = decode_token(token)
        assert "exp" in payload

    def test_refresh_token_has_expiration(self):
        """Refresh token payload must include an 'exp' claim."""
        token = create_refresh_token("user-1")
        payload = decode_token(token)
        assert "exp" in payload

    def test_decode_expired_token_raises(self):
        """Decoding an expired token should raise AuthenticationError."""
        from app.config import settings

        expired_payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "type": "access",
        }
        expired_token = jwt.encode(
            expired_payload, settings.SECRET_KEY, algorithm=ALGORITHM
        )
        with pytest.raises(AuthenticationError, match="Invalid or expired token"):
            decode_token(expired_token)

    def test_decode_token_with_wrong_secret_raises(self):
        """Token signed with wrong secret should fail."""
        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "type": "access",
        }
        bad_token = jwt.encode(
            payload,
            "wrong-secret-key-that-is-at-least-32-bytes-long",
            algorithm=ALGORITHM,
        )
        with pytest.raises(AuthenticationError, match="Invalid or expired token"):
            decode_token(bad_token)

    def test_decode_token_missing_subject_raises(self):
        """Token without 'sub' claim should raise AuthenticationError."""
        from app.config import settings

        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(AuthenticationError, match="missing subject"):
            decode_token(token)

    def test_decode_garbage_token_raises(self):
        """Completely invalid token string should raise AuthenticationError."""
        with pytest.raises(AuthenticationError):
            decode_token("not.a.valid.jwt.token")


# ─── Token Blacklist Tests ───────────────────────────────────────


class TestTokenBlacklist:
    """Tests for token blacklisting (requires Redis mock)."""

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_returns_false_for_new_token(self):
        """A fresh token should not be blacklisted."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0

        with patch("app.services.auth.get_redis", return_value=mock_redis):
            result = await is_token_blacklisted("some-token")
        assert result is False
        mock_redis.exists.assert_called_once_with("blacklist:some-token")

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_returns_true_for_blacklisted(self):
        """A blacklisted token should return True."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1

        with patch("app.services.auth.get_redis", return_value=mock_redis):
            result = await is_token_blacklisted("revoked-token")
        assert result is True

    @pytest.mark.asyncio
    async def test_blacklist_token_calls_redis_setex(self):
        """blacklist_token should store the token in Redis with a TTL."""
        token = create_access_token("user-1")
        mock_redis = AsyncMock()

        with patch("app.services.auth.get_redis", return_value=mock_redis):
            await blacklist_token(token)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith("blacklist:")
        assert call_args[0][2] == "1"
        # TTL should be a positive integer
        assert call_args[0][1] > 0

    @pytest.mark.asyncio
    async def test_blacklist_expired_token_is_noop(self):
        """Blacklisting an already-expired token should not raise."""
        from app.config import settings

        expired_payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "type": "access",
        }
        expired_token = jwt.encode(
            expired_payload, settings.SECRET_KEY, algorithm=ALGORITHM
        )
        mock_redis = AsyncMock()

        with patch("app.services.auth.get_redis", return_value=mock_redis):
            # Should not raise
            await blacklist_token(expired_token)

        # Should not call setex since token is expired
        mock_redis.setex.assert_not_called()


# ─── Register User Tests ─────────────────────────────────────────


def _make_mock_user(
    user_id="user-123",
    email="test@example.com",
    username="testuser",
    is_active=True,
):
    """Create a mock User object."""
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.username = username
    user.is_active = is_active
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    user.hashed_password = hash_password("testpassword123")
    return user


class TestRegisterUser:
    """Tests for the register_user flow."""

    @pytest.mark.asyncio
    async def test_register_success(self):
        """Successful registration returns user dict and tokens."""
        mock_db = AsyncMock()
        data = UserCreate(
            email="new@example.com",
            username="newuser",
            password="securepassword123",
        )
        mock_user = _make_mock_user(
            email="new@example.com", username="newuser"
        )

        with (
            patch("app.services.auth.user_repo") as mock_user_repo,
            patch("app.services.auth.workspace_repo") as mock_ws_repo,
        ):
            mock_user_repo.get_by_email = AsyncMock(return_value=None)
            mock_user_repo.get_by_username = AsyncMock(return_value=None)
            mock_user_repo.create = AsyncMock(return_value=mock_user)
            mock_ws_repo.create = AsyncMock()

            user_dict, tokens = await register_user(mock_db, data)

        assert user_dict["email"] == "new@example.com"
        assert user_dict["username"] == "newuser"
        assert isinstance(tokens, TokenResponse)
        assert tokens.access_token
        assert tokens.refresh_token
        # Verify workspace was created
        mock_ws_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self):
        """Registration with existing email should raise ConflictError."""
        mock_db = AsyncMock()
        data = UserCreate(
            email="existing@example.com",
            username="newuser",
            password="securepassword123",
        )

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email = AsyncMock(
                return_value=_make_mock_user(email="existing@example.com")
            )

            with pytest.raises(ConflictError, match="Email already registered"):
                await register_user(mock_db, data)

    @pytest.mark.asyncio
    async def test_register_duplicate_username_raises(self):
        """Registration with existing username should raise ConflictError."""
        mock_db = AsyncMock()
        data = UserCreate(
            email="unique@example.com",
            username="takenuser",
            password="securepassword123",
        )

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email = AsyncMock(return_value=None)
            mock_user_repo.get_by_username = AsyncMock(
                return_value=_make_mock_user(username="takenuser")
            )

            with pytest.raises(ConflictError, match="Username already taken"):
                await register_user(mock_db, data)

    @pytest.mark.asyncio
    async def test_register_with_long_password(self):
        """Registration with a 128-char password must succeed (the original bug)."""
        mock_db = AsyncMock()
        long_password = "A1b2c3d4!" * 15  # 135 chars
        long_password = long_password[:128]
        data = UserCreate(
            email="longpass@example.com",
            username="longpassuser",
            password=long_password,
        )
        mock_user = _make_mock_user(
            email="longpass@example.com", username="longpassuser"
        )

        with (
            patch("app.services.auth.user_repo") as mock_user_repo,
            patch("app.services.auth.workspace_repo") as mock_ws_repo,
        ):
            mock_user_repo.get_by_email = AsyncMock(return_value=None)
            mock_user_repo.get_by_username = AsyncMock(return_value=None)
            mock_user_repo.create = AsyncMock(return_value=mock_user)
            mock_ws_repo.create = AsyncMock()

            user_dict, tokens = await register_user(mock_db, data)

        assert user_dict["email"] == "longpass@example.com"


# ─── Login User Tests ────────────────────────────────────────────


class TestLoginUser:
    """Tests for the login_user flow."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Valid credentials should return user dict and tokens."""
        mock_db = AsyncMock()
        password = "correctpassword"
        mock_user = _make_mock_user()
        mock_user.hashed_password = hash_password(password)

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=mock_user)

            user_dict, tokens = await login_user(
                mock_db, "test@example.com", password
            )

        assert user_dict["email"] == "test@example.com"
        assert isinstance(tokens, TokenResponse)

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self):
        """Wrong password should raise AuthenticationError."""
        mock_db = AsyncMock()
        mock_user = _make_mock_user()
        mock_user.hashed_password = hash_password("correctpassword")

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=mock_user)

            with pytest.raises(
                AuthenticationError, match="Invalid email/username or password"
            ):
                await login_user(mock_db, "test@example.com", "wrongpassword")

    @pytest.mark.asyncio
    async def test_login_nonexistent_email_raises(self):
        """Login with unknown email should raise AuthenticationError."""
        mock_db = AsyncMock()

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=None)

            with pytest.raises(
                AuthenticationError, match="Invalid email/username or password"
            ):
                await login_user(
                    mock_db, "nobody@example.com", "anypassword"
                )

    @pytest.mark.asyncio
    async def test_login_disabled_account_raises(self):
        """Login to a disabled account should raise AuthenticationError."""
        mock_db = AsyncMock()
        password = "correctpassword"
        mock_user = _make_mock_user(is_active=False)
        mock_user.hashed_password = hash_password(password)

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=mock_user)

            with pytest.raises(
                AuthenticationError, match="Account is disabled"
            ):
                await login_user(mock_db, "test@example.com", password)

    @pytest.mark.asyncio
    async def test_login_with_long_password(self):
        """Login with a 128-char password must succeed (the original bug)."""
        mock_db = AsyncMock()
        long_password = "S3cur3P@ss!" * 12  # 132 chars
        long_password = long_password[:128]
        mock_user = _make_mock_user()
        mock_user.hashed_password = hash_password(long_password)

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=mock_user)

            user_dict, tokens = await login_user(
                mock_db, "test@example.com", long_password
            )

        assert user_dict["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_login_with_username_instead_of_email(self):
        """login_user should accept a username in the email field."""
        mock_db = AsyncMock()
        password = "correctpassword"
        mock_user = _make_mock_user()
        mock_user.hashed_password = hash_password(password)

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=mock_user)

            user_dict, tokens = await login_user(
                mock_db, "testuser", password
            )

        assert user_dict["username"] == "testuser"
        assert isinstance(tokens, TokenResponse)
        mock_user_repo.get_by_email_or_username.assert_called_once_with(
            mock_db, "testuser"
        )

    @pytest.mark.asyncio
    async def test_login_returns_token_type_bearer(self):
        """TokenResponse should include token_type='bearer'."""
        mock_db = AsyncMock()
        password = "correctpassword"
        mock_user = _make_mock_user()
        mock_user.hashed_password = hash_password(password)

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=mock_user)

            _, tokens = await login_user(
                mock_db, "test@example.com", password
            )

        assert tokens.token_type == "bearer"


# ─── Refresh Tokens Tests ────────────────────────────────────────


class TestRefreshTokens:
    """Tests for the refresh_tokens flow."""

    @pytest.mark.asyncio
    async def test_refresh_success(self):
        """Valid refresh token should return new token pair."""
        refresh = create_refresh_token("user-1")
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0  # Not blacklisted

        with patch("app.services.auth.get_redis", return_value=mock_redis):
            result = await refresh_tokens(refresh)

        assert isinstance(result, TokenResponse)
        assert result.access_token
        assert result.refresh_token
        # Old refresh token should be blacklisted
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_with_blacklisted_token_raises(self):
        """Revoked refresh token should raise AuthenticationError."""
        refresh = create_refresh_token("user-1")
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1  # Blacklisted

        with patch("app.services.auth.get_redis", return_value=mock_redis):
            with pytest.raises(
                AuthenticationError, match="Token has been revoked"
            ):
                await refresh_tokens(refresh)

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_raises(self):
        """Using an access token for refresh should raise AuthenticationError."""
        access = create_access_token("user-1")
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0  # Not blacklisted

        with patch("app.services.auth.get_redis", return_value=mock_redis):
            with pytest.raises(
                AuthenticationError, match="Invalid token type"
            ):
                await refresh_tokens(access)

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token_raises(self):
        """Expired refresh token should raise AuthenticationError."""
        from app.config import settings

        expired_payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "type": "refresh",
        }
        expired_token = jwt.encode(
            expired_payload, settings.SECRET_KEY, algorithm=ALGORITHM
        )
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0

        with patch("app.services.auth.get_redis", return_value=mock_redis):
            with pytest.raises(AuthenticationError):
                await refresh_tokens(expired_token)


# ─── Update Password Tests ───────────────────────────────────────


class TestUpdatePasswordByEmail:
    """Tests for the update_password_by_email flow."""

    @pytest.mark.asyncio
    async def test_update_password_success(self):
        """Valid email should update the user's password."""
        mock_db = AsyncMock()
        mock_user = _make_mock_user(email="user@example.com")

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=mock_user)
            mock_user_repo.update = AsyncMock()

            await update_password_by_email(
                mock_db, "user@example.com", "newstrongpass123"
            )

        mock_user_repo.update.assert_called_once()
        call_args = mock_user_repo.update.call_args
        # Should call update(db, user.id, {"hashed_password": ...})
        assert call_args[0][0] is mock_db
        assert call_args[0][1] == mock_user.id
        assert "hashed_password" in call_args[0][2]
        # The new hash should verify against the new password
        new_hash = call_args[0][2]["hashed_password"]
        assert verify_password("newstrongpass123", new_hash) is True

    @pytest.mark.asyncio
    async def test_update_password_user_not_found_raises(self):
        """Updating password for a nonexistent user should raise AuthenticationError."""
        mock_db = AsyncMock()

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=None)

            with pytest.raises(AuthenticationError, match="User not found"):
                await update_password_by_email(
                    mock_db, "ghost@example.com", "newpass123"
                )

    @pytest.mark.asyncio
    async def test_update_password_with_long_password(self):
        """Updating to a 128-char password must work (bcrypt pre-hash fix)."""
        mock_db = AsyncMock()
        mock_user = _make_mock_user()
        long_password = "N3wP@ssw0rd!" * 11  # 132 chars
        long_password = long_password[:128]

        with patch("app.services.auth.user_repo") as mock_user_repo:
            mock_user_repo.get_by_email_or_username = AsyncMock(return_value=mock_user)
            mock_user_repo.update = AsyncMock()

            await update_password_by_email(
                mock_db, "test@example.com", long_password
            )

        new_hash = mock_user_repo.update.call_args[0][2]["hashed_password"]
        assert verify_password(long_password, new_hash) is True
