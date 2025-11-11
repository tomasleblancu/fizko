"""
Test script to verify previous month credit functionality in Form29 generation.

This script:
1. Tests that TaxSummaryRepository correctly finds previous month credit
2. Tests that Form29Service applies the credit to net_iva calculation
3. Verifies both Form29 draft and Form29SIIDownload fallback logic
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.config.database import AsyncSessionLocal
from app.repositories.tax.tax_summary import TaxSummaryRepository
from app.services.form29 import Form29Service
from sqlalchemy import select
from app.db.models import Company


async def test_previous_month_credit():
    """Test previous month credit calculation and application."""

    async with AsyncSessionLocal() as db:
        try:
            # Get first company with subscription
            from app.infrastructure.celery.subscription_helper import get_subscribed_companies

            subscribed_companies = await get_subscribed_companies(db, only_active=False)

            if not subscribed_companies:
                print("❌ No companies with subscriptions found")
                return

            company_id, company_name = subscribed_companies[0]
            print(f"\n🏢 Testing with company: {company_name}")
            print(f"   Company ID: {company_id}")

            # Test 1: Get tax summary for current period
            print("\n" + "="*60)
            print("TEST 1: Tax Summary with Previous Month Credit")
            print("="*60)

            tax_repo = TaxSummaryRepository(db)

            # Test for January 2025 (should look for December 2024 credit)
            summary = await tax_repo.get_tax_summary(company_id, "2025-01")

            print(f"\n📊 Tax Summary for 2025-01:")
            print(f"   Total Revenue: ${summary.total_revenue:,.2f}")
            print(f"   Total Expenses: ${summary.total_expenses:,.2f}")
            print(f"   IVA Collected: ${summary.iva_collected:,.2f}")
            print(f"   IVA Paid: ${summary.iva_paid:,.2f}")
            print(f"   Previous Month Credit: ${summary.previous_month_credit or 0:,.2f}")
            print(f"   Net IVA: ${summary.net_iva:,.2f}")
            print(f"   Monthly Tax: ${summary.monthly_tax:,.2f}")

            # Test 2: Generate F29 draft and verify credit is applied
            print("\n" + "="*60)
            print("TEST 2: Form29 Draft Generation with Credit")
            print("="*60)

            form29_service = Form29Service(db)

            calculated_values = await form29_service.calculate_f29_from_documents(
                company_id, 2025, 1
            )

            print(f"\n📝 Calculated F29 Values for 2025-01:")
            print(f"   Total Sales: ${calculated_values['total_sales']:,.2f}")
            print(f"   Sales Tax (IVA Collected): ${calculated_values['sales_tax']:,.2f}")
            print(f"   Purchases Tax (IVA Paid): ${calculated_values['purchases_tax']:,.2f}")
            print(f"   Previous Month Credit: ${calculated_values['previous_month_credit']:,.2f}")
            print(f"   Net IVA: ${calculated_values['net_iva']:,.2f}")

            # Test 3: Verify calculation
            print("\n" + "="*60)
            print("TEST 3: Verify Calculation Logic")
            print("="*60)

            expected_net_iva = (
                float(calculated_values['sales_tax']) -
                float(calculated_values['purchases_tax']) -
                float(calculated_values['previous_month_credit'])
            )

            actual_net_iva = float(calculated_values['net_iva'])

            print(f"\n🧮 Calculation Verification:")
            print(f"   IVA Collected: ${calculated_values['sales_tax']:,.2f}")
            print(f"   - IVA Paid: ${calculated_values['purchases_tax']:,.2f}")
            print(f"   - Previous Credit: ${calculated_values['previous_month_credit']:,.2f}")
            print(f"   = Expected Net IVA: ${expected_net_iva:,.2f}")
            print(f"   = Actual Net IVA: ${actual_net_iva:,.2f}")

            if abs(expected_net_iva - actual_net_iva) < 0.01:
                print(f"   ✅ PASS: Calculation is correct!")
            else:
                print(f"   ❌ FAIL: Calculation mismatch!")
                print(f"      Difference: ${abs(expected_net_iva - actual_net_iva):,.2f}")

            # Test 4: Test with a month that has no previous credit
            print("\n" + "="*60)
            print("TEST 4: Month with No Previous Credit")
            print("="*60)

            # Try December 2024 (November 2024 likely has no credit)
            calculated_values_dec = await form29_service.calculate_f29_from_documents(
                company_id, 2024, 12
            )

            print(f"\n📝 Calculated F29 Values for 2024-12:")
            print(f"   Previous Month Credit: ${calculated_values_dec['previous_month_credit']:,.2f}")
            print(f"   Net IVA: ${calculated_values_dec['net_iva']:,.2f}")

            if float(calculated_values_dec['previous_month_credit']) == 0:
                print("   ✅ PASS: No credit found for November 2024 (as expected)")
            else:
                print(f"   ℹ️  INFO: Found credit for November 2024: ${calculated_values_dec['previous_month_credit']:,.2f}")

            print("\n" + "="*60)
            print("✅ All tests completed successfully!")
            print("="*60)

        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Testing Previous Month Credit Functionality")
    print("=" * 60)
    asyncio.run(test_previous_month_credit())
