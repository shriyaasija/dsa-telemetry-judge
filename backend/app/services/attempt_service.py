from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.attempt import Attempt, AttemptStatus
from app.models.problem import Problem
from app.schemas.attempt import AttemptCreate, AttemptUpdate, AttemptSubmit, AttemptResponse, AttemptListResponse
from typing import Optional
from datetime import datetime, timezone
from app.services.dashboard_service import DashboardService


class AttemptService:
    @staticmethod
    async def start_attempt(db: AsyncSession, user_id: int, attempt_data: AttemptCreate) -> Attempt:
        """Start a new attempt on a problem"""
        # Verify problem exists
        stmt = select(Problem).where(Problem.id == attempt_data.problem_id)
        result = await db.execute(stmt)
        problem = result.scalar_one_or_none()
        if not problem:
            raise ValueError("Problem not found")

        attempt = Attempt(
            user_id=user_id,
            problem_id=attempt_data.problem_id,
            language=attempt_data.language,
            status=AttemptStatus.STARTED,
        )

        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
        await DashboardService.invalidate_user_stats(user_id)
        return attempt

    @staticmethod
    async def submit_attempt(
        db: AsyncSession, attempt_id: int, user_id: int, submit_data: AttemptSubmit
    ) -> Attempt:
        """Submit code for an attempt"""
        attempt = await AttemptService.get_attempt(db, attempt_id, user_id)
        if not attempt:
            raise ValueError("Attempt not found")
        
        if attempt.status not in (AttemptStatus.STARTED, AttemptStatus.SUBMITTED):
            raise ValueError(f"Cannot submit attempt with status '{attempt.status}'")

        now = datetime.now(timezone.utc)
        attempt.code = submit_data.code
        attempt.language = submit_data.language
        attempt.status = AttemptStatus.SUBMITTED
        attempt.submitted_at = now
        attempt.duration_seconds = int((now - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds())

        # For now, marking as passed with dummy results
        # Later, actual code execution will be added
        attempt.status = AttemptStatus.PASSED
        attempt.is_correct = True
        attempt.completed_at = now
        attempt.test_cases_passed = 1
        attempt.test_cases_total = 1

        await db.commit()
        await db.refresh(attempt)
        await DashboardService.invalidate_user_stats(user_id)
        return attempt

    @staticmethod
    async def get_attempt(db: AsyncSession, attempt_id: int, user_id: int) -> Optional[Attempt]:
        """Get a specific attempt"""
        stmt = select(Attempt).where(Attempt.id == attempt_id, Attempt.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_user_attempts(
        db: AsyncSession,
        user_id: int,
        problem_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Attempt], int]:
        """List attempts for a user with optional filters."""
        stmt = select(Attempt).where(Attempt.user_id == user_id)
        if problem_id:
            stmt = stmt.where(Attempt.problem_id == problem_id)
        if status:
            stmt = stmt.where(Attempt.status == status)

        # Count
        count_stmt = select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)
        if problem_id:
            count_stmt = count_stmt.where(Attempt.problem_id == problem_id)
        if status:
            count_stmt = count_stmt.where(Attempt.status == status)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # Paginate
        stmt = stmt.order_by(Attempt.started_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        attempts = result.scalars().all()
        return attempts, total

    @staticmethod
    async def abandon_attempt(db: AsyncSession, attempt_id: int, user_id: int) -> Attempt:
        """Mark an attempt as abandoned."""
        attempt = await AttemptService.get_attempt(db, attempt_id, user_id)
        if not attempt:
            raise ValueError("Attempt not found")
        if attempt.status != AttemptStatus.STARTED:
            raise ValueError("Can only abandon a started attempt")

        now = datetime.now(timezone.utc)
        attempt.status = AttemptStatus.ABANDONED
        attempt.completed_at = now
        attempt.duration_seconds = int((now - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds())
        
        await db.commit()
        await db.refresh(attempt)
        await DashboardService.invalidate_user_stats(user_id)
        return attempt