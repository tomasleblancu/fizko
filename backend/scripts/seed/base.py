"""
Base classes and utilities for seed scripts.
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections for different environments."""

    ENVIRONMENTS = {
        "local": "DATABASE_URL",
        "staging": "STAGING_DATABASE_URL",
        "production": "DATABASE_URL_PRODUCTION",
    }

    @classmethod
    def get_connection_string(cls, env: str) -> str:
        """
        Get database connection string for an environment.

        Args:
            env: Environment name (local, staging, production)

        Returns:
            Database connection string

        Raises:
            ValueError: If environment is invalid or env var not set
        """
        if env not in cls.ENVIRONMENTS:
            raise ValueError(
                f"Invalid environment: {env}. "
                f"Valid options: {', '.join(cls.ENVIRONMENTS.keys())}"
            )

        env_var = cls.ENVIRONMENTS[env]
        connection_string = os.getenv(env_var)

        if not connection_string:
            raise ValueError(
                f"Environment variable {env_var} not set for environment '{env}'"
            )

        # Convert postgres:// to postgresql+asyncpg:// if needed
        if connection_string.startswith("postgres://"):
            connection_string = connection_string.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        return connection_string

    @classmethod
    async def create_session(cls, env: str) -> AsyncSession:
        """
        Create an async database session for an environment.

        Args:
            env: Environment name

        Returns:
            AsyncSession instance
        """
        connection_string = cls.get_connection_string(env)
        engine = create_async_engine(connection_string, echo=False, pool_pre_ping=True)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        return async_session()


