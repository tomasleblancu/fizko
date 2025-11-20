"""
Calendar Sync Service - Generates calendar_events from company_events

This service is responsible for:
1. Synchronizing calendar events for companies with active company_events
2. Generating monthly and annual tax events (F29, F22, etc.)
3. Managing event statuses (pending, in_progress, overdue)
4. Ensuring idempotent event creation (no duplicates)

Based on backend/app/services/calendar/sync_service.py
"""
import logging
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, Any, List

from app.config.supabase import SupabaseClient
from app.repositories.calendar import CalendarRepository
from app.repositories.companies import CompaniesRepository

logger = logging.getLogger(__name__)


class CalendarSyncService:
    """
    Service for synchronizing calendar events from company_events.

    Responsibilities:
    - Sync calendar for one company or all companies
    - Generate monthly events (F29, Previred, etc.)
    - Generate annual events (F22, etc.)
    - Update event statuses
    - Ensure idempotency (no duplicate events)
    """

    def __init__(self, supabase: SupabaseClient):
        """
        Initialize the service.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase
        self.calendar_repo = CalendarRepository(supabase._client)
        self.companies_repo = CompaniesRepository(supabase._client)

    async def sync_company_calendar(
        self,
        company_id: str
    ) -> Dict[str, Any]:
        """
        Synchronize calendar events for a specific company.

        This method is idempotent - can be run multiple times without duplicating events.

        Flow:
        1. Verify company exists
        2. Get active company_events (is_active=true)
        3. For each company_event:
           - Get existing calendar_events
           - Generate missing events for next periods
           - Update event statuses
        4. Return summary

        Args:
            company_id: UUID of the company (str format)

        Returns:
            Dict with sync results:
            {
                "success": bool,
                "company_id": str,
                "company_name": str,
                "active_company_events": list[str],  # event template codes
                "created_events": list[str],  # labels like "f29:2025-01"
                "updated_events": list[str],
                "total_created": int,
                "total_updated": int,
                "message": str
            }

        Raises:
            ValueError: If company not found or no active events
        """
        logger.info(f"🔄 [Calendar Sync] Starting sync for company {company_id}")

        # 1. Verify company exists
        company = await self.companies_repo.get_by_id(company_id, include_tax_info=False)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        company_name = company.get('business_name', 'Unknown')
        logger.info(f"📅 [Calendar Sync] Syncing calendar for: {company_name}")

        # 2. Get active company_events
        active_company_events = await self.calendar_repo.get_active_company_events(company_id)

        if not active_company_events:
            raise ValueError(
                "No hay eventos activos configurados para esta empresa. "
                "Primero activa eventos en company_events."
            )

        logger.info(
            f"📋 [Calendar Sync] Found {len(active_company_events)} active company_events: "
            f"{[ce['event_template']['code'] for ce in active_company_events]}"
        )

        # 3. Sync all company_events
        created_events, updated_events = await self._sync_all_company_events(
            company_id=company_id,
            active_company_events=active_company_events
        )

        # 4. Build result
        message = self._build_sync_message(created_events, updated_events)

        logger.info(
            f"✅ [Calendar Sync] Completed for {company_id}: "
            f"{len(created_events)} created, {len(updated_events)} updated"
        )

        return {
            "success": True,
            "company_id": company_id,
            "company_name": company_name,
            "active_company_events": [ce['event_template']['code'] for ce in active_company_events],
            "created_events": created_events,
            "updated_events": updated_events,
            "total_created": len(created_events),
            "total_updated": len(updated_events),
            "message": message
        }

    async def sync_all_companies(self) -> Dict[str, Any]:
        """
        Synchronize calendar events for ALL companies with active events.

        Returns:
            Dict with batch sync results:
            {
                "success": bool,
                "total_companies": int,
                "synced_companies": int,
                "failed_companies": int,
                "results": list[dict]  # Per-company results
            }
        """
        logger.info("🚀 [Calendar Sync] Starting batch sync for ALL companies")

        # Get all companies with active events
        companies = await self.calendar_repo.get_all_companies_with_active_events()

        if not companies:
            logger.info("ℹ️  [Calendar Sync] No companies with active events found")
            return {
                "success": True,
                "total_companies": 0,
                "synced_companies": 0,
                "failed_companies": 0,
                "results": []
            }

        total_companies = len(companies)
        logger.info(f"📋 [Calendar Sync] Found {total_companies} companies with active events")

        synced_companies = 0
        failed_companies = 0
        results = []

        for i, company in enumerate(companies, 1):
            company_id = company['id']
            company_name = company.get('business_name', 'Unknown')

            logger.info(
                f"[{i}/{total_companies}] Syncing calendar for: {company_name} ({company_id})"
            )

            try:
                result = await self.sync_company_calendar(company_id)
                synced_companies += 1
                results.append(result)
                logger.info(f"✅ [{i}/{total_companies}] Synced: {company_name}")

            except Exception as e:
                failed_companies += 1
                error_msg = str(e)
                logger.error(
                    f"❌ [{i}/{total_companies}] Failed to sync {company_name}: {error_msg}"
                )
                results.append({
                    "success": False,
                    "company_id": company_id,
                    "company_name": company_name,
                    "error": error_msg
                })

        logger.info(
            f"✅ [Calendar Sync] Batch sync completed: "
            f"{synced_companies}/{total_companies} synced, {failed_companies} failed"
        )

        return {
            "success": True,
            "total_companies": total_companies,
            "synced_companies": synced_companies,
            "failed_companies": failed_companies,
            "results": results
        }

    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================

    async def _sync_all_company_events(
        self,
        company_id: str,
        active_company_events: List[Dict[str, Any]]
    ) -> tuple[List[str], List[str]]:
        """
        Sync all active company_events for a company.

        Args:
            company_id: UUID of the company
            active_company_events: List of active company_events with templates

        Returns:
            Tuple of (created_event_labels, updated_event_labels)
        """
        created_events = []
        updated_events = []
        today = date.today()

        for company_event in active_company_events:
            event_template = company_event['event_template']
            template_code = event_template['code']

            # Get event config (default + custom overrides)
            config = self._get_event_config(company_event)

            logger.debug(
                f"🔄 [Calendar Sync] Syncing {template_code} with config: {config}"
            )

            # Get existing events from today onwards
            existing_events = await self.calendar_repo.get_existing_calendar_events(
                company_event_id=company_event['id'],
                from_date=today
            )

            # Create map of existing events (due_date, period_start) -> event
            existing_events_map = {
                (event['due_date'], event['period_start']): event
                for event in existing_events
            }

            # Generate events to create based on frequency
            events_to_create = self._generate_events_by_frequency(
                config=config,
                today=today,
                existing_events_map=existing_events_map
            )

            # Create new calendar events
            new_labels = await self._create_calendar_events(
                company_event=company_event,
                company_id=company_id,
                events_to_create=events_to_create,
                config=config
            )
            created_events.extend(new_labels)

            # Update statuses of existing events
            updated_labels = await self._update_event_statuses(
                existing_events=existing_events,
                template_code=template_code
            )
            updated_events.extend(updated_labels)

        return created_events, updated_events

    def _get_event_config(self, company_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get event configuration with custom overrides applied.

        Args:
            company_event: Company event dict with event_template

        Returns:
            Merged configuration dict
        """
        event_template = company_event['event_template']
        default_config = event_template.get('default_recurrence', {})
        custom_config = company_event.get('custom_config', {})

        # Merge custom recurrence overrides
        if custom_config and 'recurrence' in custom_config:
            return {**default_config, **custom_config['recurrence']}

        return default_config

    def _generate_events_by_frequency(
        self,
        config: Dict[str, Any],
        today: date,
        existing_events_map: Dict[tuple, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate events based on frequency config.

        Args:
            config: Event recurrence configuration
            today: Current date
            existing_events_map: Map of (due_date, period_start) -> event

        Returns:
            List of event data dicts to create
        """
        frequency = config.get('frequency', 'monthly')

        if frequency == 'monthly':
            return self._generate_monthly_events(config, today, existing_events_map)
        elif frequency == 'annual':
            return self._generate_annual_events(config, today, existing_events_map)

        logger.warning(f"Unknown frequency: {frequency}, skipping event generation")
        return []

    def _generate_monthly_events(
        self,
        config: Dict[str, Any],
        today: date,
        existing_events_map: Dict[tuple, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate monthly events for the next 4 months.

        Args:
            config: Event configuration
            today: Current date
            existing_events_map: Map of existing events

        Returns:
            List of event data dicts to create
        """
        events_to_create = []
        day_of_month = config.get('day_of_month', 12)

        for months_ahead in range(4):
            # Period: first day of month to last day of month
            period_start = date(today.year, today.month, 1) + relativedelta(months=months_ahead)
            period_end = period_start + relativedelta(months=1) - timedelta(days=1)

            # Due date: specific day of the month
            due_date = date(period_start.year, period_start.month, day_of_month)

            # Skip if due date is in the past
            if due_date < today:
                continue

            # Skip if event already exists
            if (due_date.isoformat(), period_start.isoformat()) in existing_events_map:
                continue

            events_to_create.append({
                'due_date': due_date,
                'period_start': period_start,
                'period_end': period_end
            })

        return events_to_create

    def _generate_annual_events(
        self,
        config: Dict[str, Any],
        today: date,
        existing_events_map: Dict[tuple, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate annual events for the next year if not passed.

        Args:
            config: Event configuration
            today: Current date
            existing_events_map: Map of existing events

        Returns:
            List of event data dicts to create
        """
        events_to_create = []

        # Support both 'month_of_year' and 'months' (list)
        month = (
            config.get('month_of_year') or
            (config.get('months', [1])[0] if config.get('months') else 4)  # Default: April
        )
        day_of_month = config.get('day_of_month', 30)

        # Determine target year
        year = today.year
        if today.month >= month:
            year += 1

        # Period: previous calendar year
        period_start = date(year - 1, 1, 1)
        period_end = date(year - 1, 12, 31)

        # Due date: specific date in target year
        due_date = date(year, month, day_of_month)

        # Skip if due date is in the past
        if due_date < today:
            return []

        # Skip if event already exists
        if (due_date.isoformat(), period_start.isoformat()) in existing_events_map:
            return []

        events_to_create.append({
            'due_date': due_date,
            'period_start': period_start,
            'period_end': period_end
        })

        return events_to_create

    async def _create_calendar_events(
        self,
        company_event: Dict[str, Any],
        company_id: str,
        events_to_create: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[str]:
        """
        Create calendar events in the database.

        Args:
            company_event: Parent company_event dict
            company_id: UUID of the company
            events_to_create: List of event data dicts
            config: Event configuration

        Returns:
            List of created event labels (e.g., "f29:2025-01")
        """
        created_labels = []
        event_template = company_event['event_template']
        template_code = event_template['code']

        for event_data in events_to_create:
            # Create calendar event
            await self.calendar_repo.create_calendar_event(
                company_event_id=company_event['id'],
                company_id=company_id,
                event_template_id=event_template['id'],
                due_date=event_data['due_date'],
                period_start=event_data['period_start'],
                period_end=event_data['period_end'],
                status='pending',
                auto_generated=True
            )

            # Build label for tracking
            if config.get('frequency') == 'monthly':
                period_label = event_data['period_start'].strftime('%Y-%m')
            else:
                period_label = f"AT{event_data['period_start'].year}"

            created_labels.append(f"{template_code}:{period_label}")
            logger.debug(f"  ✅ Created event: {template_code} for {period_label}")

        return created_labels

    async def _update_event_statuses(
        self,
        existing_events: List[Dict[str, Any]],
        template_code: str
    ) -> List[str]:
        """
        Update event statuses - first event becomes in_progress, rest stay pending.

        Args:
            existing_events: List of existing calendar events
            template_code: Event template code

        Returns:
            List of updated event labels
        """
        updated_labels = []

        if not existing_events:
            return updated_labels

        # Sort by due date
        sorted_events = sorted(existing_events, key=lambda e: e['due_date'])

        for idx, event in enumerate(sorted_events):
            # First event should be in_progress, others pending
            expected_status = 'in_progress' if idx == 0 else 'pending'

            current_status = event['status']

            # Only update if status should change and event is in editable state
            if (current_status != expected_status and
                current_status in ['pending', 'in_progress', 'overdue']):

                await self.calendar_repo.update_calendar_event_status(
                    event_id=event['id'],
                    status=expected_status
                )

                period_label = (
                    event['period_start'][:7]  # YYYY-MM from ISO string
                    if event.get('period_start')
                    else 'N/A'
                )
                updated_labels.append(f"{template_code}:{period_label}")

        return updated_labels

    def _build_sync_message(
        self,
        created_events: List[str],
        updated_events: List[str]
    ) -> str:
        """
        Build descriptive sync message.

        Args:
            created_events: List of created event labels
            updated_events: List of updated event labels

        Returns:
            Human-readable sync message
        """
        messages = []

        if created_events:
            messages.append(f"{len(created_events)} eventos creados")

        if updated_events:
            messages.append(f"{len(updated_events)} eventos actualizados")

        return (
            "Calendario sincronizado: " + ", ".join(messages)
            if messages
            else "Calendario sincronizado: sin cambios"
        )
