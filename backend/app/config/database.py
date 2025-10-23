"""Database engine and session configuration for SQLAlchemy."""

from __future__ import annotations

import logging
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..db.models import Base

# Set up logging for SQLAlchemy
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

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

# Validate that DATABASE_URL contains a database name
# Format should be: postgresql+asyncpg://user:pass@host:port/dbname?params
if DATABASE_URL.count('/') < 3:
    logger.error(f"DATABASE_URL appears to be missing database name. URL structure: {DATABASE_URL.split('@')[0]}@<host>")
    raise ValueError(
        "DATABASE_URL must include database name. "
        "Format: postgresql+asyncpg://user:pass@host:port/dbname?sslmode=require"
    )

# Extract and remove SSL parameters from URL (asyncpg doesn't accept them in URL)
# We'll pass SSL via connect_args instead
import re
ssl_mode = "prefer"  # Default SSL mode
if 'ssl=' in DATABASE_URL.lower() or 'sslmode=' in DATABASE_URL.lower():
    # Extract the ssl/sslmode value
    ssl_match = re.search(r'[?&](ssl|sslmode)=([^&]+)', DATABASE_URL, re.IGNORECASE)
    if ssl_match:
        ssl_value = ssl_match.group(2).lower()
        # Map ssl=true/require to sslmode values
        if ssl_value in ('true', 'require', 'on', '1'):
            ssl_mode = "require"
        elif ssl_value in ('disable', 'allow', 'prefer', 'verify-ca', 'verify-full'):
            ssl_mode = ssl_value
    # Remove SSL parameters from URL
    DATABASE_URL = re.sub(r'[?&](ssl|sslmode)=[^&]*&?', '', DATABASE_URL, flags=re.IGNORECASE)
    # Clean up trailing ? or &
    DATABASE_URL = re.sub(r'[?&]$', '', DATABASE_URL)
    logger.info(f"Extracted SSL mode: {ssl_mode}, removed from URL")

# Log the sanitized connection info (hide password)
safe_url = DATABASE_URL.split('@')[0].split(':')[0] + ':***@' + DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL
logger.info(f"Connecting to database: {safe_url}")

# Prepare connect_args with SSL
connect_args = {
    "server_settings": {"jit": "off"},
}

# Add SSL if needed (not for local connections)
if ssl_mode != "disable" and "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
    import ssl as ssl_module
    ssl_context = ssl_module.create_default_context()
    if ssl_mode == "require":
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl_module.CERT_NONE
    connect_args["ssl"] = ssl_context
    logger.info(f"SSL context configured with mode: {ssl_mode}")

# Create async engine with pgbouncer-compatible settings
# CRITICAL: prepared_statement_cache_size=0 MUST be at engine level for asyncpg
from sqlalchemy.pool import NullPool
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries in logs
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=1800,  # Recycle connections after 30 minutes to avoid stale connections
    poolclass=NullPool,  # Disable connection pooling (pgbouncer handles pooling)
    connect_args={
        **connect_args,
        "prepared_statement_cache_size": 0,  # Disable prepared statements for pgbouncer transaction mode
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


async def check_db_connection() -> None:
    """
    Sanity check database connection at startup.

    Raises an exception if the database is not accessible.
    """
    from sqlalchemy import text

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection check passed")
    except Exception as e:
        logger.error(f"Database connection check FAILED: {e}")
        raise
