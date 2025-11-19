"""Database engine and session configuration for SQLAlchemy."""

from __future__ import annotations

import logging
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..db.models import Base

# Set up logging for SQLAlchemy
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

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

# Detect if using pgbouncer EARLY (before modifications)
is_using_pooler_early = ":6543" in DATABASE_URL or "pooler.supabase.com" in DATABASE_URL

# For pgbouncer transaction mode, pgbouncer MUST be disabled via connect params
# According to asyncpg docs, this is done via prepared_statement_cache_size
# We'll set it in connect_args below
if is_using_pooler_early:
    logger.info("pgbouncer detected - will disable prepared statements via connect_args")

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

# Determine if this is a localhost connection OR local development environment
is_local = "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL
is_dev_environment = os.getenv("ENVIRONMENT", "production") == "development"

# Detect if using pgbouncer connection pooler (port 6543) or direct connection (port 5432)
# Port 6543 = transaction mode (incompatible with prepared statements)
# Port 5432 = session mode (compatible with prepared statements)
is_using_pooler = ":6543" in DATABASE_URL or ("pooler.supabase.com" in DATABASE_URL and ":5432" not in DATABASE_URL)
is_transaction_mode = ":6543" in DATABASE_URL
logger.info(f"Connection type: {'pgbouncer transaction mode' if is_transaction_mode else ('pgbouncer session mode' if 'pooler.supabase.com' in DATABASE_URL else 'direct connection')}")

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
    # Remove SSL parameters from URL (we'll pass via connect_args)
    DATABASE_URL = re.sub(r'[?&](ssl|sslmode)=[^&]*&?', '', DATABASE_URL, flags=re.IGNORECASE)
    # Clean up trailing ? or &
    DATABASE_URL = re.sub(r'[?&]$', '', DATABASE_URL)
    logger.info(f"Extracted SSL mode: {ssl_mode}, removed from URL")

# Override SSL mode for localhost connections (disable SSL for local dev)
if is_local:
    ssl_mode = "disable"
    logger.info("Localhost detected - SSL disabled for local development")
else:
    # For remote connections (like Supabase), default to require mode
    # This allows self-signed certificates (needed for pgbouncer)
    if ssl_mode == "prefer":
        ssl_mode = "require"
        logger.info("Remote connection detected - SSL mode set to 'require' (no cert verification)")

# For pgbouncer transaction mode, we will disable prepared statements via connect_args
# NOTE: URL parameters don't work reliably with asyncpg for this purpose
# We'll use server_settings in connect_args instead

# Log the sanitized connection info (hide password)
safe_url = DATABASE_URL.split('@')[0].split(':')[0] + ':***@' + DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL
logger.info(f"Connecting to database: {safe_url}")

# Prepare connect_args based on connection type
connect_args = {}

# Add SSL if needed (not for local connections)
if ssl_mode != "disable" and "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
    import ssl as ssl_module
    ssl_context = ssl_module.create_default_context()
    if ssl_mode == "require":
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl_module.CERT_NONE
    connect_args["ssl"] = ssl_context
    logger.info(f"SSL context configured with mode: {ssl_mode}")

# DON'T try to disable prepared statements via connect_args - it doesn't work with asyncpg
# If using pgbouncer transaction mode, you MUST use direct connection instead

# Detect service type to prioritize FastAPI over Celery
service_type = os.getenv("SERVICE_TYPE", "fastapi")  # fastapi, celery-worker, celery-beat
is_celery = service_type.startswith("celery")

# Create async engine with appropriate settings based on connection type
if "pooler.supabase.com" in DATABASE_URL:
    # pgbouncer pooler (session or transaction mode): Use SMALL pool
    # CRITICAL: Even with pgbouncer, we MUST limit connections per process
    # to prevent "max clients reached" errors in pgbouncer session mode.
    # With multiple workers (Gunicorn/Celery), each worker gets its own pool.

    # Prioritize FastAPI: Give it more connections than Celery
    if is_celery:
        async_pool_size = 1  # Celery: minimal pool
        async_max_overflow = 1  # Max 2 connections per Celery worker
        logger.warning("⚠️  Celery worker: Using minimal pool (1+1) to prioritize FastAPI")
    else:
        async_pool_size = 2  # FastAPI: small pool for concurrent requests
        async_max_overflow = 3  # Allow up to 5 connections per worker under load
        logger.warning("⚠️  FastAPI: Using small pool (2+3) per worker")

    logger.warning("⚠️  Session mode (port 5432) recommended over transaction mode (port 6543)")

    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=async_pool_size,  # Varies by service
        max_overflow=async_max_overflow,  # Varies by service
        pool_pre_ping=True,  # Check connection health before use
        pool_recycle=300,  # Recycle connections after 5 minutes
        pool_timeout=30,  # Wait up to 30s for a connection from pool
        connect_args=connect_args,
        execution_options={
            "compiled_cache": None,  # Disable query cache
        }
    )

    logger.info("✅ pgbouncer pooler configured")
else:
    # Direct connection: use normal pooling with prepared statements
    # For direct connections, we can disable JIT to improve query planning performance
    logger.info("Using standard pool with prepared statements for direct connection")
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=10,
        connect_args={
            **connect_args,
            "server_settings": {"jit": "off"},  # Only for direct connections
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

# Sync engine connect_args (psycopg2 also doesn't work with jit via pgbouncer)
sync_connect_args = {}
if not is_using_pooler:
    # Only set jit=off for direct connections
    sync_connect_args["options"] = "-c jit=off"

# Sync engine: Prioritize FastAPI over Celery (sync is used for Selenium)
if is_using_pooler:
    # FastAPI uses sync engine for SII service calls (document extraction, etc.)
    # These run Selenium inside async endpoints using sync sessions
    if is_celery:
        sync_pool_size = 0  # Celery: NullPool - creates connections on demand
        sync_max_overflow = 0  # No pool at all
        logger.info("Sync engine (Celery): NullPool (0+0) - creates connections on demand")
    else:
        # FastAPI needs more sync connections because SII services use SyncSessionLocal()
        # With 2 Gunicorn workers and concurrent requests, need bigger pool
        sync_pool_size = 2  # FastAPI: small pool for SII services
        sync_max_overflow = 3  # Allow up to 5 connections per worker under load
        logger.info("Sync engine (FastAPI): Small pool (2+3) for SII services")
    sync_pool_recycle = 300
else:
    logger.info("Sync engine: Using standard pool (5+10) for direct connection")
    sync_pool_size = 5
    sync_max_overflow = 10
    sync_pool_recycle = 1800

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=sync_pool_size,
    max_overflow=sync_max_overflow,
    pool_recycle=sync_pool_recycle,
    pool_timeout=30,
    connect_args=sync_connect_args
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
