"""
Test script for new classification-based chat system.

Tests the new AgentRunnerV2 flow:
1. User message → Classifier Agent → Returns agent_name
2. Agent_name → Specialized Agent → Processes with full history
"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.chat import ChatService


async def test_chat_flow():
    """Test the new chat system with classification-based routing."""

    print("=" * 80)
    print("🧪 TESTING NEW CLASSIFICATION-BASED CHAT SYSTEM")
    print("=" * 80)
    print()

    # Initialize service
    print("1️⃣ Initializing ChatService with AgentRunnerV2...")
    service = ChatService()
    print(f"   ✅ Service initialized")
    print(f"   - OpenAI client: {service.openai_client}")
    print(f"   - Runner type: {type(service.runner).__name__}")
    print()

    # Test cases
    test_cases = [
        {
            "name": "Greeting (should route to general_knowledge)",
            "message": "Hola",
            "thread_id": "test_thread_1",
        },
        {
            "name": "Tax question (should route to tax_documents)",
            "message": "¿Cuántas facturas tengo?",
            "thread_id": "test_thread_2",
        },
        {
            "name": "F29 question (should route to monthly_taxes)",
            "message": "¿Cuánto debo pagar en mi F29?",
            "thread_id": "test_thread_3",
        },
        {
            "name": "Follow-up question (should see full history)",
            "message": "Y el mes pasado?",
            "thread_id": "test_thread_3",  # Same thread as previous
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}️⃣ TEST: {test_case['name']}")
        print(f"   Message: \"{test_case['message']}\"")
        print(f"   Thread: {test_case['thread_id']}")
        print()

        try:
            result = await service.execute(
                message=test_case["message"],
                thread_id=test_case["thread_id"],
                user_id="test_user",
                company_id=None,
            )

            print(f"   ✅ SUCCESS")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Elapsed: {result['metadata']['elapsed_ms']}ms")
            print(f"   Characters: {result['metadata']['char_count']}")
            print()

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 80)
    print("🏁 TESTS COMPLETE")
    print("=" * 80)
    print()
    print("Expected behavior:")
    print("  1. NO 'For context...' messages in agent responses")
    print("  2. All agents see full thread history from SQLite session")
    print("  3. Classifier routes to appropriate specialized agent")
    print("  4. Follow-up questions maintain context")
    print()


if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("   Please set it before running this test:")
        print("   export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    # Run test
    asyncio.run(test_chat_flow())
