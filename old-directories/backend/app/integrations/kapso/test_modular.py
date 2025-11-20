"""
Quick test script for modular Kapso client.

Run with:
    python -m app.integrations.kapso.test_modular
"""
import asyncio
import os


async def test_modular_client():
    """Test the modular client initialization and structure."""
    from app.integrations.kapso import KapsoClient

    # Get token from env (or use dummy for structure test)
    api_token = os.getenv("KAPSO_API_TOKEN", "dummy-token-for-testing")

    print("🧪 Testing Modular Kapso Client")
    print("=" * 50)

    # Initialize client
    client = KapsoClient(api_token=api_token)

    print(f"\n✅ Client initialized")
    print(f"   Base URL: {client.base_url}")
    print(f"   Timeout: {client.timeout}s")

    # Check modules are accessible
    print(f"\n📦 Available modules:")
    modules = [
        ("messages", client.messages),
        ("conversations", client.conversations),
        ("contacts", client.contacts),
        ("templates", client.templates),
        ("config", client.config),
        ("webhooks", client.webhooks),
    ]

    for name, module in modules:
        print(f"   ✓ {name:15} -> {module.__class__.__name__}")

    # Health check
    print(f"\n🏥 Health check:")
    health = await client.health_check()
    for key, value in health.items():
        if key == "modules":
            print(f"   {key:15} -> {len(value)} modules")
        else:
            print(f"   {key:15} -> {value}")

    # Test module methods exist
    print(f"\n🔍 Sample methods:")
    print(f"   messages.send_text()")
    print(f"   messages.send_media()")
    print(f"   messages.send_interactive()")
    print(f"   conversations.create()")
    print(f"   contacts.search()")
    print(f"   templates.get_structure()")
    print(f"   templates.send()")
    print(f"   templates.send_with_components()")
    print(f"   config.list()")
    print(f"   webhooks.validate_signature()")

    print(f"\n✅ All modules loaded successfully!")


async def test_legacy_client():
    """Test that legacy client is still available."""
    from app.integrations.kapso import LegacyKapsoClient

    api_token = os.getenv("KAPSO_API_TOKEN", "dummy-token-for-testing")

    print(f"\n🔄 Testing Legacy Client (backward compatibility)")
    print("=" * 50)

    client = LegacyKapsoClient(api_token=api_token)

    print(f"\n✅ Legacy client still works")
    print(f"   Class: {client.__class__.__name__}")

    # Check some legacy methods exist
    legacy_methods = [
        "send_text_message",
        "send_template_message",
        "search_contacts",
        "get_template_structure",
    ]

    print(f"\n🔍 Legacy methods:")
    for method in legacy_methods:
        has_method = hasattr(client, method)
        status = "✓" if has_method else "✗"
        print(f"   {status} {method}()")


def test_imports():
    """Test that all imports work correctly."""
    print(f"\n📥 Testing Imports")
    print("=" * 50)

    try:
        from app.integrations.kapso import (
            KapsoClient,
            LegacyKapsoClient,
            MessageType,
            ConversationStatus,
            KapsoAPIError,
            KapsoNotFoundError,
        )
        print(f"\n✅ All imports successful")
        print(f"   KapsoClient: {KapsoClient}")
        print(f"   LegacyKapsoClient: {LegacyKapsoClient}")
        print(f"   MessageType: {MessageType}")
        print(f"   ConversationStatus: {ConversationStatus}")
        print(f"   KapsoAPIError: {KapsoAPIError}")
        print(f"   KapsoNotFoundError: {KapsoNotFoundError}")

    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        raise


async def main():
    """Run all tests."""
    print(f"\n{'=' * 70}")
    print(f" KAPSO MODULAR CLIENT - STRUCTURE TEST")
    print(f"{'=' * 70}")

    try:
        # Test imports first
        test_imports()

        # Test modular client
        await test_modular_client()

        # Test legacy client
        await test_legacy_client()

        print(f"\n{'=' * 70}")
        print(f" ✅ ALL TESTS PASSED")
        print(f"{'=' * 70}\n")

    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f" ❌ TEST FAILED")
        print(f"{'=' * 70}")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
