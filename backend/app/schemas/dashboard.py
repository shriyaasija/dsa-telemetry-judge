from pydantic import BaseModel
from typing import Optional


class UserStats(BaseModel):
    """Aggregated stats for a user's dashboard."""
    user_id: int
    total_attempts: int
    total_solved: int
    total_failed: int
    total_abandoned: int
    solve_rate: float                  # solved / total_attempts
    avg_solve_time_seconds: float      # average duration for solved problems
    fastest_solve_seconds: Optional[int]
    current_streak: int                # consecutive days with at least 1 solve
    problems_by_difficulty: dict       # {"easy": 5, "medium": 3, "hard": 1}
    recent_activity: list[dict]        # last 10 attempts (summary)


class ProblemStats(BaseModel):
    """Stats for a specific problem."""
    problem_id: int
    total_attempts: int
    total_solves: int
    solve_rate: float
    avg_solve_time_seconds: float
    avg_undo_rate: float
