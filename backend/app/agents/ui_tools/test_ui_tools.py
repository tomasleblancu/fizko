#!/usr/bin/env python3
"""
Test script for UI Tools system.

Run this to verify UI tools are working correctly:
    python3 test_ui_tools.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


async def test_registry():
    """Test that tools are registered correctly."""
    from app.agents.ui_tools import ui_tool_registry

    print("\n" + "="*60)
    print("TEST 1: Registry")
    print("="*60)

    tools = ui_tool_registry.list_tools()

    if not tools:
        print("❌ FAILED: No tools registered!")
        return False

    print(f"✅ PASSED: {len(tools)} tools registered\n")

    for name, domain, desc in tools:
        print(f"  ✓ {name:20s} | {domain:15s}")
        print(f"    └─ {desc[:60]}...")

    return True


async def test_dispatcher():
    """Test dispatcher routing."""
    from app.agents.ui_tools import UIToolDispatcher

    print("\n" + "="*60)
    print("TEST 2: Dispatcher")
    print("="*60)

    # Test 1: Valid component
    print("\n→ Testing contact_card...")
    result = await UIToolDispatcher.dispatch(
        ui_component="contact_card",
        user_message="Test message",
        company_id="test-company-id",
    )

    if result and not result.success:
        print(f"  ℹ️  Expected failure (no DB): {result.error[:50]}...")
        print("  ✅ PASSED: Dispatcher routed correctly")
    elif result:
        print("  ⚠️  WARNING: Got success without DB (unexpected)")
    else:
        print("  ❌ FAILED: No result returned")
        return False

    # Test 2: Unknown component
    print("\n→ Testing unknown_component...")
    result = await UIToolDispatcher.dispatch(
        ui_component="unknown_component",
        user_message="Test message",
    )

    if result and not result.success:
        print(f"  ℹ️  Expected failure: {result.error[:50]}...")
        print("  ✅ PASSED: Unknown component handled correctly")
    else:
        print("  ❌ FAILED: Should have failed for unknown component")
        return False

    # Test 3: Null component
    print("\n→ Testing null component...")
    result = await UIToolDispatcher.dispatch(
        ui_component=None,
        user_message="Test message",
    )

    if result is None:
        print("  ✅ PASSED: Null component skipped correctly")
    else:
        print("  ❌ FAILED: Should return None for null component")
        return False

    return True


async def test_tool_interfaces():
    """Test that tools implement the interface correctly."""
    from app.agents.ui_tools import ui_tool_registry

    print("\n" + "="*60)
    print("TEST 3: Tool Interfaces")
    print("="*60)

    tools_dict = ui_tool_registry._tools
    all_passed = True

    for component_name, tool in tools_dict.items():
        print(f"\n→ Testing {tool.__class__.__name__}...")

        # Check required properties
        try:
            name = tool.component_name
            desc = tool.description
            domain = tool.domain

            assert isinstance(name, str), "component_name must be string"
            assert isinstance(desc, str), "description must be string"
            assert isinstance(domain, str), "domain must be string"
            assert len(name) > 0, "component_name cannot be empty"

            print(f"  ✓ component_name: {name}")
            print(f"  ✓ description: {desc[:50]}...")
            print(f"  ✓ domain: {domain}")

            # Check process method exists
            assert hasattr(tool, 'process'), "Must have process method"
            assert callable(tool.process), "process must be callable"

            print(f"  ✓ process method exists")
            print(f"  ✅ PASSED")

        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            all_passed = False
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            all_passed = False

    return all_passed


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 UI TOOLS SYSTEM TEST SUITE")
    print("="*60)

    results = []

    # Run tests
    results.append(("Registry", await test_registry()))
    results.append(("Dispatcher", await test_dispatcher()))
    results.append(("Tool Interfaces", await test_tool_interfaces()))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")

    print()
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        return 0
    else:
        print(f"⚠️  Some tests failed ({passed}/{total})")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
