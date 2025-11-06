"""
CLI entry point for seed commands.

Usage:
    python -m scripts.seed <command> [options]
"""
import logging
import sys
from typing import Optional, Set

import click

from .generic import GenericSupabaseSeeder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@click.group()
def cli():
    """
    Fizko Seed CLI - Sync data between environments.

    Use this tool to sync configuration data (templates, etc.) from staging
    to production or between any environments.

    Examples:

        # Sync notification templates from staging to production (dry run)
        python -m scripts.seed notification-templates --to production --dry-run

        # Sync event templates (live)
        python -m scripts.seed event-templates --to production

        # Sync specific templates only
        python -m scripts.seed notification-templates --to production --codes f29_reminder,calendar_event

        # Sync any table
        python -m scripts.seed sync --table brain_contexts --unique-key context_id --to production --dry-run
    """
    pass


@cli.command()
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
    help="Comma-separated list of template codes to sync (default: all)",
)
def notification_templates(
    source_env: str,
    target_env: str,
    dry_run: bool,
    verbose: bool,
    codes: Optional[str],
):
    """
    Sync notification templates between environments.

    Notification templates define automated notifications like:
    - F29 reminders
    - Calendar event notifications
    - Daily/weekly business summaries

    Examples:

        # Sync all templates (dry run)
        python -m scripts.seed notification-templates --to production --dry-run

        # Sync specific templates only
        python -m scripts.seed notification-templates --to production --codes f29_reminder,daily_summary
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
                "⚠️  You are about to sync to PRODUCTION. Continue?",
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
    seeder = GenericSupabaseSeeder(
        table_name="notification_templates",
        unique_key="code",
        source_env=source_env,
        target_env=target_env,
        dry_run=dry_run,
        verbose=verbose,
    )

    try:
        stats = seeder.sync(filter_codes=filter_codes)

        # Exit with error if there were failures
        if stats["errors"] > 0:
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"\n❌ Sync failed: {e}", fg="red", bold=True))
        if verbose:
            import traceback
            click.echo(traceback.format_exc())
        sys.exit(1)


@cli.command()
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
    help="Comma-separated list of event codes to sync (default: all)",
)
def event_templates(
    source_env: str,
    target_env: str,
    dry_run: bool,
    verbose: bool,
    codes: Optional[str],
):
    """
    Sync event templates between environments.

    Event templates define tax and calendar obligations like:
    - F29 (monthly VAT)
    - F22 (annual income tax)
    - Boletas de honorarios
    - Custom tax events

    Examples:

        # Sync all event templates (dry run)
        python -m scripts.seed event-templates --to production --dry-run

        # Sync specific events only
        python -m scripts.seed event-templates --to production --codes f29_monthly,f22_annual
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
                "⚠️  You are about to sync to PRODUCTION. Continue?",
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
    seeder = GenericSupabaseSeeder(
        table_name="event_templates",
        unique_key="code",
        source_env=source_env,
        target_env=target_env,
        dry_run=dry_run,
        verbose=verbose,
    )

    try:
        stats = seeder.sync(filter_codes=filter_codes)

        # Exit with error if there were failures
        if stats["errors"] > 0:
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"\n❌ Sync failed: {e}", fg="red", bold=True))
        if verbose:
            import traceback
            click.echo(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--table",
    type=str,
    required=True,
    help="Table name to sync",
)
@click.option(
    "--unique-key",
    type=str,
    required=True,
    help="Column name to use as unique identifier (e.g., 'code', 'id')",
)
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
    "--filter",
    type=str,
    help="Comma-separated list of unique key values to sync (default: all)",
)
def sync(
    table: str,
    unique_key: str,
    source_env: str,
    target_env: str,
    dry_run: bool,
    verbose: bool,
    filter: Optional[str],
):
    """
    Generic sync command for any table.

    Examples:

        # Sync brain_contexts table
        python -m scripts.seed sync --table brain_contexts --unique-key context_id --to production --dry-run

        # Sync specific records only
        python -m scripts.seed sync --table brain_contexts --unique-key context_id --to production --filter ctx_123,ctx_456
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
                f"⚠️  You are about to sync table '{table}' to PRODUCTION. Continue?",
                fg="yellow",
                bold=True,
            ),
            abort=True,
        )

    # Parse filter
    filter_codes: Optional[Set[str]] = None
    if filter:
        filter_codes = set(c.strip() for c in filter.split(",") if c.strip())

    # Run seeder
    seeder = GenericSupabaseSeeder(
        table_name=table,
        unique_key=unique_key,
        source_env=source_env,
        target_env=target_env,
        dry_run=dry_run,
        verbose=verbose,
    )

    try:
        stats = seeder.sync(filter_codes=filter_codes)

        # Exit with error if there were failures
        if stats["errors"] > 0:
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"\n❌ Sync failed: {e}", fg="red", bold=True))
        if verbose:
            import traceback
            click.echo(traceback.format_exc())
        sys.exit(1)


@cli.command()
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
def all(
    source_env: str,
    target_env: str,
    dry_run: bool,
    verbose: bool,
):
    """
    Sync all supported data types between environments.

    This will sync:
    - Notification templates
    - Event templates

    Example:

        # Sync everything from staging to production (dry run)
        python -m scripts.seed all --to production --dry-run
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
                "⚠️  You are about to sync ALL data to PRODUCTION. Continue?",
                fg="yellow",
                bold=True,
            ),
            abort=True,
        )

    click.echo(click.style("\n🚀 Syncing all data types...\n", fg="cyan", bold=True))

    all_success = True

    # Sync notification templates
    try:
        seeder = GenericSupabaseSeeder(
            table_name="notification_templates",
            unique_key="code",
            source_env=source_env,
            target_env=target_env,
            dry_run=dry_run,
            verbose=verbose,
        )
        stats = seeder.sync()
        if stats["errors"] > 0:
            all_success = False
    except Exception as e:
        click.echo(
            click.style(
                f"❌ Failed to sync notification templates: {e}",
                fg="red",
            )
        )
        all_success = False

    # Sync event templates
    try:
        seeder = GenericSupabaseSeeder(
            table_name="event_templates",
            unique_key="code",
            source_env=source_env,
            target_env=target_env,
            dry_run=dry_run,
            verbose=verbose,
        )
        stats = seeder.sync()
        if stats["errors"] > 0:
            all_success = False
    except Exception as e:
        click.echo(
            click.style(
                f"❌ Failed to sync event templates: {e}",
                fg="red",
            )
        )
        all_success = False

    # Final summary
    if all_success:
        click.echo(
            click.style(
                "\n✅ All data types synced successfully!",
                fg="green",
                bold=True,
            )
        )
    else:
        click.echo(
            click.style(
                "\n⚠️  Some data types failed to sync. Check logs above.",
                fg="yellow",
                bold=True,
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    cli()
