"""Content generation routes."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form

from neurosync.api.schemas.responses import ContentGenerationResponse, StatusResponse

router = APIRouter(prefix="/content", tags=["content"])

# Track async generation tasks
_generation_tasks: dict[str, ContentGenerationResponse] = {}


@router.post("/upload", response_model=ContentGenerationResponse)
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(""),
    generate_video: bool = Form(False),
    generate_slides: bool = Form(True),
    generate_notes: bool = Form(True),
    generate_story: bool = Form(True),
    generate_quiz: bool = Form(True),
) -> ContentGenerationResponse:
    """Upload a PDF and start content generation."""
    task_id = str(uuid.uuid4())

    # Read file content (in production, save to disk and process async)
    _content = await file.read()

    result = ContentGenerationResponse(
        task_id=task_id,
        status="processing",
        progress=0.0,
        title=title or (file.filename or "Untitled"),
    )
    _generation_tasks[task_id] = result
    return result


@router.get("/status/{task_id}", response_model=ContentGenerationResponse)
async def get_generation_status(task_id: str) -> ContentGenerationResponse:
    """Check the status of a content generation task."""
    if task_id in _generation_tasks:
        return _generation_tasks[task_id]
    return ContentGenerationResponse(task_id=task_id, status="not_found")


@router.get("/library", response_model=list[ContentGenerationResponse])
async def list_content_library() -> list[ContentGenerationResponse]:
    """List all generated content."""
    return list(_generation_tasks.values())


@router.delete("/{task_id}", response_model=StatusResponse)
async def delete_content(task_id: str) -> StatusResponse:
    """Delete generated content."""
    if task_id in _generation_tasks:
        del _generation_tasks[task_id]
        return StatusResponse(status="deleted")
    return StatusResponse(status="not_found")
