"""Intervention routes."""

from __future__ import annotations

from fastapi import APIRouter

from neurosync.api.schemas.responses import InterventionResponse, StatusResponse

router = APIRouter(prefix="/interventions", tags=["interventions"])


@router.get("/{session_id}/active", response_model=list[InterventionResponse])
async def get_active_interventions(session_id: str) -> list[InterventionResponse]:
    """Get currently active interventions for a session."""
    return []


@router.post("/{intervention_id}/acknowledge", response_model=StatusResponse)
async def acknowledge_intervention(intervention_id: str) -> StatusResponse:
    """Acknowledge an intervention (student dismissed it)."""
    return StatusResponse(status="acknowledged", message=f"Intervention {intervention_id} acknowledged")
