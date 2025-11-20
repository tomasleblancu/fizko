#!/usr/bin/env python3
"""
Test script to send a real SII sync task for October 2025.
"""
import os
from celery import Celery
from dotenv import load_dotenv

# Load environment
load_dotenv("backend-v2/.env")

# Use localhost for Redis (we're running outside Docker)
redis_url = "redis://localhost:6379/0"

# Create Celery app (connect to broker only)
celery_app = Celery(
    "fizko-celery-test",
    broker=redis_url,
    backend=redis_url,
)

def send_sync_task():
    """Send document sync task for October 2025."""

    # Real company ID from Supabase
    company_id = "eb5dc3a8-cfea-4e85-9424-e1c9e7dec097"  # APP PASTELERIA Y BANQUETERIA SPA

    print("=" * 60)
    print("🚀 Sending SII document sync task for OCTOBER 2025")
    print("=" * 60)
    print(f"Company ID: {company_id}")
    print(f"Months: 1")
    print(f"Offset: 1 (October 2025)")
    print()

    # Send task
    result = celery_app.send_task(
        "sii.sync_documents",
        args=[company_id],
        kwargs={"months": 1, "month_offset": 1},
        queue="default"
    )

    print(f"✅ Task sent successfully!")
    print(f"   Task ID: {result.id}")
    print(f"   Task State: {result.state}")
    print()
    print("⏳ Waiting for result (timeout: 20 seconds)...")
    print()

    try:
        # Wait for result
        task_result = result.get(timeout=20)
        print("✅ Task completed!")
        print()
        print("📊 Result:")
        for key, value in task_result.items():
            print(f"   {key}: {value}")

        if not task_result.get("success"):
            print()
            print("⚠️  Task returned error:")
            print(f"   Error: {task_result.get('error')}")

    except Exception as e:
        print(f"❌ Error getting task result: {e}")
        return False

    return True


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("🔬 SII Sync Test - October 2025")
    print("=" * 60)
    print()

    success = send_sync_task()

    if success:
        print()
        print("=" * 60)
        print("✅ Test completed!")
        print("=" * 60)
        print()
        print("💡 Check worker logs for details:")
        print("   cd backend-v2 && docker compose logs -f celery-worker")
        print()
    else:
        print()
        print("=" * 60)
        print("❌ Test failed!")
        print("=" * 60)
        print()
        exit(1)
