"""Workspace repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.repositories.base import GenericRepo


class WorkspaceRepo(GenericRepo[Workspace]):
    model = Workspace

    async def list_by_owner(
        self, db: AsyncSession, owner_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[Workspace]:
        """List workspaces owned by a specific user."""
        result = await db.execute(
            select(Workspace)
            .where(Workspace.owner_id == owner_id)
            .order_by(Workspace.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
