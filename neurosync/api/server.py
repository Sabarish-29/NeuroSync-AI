"""NeuroSync FastAPI server — bridge between Electron UI and Python backend.

Usage:
    python -m neurosync.api.server          # production
    uvicorn neurosync.api.server:app --reload  # development
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from neurosync.api.routes import session, signals, interventions, content
from neurosync.api.schemas.responses import (
    HealthResponse,
    SignalSnapshot,
    ReadinessResponse,
    DueReviewsListResponse,
    DueReviewResponse,
    ReviewResultResponse,
    KnowledgeMapResponse,
    KnowledgeNodeResponse,
    KnowledgeEdgeResponse,
)
from neurosync.api.schemas import ReadinessRequest, ReviewSubmitRequest

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="NeuroSync API",
        description="Backend API for NeuroSync AI adaptive learning platform",
        version="5.1.0",
    )

    # CORS — allow Electron renderer (localhost:5173) and any origin for dev
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    application.include_router(session.router)
    application.include_router(signals.router)
    application.include_router(interventions.router)
    application.include_router(content.router)

    return application


app = create_app()

# ---------------------------------------------------------------------------
# Top-level routes
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    from neurosync.api.routes.session import _get_sessions

    return HealthResponse(
        status="healthy",
        version="5.1.0",
        active_sessions=len(_get_sessions()),
    )


# ---------------------------------------------------------------------------
# Events (top-level, matches Electron IPC handler)
# ---------------------------------------------------------------------------


@app.post("/events")
async def record_event(event: dict[str, Any]) -> dict[str, str]:
    """Record a learning event (convenience route for IPC)."""
    return {"status": "recorded"}


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


@app.get("/reviews/{student_id}/due", response_model=DueReviewsListResponse)
async def get_due_reviews(student_id: str) -> DueReviewsListResponse:
    """Get due spaced-repetition reviews for a student."""
    # In production, delegates to SpacedRepetitionScheduler.get_due_reviews()
    return DueReviewsListResponse(student_id=student_id, reviews=[], total=0)


@app.post("/reviews/submit", response_model=ReviewResultResponse)
async def submit_review(data: ReviewSubmitRequest) -> ReviewResultResponse:
    """Submit a review result."""
    return ReviewResultResponse(
        student_id=data.student_id,
        concept_id=data.concept_id,
        score=data.score,
        status="recorded",
    )


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------


@app.post("/readiness/start", response_model=ReadinessResponse)
async def start_readiness_check(request: ReadinessRequest) -> ReadinessResponse:
    """Start a pre-lesson readiness check."""
    return ReadinessResponse(
        check_id=str(uuid.uuid4()),
        session_id=request.session_id,
        student_id=request.student_id,
        lesson_topic=request.lesson_topic,
        readiness_score=0.75,
        anxiety_score=0.2,
        status="ready",
        recommendation="Student is ready to begin.",
    )


# ---------------------------------------------------------------------------
# Knowledge map
# ---------------------------------------------------------------------------


@app.get("/knowledge/map/{student_id}", response_model=KnowledgeMapResponse)
async def get_knowledge_map(student_id: str) -> KnowledgeMapResponse:
    """Get the knowledge map for a student."""
    # Example placeholder data for demo
    nodes = [
        KnowledgeNodeResponse(id="c1", label="Photosynthesis", category="biology", mastery=0.8, status="mastered"),
        KnowledgeNodeResponse(id="c2", label="Cellular Respiration", category="biology", mastery=0.5, status="learning"),
        KnowledgeNodeResponse(id="c3", label="ATP Cycle", category="biology", mastery=0.3, status="learning"),
        KnowledgeNodeResponse(id="c4", label="Chloroplast Structure", category="biology", mastery=0.9, status="mastered"),
        KnowledgeNodeResponse(id="c5", label="Mitochondria", category="biology", mastery=0.4, status="learning"),
    ]
    edges = [
        KnowledgeEdgeResponse(source="c1", target="c2", relationship="prerequisite"),
        KnowledgeEdgeResponse(source="c2", target="c3", relationship="prerequisite"),
        KnowledgeEdgeResponse(source="c4", target="c1", relationship="part_of"),
        KnowledgeEdgeResponse(source="c5", target="c2", relationship="part_of"),
    ]
    return KnowledgeMapResponse(student_id=student_id, nodes=nodes, edges=edges)


# ---------------------------------------------------------------------------
# WebSocket for real-time signal streaming
# ---------------------------------------------------------------------------


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """WebSocket for real-time signal updates (250ms interval)."""
    await websocket.accept()
    try:
        while True:
            snapshot = SignalSnapshot(session_id=session_id, timestamp=asyncio.get_event_loop().time())
            await websocket.send_json(snapshot.model_dump())
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
