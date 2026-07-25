import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.notebook import Notebook
from app.repositories.chat_session import ChatSessionRepo

async def main():
    engine = create_async_engine("postgresql+asyncpg://thinkora:thinkora@localhost:5434/thinkora")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create a notebook
        nb = Notebook(name="Test Notebook")
        session.add(nb)
        await session.commit()
        await session.refresh(nb)
        
        print(f"Created notebook: {nb.id}")
        
        # Create a chat session
        repo = ChatSessionRepo()
        try:
            chat_session = await repo.create(session, notebook_id=str(nb.id), title="Test Chat")
            print(f"Created chat session: {chat_session.id}")
        except Exception as e:
            print(f"Error creating chat session: {e}")
            
if __name__ == "__main__":
    asyncio.run(main())
