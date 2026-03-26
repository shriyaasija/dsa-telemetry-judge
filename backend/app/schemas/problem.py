from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.problem import DifficultyLevel


class ProblemBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    difficulty: DifficultyLevel
    tags: Optional[str] = None
    time_limit_ms: int = Field(default=2000, ge=100, le=10000)
    memory_limit_mb: int = Field(default=256, ge=32, le=1024)
    sample_input: Optional[str] = None
    sample_output: Optional[str] = None


class ProblemCreate(ProblemBase):
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class ProblemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    difficulty: Optional[DifficultyLevel] = None
    tags: Optional[str] = None
    time_limit_ms: Optional[int] = Field(None, ge=100, le=10000)
    memory_limit_mb: Optional[int] = Field(None, ge=32, le=1024)
    sample_input: Optional[str] = None
    sample_output: Optional[str] = None


class ProblemResponse(ProblemBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProblemListResponse(BaseModel):
    problems: list[ProblemResponse]
    total: int
    page: int
    page_size: int