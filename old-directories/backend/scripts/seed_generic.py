#!/usr/bin/env python3
"""
Generic seed script using Supabase SDK.

Usage:
    python scripts/seed_generic.py <table_name> <unique_key> --from <env> --to <env> [options]

Examples:
    # Sync notification templates
    python scripts/seed_generic.py notification_templates code --from staging --to production --dry-run

    # Sync event templates
    python scripts/seed_generic.py event_templates code --from staging --to production

    # Sync specific records
    python scripts/seed_generic.py notification_templates code \
        --from staging --to production \
        --codes f29_reminder,daily_summary

    # Reverse sync (production to staging)
    python scripts/seed_generic.py notification_templates code --from production --to staging
"""
import sys
import logging
import click
from typing import Optional, Set

# Add parent directory to path for imports
sys.path.insert(0, "/Users/tomasleblanc/Dev/akashi-labs/fizko-v2/backend")

from scripts.seed.generic import GenericSupabaseSeeder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@click.command()
@click.argument("table_name")
@click.argument("unique_key")
@click.option(
    "--from",
    "source_env",
    type=click.Choice(["staging", "production"], case_sensitive=False),
    default="staging",
    help="Source environment",
)
@click.option(
    "--to",
    "target_env",
    type=click.Choice(["staging", "production"], case_sensitive=False),
    required=True,
    help="Target environment",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be synced without applying changes",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Show detailed output",
)
@click.option(
    "--codes",
    type=str,
    help="Comma-separated list of unique key values to sync (default: all)",
)
def main(
    table_name: str,
    unique_key: str,
    source_env: str,
    target_env: str,
    dry_run: bool,
    verbose: bool,
    codes: Optional[str],
):
    """
    Generic seed script for any table using Supabase SDK.

    TABLE_NAME: Name of the table to sync (e.g., notification_templates)

    UNIQUE_KEY: Column to use as unique identifier (e.g., code)

    Examples:

        # Sync all notification templates (dry run)
        python scripts/seed_generic.py notification_templates code --to production --dry-run

        # Sync specific templates
        python scripts/seed_generic.py notification_templates code \\
            --to production \\
            --codes f29_reminder,daily_summary

        # Reverse sync from production to staging
        python scripts/seed_generic.py notification_templates code \\
            --from production --to staging

    Common Tables:
        - notification_templates (unique_key: code)
        - event_templates (unique_key: code)
        - notification_event_triggers (unique_key: name or id)
    """
    # Prevent syncing to same environment
    if source_env == target_env:
        click.echo(
            click.style(
                f"❌ Error: Source and target cannot be the same ({source_env})",
                fg="red",
            )
        )
        sys.exit(1)

    # Warn if syncing to production
    if target_env == "production" and not dry_run:
        click.confirm(
            click.style(
                f"⚠️  You are about to sync {table_name} to PRODUCTION. Continue?",
                fg="yellow",
                bold=True,
            ),
            abort=True,
        )

    # Parse codes filter
    filter_codes: Optional[Set[str]] = None
    if codes:
        filter_codes = set(c.strip() for c in codes.split(",") if c.strip())

    # Run seeder
    try:
        seeder = GenericSupabaseSeeder(
            table_name=table_name,
            unique_key=unique_key,
            source_env=source_env,
            target_env=target_env,
            dry_run=dry_run,
            verbose=verbose,
        )

        stats = seeder.sync(filter_codes=filter_codes)

        # Exit with error if there were failures
        if stats["errors"] > 0:
            sys.exit(1)

    except ValueError as e:
        click.echo(click.style(f"\n❌ Configuration error: {e}", fg="red", bold=True))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"\n❌ Sync failed: {e}", fg="red", bold=True))
        if verbose:
            import traceback

            click.echo(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
