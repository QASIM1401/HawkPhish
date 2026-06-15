"""HawkPhish - Database Setup (SQLite / PostgreSQL / MySQL)"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# Load from environment variable, fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./hawkphish.db")

# Create engine based on URL scheme
if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(DATABASE_URL, echo=False)
elif DATABASE_URL.startswith("postgresql"):
    engine = create_async_engine(DATABASE_URL, echo=False)
elif DATABASE_URL.startswith("mysql"):
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
else:
    raise ValueError(f"Unsupported database URL: {DATABASE_URL}")

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        yield session


def get_db_url():
    return DATABASE_URL
