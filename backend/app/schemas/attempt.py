from email.policy import default
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.attempt import AttemptStatus


class AttemptCreate(BaseModel):
    problem_id: int
    language: str = Field(default="python", max_length=50)

class AttemptUpdate(BaseModel):
    code: Optional[str] = None
    status: Optional[AttemptStatus] = None

class AttemptSubmit(BaseModel):
    code: str
    language: str = Field(default="python", max_length=50)

class AttemptResponse(BaseModel):
    id: int
    user_id: int
    problem_id: int
    status: AttemptStatus
    code: Optional[str] = None
    language: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    is_correct: Optional[bool] = None
    test_cases_passed: int
    test_cases_total: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AttemptListResponse(BaseModel):
    attempts: list[AttemptResponse]
    total: int
    page: int
    page_size: int