class BaseSeeder(ABC):
    """
    Base class for all seeders.

    Provides common functionality for syncing data between environments.
    """

    def __init__(
        self,
        source_env: str,
        target_env: str,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize seeder.

        Args:
            source_env: Source environment (local, staging, production)
            target_env: Target environment (local, staging, production)
            dry_run: If True, show what would be done without applying changes
            verbose: If True, show detailed output
        """
        self.source_env = source_env
        self.target_env = target_env
        self.dry_run = dry_run
        self.verbose = verbose

        # Stats
        self.stats = {
            "to_create": 0,
            "to_update": 0,
            "to_skip": 0,
            "errors": 0,
        }

    @abstractmethod
    def get_entity_name(self) -> str:
        """Return the name of the entity being synced (for logging)."""
        pass

    @abstractmethod
    async def fetch_source_data(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """
        Fetch data from source environment.

        Args:
            session: Database session

        Returns:
            List of records as dictionaries
        """
        pass

    @abstractmethod
    async def fetch_target_data(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """
        Fetch data from target environment.

        Args:
            session: Database session

        Returns:
            List of records as dictionaries
        """
        pass

    @abstractmethod
    def get_unique_key(self, record: Dict[str, Any]) -> str:
        """
        Get unique identifier for a record (e.g., 'code' field).

        Args:
            record: Record dictionary

        Returns:
            Unique key as string
        """
        pass

    @abstractmethod
    async def create_record(
        self, session: AsyncSession, record: Dict[str, Any]
    ) -> None:
        """
        Create a new record in target environment.

        Args:
            session: Database session
            record: Record data
        """
        pass

    @abstractmethod
    async def update_record(
        self,
        session: AsyncSession,
        existing_id: UUID,
        source_record: Dict[str, Any],
    ) -> None:
        """
        Update an existing record in target environment.

        Args:
            session: Database session
            existing_id: ID of existing record
            source_record: Source record data
        """
        pass

    def should_update(
        self, source_record: Dict[str, Any], target_record: Dict[str, Any]
    ) -> bool:
        """
        Determine if a record should be updated.

        Default implementation compares updated_at timestamps.
        Override for custom logic.

        Args:
            source_record: Source record
            target_record: Target record

        Returns:
            True if record should be updated
        """
        source_updated = source_record.get("updated_at")
        target_updated = target_record.get("updated_at")

        if source_updated and target_updated:
            return source_updated > target_updated

        # If no timestamps, always update
        return True

    def filter_records(
        self, records: List[Dict[str, Any]], filter_keys: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter records by unique keys.

        Args:
            records: List of records
            filter_keys: Set of unique keys to include (None = include all)

        Returns:
            Filtered list of records
        """
        if not filter_keys:
            return records

        return [r for r in records if self.get_unique_key(r) in filter_keys]

    async def sync(self, filter_keys: Optional[Set[str]] = None) -> Dict[str, int]:
        """
        Sync data from source to target environment.

        Args:
            filter_keys: Optional set of unique keys to sync (None = sync all)

        Returns:
            Statistics dictionary
        """
        entity_name = self.get_entity_name()

        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Syncing {entity_name}")
        logger.info(f"   Source: {self.source_env}")
        logger.info(f"   Target: {self.target_env}")
        logger.info(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        if filter_keys:
            logger.info(f"   Filter: {', '.join(sorted(filter_keys))}")
        logger.info(f"{'='*60}\n")

        # Fetch data from both environments
        logger.info(f"📥 Fetching data from {self.source_env}...")
        source_session = await DatabaseConnection.create_session(self.source_env)
        try:
            source_records = await self.fetch_source_data(source_session)
            source_records = self.filter_records(source_records, filter_keys)
            logger.info(f"   Found {len(source_records)} records in source")
        finally:
            await source_session.close()

        logger.info(f"📥 Fetching data from {self.target_env}...")
        target_session = await DatabaseConnection.create_session(self.target_env)
        try:
            target_records = await self.fetch_target_data(target_session)
            logger.info(f"   Found {len(target_records)} records in target")

            # Build lookup map by unique key
            target_map = {self.get_unique_key(r): r for r in target_records}

            # Determine what to create/update/skip
            to_create = []
            to_update = []
            to_skip = []

            for source_record in source_records:
                key = self.get_unique_key(source_record)
                target_record = target_map.get(key)

                if not target_record:
                    to_create.append(source_record)
                elif self.should_update(source_record, target_record):
                    to_update.append((target_record["id"], source_record))
                else:
                    to_skip.append(source_record)

            # Update stats
            self.stats["to_create"] = len(to_create)
            self.stats["to_update"] = len(to_update)
            self.stats["to_skip"] = len(to_skip)

            # Display plan
            logger.info(f"\n📊 Sync Plan:")
            logger.info(f"   ✨ Create: {len(to_create)} records")
            logger.info(f"   🔄 Update: {len(to_update)} records")
            logger.info(f"   ⏭️  Skip: {len(to_skip)} records")

            if self.verbose:
                if to_create:
                    logger.info(f"\n   Records to create:")
                    for record in to_create:
                        logger.info(f"      - {self.get_unique_key(record)}")

                if to_update:
                    logger.info(f"\n   Records to update:")
                    for _, record in to_update:
                        logger.info(f"      - {self.get_unique_key(record)}")

            # Execute changes
            if not self.dry_run:
                logger.info(f"\n🚀 Applying changes...")

                # Create new records
                for record in to_create:
                    try:
                        await self.create_record(target_session, record)
                        logger.info(f"   ✅ Created: {self.get_unique_key(record)}")
                    except Exception as e:
                        logger.error(
                            f"   ❌ Failed to create {self.get_unique_key(record)}: {e}"
                        )
                        self.stats["errors"] += 1

                # Update existing records
                for existing_id, record in to_update:
                    try:
                        await self.update_record(target_session, existing_id, record)
                        logger.info(f"   ✅ Updated: {self.get_unique_key(record)}")
                    except Exception as e:
                        logger.error(
                            f"   ❌ Failed to update {self.get_unique_key(record)}: {e}"
                        )
                        self.stats["errors"] += 1

                # Commit changes
                await target_session.commit()
                logger.info(f"\n✅ Changes committed to {self.target_env}")
            else:
                logger.info(f"\n💡 DRY RUN - No changes applied")

        finally:
            await target_session.close()

        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"📈 Sync Summary for {entity_name}")
        logger.info(f"{'='*60}")
        logger.info(f"   Created: {self.stats['to_create']}")
        logger.info(f"   Updated: {self.stats['to_update']}")
        logger.info(f"   Skipped: {self.stats['to_skip']}")
        logger.info(f"   Errors: {self.stats['errors']}")
        logger.info(f"{'='*60}\n")

        return self.stats
