"""Session management routes."""

from __future__ import annotations

from fastapi import APIRouter

from neurosync.api.schemas import SessionStartRequest
from neurosync.api.schemas.responses import SessionResponse, StatusResponse

router = APIRouter(prefix="/session", tags=["session"])

# In-memory session registry (shared via app.state in server.py)
_sessions: dict = {}


def _get_sessions() -> dict:
    return _sessions


def set_sessions(sessions: dict) -> None:
    global _sessions
    _sessions = sessions


@router.post("/start", response_model=SessionResponse)
async def start_session(config: SessionStartRequest) -> SessionResponse:
    """Start a new learning session."""
    _sessions[config.session_id] = {
        "session_id": config.session_id,
        "student_id": config.student_id,
        "lesson_id": config.lesson_id,
        "webcam_enabled": config.webcam_enabled,
        "status": "active",
        "signals": {
            "attention": 1.0,
            "frustration": 0.0,
            "fatigue": 0.0,
            "boredom": 0.0,
            "engagement": 1.0,
            "cognitive_load": 0.3,
        },
    }
    return SessionResponse(session_id=config.session_id, status="started")


@router.post("/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: str) -> SessionResponse:
    """End a learning session."""
    if session_id in _sessions:
        _sessions[session_id]["status"] = "ended"
        del _sessions[session_id]
    return SessionResponse(session_id=session_id, status="ended")


@router.get("/{session_id}", response_model=StatusResponse)
async def get_session_status(session_id: str) -> StatusResponse:
    """Get session status."""
    if session_id in _sessions:
        return StatusResponse(status="active", message=f"Session {session_id} is active")
    return StatusResponse(status="not_found", message=f"Session {session_id} not found")
