"""
Test script for Form29 draft generation.

This script tests the Form29 service and Celery task.

Usage:
    # Test service directly (async)
    python -m scripts.test_form29_generation service --year 2025 --month 1

    # Test Celery task
    python -m scripts.test_form29_generation task --year 2025 --month 1

    # Test with current period (previous month)
    python -m scripts.test_form29_generation service
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_service(period_year: int, period_month: int):
    """Test the Form29Service directly."""
    from app.config.database import AsyncSessionLocal
    from app.services.form29 import Form29Service

    logger.info(
        f"Testing Form29Service for period {period_year}-{period_month:02d}"
    )

    async with AsyncSessionLocal() as db:
        service = Form29Service(db)

        try:
            # Generate drafts
            summary = await service.create_drafts_for_all_companies(
                period_year=period_year,
                period_month=period_month,
                auto_calculate=True
            )

            # Print summary
            logger.info("=" * 80)
            logger.info("SUMMARY:")
            logger.info(f"  Period: {summary['period_year']}-{summary['period_month']:02d}")
            logger.info(f"  Total companies: {summary['total_companies']}")
            logger.info(f"  Created: {summary['created']}")
            logger.info(f"  Skipped: {summary['skipped']}")
            logger.info(f"  Errors: {summary['errors']}")

            if summary['error_details']:
                logger.error("=" * 80)
                logger.error("ERROR DETAILS:")
                for error in summary['error_details']:
                    logger.error(
                        f"  Company: {error['company_name']} ({error['company_id']})"
                    )
                    logger.error(f"  Error: {error['error']}")

            logger.info("=" * 80)

            return summary

        except Exception as e:
            logger.error(f"Error testing service: {e}", exc_info=True)
            raise


def test_task(period_year: int, period_month: int):
    """Test the Celery task."""
    from app.infrastructure.celery.tasks.forms import (
        generate_f29_drafts_all_companies
    )

    logger.info(
        f"Testing Celery task for period {period_year}-{period_month:02d}"
    )

    try:
        # Run task synchronously (not .delay())
        result = generate_f29_drafts_all_companies(
            period_year=period_year,
            period_month=period_month,
            auto_calculate=True
        )

        # Print summary
        logger.info("=" * 80)
        logger.info("TASK RESULT:")
        logger.info(f"  Success: {result['success']}")
        logger.info(f"  Period: {result['period_year']}-{result['period_month']:02d}")
        logger.info(f"  Total companies: {result['total_companies']}")
        logger.info(f"  Created: {result['created']}")
        logger.info(f"  Skipped: {result['skipped']}")
        logger.info(f"  Errors: {result['errors']}")
        logger.info(f"  Execution time: {result['execution_time_seconds']:.2f}s")

        if result.get('error_details'):
            logger.error("=" * 80)
            logger.error("ERROR DETAILS:")
            for error in result['error_details']:
                logger.error(
                    f"  Company: {error['company_name']} ({error['company_id']})"
                )
                logger.error(f"  Error: {error['error']}")

        logger.info("=" * 80)

        return result

    except Exception as e:
        logger.error(f"Error testing task: {e}", exc_info=True)
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test Form29 draft generation'
    )
    parser.add_argument(
        'mode',
        choices=['service', 'task'],
        help='Test mode: service (direct) or task (Celery)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=None,
        help='Period year (defaults to previous month)'
    )
    parser.add_argument(
        '--month',
        type=int,
        default=None,
        help='Period month (1-12, defaults to previous month)'
    )

    args = parser.parse_args()

    # Default to previous month if not specified
    if args.year is None or args.month is None:
        now = datetime.utcnow()
        period_month = now.month - 1 if now.month > 1 else 12
        period_year = now.year if now.month > 1 else now.year - 1
    else:
        period_year = args.year
        period_month = args.month

    # Validate month
    if not 1 <= period_month <= 12:
        logger.error(f"Invalid month: {period_month}. Must be between 1 and 12.")
        sys.exit(1)

    logger.info(f"Starting test in '{args.mode}' mode")
    logger.info(f"Period: {period_year}-{period_month:02d}")

    try:
        if args.mode == 'service':
            result = asyncio.run(test_service(period_year, period_month))
        else:
            result = test_task(period_year, period_month)

        if result.get('success', False):
            logger.info("✅ Test completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Test failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
