from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from typing import Optional
from datetime import datetime, timezone


class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """create a new user with hashed password"""
        # hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # create user
        user = User(
            email=user_data.email.lower(),
            username=user_data.username.lower(),
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False
        )
        
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            raise ValueError("User with this email or username already exists")
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """get user by ID"""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """get user by email"""
        stmt = select(User).where(User.email == email.lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """get user by username"""
        stmt = select(User).where(User.username == username.lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """authenticate a user by username and password"""
        user = await UserService.get_user_by_username(db, username)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # update last login
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        user_data: UserUpdate
    ) -> Optional[User]:
        """update user information"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        # hash password if it's being updated
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        try:
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            raise ValueError("Email already in use")