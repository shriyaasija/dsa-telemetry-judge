from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import UserStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=UserStats)
async def get_my_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get your aggregated dashboard stats"""
    stats = await DashboardService.get_user_stats(db, current_user.id)
    return stats


@router.post("/stats/refresh", response_model=UserStats)
async def refresh_my_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Force-refresh your dashboard stats"""
    await DashboardService.invalidate_user_stats(current_user.id)
    stats = await DashboardService.get_user_stats(db, current_user.id)
    return stats