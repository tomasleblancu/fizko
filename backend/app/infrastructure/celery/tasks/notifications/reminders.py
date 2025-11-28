"""
Celery tasks for F29 reminder notifications.

These tasks handle scheduled push notifications and WhatsApp messages
to remind users about upcoming F29 due dates.

Example usage:
    # Send reminders to all companies (run daily by Celery Beat)
    send_f29_reminders.delay()

    # Send reminder to specific company
    send_f29_reminder_for_company.delay(
        company_id="uuid",
        days_before=3
    )
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


def _get_f29_due_date(year: int, month: int) -> datetime:
    """
    Calculate F29 due date for a given period.

    F29 is due on the 12th of the month following the tax period.
    If the 12th falls on a weekend, it's due the next business day.

    Args:
        year: Tax period year
        month: Tax period month (1-12)

    Returns:
        Due date as datetime
    """
    # Calculate next month
    if month == 12:
        due_month = 1
        due_year = year + 1
    else:
        due_month = month + 1
        due_year = year

    # Due on the 12th
    due_date = datetime(due_year, due_month, 12)

    # If it's Saturday (5) or Sunday (6), move to next Monday
    while due_date.weekday() >= 5:
        due_date += timedelta(days=1)

    return due_date


@celery_app.task(
    bind=True,
    name="notifications.send_f29_reminders",
    max_retries=2,
    default_retry_delay=300,
)
def send_f29_reminders(
    self,
    days_before: int = 3,
) -> Dict[str, Any]:
    """
    Send F29 reminder notifications to all companies with due dates approaching.

    This task checks all companies for F29 forms due in X days and sends
    push notifications and/or WhatsApp messages to remind users.

    Designed to run daily via Celery Beat. Common reminder intervals:
    - 7 days before
    - 3 days before
    - 1 day before
    - On due date

    Args:
        days_before: How many days before due date to send reminder (default: 3)

    Returns:
        Dict with summary:
        {
            "success": bool,
            "days_before": int,
            "target_date": str,
            "companies_checked": int,
            "notifications_sent": int,
            "errors": int,
            "execution_time_seconds": float
        }

    Example:
        # Send 3-day reminder (default)
        send_f29_reminders.delay()

        # Send 7-day reminder
        send_f29_reminders.delay(days_before=7)
    """
    from app.services.notifications import send_push_notification_to_company

    start_time = datetime.utcnow()

    try:
        # Calculate target due date
        target_date = datetime.utcnow().date() + timedelta(days=days_before)

        logger.info(
            f"📬 [CELERY TASK] Starting F29 reminder notifications: "
            f"days_before={days_before}, target_date={target_date}"
        )

        # Run async logic
        async def _send_reminders():
            from app.config.supabase import get_supabase_client

            supabase = get_supabase_client()

            # Get all active companies
            companies_response = supabase.client.table("companies").select("id, business_name").execute()

            if not companies_response.data:
                logger.info("No companies found")
                return {
                    "companies_checked": 0,
                    "notifications_sent": 0,
                    "errors": 0,
                }

            companies = companies_response.data
            notifications_sent = 0
            errors = 0

            # Check each company for upcoming F29 due dates
            for company in companies:
                    company_id = company["id"]
                    company_name = company["business_name"]

                    try:
                        # Get current tax period (previous month)
                        now = datetime.utcnow()
                        period_month = now.month - 1 if now.month > 1 else 12
                        period_year = now.year if now.month > 1 else now.year - 1

                        # Calculate due date for this period
                        due_date = _get_f29_due_date(period_year, period_month)

                        # Check if due date matches our target
                        if due_date.date() == target_date:
                            logger.info(
                                f"📅 Company {company_name} has F29 due on {due_date.date()}"
                            )

                            # Send push notification
                            title = "Recordatorio F29"
                            body = f"Tu F29 vence en {days_before} día{'s' if days_before != 1 else ''}. No olvides presentarlo a tiempo."

                            result = await send_push_notification_to_company(
                                company_id=company_id,
                                title=title,
                                body=body,
                                data={
                                    "type": "f29_reminder",
                                    "company_id": company_id,
                                    "due_date": due_date.isoformat(),
                                    "days_before": days_before,
                                    "period_year": period_year,
                                    "period_month": period_month,
                                },
                                badge=1,
                            )

                            if result.get("status") == "sent" or result.get("sent", 0) > 0:
                                notifications_sent += result.get("sent", 1)
                                logger.info(
                                    f"✅ Sent F29 reminder to company {company_name}: "
                                    f"{result.get('sent', 1)} users notified"
                                )
                            else:
                                logger.info(
                                    f"⏭️  Skipped company {company_name}: {result.get('status')}"
                                )

                    except Exception as e:
                        errors += 1
                        logger.error(
                            f"❌ Failed to send reminder to company {company_name}: {e}",
                            exc_info=True
                        )

            return {
                "companies_checked": len(companies),
                "notifications_sent": notifications_sent,
                "errors": errors,
            }

        summary = asyncio.run(_send_reminders())
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"✅ [CELERY TASK] F29 reminders completed: "
            f"checked={summary['companies_checked']}, sent={summary['notifications_sent']}, "
            f"errors={summary['errors']}, time={execution_time:.2f}s"
        )

        return {
            "success": True,
            "days_before": days_before,
            "target_date": str(target_date),
            "execution_time_seconds": execution_time,
            **summary
        }

    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"❌ [CELERY TASK] F29 reminders failed: {e}",
            exc_info=True
        )

        # Retry on certain errors
        if "database" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(exc=e)

        return {
            "success": False,
            "error": str(e),
            "days_before": days_before,
            "execution_time_seconds": execution_time,
            "companies_checked": 0,
            "notifications_sent": 0,
            "errors": 0,
        }


@celery_app.task(
    bind=True,
    name="notifications.send_f29_reminder_for_company",
    max_retries=2,
    default_retry_delay=60,
)
def send_f29_reminder_for_company(
    self,
    company_id: str,
    days_before: int,
    period_year: int = None,
    period_month: int = None,
) -> Dict[str, Any]:
    """
    Send F29 reminder notification to a specific company.

    Used for on-demand reminders or when a company subscribes to notifications.

    Args:
        company_id: Company UUID
        days_before: How many days before due date
        period_year: Tax period year (defaults to previous month)
        period_month: Tax period month (defaults to previous month)

    Returns:
        Dict with result:
        {
            "success": bool,
            "company_id": str,
            "notifications_sent": int,
            "error": str (optional),
            "execution_time_seconds": float
        }

    Example:
        send_f29_reminder_for_company.delay(
            company_id="uuid-here",
            days_before=3
        )
    """
    from app.services.notifications import send_push_notification_to_company

    start_time = datetime.utcnow()

    try:
        # Default to previous month if not specified
        if period_year is None or period_month is None:
            now = datetime.utcnow()
            period_month = now.month - 1 if now.month > 1 else 12
            period_year = now.year if now.month > 1 else now.year - 1

        logger.info(
            f"📬 [CELERY TASK] Sending F29 reminder for company {company_id}: "
            f"period={period_year}-{period_month:02d}, days_before={days_before}"
        )

        # Calculate due date
        due_date = _get_f29_due_date(period_year, period_month)

        # Send notification
        async def _send():
            title = "Recordatorio F29"
            body = f"Tu F29 vence en {days_before} día{'s' if days_before != 1 else ''}. No olvides presentarlo a tiempo."

            return await send_push_notification_to_company(
                company_id=company_id,
                title=title,
                body=body,
                data={
                    "type": "f29_reminder",
                    "company_id": company_id,
                    "due_date": due_date.isoformat(),
                    "days_before": days_before,
                    "period_year": period_year,
                    "period_month": period_month,
                },
                badge=1,
            )

        result = asyncio.run(_send())
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        notifications_sent = result.get("sent", 0)

        logger.info(
            f"✅ [CELERY TASK] F29 reminder sent to company {company_id}: "
            f"sent={notifications_sent}, time={execution_time:.2f}s"
        )

        return {
            "success": True,
            "company_id": company_id,
            "notifications_sent": notifications_sent,
            "period_year": period_year,
            "period_month": period_month,
            "due_date": due_date.isoformat(),
            "execution_time_seconds": execution_time
        }

    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"❌ [CELERY TASK] F29 reminder failed for company {company_id}: {e}",
            exc_info=True
        )

        # Retry on certain errors
        if "database" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(exc=e)

        return {
            "success": False,
            "company_id": company_id,
            "error": str(e),
            "execution_time_seconds": execution_time,
            "notifications_sent": 0,
        }
