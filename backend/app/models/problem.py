from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class DifficultyLevel(str, enum.Enum):
    EASY="easy"
    MEDIUM="medium"
    HARD="hard"

class Problem(Base):
    __tablename__="problems"

    # primary key
    id = Column(Integer, primary_key=True, index=True)

    # core Fields
    title = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum(DifficultyLevel), nullable=False, index=True)
    
    # metadata
    tags = Column(String(500), nullable=True)  # Comma-separated for now
    time_limit_ms = Column(Integer, default=2000)  # 2 seconds default
    memory_limit_mb = Column(Integer, default=256)  # 256 MB default
    
    # test Cases 
    sample_input = Column(Text, nullable=True)
    sample_output = Column(Text, nullable=True)
    
    # timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # indexes for common queries
    __table_args__ = (
        Index('idx_difficulty_created', 'difficulty', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Problem(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')>"