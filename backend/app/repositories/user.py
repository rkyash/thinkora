"""User repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import GenericRepo


class UserRepo(GenericRepo[User]):
    model = User

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Find user by email address."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        """Find user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username(self, db: AsyncSession, email: str) -> User | None:
        """Find user by email or username."""
        result = await db.execute(select(User).where((User.email == email) | (User.username == email)))
        return result.scalar_one_or_none()
