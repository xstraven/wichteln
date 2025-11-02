from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from wichteln.models import Base
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use POSTGRES_CONNECT_STRING from .env, fallback to default if not set
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "POSTGRES_CONNECT_STRING",
        "postgresql+psycopg://localhost/wichteln"
    )
)

# Update DATABASE_URL to use async driver if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database - creates tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency injection for FastAPI routes - provides AsyncSession."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
