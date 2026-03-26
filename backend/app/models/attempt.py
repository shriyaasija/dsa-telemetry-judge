from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AttemptStatus(str, enum.Enum):
    STARTED = "started"
    SUBMITTED = "submitted"
    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    ABANDONED = "abandoned"


class Attempt(Base):
    __tablename__ = "attempts"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)

    # Attempt State
    status = Column(Enum(AttemptStatus), nullable=False, default=AttemptStatus.STARTED)
    
    # Code
    code = Column(Text, nullable=True)
    language = Column(String(50), nullable=False)

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Results 
    is_correct = Column(Boolean, nullable=True)
    test_cases_passed = Column(Integer, default=0)
    test_cases_total = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="attempts")
    problem = relationship("Problem", backref="attempts")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_problem', 'user_id', 'problem_id'),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_problem_status', 'problem_id', 'status'),
        Index('idx_started_at', 'started_at'),
    )

    def __repr__(self):
        return f"<Attempt(id={self.id}, user={self.user_id}, problem={self.problem_id}, status='{self.status}')>"