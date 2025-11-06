"""
Generic seeder using Supabase Python SDK.

Syncs any table between environments with automatic column validation.
"""
import logging
import os
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from supabase import create_client, Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class GenericSupabaseSeeder:
    """
    Generic seeder for any table using Supabase SDK.

    Automatically handles:
    - Column validation
    - Unique key detection
    - Create/update logic
    - Timestamp comparison
    """

    ENVIRONMENTS = {
        "staging": {
            "url": os.getenv("STAGING_SUPABASE_URL"),
            "key": os.getenv("STAGING_SUPABASE_SERVICE_KEY"),
        },
        "production": {
            "url": os.getenv("PROD_SUPABASE_URL"),
            "key": os.getenv("PROD_SUPABASE_SERVICE_KEY"),
        },
    }

    def __init__(
        self,
        table_name: str,
        unique_key: str,
        source_env: str,
        target_env: str,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize generic seeder.

        Args:
            table_name: Name of the table to sync
            unique_key: Column name to use as unique identifier (e.g., 'code')
            source_env: Source environment (staging, production)
            target_env: Target environment (staging, production)
            dry_run: If True, show what would be done without applying
            verbose: If True, show detailed output
        """
        self.table_name = table_name
        self.unique_key = unique_key
        self.source_env = source_env
        self.target_env = target_env
        self.dry_run = dry_run
        self.verbose = verbose

        # Validate environments
        if source_env not in self.ENVIRONMENTS:
            raise ValueError(f"Invalid source environment: {source_env}")
        if target_env not in self.ENVIRONMENTS:
            raise ValueError(f"Invalid target environment: {target_env}")
        if source_env == target_env:
            raise ValueError(f"Source and target cannot be the same: {source_env}")

        # Initialize Supabase clients
        source_config = self.ENVIRONMENTS[source_env]
        target_config = self.ENVIRONMENTS[target_env]

        if not source_config["url"] or not source_config["key"]:
            raise ValueError(
                f"Missing Supabase config for {source_env}. "
                f"Set {source_env.upper()}_SUPABASE_URL and "
                f"{source_env.upper()}_SUPABASE_SERVICE_KEY"
            )

        if not target_config["url"] or not target_config["key"]:
            raise ValueError(
                f"Missing Supabase config for {target_env}. "
                f"Set {target_env.upper()}_SUPABASE_URL and "
                f"{target_env.upper()}_SUPABASE_SERVICE_KEY"
            )

        self.source_client: Client = create_client(
            source_config["url"], source_config["key"]
        )
        self.target_client: Client = create_client(
            target_config["url"], target_config["key"]
        )

        # Stats
        self.stats = {
            "fetched_source": 0,
            "fetched_target": 0,
            "to_create": 0,
            "to_update": 0,
            "to_skip": 0,
            "created": 0,
            "updated": 0,
            "errors": 0,
        }

    def _get_table_columns(self, client: Client) -> Set[str]:
        """
        Get column names for a table.

        Uses Supabase introspection to get schema info.
        """
        # Query information_schema to get columns
        try:
            result = (
                client.table("information_schema.columns")
                .select("column_name")
                .eq("table_name", self.table_name)
                .execute()
            )

            if result.data:
                return {row["column_name"] for row in result.data}

            # Fallback: Get columns from first record
            sample = client.table(self.table_name).select("*").limit(1).execute()
            if sample.data:
                return set(sample.data[0].keys())

            raise ValueError(f"Table {self.table_name} appears to be empty")

        except Exception as e:
            logger.error(f"Failed to get columns for {self.table_name}: {e}")
            raise

    def _validate_columns(self) -> Set[str]:
        """
        Validate that source and target have compatible columns.

        Returns:
            Set of common columns (excluding auto-generated ones)
        """
        logger.info(f"🔍 Validating columns for {self.table_name}...")

        source_cols = self._get_table_columns(self.source_client)
        target_cols = self._get_table_columns(self.target_client)

        if self.verbose:
            logger.info(f"   Source columns ({len(source_cols)}): {sorted(source_cols)}")
            logger.info(f"   Target columns ({len(target_cols)}): {sorted(target_cols)}")

        # Find common columns
        common_cols = source_cols & target_cols

        # Columns to exclude from sync (auto-generated)
        exclude_cols = {"id", "created_at"}

        # Ensure unique key exists
        if self.unique_key not in common_cols:
            raise ValueError(
                f"Unique key '{self.unique_key}' not found in both environments. "
                f"Common columns: {sorted(common_cols)}"
            )

        sync_cols = common_cols - exclude_cols

        logger.info(
            f"   ✅ Validated. Will sync {len(sync_cols)} columns: {sorted(sync_cols)}"
        )

        # Warn about missing columns
        source_only = source_cols - target_cols
        target_only = target_cols - source_cols

        if source_only:
            logger.warning(
                f"   ⚠️  Columns in source but not target: {sorted(source_only)}"
            )
        if target_only:
            logger.warning(
                f"   ⚠️  Columns in target but not source: {sorted(target_only)}"
            )

        return sync_cols

    def _fetch_records(self, client: Client, env_name: str) -> List[Dict[str, Any]]:
        """Fetch all records from a table."""
        logger.info(f"📥 Fetching records from {env_name}...")

        try:
            result = client.table(self.table_name).select("*").execute()
            records = result.data

            logger.info(f"   Found {len(records)} records")
            return records

        except Exception as e:
            logger.error(f"Failed to fetch from {env_name}: {e}")
            raise

    def _should_update(
        self, source_record: Dict[str, Any], target_record: Dict[str, Any]
    ) -> bool:
        """
        Determine if a record should be updated.

        Compares updated_at timestamps if available, otherwise always updates.
        """
        # Check timestamps
        source_updated = source_record.get("updated_at")
        target_updated = target_record.get("updated_at")

        if source_updated and target_updated:
            # Parse ISO strings to datetime for comparison
            if isinstance(source_updated, str):
                source_updated = datetime.fromisoformat(
                    source_updated.replace("Z", "+00:00")
                )
            if isinstance(target_updated, str):
                target_updated = datetime.fromisoformat(
                    target_updated.replace("Z", "+00:00")
                )

            if source_updated > target_updated:
                return True

            # If source is older, skip
            if source_updated < target_updated:
                return False

        # If timestamps equal or missing, compare content
        # (excluding id, created_at, updated_at)
        exclude_keys = {"id", "created_at", "updated_at"}

        for key in source_record.keys():
            if key in exclude_keys:
                continue

            if source_record.get(key) != target_record.get(key):
                if self.verbose:
                    logger.info(
                        f"      Field '{key}' differs for "
                        f"{source_record.get(self.unique_key)}"
                    )
                return True

        return False

    def sync(self, filter_codes: Optional[Set[str]] = None) -> Dict[str, int]:
        """
        Sync records from source to target.

        Args:
            filter_codes: Optional set of unique key values to sync

        Returns:
            Statistics dictionary
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Syncing {self.table_name}")
        logger.info(f"   Source: {self.source_env}")
        logger.info(f"   Target: {self.target_env}")
        logger.info(f"   Unique key: {self.unique_key}")
        logger.info(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        if filter_codes:
            logger.info(f"   Filter: {', '.join(sorted(filter_codes))}")
        logger.info(f"{'='*60}\n")

        # Validate columns
        sync_columns = self._validate_columns()

        # Fetch data
        source_records = self._fetch_records(self.source_client, self.source_env)
        target_records = self._fetch_records(self.target_client, self.target_env)

        self.stats["fetched_source"] = len(source_records)
        self.stats["fetched_target"] = len(target_records)

        # Apply filter
        if filter_codes:
            source_records = [
                r for r in source_records if r.get(self.unique_key) in filter_codes
            ]
            logger.info(
                f"   📌 Filtered to {len(source_records)} records matching filter"
            )

        # Build lookup map
        target_map = {r[self.unique_key]: r for r in target_records}

        # Determine actions
        to_create = []
        to_update = []
        to_skip = []

        for source_record in source_records:
            key = source_record[self.unique_key]
            target_record = target_map.get(key)

            if not target_record:
                to_create.append(source_record)
            elif self._should_update(source_record, target_record):
                to_update.append((target_record, source_record))
            else:
                to_skip.append(source_record)

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
                    logger.info(f"      - {record[self.unique_key]}")

            if to_update:
                logger.info(f"\n   Records to update:")
                for _, record in to_update:
                    logger.info(f"      - {record[self.unique_key]}")

        # Execute changes
        if not self.dry_run:
            logger.info(f"\n🚀 Applying changes...")

            # Create new records
            for record in to_create:
                try:
                    # Prepare data (exclude id, created_at)
                    data = {
                        k: v
                        for k, v in record.items()
                        if k in sync_columns and k != "id"
                    }

                    self.target_client.table(self.table_name).insert(data).execute()

                    self.stats["created"] += 1
                    logger.info(f"   ✅ Created: {record[self.unique_key]}")

                except Exception as e:
                    logger.error(
                        f"   ❌ Failed to create {record[self.unique_key]}: {e}"
                    )
                    self.stats["errors"] += 1

            # Update existing records
            for target_record, source_record in to_update:
                try:
                    # Prepare data (exclude id, created_at, unique_key)
                    data = {
                        k: v
                        for k, v in source_record.items()
                        if k in sync_columns
                        and k not in {"id", self.unique_key, "created_at"}
                    }

                    # Update updated_at timestamp
                    data["updated_at"] = datetime.utcnow().isoformat()

                    self.target_client.table(self.table_name).update(data).eq(
                        self.unique_key, source_record[self.unique_key]
                    ).execute()

                    self.stats["updated"] += 1
                    logger.info(f"   ✅ Updated: {source_record[self.unique_key]}")

                except Exception as e:
                    logger.error(
                        f"   ❌ Failed to update {source_record[self.unique_key]}: {e}"
                    )
                    self.stats["errors"] += 1

            logger.info(f"\n✅ Changes applied to {self.target_env}")
        else:
            logger.info(f"\n💡 DRY RUN - No changes applied")

        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"📈 Sync Summary for {self.table_name}")
        logger.info(f"{'='*60}")
        logger.info(f"   Created: {self.stats.get('created', self.stats['to_create'])}")
        logger.info(f"   Updated: {self.stats.get('updated', self.stats['to_update'])}")
        logger.info(f"   Skipped: {self.stats['to_skip']}")
        logger.info(f"   Errors: {self.stats['errors']}")
        logger.info(f"{'='*60}\n")

        return self.stats
