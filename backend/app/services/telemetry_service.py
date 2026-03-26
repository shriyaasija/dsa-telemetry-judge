from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.telemetry_event import TelemetryEvent
from app.models.attempt import Attempt
from app.schemas.telemetry import TelemetryEventCreate, TelemetryBatchCreate, TelemetrySummary
from typing import Optional


class TelemetryService:
    @staticmethod
    async def record_event(
        db: AsyncSession, attempt_id: int, user_id: int, event_data: TelemetryEventCreate
    ) -> TelemetryEvent:
        """Record a single telemetry event."""
        # Verify attempt belongs to user
        stmt = select(Attempt).where(Attempt.id == attempt_id, Attempt.user_id == user_id)
        result = await db.execute(stmt)
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise ValueError("Attempt not found")

        event = TelemetryEvent(
            attempt_id=attempt_id,
            event_type=event_data.event_type,
            time_since_start_ms=event_data.time_since_start_ms,
            data=event_data.data,
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def record_batch(
        db: AsyncSession, attempt_id: int, user_id: int, batch_data: TelemetryBatchCreate
    ) -> int:
        """Record a batch of telemetry events. Returns count of events created."""
        # Verify attempt belongs to user
        stmt = select(Attempt).where(Attempt.id == attempt_id, Attempt.user_id == user_id)
        result = await db.execute(stmt)
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise ValueError("Attempt not found")

        events = [
            TelemetryEvent(
                attempt_id=attempt_id,
                event_type=e.event_type,
                time_since_start_ms=e.time_since_start_ms,
                data=e.data,
            )
            for e in batch_data.events
        ]

        db.add_all(events)
        await db.commit()
        return len(events)

    @staticmethod
    async def get_events(
        db: AsyncSession,
        attempt_id: int,
        user_id: int,
        event_type: Optional[str] = None,
    ) -> list[TelemetryEvent]:
        """Get all telemetry events for an attempt."""
        # Verify attempt belongs to user
        stmt = select(Attempt).where(Attempt.id == attempt_id, Attempt.user_id == user_id)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise ValueError("Attempt not found")

        stmt = select(TelemetryEvent).where(TelemetryEvent.attempt_id == attempt_id)
        if event_type:
            stmt = stmt.where(TelemetryEvent.event_type == event_type)

        stmt = stmt.order_by(TelemetryEvent.timestamp.asc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_summary(db: AsyncSession, attempt_id: int, user_id: int) -> TelemetrySummary:
        """Get aggregated telemetry summary for an attempt."""
        # Verify attempt belongs to user
        stmt = select(Attempt).where(Attempt.id == attempt_id, Attempt.user_id == user_id)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise ValueError("Attempt not found")

        # Count events by type
        async def count_type(event_type: str) -> int:
            stmt = select(func.count()).select_from(TelemetryEvent).where(
                TelemetryEvent.attempt_id == attempt_id,
                TelemetryEvent.event_type == event_type,
            )
            result = await db.execute(stmt)
            return result.scalar() or 0

        total_keystrokes = await count_type("keystroke")
        total_pastes = await count_type("paste")
        total_undos = await count_type("undo")
        total_redos = await count_type("redo")
        total_runs = await count_type("run_code")

        # Count total events
        total_stmt = select(func.count()).select_from(TelemetryEvent).where(
            TelemetryEvent.attempt_id == attempt_id
        )
        total_result = await db.execute(total_stmt)
        events_count = total_result.scalar() or 0

        # Calculate idle time from idle_start/idle_end events
        idle_events = await TelemetryService.get_events(db, attempt_id, user_id, "idle_start")
        idle_time_ms = sum(
            (e.data or {}).get("duration_ms", 0) for e in idle_events
        )

        # Active time = total time - idle time (approximation)
        attempt_stmt = select(Attempt).where(Attempt.id == attempt_id)
        attempt_result = await db.execute(attempt_stmt)
        attempt = attempt_result.scalar_one_or_none()
        total_time_ms = (attempt.duration_seconds or 0) * 1000
        active_time_ms = max(0, total_time_ms - idle_time_ms)

        # Undo rate
        undo_rate = (total_undos / total_keystrokes) if total_keystrokes > 0 else 0.0

        return TelemetrySummary(
            attempt_id=attempt_id,
            total_keystrokes=total_keystrokes,
            total_pastes=total_pastes,
            total_undos=total_undos,
            total_redos=total_redos,
            total_runs=total_runs,
            idle_time_ms=idle_time_ms,
            active_time_ms=active_time_ms,
            undo_rate=round(undo_rate, 4),
            events_count=events_count,
        )