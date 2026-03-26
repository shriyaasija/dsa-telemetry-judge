from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_
from app.models.attempt import Attempt, AttemptStatus
from app.models.problem import Problem
from app.models.telemetry_event import TelemetryEvent
from app.schemas.dashboard import UserStats, ProblemStats
from app.core.redis import RedisService, user_stats_key
from typing import Optional
from datetime import datetime, timezone, timedelta


class DashboardService:
    STATS_TTL = 300  # 5 minutes

    @staticmethod
    async def get_user_stats(db: AsyncSession, user_id: int) -> UserStats:
        """Get aggregated stats for a user"""

        # 1. Check cache first
        cache_key = user_stats_key(user_id)
        try:
            cached = await RedisService.get(cache_key)
            if cached:
                return UserStats(**cached)
        except Exception:
            pass  

        # 2. Cache miss 
        stats = await DashboardService._compute_user_stats(db, user_id)

        # 3. Store in cache
        try:
            await RedisService.set(cache_key, stats.model_dump(), DashboardService.STATS_TTL)
        except Exception:
            pass  # Redis down 

        return stats

    @staticmethod
    async def _compute_user_stats(db: AsyncSession, user_id: int) -> UserStats:
        """Run the actual database queries to compute user stats"""

        # Total attempts by status
        status_counts_stmt = (
            select(
                Attempt.status,
                func.count().label("count"),
            )
            .where(Attempt.user_id == user_id)
            .group_by(Attempt.status)
        )
        result = await db.execute(status_counts_stmt)
        status_counts = {row.status: row.count for row in result}

        total_attempts = sum(status_counts.values())
        total_solved = status_counts.get(AttemptStatus.PASSED, 0)
        total_failed = status_counts.get(AttemptStatus.FAILED, 0)
        total_abandoned = status_counts.get(AttemptStatus.ABANDONED, 0)
        solve_rate = (total_solved / total_attempts) if total_attempts > 0 else 0.0

        time_stmt = (
            select(
                func.avg(Attempt.duration_seconds).label("avg_time"),
                func.min(Attempt.duration_seconds).label("min_time"),
            )
            .where(
                Attempt.user_id == user_id,
                Attempt.status == AttemptStatus.PASSED,
                Attempt.duration_seconds.isnot(None),
            )
        )
        time_result = await db.execute(time_stmt)
        time_row = time_result.one()
        avg_solve_time = float(time_row.avg_time or 0)
        fastest_solve = int(time_row.min_time) if time_row.min_time else None

        # Problems solved by difficulty
        difficulty_stmt = (
            select(
                Problem.difficulty,
                func.count(func.distinct(Attempt.problem_id)).label("count"),
            )
            .join(Problem, Attempt.problem_id == Problem.id)
            .where(
                Attempt.user_id == user_id,
                Attempt.status == AttemptStatus.PASSED,
            )
            .group_by(Problem.difficulty)
        )
        diff_result = await db.execute(difficulty_stmt)
        problems_by_difficulty = {row.difficulty.value: row.count for row in diff_result}

        streak = await DashboardService._compute_streak(db, user_id)

        recent_stmt = (
            select(
                Attempt.id,
                Attempt.problem_id,
                Attempt.status,
                Attempt.duration_seconds,
                Attempt.started_at,
                Problem.title.label("problem_title"),
                Problem.difficulty,
            )
            .join(Problem, Attempt.problem_id == Problem.id)
            .where(Attempt.user_id == user_id)
            .order_by(Attempt.started_at.desc())
            .limit(10)
        )
        recent_result = await db.execute(recent_stmt)
        recent_activity = [
            {
                "attempt_id": row.id,
                "problem_id": row.problem_id,
                "problem_title": row.problem_title,
                "difficulty": row.difficulty.value,
                "status": row.status.value,
                "duration_seconds": row.duration_seconds,
                "started_at": row.started_at.isoformat() if row.started_at else None,
            }
            for row in recent_result
        ]

        return UserStats(
            user_id=user_id,
            total_attempts=total_attempts,
            total_solved=total_solved,
            total_failed=total_failed,
            total_abandoned=total_abandoned,
            solve_rate=round(solve_rate, 4),
            avg_solve_time_seconds=round(avg_solve_time, 2),
            fastest_solve_seconds=fastest_solve,
            current_streak=streak,
            problems_by_difficulty=problems_by_difficulty,
            recent_activity=recent_activity,
        )

    @staticmethod
    async def _compute_streak(db: AsyncSession, user_id: int) -> int:
        """Count consecutive days (ending today) with at least 1 solved attempt."""
        today = datetime.now(timezone.utc).date()
        streak = 0
        check_date = today

        while True:
            start = datetime.combine(check_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end = start + timedelta(days=1)

            stmt = (
                select(func.count())
                .select_from(Attempt)
                .where(
                    Attempt.user_id == user_id,
                    Attempt.status == AttemptStatus.PASSED,
                    Attempt.completed_at >= start,
                    Attempt.completed_at < end,
                )
            )
            result = await db.execute(stmt)
            count = result.scalar()

            if count and count > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return streak

    @staticmethod
    async def invalidate_user_stats(user_id: int) -> None:
        """Call this whenever a user's attempt data changes."""
        try:
            await RedisService.delete_pattern(f"user:{user_id}:*")
        except Exception:
            pass  