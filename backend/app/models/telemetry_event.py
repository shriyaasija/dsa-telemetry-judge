from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key — links to an attempt
    attempt_id = Column(Integer, ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False)
    # Event Info
    event_type = Column(String(50), nullable=False)
    # Event types: "keystroke", "paste", "undo", "redo", "idle_start",
    #              "idle_end", "tab_switch", "run_code", "submit"

    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_since_start_ms = Column(Integer, nullable=True)  # Milliseconds since attempt started

    # Event-specific data (flexible JSON column)
    data = Column(JSON, nullable=True)
    # Examples:
    #   keystroke: {"key": "a", "cursor_position": 42}
    #   paste: {"length": 150, "cursor_position": 10}
    #   undo: {"cursor_position": 35}
    #   idle_start: {"duration_ms": 30000}
    #   run_code: {"success": true, "output": "..."}

    # Relationships
    attempt = relationship("Attempt", backref="telemetry_events")

    # Indexes 
    __table_args__ = (
        Index('idx_attempt_type', 'attempt_id', 'event_type'),
        Index('idx_attempt_timestamp', 'attempt_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<TelemetryEvent(id={self.id}, attempt={self.attempt_id}, type='{self.event_type}')>"