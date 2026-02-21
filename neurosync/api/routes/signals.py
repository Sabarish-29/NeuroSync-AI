"""Signal and event routes."""

from __future__ import annotations

from fastapi import APIRouter

from neurosync.api.schemas import EventRequest, FusionCycleRequest
from neurosync.api.schemas.responses import (
    EventResponse,
    FusionCycleResponse,
    InterventionResponse,
    SignalSnapshot,
)

router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("/event", response_model=EventResponse)
async def record_event(event: EventRequest) -> EventResponse:
    """Record a learning event (video, question, idle, etc.)."""
    return EventResponse(status="recorded", event_type=event.event_type)


@router.post("/fusion-cycle", response_model=FusionCycleResponse)
async def run_fusion_cycle(request: FusionCycleRequest) -> FusionCycleResponse:
    """Run a single fusion cycle and return interventions + signals."""
    # In production this delegates to NeuroSyncOrchestrator.run_lesson_cycle()
    # For the UI layer we return a snapshot
    return FusionCycleResponse(
        session_id=request.session_id,
        interventions=[],
        signals=SignalSnapshot(session_id=request.session_id),
    )


@router.get("/{session_id}", response_model=SignalSnapshot)
async def get_current_signals(session_id: str) -> SignalSnapshot:
    """Get the latest signal snapshot for a session."""
    return SignalSnapshot(session_id=session_id)
