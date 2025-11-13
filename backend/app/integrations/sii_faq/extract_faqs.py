"""
Script for extracting FAQs from SII website

Usage:
    # Extract all FAQs (10-30 minutes)
    python -m app.integrations.sii_faq.extract_faqs --export-md

    # Extract limited number of topics
    python -m app.integrations.sii_faq.extract_faqs --limit 2 --export-md

    # Search for specific topic
    python -m app.integrations.sii_faq.extract_faqs --search "IVA" --export-md
"""

import argparse
import logging
import json
from typing import List

from app.integrations.sii_faq import SIIFAQClient, FAQTopic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_topic_summary(topics: List[FAQTopic]):
    """Print a summary of extracted topics"""
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)

    total_questions = 0
    for topic in topics:
        subtopic_count = len(topic.subtopics)
        questions = topic.get_all_questions()
        question_count = len(questions)
        total_questions += question_count

        print(f"\n📁 {topic.name}")
        print(f"   URL: {topic.url}")
        print(f"   Subtopics: {subtopic_count}")
        print(f"   Questions: {question_count}")

        # Show first few subtopics
        for i, subtopic in enumerate(topic.subtopics[:3]):
            print(f"      └─ {subtopic.name} ({len(subtopic.questions)} questions)")
        if len(topic.subtopics) > 3:
            print(f"      └─ ... and {len(topic.subtopics) - 3} more subtopics")

    print("\n" + "="*80)
    print(f"TOTALS: {len(topics)} topics, {total_questions} questions")
    print("="*80 + "\n")


def print_question_sample(topics: List[FAQTopic], limit: int = 5):
    """Print a sample of extracted questions"""
    print("\n" + "="*80)
    print(f"QUESTION SAMPLES (first {limit})")
    print("="*80)

    count = 0
    for topic in topics:
        for question in topic.get_all_questions():
            if count >= limit:
                break

            print(f"\n[{count + 1}] {question.topic_name} > {question.subtopic_name}")
            print(f"    ID: {question.id}")
            print(f"    URL: {question.url}")
            print(f"    Q: {question.question[:100]}...")
            print(f"    A: {question.answer[:150]}...")
            if question.created_at:
                print(f"    Created: {question.created_at.strftime('%Y-%m-%d')}")
            if question.updated_at:
                print(f"    Updated: {question.updated_at.strftime('%Y-%m-%d')}")

            count += 1
        if count >= limit:
            break

    print("\n" + "="*80 + "\n")


def test_topics_summary():
    """Test getting topics summary"""
    print("\n🔍 Testing topics summary...")
    with SIIFAQClient() as client:
        summary = client.get_topics_summary()

        print("\nTopics list:")
        for i, topic in enumerate(summary[:10], 1):
            print(f"  {i}. {topic['name']}")
        if len(summary) > 10:
            print(f"  ... and {len(summary) - 10} more")

        return summary


def test_full_extraction(limit: int = None, export_md: bool = False):
    """Test full FAQ extraction"""
    print(f"\n📥 Testing full extraction (limit={limit or 'all'})...")
    with SIIFAQClient() as client:
        topics = client.extract_all_faqs(limit_topics=limit)
        print(f"✅ Extracted {len(topics)} topics")

        print_topic_summary(topics)
        print_question_sample(topics)

        # Export to Markdown if requested
        if export_md:
            print("\n💾 Exporting to Markdown...")
            version_dir = client.export_to_markdown(topics)
            print(f"✅ Exported to: {version_dir}")
            print(f"   - Open INDEX.md to see all files")

        return topics


def test_search(query: str, topics: List[FAQTopic] = None):
    """Test question search"""
    print(f"\n🔎 Testing search for: '{query}'...")
    with SIIFAQClient() as client:
        results = client.search_questions(query, topics=topics)

        if results:
            print("\nSearch results:")
            for i, question in enumerate(results[:10], 1):
                print(f"\n[{i}] {question.topic_name} > {question.subtopic_name}")
                print(f"    Q: {question.question[:80]}...")
                print(f"    URL: {question.url}")
            if len(results) > 10:
                print(f"\n... and {len(results) - 10} more results")

        return results


def export_to_json(topics: List[FAQTopic], filename: str = "sii_faqs.json"):
    """Export extracted FAQs to JSON file"""
    print(f"\n💾 Exporting to {filename}...")

    data = []
    for topic in topics:
        topic_data = {
            "topic_name": topic.name,
            "topic_url": topic.url,
            "subtopics": []
        }

        for subtopic in topic.subtopics:
            subtopic_data = {
                "subtopic_name": subtopic.name,
                "subtopic_url": subtopic.url,
                "questions": []
            }

            for question in subtopic.questions:
                question_data = {
                    "id": question.id,
                    "question": question.question,
                    "answer": question.answer,
                    "url": question.url,
                    "created_at": question.created_at.isoformat() if question.created_at else None,
                    "updated_at": question.updated_at.isoformat() if question.updated_at else None,
                }
                subtopic_data["questions"].append(question_data)

            topic_data["subtopics"].append(subtopic_data)

        data.append(topic_data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Exported to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Test SII FAQ extraction')
    parser.add_argument('--limit', type=int, help='Limit number of topics to extract')
    parser.add_argument('--search', type=str, help='Search for questions matching query')
    parser.add_argument('--export', type=str, help='Export to JSON file')
    parser.add_argument('--export-md', action='store_true', help='Export to Markdown files (versioned)')
    parser.add_argument('--summary-only', action='store_true', help='Only show topics summary')
    args = parser.parse_args()

    try:
        if args.summary_only:
            # Just show topics summary
            test_topics_summary()
        elif args.search:
            # Extract and search
            if args.limit:
                topics = test_full_extraction(limit=args.limit, export_md=args.export_md)
            else:
                print("⚠️  No limit specified. This will extract ALL topics (may take 10-30 minutes).")
                response = input("Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    return
                topics = test_full_extraction(export_md=args.export_md)

            test_search(args.search, topics=topics)

            if args.export:
                export_to_json(topics, args.export)
        else:
            # Standard extraction test
            if args.limit:
                topics = test_full_extraction(limit=args.limit, export_md=args.export_md)
            else:
                print("⚠️  No limit specified. This will extract ALL topics (may take 10-30 minutes).")
                response = input("Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    return
                topics = test_full_extraction(export_md=args.export_md)

            if args.export:
                export_to_json(topics, args.export)

        print("\n✅ All tests completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    main()
