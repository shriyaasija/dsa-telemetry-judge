from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.telemetry_service import TelemetryService
from app.schemas.telemetry import (
    TelemetryEventCreate, TelemetryBatchCreate,
    TelemetryEventResponse, TelemetrySummary,
)
from typing import Optional

router = APIRouter(prefix="/attempts/{attempt_id}/telemetry", tags=["telemetry"])


@router.post("/events", response_model=TelemetryEventResponse, status_code=status.HTTP_201_CREATED)
async def record_event(
    attempt_id: int,
    event_data: TelemetryEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a single telemetry event."""
    try:
        event = await TelemetryService.record_event(db, attempt_id, current_user.id, event_data)
        return event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/events/batch", status_code=status.HTTP_201_CREATED)
async def record_batch(
    attempt_id: int,
    batch_data: TelemetryBatchCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a batch of telemetry events (more efficient)."""
    try:
        count = await TelemetryService.record_batch(db, attempt_id, current_user.id, batch_data)
        return {"message": f"Recorded {count} events", "count": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events", response_model=list[TelemetryEventResponse])
async def get_events(
    attempt_id: int,
    event_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all telemetry events for an attempt."""
    try:
        events = await TelemetryService.get_events(db, attempt_id, current_user.id, event_type)
        return events
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary", response_model=TelemetrySummary)
async def get_telemetry_summary(
    attempt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated telemetry summary for an attempt."""
    try:
        summary = await TelemetryService.get_summary(db, attempt_id, current_user.id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
