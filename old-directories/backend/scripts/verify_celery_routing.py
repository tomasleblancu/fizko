#!/usr/bin/env python3
"""
Celery Routing Verification Script

This script verifies that all registered Celery tasks have proper routing configured.
It helps detect:
- Tasks missing from routing configuration
- Routing rules pointing to non-existent tasks
- Queue distribution

Usage:
    python scripts/verify_celery_routing.py
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.celery import celery_app
from app.infrastructure.celery.config import task_routes


def main():
    print("=" * 80)
    print("Celery Task Routing Verification")
    print("=" * 80)
    print()

    # Get all registered tasks
    registered_tasks = set(celery_app.tasks.keys())

    # Filter out Celery internal tasks
    user_tasks = {
        task for task in registered_tasks
        if not task.startswith('celery.')
    }

    # Get configured routes
    routed_tasks = set(task_routes.keys())

    print(f"📊 Summary:")
    print(f"   Total registered tasks: {len(registered_tasks)}")
    print(f"   User tasks: {len(user_tasks)}")
    print(f"   Configured routes: {len(routed_tasks)}")
    print()

    # Check for tasks without routing
    unrouted_tasks = user_tasks - routed_tasks

    if unrouted_tasks:
        print("⚠️  Tasks WITHOUT routing configuration (will use default queue):")
        for task in sorted(unrouted_tasks):
            print(f"   - {task}")
        print()
    else:
        print("✅ All user tasks have routing configured")
        print()

    # Check for routes pointing to non-existent tasks
    missing_tasks = routed_tasks - user_tasks

    if missing_tasks:
        print("⚠️  Routing rules for NON-EXISTENT tasks:")
        for task in sorted(missing_tasks):
            queue = task_routes[task].get('queue', 'default')
            print(f"   - {task} → {queue}")
        print()
    else:
        print("✅ All routing rules point to existing tasks")
        print()

    # Show queue distribution
    print("📋 Queue Distribution:")
    queue_counts = {}
    for task in user_tasks:
        # Check if task has explicit routing
        if task in task_routes:
            queue = task_routes[task].get('queue', 'default')
        else:
            queue = 'default (fallback)'

        queue_counts[queue] = queue_counts.get(queue, 0) + 1

    for queue, count in sorted(queue_counts.items()):
        print(f"   {queue}: {count} tasks")
    print()

    # Show tasks by queue
    print("=" * 80)
    print("Tasks by Queue")
    print("=" * 80)
    print()

    for queue_name in ['high', 'default', 'low']:
        tasks_in_queue = [
            task for task in sorted(user_tasks)
            if task_routes.get(task, {}).get('queue', 'default') == queue_name
        ]

        if tasks_in_queue:
            print(f"🔹 Queue: {queue_name.upper()}")
            for task in tasks_in_queue:
                print(f"   ✓ {task}")
            print()

    # Tasks using fallback (not explicitly routed)
    fallback_tasks = [
        task for task in sorted(user_tasks)
        if task not in task_routes
    ]

    if fallback_tasks:
        print(f"🔹 Queue: DEFAULT (FALLBACK)")
        for task in fallback_tasks:
            print(f"   ⚠️  {task} (no explicit route)")
        print()

    print("=" * 80)

    # Exit code
    if unrouted_tasks or missing_tasks:
        print("⚠️  Warnings found - review configuration")
        return 1
    else:
        print("✅ Routing configuration is complete and valid")
        return 0


if __name__ == "__main__":
    sys.exit(main())
