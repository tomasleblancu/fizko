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
        company_id: str,
        auto_initialize: bool = True
    ) -> Dict[str, Any]:
        """
        Synchronize calendar events for a specific company.

        This method is idempotent - can be run multiple times without duplicating events.

        Flow:
        1. Verify company exists
        2. (Optional) Auto-initialize company_events if none exist
           - Uses internal business logic to determine which templates to activate
        3. Get active company_events (is_active=true)
        4. For each company_event:
           - Get existing calendar_events
           - Generate missing events for next periods
           - Update event statuses
        5. Return summary

        Args:
            company_id: UUID of the company (str format)
            auto_initialize: Whether to auto-initialize company_events if none exist (default: True)

        Returns:
            Dict with sync results:
            {
                "success": bool,
                "company_id": str,
                "company_name": str,
                "initialized": bool,  # True if company_events were created
                "company_events_created": int,  # Number of company_events created (if initialized)
                "active_company_events": list[str],  # event template codes
                "created_events": list[str],  # labels like "f29:2025-01"
                "updated_events": list[str],
                "total_created": int,
                "total_updated": int,
                "message": str
            }

        Raises:
            ValueError: If company not found or no active events (and auto_initialize=False)
        """
        logger.info(f"🔄 [Calendar Sync] Starting sync for company {company_id}")

        # 1. Verify company exists
        company = await self.companies_repo.get_by_id(company_id, include_tax_info=False)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        company_name = company.get('business_name', 'Unknown')
        logger.info(f"📅 [Calendar Sync] Syncing calendar for: {company_name}")

        # 2. Check if company_events exist, initialize if needed
        active_company_events = await self.calendar_repo.get_active_company_events(company_id)

        initialized = False
        company_events_created = 0

        if not active_company_events:
            if auto_initialize:
                logger.info(
                    f"🔧 [Calendar Sync] No company_events found, auto-initializing..."
                )

                # Get company settings to inform template selection logic
                company_settings = await self.companies_repo.get_company_settings(company_id)

                # Initialize company_events using internal business logic
                init_result = await self.initialize_company_events(
                    company_id=company_id,
                    company_settings=company_settings
                )

                initialized = True
                company_events_created = init_result.get('company_events_created', 0)

                logger.info(
                    f"✅ [Calendar Sync] Auto-initialized {company_events_created} company_events"
                )

                # Re-fetch active company_events after initialization
                active_company_events = await self.calendar_repo.get_active_company_events(company_id)
            else:
                raise ValueError(
                    "No hay eventos activos configurados para esta empresa. "
                    "Primero activa eventos en company_events."
                )

        if not active_company_events:
            raise ValueError(
                "No se pudieron inicializar company_events para esta empresa."
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
        message = self._build_sync_message(created_events, updated_events, initialized, company_events_created)

        logger.info(
            f"✅ [Calendar Sync] Completed for {company_id}: "
            f"initialized={initialized}, "
            f"company_events_created={company_events_created}, "
            f"{len(created_events)} calendar_events created, {len(updated_events)} updated"
        )

        return {
            "success": True,
            "company_id": company_id,
            "company_name": company_name,
            "initialized": initialized,
            "company_events_created": company_events_created,
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

    async def initialize_company_events(
        self,
        company_id: str,
        company_settings: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        Initialize company_events for a company during onboarding.

        This creates company_events for:
        1. All mandatory event templates (is_mandatory = true)
        2. Additional templates determined by internal business logic

        This method is idempotent - can be run multiple times without duplicating events.

        Args:
            company_id: UUID of the company
            company_settings: Optional company settings dict to inform template selection logic

        Returns:
            Dict with initialization results:
            {
                "success": bool,
                "company_id": str,
                "company_events_created": int,
                "template_codes": list[str],  # codes of created templates
                "message": str
            }

        Raises:
            ValueError: If company not found
        """
        logger.info(f"📋 [Calendar Init] Initializing company_events for company {company_id}")

        # 1. Verify company exists
        company = await self.companies_repo.get_by_id(company_id, include_tax_info=False)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        company_name = company.get('business_name', 'Unknown')
        logger.info(f"📅 [Calendar Init] Initializing for: {company_name}")

        # 2. Get mandatory event templates
        mandatory_templates = await self.calendar_repo.get_mandatory_event_templates()
        logger.info(
            f"📋 [Calendar Init] Found {len(mandatory_templates)} mandatory templates: "
            f"{[t['code'] for t in mandatory_templates]}"
        )

        # 3. Determine additional templates based on company settings
        additional_template_ids = await self._determine_additional_templates(
            company_id=company_id,
            company_settings=company_settings
        )

        additional_templates = []
        if additional_template_ids:
            additional_templates = await self.calendar_repo.get_event_templates_by_ids(
                additional_template_ids
            )
            logger.info(
                f"📋 [Calendar Init] Auto-selected {len(additional_templates)} additional templates: "
                f"{[t['code'] for t in additional_templates]}"
            )

        # 4. Combine and deduplicate templates
        all_templates = mandatory_templates + additional_templates
        unique_templates = {t['id']: t for t in all_templates}.values()

        logger.info(
            f"📋 [Calendar Init] Creating company_events for {len(unique_templates)} unique templates"
        )

        # 5. Check which company_events already exist
        existing_company_events = await self.calendar_repo.get_existing_company_events_by_company(
            company_id
        )
        existing_template_ids = {ce['event_template_id'] for ce in existing_company_events}

        logger.info(
            f"📋 [Calendar Init] Found {len(existing_template_ids)} existing company_events"
        )

        # 6. Filter out templates that already have company_events
        templates_to_create = [
            t for t in unique_templates
            if t['id'] not in existing_template_ids
        ]

        if len(templates_to_create) == 0:
            logger.info("✅ [Calendar Init] All templates already have company_events")
            return {
                "success": True,
                "company_id": company_id,
                "company_events_created": 0,
                "template_codes": [],
                "message": "No new company_events needed (all templates already configured)"
            }

        logger.info(
            f"📋 [Calendar Init] Creating {len(templates_to_create)} new company_events"
        )

        # 7. Create company_events
        created_codes = []
        for template in templates_to_create:
            created_event = await self.calendar_repo.create_company_event(
                company_id=company_id,
                event_template_id=template['id'],
                is_active=True
            )

            if created_event:
                created_codes.append(template['code'])
                logger.debug(f"  ✅ Created company_event for template: {template['code']}")
            else:
                logger.warning(f"  ⚠️  Failed to create company_event for template: {template['code']}")

        logger.info(
            f"✅ [Calendar Init] Completed for {company_id}: "
            f"{len(created_codes)} company_events created"
        )

        return {
            "success": True,
            "company_id": company_id,
            "company_events_created": len(created_codes),
            "template_codes": created_codes,
            "message": f"{len(created_codes)} company_events created successfully"
        }

    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================

    async def _determine_additional_templates(
        self,
        company_id: str,
        company_settings: Dict[str, Any] | None = None
    ) -> List[str]:
        """
        Determine which additional (non-mandatory) event templates should be activated
        for a company based on their settings and business characteristics.

        This method contains the business logic to automatically enable optional templates
        based on company configuration (e.g., has_formal_employees → enable Previred).

        Args:
            company_id: UUID of the company
            company_settings: Optional company settings dict (from company_settings table)

        Returns:
            List of event template IDs to activate (in addition to mandatory templates)

        Business rules (to be implemented):
        - If has_formal_employees=True → Enable previred_payment template
        - If has_lease_contracts=True → Enable lease_payment template
        - If has_imports=True → Enable import_declaration template
        - If has_exports=True → Enable export_declaration template
        - etc.
        """
        logger.debug(f"🔍 [Template Selection] Determining additional templates for company {company_id}")

        additional_template_ids: List[str] = []

        # TODO: Implement business logic here
        # For now, return empty list (no additional templates beyond mandatory)

        # Example implementation (commented out):
        # if company_settings:
        #     if company_settings.get('has_formal_employees'):
        #         previred_template = await self.calendar_repo.get_event_template_by_code('previred_payment')
        #         if previred_template:
        #             additional_template_ids.append(previred_template['id'])
        #
        #     if company_settings.get('has_lease_contracts'):
        #         lease_template = await self.calendar_repo.get_event_template_by_code('lease_payment')
        #         if lease_template:
        #             additional_template_ids.append(lease_template['id'])
        #
        #     # Add more rules as needed...

        logger.debug(
            f"🔍 [Template Selection] Selected {len(additional_template_ids)} additional templates "
            f"for company {company_id}"
        )

        return additional_template_ids

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
        updated_events: List[str],
        initialized: bool = False,
        company_events_created: int = 0
    ) -> str:
        """
        Build descriptive sync message.

        Args:
            created_events: List of created event labels
            updated_events: List of updated event labels
            initialized: Whether company_events were initialized
            company_events_created: Number of company_events created during initialization

        Returns:
            Human-readable sync message
        """
        messages = []

        if initialized and company_events_created > 0:
            messages.append(f"{company_events_created} plantillas activadas")

        if created_events:
            messages.append(f"{len(created_events)} eventos creados")

        if updated_events:
            messages.append(f"{len(updated_events)} eventos actualizados")

        return (
            "Calendario sincronizado: " + ", ".join(messages)
            if messages
            else "Calendario sincronizado: sin cambios"
        )
