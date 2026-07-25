"""Notebook repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notebook import Notebook
from app.repositories.base import GenericRepo


class NotebookRepo(GenericRepo[Notebook]):
    model = Notebook

    async def list_by_workspace(
        self, db: AsyncSession, workspace_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[Notebook]:
        """List notebooks in a workspace."""
        result = await db.execute(
            select(Notebook)
            .where(Notebook.workspace_id == workspace_id)
            .order_by(Notebook.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
