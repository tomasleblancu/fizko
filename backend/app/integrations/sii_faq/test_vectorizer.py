"""
Test script for SII FAQ vectorization with OpenAI

Usage:
    # Create vector store from existing extraction
    python -m app.integrations.sii_faq.test_vectorizer --from-directory output/20251110_115900 --name "SII FAQs Test"

    # Extract and vectorize (limit for testing)
    python -m app.integrations.sii_faq.test_vectorizer --extract --limit 2 --name "SII FAQs - 2 Topics"

    # List existing vector stores
    python -m app.integrations.sii_faq.test_vectorizer --list

    # Delete a vector store
    python -m app.integrations.sii_faq.test_vectorizer --delete vs_abc123
"""

import argparse
import logging
from pathlib import Path

from app.integrations.sii_faq.vectorizer import FAQVectorizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_vectorize_from_directory(directory: str, name: str):
    """Test vectorizing an existing extraction"""
    print(f"\n📥 Vectorizing from directory: {directory}")
    print(f"   Vector store name: {name}")

    vectorizer = FAQVectorizer()

    try:
        vector_store = vectorizer.vectorize_from_directory(
            directory=directory,
            name=name,
            expires_after_days=30
        )

        print("\n✅ Vector store created successfully!")
        print(f"   Vector Store ID: {vector_store.vector_store_id}")
        print(f"   Name: {vector_store.name}")
        print(f"   Status: {vector_store.status}")
        print(f"   File counts: {vector_store.file_counts}")
        print(f"   Created at: {vector_store.created_at}")

        print("\n💡 Use this vector_store_id in your agent configuration:")
        print(f"   vector_store_id = '{vector_store.vector_store_id}'")

        return vector_store

    except Exception as e:
        print(f"\n❌ Failed to create vector store: {e}")
        logger.error(f"Vectorization failed", exc_info=True)
        return None


def test_extract_and_vectorize(limit: int, name: str):
    """Test extracting FAQs and creating vector store"""
    print(f"\n📥 Extracting FAQs (limit={limit}) and creating vector store")
    print(f"   Vector store name: {name}")

    vectorizer = FAQVectorizer()

    try:
        vector_store = vectorizer.extract_and_vectorize(
            name=name,
            limit_topics=limit,
            expires_after_days=30
        )

        print("\n✅ Extraction and vectorization completed!")
        print(f"   Vector Store ID: {vector_store.vector_store_id}")
        print(f"   Name: {vector_store.name}")
        print(f"   Status: {vector_store.status}")
        print(f"   File counts: {vector_store.file_counts}")
        print(f"   Created at: {vector_store.created_at}")

        print("\n💡 Use this vector_store_id in your agent configuration:")
        print(f"   vector_store_id = '{vector_store.vector_store_id}'")

        return vector_store

    except Exception as e:
        print(f"\n❌ Failed to extract and vectorize: {e}")
        logger.error(f"Extraction failed", exc_info=True)
        return None


def test_list_vector_stores():
    """List all vector stores"""
    print("\n📋 Listing all vector stores...")

    vectorizer = FAQVectorizer()

    try:
        vector_stores = vectorizer.list_vector_stores()

        if not vector_stores:
            print("   No vector stores found")
            return []

        print(f"\n✅ Found {len(vector_stores)} vector stores:\n")

        for i, vs in enumerate(vector_stores, 1):
            print(f"{i}. {vs.name}")
            print(f"   ID: {vs.vector_store_id}")
            print(f"   Status: {vs.status}")
            print(f"   Files: {vs.file_counts}")
            print(f"   Created: {vs.created_at}")
            if vs.metadata:
                print(f"   Metadata: {vs.metadata}")
            print()

        return vector_stores

    except Exception as e:
        print(f"\n❌ Failed to list vector stores: {e}")
        logger.error(f"List failed", exc_info=True)
        return []


def test_delete_vector_store(vector_store_id: str):
    """Delete a vector store"""
    print(f"\n🗑️  Deleting vector store: {vector_store_id}")

    response = input("Are you sure? This cannot be undone. (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return False

    vectorizer = FAQVectorizer()

    try:
        success = vectorizer.delete_vector_store(vector_store_id)

        if success:
            print("✅ Vector store deleted successfully")
        else:
            print("❌ Failed to delete vector store")

        return success

    except Exception as e:
        print(f"\n❌ Failed to delete: {e}")
        logger.error(f"Delete failed", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Test SII FAQ vectorization with OpenAI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Vectorize existing extraction
  python -m app.integrations.sii_faq.test_vectorizer \\
      --from-directory app/integrations/sii_faq/output/20251110_115900 \\
      --name "SII FAQs Test"

  # Extract and vectorize (with limit)
  python -m app.integrations.sii_faq.test_vectorizer \\
      --extract --limit 2 \\
      --name "SII FAQs - 2 Topics"

  # List all vector stores
  python -m app.integrations.sii_faq.test_vectorizer --list

  # Delete a vector store
  python -m app.integrations.sii_faq.test_vectorizer --delete vs_abc123
        """
    )

    parser.add_argument(
        '--from-directory',
        type=str,
        help='Path to extraction directory to vectorize'
    )
    parser.add_argument(
        '--extract',
        action='store_true',
        help='Extract FAQs before vectorizing'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of topics to extract (only with --extract)'
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Name for the vector store'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all vector stores'
    )
    parser.add_argument(
        '--delete',
        type=str,
        metavar='VECTOR_STORE_ID',
        help='Delete a vector store by ID'
    )

    args = parser.parse_args()

    try:
        if args.list:
            # List vector stores
            test_list_vector_stores()

        elif args.delete:
            # Delete vector store
            test_delete_vector_store(args.delete)

        elif args.extract:
            # Extract and vectorize
            if not args.name:
                print("❌ Error: --name is required with --extract")
                return

            if args.limit:
                test_extract_and_vectorize(args.limit, args.name)
            else:
                print("⚠️  No --limit specified. This will extract ALL topics (may take 10-30 minutes).")
                response = input("Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    return
                test_extract_and_vectorize(None, args.name)

        elif args.from_directory:
            # Vectorize from directory
            if not args.name:
                print("❌ Error: --name is required with --from-directory")
                return

            test_vectorize_from_directory(args.from_directory, args.name)

        else:
            parser.print_help()
            return

        print("\n✅ Test completed!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    main()
