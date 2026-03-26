from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.attempt_service import AttemptService
from app.schemas.attempt import (
    AttemptCreate, AttemptSubmit, AttemptResponse, AttemptListResponse
)
from typing import Optional

router = APIRouter(prefix="/attempts", tags=["attempts"])


@router.post("/", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
async def start_attempt(
    attempt_data: AttemptCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new attempt on a problem."""
    try:
        attempt = await AttemptService.start_attempt(db, current_user.id, attempt_data)
        return attempt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=AttemptListResponse)
async def list_attempts(
    problem_id: Optional[int] = Query(None),
    attempt_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List your attempts with optional filters."""
    skip = (page - 1) * page_size
    attempts, total = await AttemptService.list_user_attempts(
        db, current_user.id,
        problem_id=problem_id, status=attempt_status,
        skip=skip, limit=page_size,
    )
    return AttemptListResponse(
        attempts=attempts, total=total, page=page, page_size=page_size
    )

@router.get("/{attempt_id}", response_model=AttemptResponse)
async def get_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific attempt."""
    attempt = await AttemptService.get_attempt(db, attempt_id, current_user.id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt

@router.post("/{attempt_id}/submit", response_model=AttemptResponse)
async def submit_attempt(
    attempt_id: int,
    submit_data: AttemptSubmit,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit code for an attempt."""
    try:
        attempt = await AttemptService.submit_attempt(db, attempt_id, current_user.id, submit_data)
        return attempt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{attempt_id}/abandon", response_model=AttemptResponse)
async def abandon_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Abandon an in-progress attempt."""
    try:
        attempt = await AttemptService.abandon_attempt(db, attempt_id, current_user.id)
        return attempt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))