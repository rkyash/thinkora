"""
Generic repository base class — all domain repos inherit from this.
Provides standard CRUD operations against SQLAlchemy async sessions.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class GenericRepo(Generic[ModelT]):
    """
    Generic async repository with standard CRUD operations.

    Usage:
        class UserRepo(GenericRepo[User]):
            model = User
    """

    model: type[ModelT]

    async def get(self, db: AsyncSession, id: str) -> ModelT | None:
        """Get a record by ID, or None if not found."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, id: str) -> ModelT:
        """Get a record by ID, or raise NotFoundError."""
        record = await self.get(db, id)
        if record is None:
            raise NotFoundError(
                resource=self.model.__tablename__.rstrip("s").capitalize(),
                resource_id=id,
            )
        return record

    async def exists(self, db: AsyncSession, id: str) -> bool:
        """Cheap EXISTS check."""
        result = await db.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0

    async def list_all(
        self,
        db: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 50,
        **filters: Any,
    ) -> list[ModelT]:
        """List records with pagination and optional filters."""
        query = select(self.model)

        # Apply simple equality filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)

        # Order by created_at if available, else by id
        if hasattr(self.model, "created_at"):
            query = query.order_by(self.model.created_at.desc())  # type: ignore[attr-defined]

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count(self, db: AsyncSession, **filters: Any) -> int:
        """Count records with optional filters."""
        query = select(func.count()).select_from(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)

        result = await db.execute(query)
        return result.scalar() or 0

    async def create(self, db: AsyncSession, data: dict[str, Any]) -> ModelT:
        """Create a single record."""
        record = self.model(**data)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def bulk_create(self, db: AsyncSession, rows: list[dict[str, Any]]) -> list[ModelT]:
        """Batch insert multiple records."""
        records = [self.model(**row) for row in rows]
        db.add_all(records)
        await db.flush()
        for record in records:
            await db.refresh(record)
        return records

    async def update(self, db: AsyncSession, id: str, data: dict[str, Any]) -> ModelT:
        """Update a record by ID."""
        record = await self.get_or_404(db, id)
        for field, value in data.items():
            if hasattr(record, field):
                setattr(record, field, value)
        await db.flush()
        await db.refresh(record)
        return record

    async def delete(self, db: AsyncSession, id: str) -> bool:
        """Delete a record by ID. Returns True if deleted."""
        record = await self.get(db, id)
        if record is None:
            return False
        await db.delete(record)
        await db.flush()
        return True
