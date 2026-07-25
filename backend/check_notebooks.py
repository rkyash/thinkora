import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, name FROM notebooks"))
        rows = result.fetchall()
        print(f"Notebooks: {rows}")

if __name__ == "__main__":
    asyncio.run(main())
