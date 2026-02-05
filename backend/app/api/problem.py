from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.problem_service import ProblemService
from app.schemas.problem import (
    ProblemCreate,
    ProblemUpdate,
    ProblemResponse,
    ProblemListResponse
)
from typing import Optional

router = APIRouter(prefix="/problems", tags=["problems"])


@router.post("/", response_model=ProblemResponse, status_code=201)
async def create_problem(
    problem: ProblemCreate,
    db: AsyncSession = Depends(get_db)
):
    """create a new problem"""
    try:
        new_problem = await ProblemService.create_problem(db, problem)
        return new_problem
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ProblemListResponse)
async def list_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    difficulty: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """list all problems with pagination"""
    skip = (page - 1) * page_size
    problems, total = await ProblemService.list_problems(
        db, skip=skip, limit=page_size, difficulty=difficulty
    )
    
    return ProblemListResponse(
        problems=problems,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{problem_id}", response_model=ProblemResponse)
async def get_problem(
    problem_id: int,
    db: AsyncSession = Depends(get_db)
):
    """get a specific problem by ID"""
    problem = await ProblemService.get_problem(db, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.get("/slug/{slug}", response_model=ProblemResponse)
async def get_problem_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """get a problem by its slug"""
    problem = await ProblemService.get_problem_by_slug(db, slug)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.put("/{problem_id}", response_model=ProblemResponse)
async def update_problem(
    problem_id: int,
    problem: ProblemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """update a problem"""
    try:
        updated_problem = await ProblemService.update_problem(db, problem_id, problem)
        if not updated_problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        return updated_problem
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{problem_id}", status_code=204)
async def delete_problem(
    problem_id: int,
    db: AsyncSession = Depends(get_db)
):
    """delete a problem"""
    success = await ProblemService.delete_problem(db, problem_id)
    if not success:
        raise HTTPException(status_code=404, detail="Problem not found")
    return None