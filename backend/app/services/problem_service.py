from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.models.problem import Problem
from app.schemas.problem import ProblemCreate, ProblemUpdate
from slugify import slugify
from typing import Optional


class ProblemService:
    @staticmethod
    async def create_problem(db: AsyncSession, problem_data: ProblemCreate) -> Problem:
        """create a new problem"""
        # Generate slug from title
        slug = slugify(problem_data.title)
        
        # check if slug already exists
        stmt = select(Problem).where(Problem.slug == slug)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            # append a number if slug exists
            count_stmt = select(func.count()).select_from(Problem).where(
                Problem.slug.like(f"{slug}%")
            )
            count_result = await db.execute(count_stmt)
            count = count_result.scalar()
            slug = f"{slug}-{count + 1}"
        
        problem = Problem(
            **problem_data.model_dump(),
            slug=slug
        )
        
        db.add(problem)
        try:
            await db.commit()
            await db.refresh(problem)
            return problem
        except IntegrityError:
            await db.rollback()
            raise ValueError("Problem with this title already exists")
    
    @staticmethod
    async def get_problem(db: AsyncSession, problem_id: int) -> Optional[Problem]:
        """get a problem by ID"""
        stmt = select(Problem).where(Problem.id == problem_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_problem_by_slug(db: AsyncSession, slug: str) -> Optional[Problem]:
        """get a problem by slug"""
        stmt = select(Problem).where(Problem.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_problems(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        difficulty: Optional[str] = None
    ) -> tuple[list[Problem], int]:
        """list problems with pagination and filtering"""
        # build query
        stmt = select(Problem)
        
        if difficulty:
            stmt = stmt.where(Problem.difficulty == difficulty)
        
        # get total count
        count_stmt = select(func.count()).select_from(Problem)
        if difficulty:
            count_stmt = count_stmt.where(Problem.difficulty == difficulty)
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # apply pagination and ordering
        stmt = stmt.order_by(Problem.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        problems = result.scalars().all()
        
        return problems, total
    
    @staticmethod
    async def update_problem(
        db: AsyncSession,
        problem_id: int,
        problem_data: ProblemUpdate
    ) -> Optional[Problem]:
        """update a problem"""
        problem = await ProblemService.get_problem(db, problem_id)
        if not problem:
            return None
        
        update_data = problem_data.model_dump(exclude_unset=True)
        
        # update slug if title changed
        if "title" in update_data:
            update_data["slug"] = slugify(update_data["title"])
        
        for field, value in update_data.items():
            setattr(problem, field, value)
        
        try:
            await db.commit()
            await db.refresh(problem)
            return problem
        except IntegrityError:
            await db.rollback()
            raise ValueError("Problem with this title already exists")
    
    @staticmethod
    async def delete_problem(db: AsyncSession, problem_id: int) -> bool:
        """delete a problem"""
        problem = await ProblemService.get_problem(db, problem_id)
        if not problem:
            return False
        
        await db.delete(problem)
        await db.commit()
        return True
