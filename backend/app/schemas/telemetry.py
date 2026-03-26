from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any

class TelemetryEventCreate(BaseModel):
    event_type: str = Field(..., max_length=50)
    time_since_start_ms: Optional[int] = None
    data: Optional[dict[str, Any]] = None

class TelemetryBatchCreate(BaseModel):
    """Send multiple events at once (more efficient than one-by-one)."""
    events: list[TelemetryEventCreate] = Field(..., max_length=500)

class TelemetryEventResponse(BaseModel):
    id: int
    attempt_id: int
    event_type: str
    timestamp: datetime
    time_since_start_ms: Optional[int] = None
    data: Optional[dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)
    
class TelemetrySummary(BaseModel):
    """Aggregated telemetry stats for an attempt."""
    attempt_id: int
    total_keystrokes: int
    total_pastes: int
    total_undos: int
    total_redos: int
    total_runs: int
    idle_time_ms: int
    active_time_ms: int
    undo_rate: float  # undos / keystrokes
    events_count: int