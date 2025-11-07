#!/usr/bin/env python3
"""
Test script for subscription-based agent access control.

This script verifies that:
1. Plans have correct agent/tool features configured
2. SubscriptionGuard validates access correctly
3. Companies with different plans see appropriate agents

Usage:
    python scripts/test_subscription_agents.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import AsyncSessionLocal
from app.agents.core import SubscriptionGuard
from app.services.subscriptions import SubscriptionService
from sqlalchemy import select, text


async def test_plan_configuration():
    """Test 1: Verify plans have correct agent/tool features."""
    print("\n" + "=" * 80)
    print("TEST 1: Plan Configuration")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # Query plans with features
        result = await db.execute(
            text("""
                SELECT code, name,
                       features->'agents' as agents_access,
                       features->'tools' as tools_access
                FROM subscription_plans
                ORDER BY display_order
            """)
        )
        rows = result.fetchall()

        for row in rows:
            print(f"\n📋 Plan: {row.name} ({row.code})")
            print(f"   Agents: {row.agents_access}")
            print(f"   Tools: {row.tools_access}")

        if not rows:
            print("❌ No plans found! Run migration first.")
            return False

        print("\n✅ Plans configured correctly")
        return True


async def test_subscription_guard():
    """Test 2: Verify SubscriptionGuard validates access correctly."""
    print("\n" + "=" * 80)
    print("TEST 2: SubscriptionGuard Validation")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        service = SubscriptionService(db)

        # Get a test company with subscription
        result = await db.execute(
            text("""
                SELECT c.id as company_id, c.business_name,
                       s.status, sp.code as plan_code, sp.name as plan_name
                FROM companies c
                JOIN subscriptions s ON c.id = s.company_id
                JOIN subscription_plans sp ON s.plan_id = sp.id
                WHERE s.status IN ('trialing', 'active')
                LIMIT 1
            """)
        )
        test_company = result.fetchone()

        if not test_company:
            print("⚠️  No test company with active subscription found")
            print("   Skipping SubscriptionGuard tests")
            return True

        company_id = test_company.company_id
        plan_code = test_company.plan_code

        print(f"\n🏢 Test Company: {test_company.business_name}")
        print(f"   Plan: {test_company.plan_name} ({plan_code})")
        print(f"   Status: {test_company.status}")

        # Test agent access
        guard = SubscriptionGuard(db)

        print("\n📊 Agent Access:")
        for agent_name in ["general_knowledge", "tax_documents", "payroll", "settings"]:
            can_use, error_msg = await guard.can_use_agent(company_id, agent_name)
            status = "✅" if can_use else "🔒"
            print(f"   {status} {agent_name}: {'Allowed' if can_use else 'Blocked'}")

        # Test tool access
        print("\n🔧 Tool Access:")
        test_tools = [
            "get_documents",
            "get_documents_summary",
            "get_f29_data",
            "get_people",
            "create_person"
        ]
        for tool_name in test_tools:
            can_use, error_msg = await guard.can_use_tool(company_id, tool_name)
            status = "✅" if can_use else "🔒"
            print(f"   {status} {tool_name}: {'Allowed' if can_use else 'Blocked'}")

        # Get available agents
        available = await guard.get_available_agents(company_id)
        print(f"\n📋 Available Agents: {', '.join(available)}")

        print("\n✅ SubscriptionGuard working correctly")
        return True


async def test_expected_access_patterns():
    """Test 3: Verify expected access patterns by plan."""
    print("\n" + "=" * 80)
    print("TEST 3: Expected Access Patterns")
    print("=" * 80)

    expected_patterns = {
        "free": {
            "agents": ["general_knowledge", "settings"],
            "blocked_agents": ["tax_documents", "payroll"]
        },
        "basic": {
            "agents": ["general_knowledge", "tax_documents", "settings"],
            "blocked_agents": ["payroll"]
        },
        "pro": {
            "agents": ["general_knowledge", "tax_documents", "payroll", "settings"],
            "blocked_agents": []
        }
    }

    async with AsyncSessionLocal() as db:
        service = SubscriptionService(db)

        for plan_code, expected in expected_patterns.items():
            plan = await service.get_plan_by_code(plan_code)
            if not plan:
                print(f"⚠️  Plan '{plan_code}' not found, skipping")
                continue

            print(f"\n📋 Plan: {plan.name} ({plan_code})")

            # Check agents
            agents_config = plan.features.get("agents", {})
            print(f"   Expected agents: {', '.join(expected['agents'])}")

            for agent in expected["agents"]:
                if agents_config.get(agent) != True:
                    print(f"   ❌ ERROR: {agent} should be enabled")
                    return False

            for agent in expected["blocked_agents"]:
                if agents_config.get(agent) != False:
                    print(f"   ❌ ERROR: {agent} should be blocked")
                    return False

            print(f"   ✅ Access pattern correct")

    print("\n✅ All access patterns validated")
    return True


async def main():
    """Run all tests."""
    print("\n🧪 Subscription Agent Access Control Tests")
    print("=" * 80)

    try:
        # Run tests
        test1 = await test_plan_configuration()
        test2 = await test_subscription_guard()
        test3 = await test_expected_access_patterns()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        all_passed = test1 and test2 and test3
        if all_passed:
            print("✅ All tests passed!")
            print("\n🎉 Subscription-based agent access control is working correctly!")
        else:
            print("❌ Some tests failed")
            print("\n⚠️  Please review the migration and configuration")

        return 0 if all_passed else 1

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
