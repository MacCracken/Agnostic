import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from webgui.auth import (
        AuthManager,
        AuthProvider,
        AuthToken,
        Permission,
        User,
        UserRole,
    )
except ImportError:
    pytest.skip("webgui.auth module not available", allow_module_level=True)


@pytest.fixture()
def auth_mgr(mock_redis):
    """Create AuthManager with mocked Redis."""
    with patch("webgui.auth.config") as mock_config:
        mock_config.get_redis_client.return_value = mock_redis
        mgr = AuthManager()
    return mgr


class TestAuthManagerInit:
    """Tests for AuthManager initialization"""

    def test_default_init(self, mock_redis):
        with patch("webgui.auth.config") as mock_config:
            mock_config.get_redis_client.return_value = mock_redis
            mgr = AuthManager()
        assert mgr.access_token_expire_minutes == 15
        assert mgr.refresh_token_expire_days == 7
        assert mgr.secret_key is not None

    def test_production_requires_secret_key(self, mock_redis):
        with patch("webgui.auth.config") as mock_config, \
             patch.dict(os.environ, {"ENVIRONMENT": "production", "WEBGUI_SECRET_KEY": ""}):
            mock_config.get_redis_client.return_value = mock_redis
            os.environ.pop("WEBGUI_SECRET_KEY", None)
            with pytest.raises(ValueError, match="WEBGUI_SECRET_KEY must be set"):
                AuthManager()

    def test_production_with_secret_key(self, mock_redis):
        with patch("webgui.auth.config") as mock_config, \
             patch.dict(os.environ, {"ENVIRONMENT": "production", "WEBGUI_SECRET_KEY": "test-secret-key-abc"}):
            mock_config.get_redis_client.return_value = mock_redis
            mgr = AuthManager()
        assert mgr.secret_key == "test-secret-key-abc"


class TestRolePermissions:
    """Tests for role-permission mapping"""

    def test_super_admin_has_all_permissions(self, auth_mgr):
        perms = auth_mgr.role_permissions[UserRole.SUPER_ADMIN]
        assert Permission.USERS_MANAGE in perms
        assert Permission.SYSTEM_CONFIGURE in perms
        assert Permission.SESSIONS_DELETE in perms

    def test_viewer_has_limited_permissions(self, auth_mgr):
        perms = auth_mgr.role_permissions[UserRole.VIEWER]
        assert Permission.SESSIONS_READ in perms
        assert Permission.USERS_MANAGE not in perms
        assert Permission.SESSIONS_WRITE not in perms

    def test_qa_engineer_permissions(self, auth_mgr):
        perms = auth_mgr.role_permissions[UserRole.QA_ENGINEER]
        assert Permission.SESSIONS_READ in perms
        assert Permission.SESSIONS_WRITE in perms
        assert Permission.AGENTS_CONTROL in perms
        assert Permission.SYSTEM_CONFIGURE not in perms


class TestTokens:
    """Tests for JWT token creation and verification"""

    @pytest.mark.asyncio
    async def test_create_tokens(self, auth_mgr):
        user = User(
            user_id="u1",
            email="test@example.com",
            name="Test User",
            role=UserRole.QA_ENGINEER,
            auth_provider=AuthProvider.LOCAL,
            organization_id=None,
            team_id=None,
            created_at=datetime.now(),
            last_login=None,
            is_active=True,
            permissions=auth_mgr.role_permissions[UserRole.QA_ENGINEER],
            metadata={},
        )
        tokens = await auth_mgr.create_tokens(user)
        assert isinstance(tokens, AuthToken)
        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_verify_valid_token(self, auth_mgr, mock_redis):
        # Ensure token is not blacklisted
        mock_redis.exists.return_value = False
        user = User(
            user_id="u2",
            email="verify@example.com",
            name="Verify User",
            role=UserRole.VIEWER,
            auth_provider=AuthProvider.LOCAL,
            organization_id=None,
            team_id=None,
            created_at=datetime.now(),
            last_login=None,
            is_active=True,
            permissions=auth_mgr.role_permissions[UserRole.VIEWER],
            metadata={},
        )
        tokens = await auth_mgr.create_tokens(user)
        payload = await auth_mgr.verify_token(tokens.access_token)
        assert payload is not None
        assert payload["user_id"] == "u2"
        assert payload["email"] == "verify@example.com"

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, auth_mgr):
        payload = await auth_mgr.verify_token("invalid.token.here")
        assert payload is None

    @pytest.mark.asyncio
    async def test_verify_blacklisted_token(self, auth_mgr, mock_redis):
        user = User(
            user_id="u3",
            email="bl@example.com",
            name="BL User",
            role=UserRole.VIEWER,
            auth_provider=AuthProvider.LOCAL,
            organization_id=None,
            team_id=None,
            created_at=datetime.now(),
            last_login=None,
            is_active=True,
            permissions=set(),
            metadata={},
        )
        tokens = await auth_mgr.create_tokens(user)
        # Simulate blacklisted token
        mock_redis.exists.return_value = True
        payload = await auth_mgr.verify_token(tokens.access_token)
        assert payload is None
