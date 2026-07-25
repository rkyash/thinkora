"""
AppSettings Repository — key-value settings storage.

The AppSetting model uses a string PK (the setting key) instead of a UUID,
so this repo does NOT inherit from GenericRepo (which assumes UUID PKs).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_settings import AppSetting


class AppSettingsRepo:
    """
    Simple key-value store built on the app_settings table.
    All methods are async-safe.
    """

    async def get(self, db: AsyncSession, key: str) -> AppSetting | None:
        """Fetch one setting by key."""
        result = await db.execute(
            select(AppSetting).where(AppSetting.id == key)
        )
        return result.scalar_one_or_none()

    async def get_value(self, db: AsyncSession, key: str) -> str | None:
        """Return the raw value string, or None if not set."""
        record = await self.get(db, key)
        return record.value if record else None

    async def get_all(self, db: AsyncSession) -> list[AppSetting]:
        """Return all settings rows."""
        result = await db.execute(select(AppSetting))
        return list(result.scalars().all())

    async def upsert(self, db: AsyncSession, key: str, value: str | None) -> AppSetting:
        """
        Insert or update a setting.
        If the row doesn't exist, create it.
        If value is an empty string, treat as clearing (store None).
        """
        stored_value = value if value else None
        record = await self.get(db, key)
        if record is None:
            record = AppSetting(id=key, value=stored_value)
            db.add(record)
        else:
            record.value = stored_value
        await db.flush()
        await db.refresh(record)
        return record

    async def delete(self, db: AsyncSession, key: str) -> bool:
        """Delete a setting. Returns True if it existed."""
        record = await self.get(db, key)
        if record is None:
            return False
        await db.delete(record)
        await db.flush()
        return True

    async def get_many(self, db: AsyncSession, keys: list[str]) -> dict[str, str | None]:
        """Batch-fetch multiple keys. Returns {key: value_or_None}."""
        result = await db.execute(
            select(AppSetting).where(AppSetting.id.in_(keys))
        )
        rows = {r.id: r.value for r in result.scalars().all()}
        # Fill missing keys with None
        return {k: rows.get(k) for k in keys}


# Singleton
app_settings_repo = AppSettingsRepo()
