"""Database engine and session configuration for SQLAlchemy."""

from __future__ import annotations

import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..db.models import Base

# Load environment variables from backend/.env
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent  # config/ -> app/ -> backend/
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(f"DATABASE_URL environment variable is not set. Checked: {env_path}")

# URL-encode special characters in password if present
from urllib.parse import quote

# Find and encode the password portion of the URL
if '://' in DATABASE_URL:
    scheme_split = DATABASE_URL.split('://', 1)
    if len(scheme_split) == 2:
        scheme = scheme_split[0]
        rest = scheme_split[1]

        # Find the last @ which separates credentials from host
        if '@' in rest:
            credentials_part, host_part = rest.rsplit('@', 1)

            # Find the password (after the last : in credentials)
            if ':' in credentials_part:
                username, password = credentials_part.rsplit(':', 1)

                # Only encode if password contains special characters
                if '@' in password or '#' in password or '/' in password:
                    encoded_password = quote(password, safe='')
                    DATABASE_URL = f"{scheme}://{username}:{encoded_password}@{host_part}"

# Convert postgres:// to postgresql+asyncpg:// if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries in logs
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Maximum number of connections to create beyond pool_size
    connect_args={
        "server_settings": {"jit": "off"},
        "statement_cache_size": 0,  # Disable prepared statements for pgbouncer compatibility
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create sync engine for blocking operations (like Selenium)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Convert async URL to sync URL
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "options": "-c jit=off"
    }
)

# Create sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields database sessions.

    Usage in FastAPI:
        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database (create all tables).

    Note: Only use this for development. In production, use migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database engine and connections."""
    await engine.dispose()
