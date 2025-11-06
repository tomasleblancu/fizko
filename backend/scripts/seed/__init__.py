"""
Seed scripts for syncing data between environments.

Usage:
    python -m scripts.seed <command> [options]

Commands:
    notification-templates  Sync notification templates from staging to production
    event-templates        Sync event templates from staging to production
    all                    Sync all supported data types

Examples:
    # Sync notification templates from staging to production
    python -m scripts.seed notification-templates --from staging --to production

    # Dry run (show what would be synced without applying changes)
    python -m scripts.seed notification-templates --from staging --to production --dry-run

    # Sync specific templates by code
    python -m scripts.seed notification-templates --from staging --to production --codes f29_reminder,calendar_event_reminder
"""
