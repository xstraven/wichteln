from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from wichteln.models import Base
import os
from sqlalchemy import inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./wichteln.db")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        def ensure_identifier_column(sync_conn):
            inspector = inspect(sync_conn)
            columns = {column["name"] for column in inspector.get_columns("exchanges")}
            if "identifier" not in columns:
                sync_conn.execute(text("ALTER TABLE exchanges ADD COLUMN identifier VARCHAR"))
        
        await conn.run_sync(ensure_identifier_column)
        await conn.execute(text("UPDATE exchanges SET identifier = name WHERE identifier IS NULL OR identifier = ''"))

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
