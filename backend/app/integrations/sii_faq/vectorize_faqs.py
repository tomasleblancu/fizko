"""
Simple script for SII FAQ vectorization with OpenAI

Usage:
    # Show available versions and select one to vectorize
    python -m app.integrations.sii_faq.vectorize_faqs

    # Vectorize specific version
    python -m app.integrations.sii_faq.vectorize_faqs --version 20251110_115900

    # Extract new FAQs and vectorize (with limit)
    python -m app.integrations.sii_faq.vectorize_faqs --extract --limit 2
"""

import argparse
import logging
import re
from pathlib import Path
from typing import Optional

from app.integrations.sii_faq.vectorizer import FAQVectorizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("app/integrations/sii_faq/output")


def list_available_versions():
    """
    List available extraction versions with metadata

    Returns:
        List of tuples (version_dir, is_latest, topic_count, question_count)
    """
    if not OUTPUT_DIR.exists():
        return []

    # Find all versioned directories
    versions = [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]

    if not versions:
        return []

    # Sort by name (timestamp) descending
    versions.sort(key=lambda x: x.name, reverse=True)

    results = []
    for i, version_dir in enumerate(versions):
        is_latest = (i == 0)

        # Try to get topic/question count from INDEX.md
        topic_count = 0
        question_count = 0
        index_file = version_dir / "INDEX.md"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
                topics_match = re.search(r'\*\*Total de temas:\*\* (\d+)', content)
                questions_match = re.search(r'\*\*Total de preguntas:\*\* (\d+)', content)
                if topics_match:
                    topic_count = int(topics_match.group(1))
                if questions_match:
                    question_count = int(questions_match.group(1))

        results.append((version_dir, is_latest, topic_count, question_count))

    return results


def show_versions_and_prompt():
    """
    Show available versions and prompt user to select one

    Returns:
        Selected version directory path or None
    """
    versions_info = list_available_versions()

    if not versions_info:
        print("\n❌ No extraction versions found in app/integrations/sii_faq/output/")
        print("   Run extraction first:")
        print("   python -m app.integrations.sii_faq.extract_faqs --limit 2 --export-md")
        return None

    print("\n📁 Available extraction versions:\n")

    for i, (version_dir, is_latest, topic_count, question_count) in enumerate(versions_info):
        marker = " (latest)" if is_latest else ""
        info = f"{topic_count} topics, {question_count} questions" if topic_count > 0 else "no metadata"
        print(f"  {i+1}. {version_dir.name}{marker} - {info}")

    print()

    # Prompt for selection
    while True:
        choice = input(f"Select version (1-{len(versions_info)}) or 'q' to quit: ").strip().lower()

        if choice == 'q':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(versions_info):
                return versions_info[idx][0]
            else:
                print(f"❌ Invalid choice. Please enter a number between 1 and {len(versions_info)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q'")


def vectorize_version(version_dir: Path):
    """Vectorize a specific version"""
    print(f"\n📥 Vectorizing: {version_dir.name}")

    # Prompt for name
    default_name = f"SII FAQs - {version_dir.name}"
    name = input(f"Vector store name [{default_name}]: ").strip()
    if not name:
        name = default_name

    print(f"\n🚀 Creating vector store '{name}'...")

    vectorizer = FAQVectorizer()

    try:
        vector_store = vectorizer.vectorize_from_directory(
            directory=version_dir,
            name=name,
            expires_after_days=30
        )

        print("\n✅ Vector store created successfully!")
        print(f"   Vector Store ID: {vector_store.vector_store_id}")
        print(f"   Name: {vector_store.name}")
        print(f"   Status: {vector_store.status}")
        print(f"   Files: {vector_store.file_counts}")
        print(f"   Created: {vector_store.created_at}")

        print("\n💡 Use this in your agent configuration:")
        print(f"   vector_store_id = '{vector_store.vector_store_id}'")

        return vector_store

    except Exception as e:
        print(f"\n❌ Failed to create vector store: {e}")
        logger.error(f"Vectorization failed", exc_info=True)
        return None


def extract_and_vectorize(limit: Optional[int] = None):
    """Extract new FAQs and vectorize"""
    if limit:
        name = f"SII FAQs - {limit} topics"
    else:
        name = "SII FAQs - Complete"

    # Prompt for confirmation if extracting all
    if not limit:
        print("\n⚠️  WARNING: Extracting ALL topics may take 10-30 minutes")
        response = input("Continue? (y/N): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return None

    # Allow custom name
    custom_name = input(f"Vector store name [{name}]: ").strip()
    if custom_name:
        name = custom_name

    print(f"\n🚀 Extracting FAQs (limit={limit or 'all'}) and creating vector store '{name}'...")

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
        print(f"   Files: {vector_store.file_counts}")
        print(f"   Created: {vector_store.created_at}")

        print("\n💡 Use this in your agent configuration:")
        print(f"   vector_store_id = '{vector_store.vector_store_id}'")

        return vector_store

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        logger.error(f"Failed", exc_info=True)
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Vectorize SII FAQs for OpenAI file search',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode - select version to vectorize
  python -m app.integrations.sii_faq.vectorize_faqs

  # Vectorize specific version
  python -m app.integrations.sii_faq.vectorize_faqs --version 20251110_115900

  # Extract and vectorize (with limit)
  python -m app.integrations.sii_faq.vectorize_faqs --extract --limit 2

  # Extract and vectorize all topics
  python -m app.integrations.sii_faq.vectorize_faqs --extract
        """
    )

    parser.add_argument(
        '--version',
        type=str,
        help='Specific version to vectorize (e.g., 20251110_115900)'
    )
    parser.add_argument(
        '--extract',
        action='store_true',
        help='Extract new FAQs before vectorizing'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of topics to extract (only with --extract)'
    )

    args = parser.parse_args()

    try:
        if args.extract:
            # Extract new FAQs and vectorize
            extract_and_vectorize(args.limit)

        elif args.version:
            # Vectorize specific version
            version_dir = OUTPUT_DIR / args.version
            if not version_dir.exists():
                print(f"\n❌ Version not found: {args.version}")
                print(f"   Looking in: {version_dir}")
                return

            vectorize_version(version_dir)

        else:
            # Interactive mode - show versions and prompt
            version_dir = show_versions_and_prompt()
            if version_dir:
                vectorize_version(version_dir)
            else:
                print("\nCancelled.")

        print("\n✅ Done!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        print(f"\n❌ Failed: {e}")


if __name__ == "__main__":
    main()
