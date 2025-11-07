#!/usr/bin/env python3
"""
Test script to verify orchestrator creation with subscription validation.

This script creates an orchestrator for a company with Basic plan and verifies
that only allowed agents are created (no payroll agent).
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import AsyncSessionLocal
from app.agents.orchestration import create_multi_agent_orchestrator
from openai import AsyncOpenAI
import os


async def test_orchestrator_creation():
    """Test that orchestrator respects subscription limits."""
    print("\n" + "=" * 80)
    print("TEST: Orchestrator Creation with Subscription Validation")
    print("=" * 80)

    # Get a test company with Basic plan (from previous test)
    test_company_id = UUID("1569bc05-7c77-4f8e-9345-e4522ae6b2d5")

    print(f"\n🏢 Test Company ID: {test_company_id}")
    print("   Expected Plan: Plan Básico")
    print("   Expected Agents: general_knowledge, tax_documents, settings")
    print("   Blocked Agents: payroll")

    async with AsyncSessionLocal() as db:
        # Create OpenAI client
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        print("\n🔀 Creating orchestrator...")
        orchestrator = await create_multi_agent_orchestrator(
            db=db,
            openai_client=openai_client,
            company_id=test_company_id,
            thread_id="test_thread_123",
            channel="web",
        )

        print(f"\n📊 Orchestrator created successfully!")
        print(f"   Total agents: {len(orchestrator.agents)}")
        print(f"   Available agents: {orchestrator._available_agents}")
        print(f"\n🔍 Agents created:")
        for agent_name in orchestrator.agents.keys():
            print(f"   - {agent_name}")

        # Verify payroll agent was NOT created
        if "payroll_agent" in orchestrator.agents:
            print("\n❌ ERROR: Payroll agent was created but should be blocked!")
            return False
        else:
            print("\n✅ SUCCESS: Payroll agent correctly blocked")

        # Verify other agents were created
        expected_agents = ["supervisor_agent", "general_knowledge_agent", "tax_documents_agent", "settings_agent"]
        missing = [a for a in expected_agents if a not in orchestrator.agents]
        if missing:
            print(f"❌ ERROR: Missing expected agents: {missing}")
            return False
        else:
            print("✅ SUCCESS: All expected agents created")

    return True


async def main():
    """Run test."""
    print("\n🧪 Orchestrator Subscription Validation Test")
    print("=" * 80)

    try:
        success = await test_orchestrator_creation()

        print("\n" + "=" * 80)
        if success:
            print("✅ TEST PASSED")
            print("\n🎉 Orchestrator correctly respects subscription limits!")
            return 0
        else:
            print("❌ TEST FAILED")
            return 1

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
