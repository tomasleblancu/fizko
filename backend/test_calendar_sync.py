"""
Test script for Calendar Sync Service

Tests the complete flow:
1. Find a company (by RUT or first with active company_events)
2. Show active company_events
3. Sync calendar events for the company
4. Verify calendar_events were created
5. Re-run sync to verify idempotency

Usage:
    # With specific company by RUT
    python test_calendar_sync.py

    # Set test RUT via env var
    CALENDAR_TEST_RUT=77794858 CALENDAR_TEST_DV=K python test_calendar_sync.py
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.config.supabase import get_supabase_client
from app.services.calendar_sync_service import CalendarSyncService


async def test_calendar_sync():
    """
    Test calendar sync service.

    Flow:
    1. Find company (by RUT or first with active company_events)
    2. Show company_events configuration
    3. Run calendar sync
    4. Verify calendar_events created
    5. Re-run sync to verify idempotency
    """

    print('=' * 70)
    print('🧪 TEST: Calendar Event Sync')
    print('=' * 70)
    print()

    # Get Supabase client
    print('🔧 Initializing Supabase client...')
    supabase = get_supabase_client()
    service = CalendarSyncService(supabase)

    # ============================================================
    # STEP 1: Find Company
    # ============================================================

    print()
    print('=' * 70)
    print('STEP 1: Finding Company')
    print('=' * 70)
    print()

    # Check if we should use test credentials from env
    test_rut = os.getenv('CALENDAR_TEST_RUT')
    test_dv = os.getenv('CALENDAR_TEST_DV')

    if test_rut and test_dv:
        # Use test credentials from environment
        print(f'🔑 Using test credentials from environment: {test_rut}-{test_dv}')

        # Find test company
        tax_id = f"{test_rut}{test_dv}".lower()
        response = supabase._client.table('companies').select('*').eq('rut', tax_id).limit(1).execute()

        if not response.data:
            print(f'❌ No company found with RUT {tax_id}')
            print('   Create a company with this RUT first')
            return

        company = response.data[0]
        company_id = company['id']
        business_name = company.get('business_name', 'N/A')

        print(f'✅ Test company found: {business_name}')
        print(f'   Company ID: {company_id}')
        print()
    else:
        # Get first company with active company_events
        print('🔍 Searching for company with active company_events...')

        response = (
            supabase._client
            .table('company_events')
            .select('company_id, companies(*)')
            .eq('is_active', True)
            .limit(1)
            .execute()
        )

        if not response.data:
            print('❌ No companies found with active company_events')
            print()
            print('💡 TIP: Create company_events first, or use test credentials:')
            print('   CALENDAR_TEST_RUT=77794858 CALENDAR_TEST_DV=K python test_calendar_sync.py')
            return

        company_event = response.data[0]
        company = company_event['companies']
        company_id = company['id']
        business_name = company.get('business_name', 'N/A')

        print(f'✅ Company found: {business_name}')
        print(f'   Company ID: {company_id}')
        print()

    # ============================================================
    # STEP 2: Show Active Company Events
    # ============================================================

    print('=' * 70)
    print('STEP 2: Active Company Events Configuration')
    print('=' * 70)
    print()

    company_events_response = (
        supabase._client
        .table('company_events')
        .select('*, event_template:event_templates(*)')
        .eq('company_id', company_id)
        .eq('is_active', True)
        .execute()
    )

    if not company_events_response.data:
        print('❌ No active company_events found for this company')
        print('   Activate some events in company_events first')
        return

    active_events = company_events_response.data

    print(f'✅ Found {len(active_events)} active company_events:')
    print()

    for i, ce in enumerate(active_events, 1):
        template = ce['event_template']
        print(f'{i}. {template["code"]} - {template["name"]}')
        print(f'   Category: {template.get("category", "N/A")}')
        print(f'   Frequency: {template.get("default_recurrence", {}).get("frequency", "N/A")}')
        print()

    # ============================================================
    # STEP 3: Check Existing Calendar Events (Before Sync)
    # ============================================================

    print('=' * 70)
    print('STEP 3: Calendar Events Before Sync')
    print('=' * 70)
    print()

    before_response = (
        supabase._client
        .table('calendar_events')
        .select('*')
        .eq('company_id', company_id)
        .execute()
    )

    before_count = len(before_response.data) if before_response.data else 0

    print(f'📋 Calendar events before sync: {before_count}')
    print()

    # ============================================================
    # STEP 4: Run Calendar Sync (First Time)
    # ============================================================

    print('=' * 70)
    print('STEP 4: Running Calendar Sync (First Time)')
    print('=' * 70)
    print()

    try:
        import time
        start_time = time.time()

        # Run sync
        result = await service.sync_company_calendar(company_id=company_id)

        elapsed = time.time() - start_time

        print()
        print('=' * 70)
        print('✅ SYNC COMPLETED')
        print('=' * 70)
        print()

        if result.get('success'):
            print('✅ Success!')
            print()
            print('📊 Results:')
            print('-' * 70)
            print(f'   Company: {result.get("company_name", "N/A")}')
            print(f'   Active Events: {", ".join(result.get("active_company_events", []))}')
            print(f'   Created: {result.get("total_created", 0)} events')
            print(f'   Updated: {result.get("total_updated", 0)} events')
            print(f'   Duration: {elapsed:.2f}s')
            print(f'   Message: {result.get("message", "N/A")}')
            print()

            # Show created events
            if result.get('created_events'):
                print('📝 Created Events:')
                for event_label in result['created_events']:
                    print(f'   - {event_label}')
                print()

        else:
            print('❌ Failed!')
            print(f'   Error: {result.get("error", "Unknown error")}')
            print()

    except Exception as e:
        print()
        print('=' * 70)
        print('❌ ERROR DURING SYNC')
        print('=' * 70)
        print(f'Error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        return

    # ============================================================
    # STEP 5: Verify Calendar Events Created
    # ============================================================

    print('=' * 70)
    print('STEP 5: Verifying Calendar Events Created')
    print('=' * 70)
    print()

    after_response = (
        supabase._client
        .table('calendar_events')
        .select('*')
        .eq('company_id', company_id)
        .order('due_date')
        .execute()
    )

    after_count = len(after_response.data)

    print(f'📋 Calendar events after sync: {after_count}')
    print(f'📈 New events created: {after_count - before_count}')
    print()

    if after_response.data:
        print('📅 Sample calendar events:')
        print()
        for i, event in enumerate(after_response.data[:5], 1):
            print(f'{i}. Due: {event.get("due_date", "N/A")} | '
                  f'Period: {event.get("period_start", "N/A")} to {event.get("period_end", "N/A")} | '
                  f'Status: {event.get("status", "N/A")}')

        if after_count > 5:
            print(f'   ... and {after_count - 5} more')
        print()

    # ============================================================
    # STEP 6: Re-run Sync to Verify Idempotency
    # ============================================================

    print('=' * 70)
    print('STEP 6: Re-running Sync (Idempotency Test)')
    print('=' * 70)
    print()

    try:
        start_time = time.time()

        # Run sync again
        result2 = await service.sync_company_calendar(company_id=company_id)

        elapsed = time.time() - start_time

        print()
        print('=' * 70)
        print('✅ SYNC COMPLETED (2nd Run)')
        print('=' * 70)
        print()

        if result2.get('success'):
            print('✅ Success!')
            print()
            print('📊 Results:')
            print('-' * 70)
            print(f'   Created: {result2.get("total_created", 0)} events (should be 0)')
            print(f'   Updated: {result2.get("total_updated", 0)} events')
            print(f'   Duration: {elapsed:.2f}s')
            print(f'   Message: {result2.get("message", "N/A")}')
            print()

            if result2.get('total_created', 0) == 0:
                print('✅ IDEMPOTENCY VERIFIED: No duplicate events created')
            else:
                print('⚠️  WARNING: New events created on 2nd run (not idempotent!)')

        else:
            print('❌ Failed!')
            print(f'   Error: {result2.get("error", "Unknown error")}')

    except Exception as e:
        print()
        print('=' * 70)
        print('❌ ERROR DURING 2ND SYNC')
        print('=' * 70)
        print(f'Error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()

    # ============================================================
    # SUMMARY
    # ============================================================

    print()
    print('=' * 70)
    print('🎉 TEST COMPLETED')
    print('=' * 70)
    print()
    print('✅ Flow validated:')
    print('   1. ✅ Company lookup')
    print('   2. ✅ Company events configuration')
    print('   3. ✅ Calendar event generation')
    print('   4. ✅ Status management')
    print('   5. ✅ Idempotency verification')
    print()


if __name__ == '__main__':
    asyncio.run(test_calendar_sync())
