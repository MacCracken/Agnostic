import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from fastapi.testclient import TestClient
except ImportError:
    pytest.skip("fastapi not available", allow_module_level=True)

try:
    from webgui.api import api_router, get_current_user
except ImportError:
    pytest.skip("webgui.api module not available", allow_module_level=True)

from fastapi import FastAPI


@pytest.fixture()
def app():
    """Create a test FastAPI app with the API router mounted."""
    test_app = FastAPI()
    test_app.include_router(api_router)

    @test_app.get("/health")
    async def health():
        return {"status": "healthy"}

    return test_app


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def auth_user():
    """Return a mock authenticated user payload."""
    return {
        "user_id": "test-user-1",
        "email": "test@example.com",
        "role": "qa_engineer",
        "permissions": [
            "sessions:read",
            "sessions:write",
            "agents:control",
            "reports:generate",
        ],
    }


@pytest.fixture()
def authed_client(app, auth_user):
    """Create a TestClient with auth dependency overridden."""

    async def override_get_current_user():
        return auth_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestAuthEndpoints:
    def test_login_missing_credentials(self, client):
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 422  # validation error

    @patch("webgui.api.auth_manager")
    def test_login_invalid_credentials(self, mock_auth, client):
        mock_auth.authenticate_user = AsyncMock(return_value=None)
        resp = client.post(
            "/api/auth/login",
            json={"email": "bad@example.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_authenticated(self, authed_client, auth_user):
        resp = authed_client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == auth_user["user_id"]
        assert data["email"] == auth_user["email"]


class TestDashboardEndpoints:
    def test_dashboard_unauthenticated(self, client):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 401

    @patch("webgui.api.auth_manager")
    def test_dashboard_authenticated(self, mock_auth, authed_client):
        with patch("webgui.dashboard.dashboard_manager") as mock_dm:
            mock_dm.export_dashboard_data = AsyncMock(return_value={
                "sessions": [],
                "agents": [],
                "metrics": {},
            })
            resp = authed_client.get("/api/dashboard")
            assert resp.status_code == 200


class TestAgentEndpoints:
    @patch("webgui.agent_monitor.agent_monitor")
    def test_agents_list(self, mock_monitor, authed_client):
        mock_monitor.get_all_agent_status = AsyncMock(return_value=[])
        resp = authed_client.get("/api/agents")
        assert resp.status_code == 200

    @patch("webgui.agent_monitor.agent_monitor")
    def test_agent_queues(self, mock_monitor, authed_client):
        mock_monitor.get_queue_depths = AsyncMock(return_value={"qa_manager": 0})
        resp = authed_client.get("/api/agents/queues")
        assert resp.status_code == 200
