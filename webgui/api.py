"""
WebGUI REST API — FastAPI router wrapping existing manager singletons.

Provides HTTP endpoints for dashboard, sessions, reports, agents, and auth.
All business logic lives in the existing manager modules; this module
only handles HTTP concerns (routing, serialization, auth dependency).
"""

import logging
import os
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Add config path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webgui.auth import Permission, auth_manager

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    authorization: str | None = None,
) -> dict[str, Any]:
    """Extract and verify JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.removeprefix("Bearer ")
    payload = await auth_manager.verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def require_permission(permission: Permission):
    """Factory for permission-checking dependencies."""

    async def _check(user: dict = Depends(get_current_user)):
        user_permissions = user.get("permissions", [])
        if permission.value not in user_permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _check


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    access_token: str


class ReportGenerateRequest(BaseModel):
    session_id: str
    report_type: str = "executive_summary"
    format: str = "json"


class SessionCompareRequest(BaseModel):
    session1_id: str
    session2_id: str


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@api_router.post("/auth/login")
async def login(req: LoginRequest):
    user = await auth_manager.authenticate_user(email=req.email, password=req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    tokens = await auth_manager.create_tokens(user)
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "token_type": tokens.token_type,
        "expires_in": tokens.expires_in,
    }


@api_router.post("/auth/refresh")
async def refresh(req: RefreshRequest):
    tokens = await auth_manager.refresh_tokens(req.refresh_token)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "token_type": tokens.token_type,
        "expires_in": tokens.expires_in,
    }


@api_router.post("/auth/logout")
async def logout(req: LogoutRequest, user: dict = Depends(get_current_user)):
    success = await auth_manager.logout(user["user_id"], req.access_token)
    if not success:
        raise HTTPException(status_code=500, detail="Logout failed")
    return {"status": "logged_out"}


@api_router.get("/auth/me")
async def auth_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "role": user.get("role"),
        "permissions": user.get("permissions", []),
    }


# ---------------------------------------------------------------------------
# Dashboard endpoints
# ---------------------------------------------------------------------------

@api_router.get("/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    from webgui.dashboard import dashboard_manager

    data = await dashboard_manager.export_dashboard_data()
    return data


@api_router.get("/dashboard/sessions")
async def get_dashboard_sessions(user: dict = Depends(get_current_user)):
    from webgui.dashboard import dashboard_manager

    sessions = await dashboard_manager.get_active_sessions()
    return [asdict(s) for s in sessions]


@api_router.get("/dashboard/agents")
async def get_dashboard_agents(user: dict = Depends(get_current_user)):
    from webgui.dashboard import dashboard_manager

    agents = await dashboard_manager.get_agent_status()
    return [asdict(a) for a in agents]


@api_router.get("/dashboard/metrics")
async def get_dashboard_metrics(user: dict = Depends(get_current_user)):
    from webgui.dashboard import dashboard_manager

    metrics = await dashboard_manager.get_resource_metrics()
    return asdict(metrics)


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------

@api_router.get("/sessions")
async def get_sessions(
    user_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    from webgui.history import history_manager

    sessions = await history_manager.get_session_history(
        user_id=user_id, limit=limit, offset=offset,
    )
    return [asdict(s) for s in sessions]


@api_router.get("/sessions/search")
async def search_sessions(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    from webgui.history import history_manager

    results = await history_manager.search_sessions(query=q, limit=limit)
    return [asdict(s) for s in results]


@api_router.get("/sessions/{session_id}")
async def get_session(session_id: str, user: dict = Depends(get_current_user)):
    from webgui.history import history_manager

    details = await history_manager.get_session_details(session_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return details


@api_router.post("/sessions/compare")
async def compare_sessions(
    req: SessionCompareRequest,
    user: dict = Depends(get_current_user),
):
    from webgui.history import history_manager

    comparison = await history_manager.compare_sessions(
        req.session1_id, req.session2_id,
    )
    if comparison is None:
        raise HTTPException(status_code=404, detail="One or both sessions not found")
    return asdict(comparison)


# ---------------------------------------------------------------------------
# Report endpoints
# ---------------------------------------------------------------------------

@api_router.get("/reports")
async def list_reports(user: dict = Depends(get_current_user)):
    from config.environment import config

    redis_client = config.get_redis_client()
    user_id = user.get("user_id", "")
    keys = redis_client.keys(f"report:*:{user_id}:*")
    reports = []
    for key in keys:
        data = redis_client.get(key)
        if data:
            import json

            reports.append(json.loads(data))
    return reports


@api_router.post("/reports/generate")
async def generate_report(
    req: ReportGenerateRequest,
    user: dict = Depends(require_permission(Permission.REPORTS_GENERATE)),
):
    from webgui.exports import ReportFormat, ReportRequest, ReportType, report_generator

    try:
        report_type = ReportType(req.report_type)
        report_format = ReportFormat(req.format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid report type or format: {e}")

    report_req = ReportRequest(
        session_id=req.session_id,
        report_type=report_type,
        format=report_format,
    )
    metadata = await report_generator.generate_report(report_req, user["user_id"])
    return {
        "report_id": metadata.report_id,
        "generated_at": metadata.generated_at.isoformat(),
        "session_id": metadata.session_id,
        "report_type": metadata.report_type.value,
        "format": metadata.format.value,
        "file_size": metadata.file_size,
    }


@api_router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    from config.environment import config

    redis_client = config.get_redis_client()
    import json

    meta_data = redis_client.get(f"report:{report_id}:meta")
    if not meta_data:
        raise HTTPException(status_code=404, detail="Report not found")

    meta = json.loads(meta_data)
    file_path = meta.get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream",
    )


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------

@api_router.get("/agents")
async def get_agents(user: dict = Depends(get_current_user)):
    from webgui.agent_monitor import agent_monitor

    statuses = await agent_monitor.get_all_agent_status()
    return [asdict(s) for s in statuses]


@api_router.get("/agents/queues")
async def get_agent_queues(user: dict = Depends(get_current_user)):
    from webgui.agent_monitor import agent_monitor

    return await agent_monitor.get_queue_depths()


@api_router.get("/agents/{agent_name}")
async def get_agent_detail(
    agent_name: str,
    user: dict = Depends(get_current_user),
):
    from webgui.agent_monitor import agent_monitor

    metrics = await agent_monitor.get_agent_metrics(agent_name)
    if metrics is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return asdict(metrics)
