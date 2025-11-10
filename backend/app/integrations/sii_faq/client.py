"""
Unified client for SII FAQ extraction
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import re

from app.integrations.sii_faq.scrapers import SIIFAQScraper
from app.integrations.sii_faq.models import FAQTopic, FAQSubtopic, FAQQuestion

logger = logging.getLogger(__name__)


class SIIFAQClient:
    """
    Unified client for extracting FAQs from SII website

    Usage:
        # Extract all FAQs
        client = SIIFAQClient()
        topics = client.extract_all_faqs()
        client.close()

        # Or use context manager
        with SIIFAQClient() as client:
            topics = client.extract_all_faqs()
    """

    def __init__(self, output_dir: str = None):
        self.scraper = SIIFAQScraper()
        # Default output directory: app/integrations/sii_faq/output
        if output_dir is None:
            # Get the directory where this file is located
            module_dir = Path(__file__).parent
            self.output_dir = str(module_dir / "output")
        else:
            self.output_dir = output_dir

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _process_subtopic_recursive(
        self, subtopic_url: str, subtopic_name: str, topic_name: str
    ) -> Optional[FAQSubtopic]:
        """
        Recursively process a subtopic page, handling nested subtopics if present.

        Args:
            subtopic_url: URL of the subtopic page
            subtopic_name: Name of the subtopic
            topic_name: Name of the parent topic

        Returns:
            FAQSubtopic object with either questions or nested_subtopics populated
        """
        # Fetch the page HTML first to check structure
        html = self.scraper._fetch_html(subtopic_url)
        if not html:
            logger.error(f"Failed to fetch subtopic page: {subtopic_url}")
            return None

        subtopic = FAQSubtopic(
            name=subtopic_name,
            url=subtopic_url,
            topic_name=topic_name,
            questions=[],
            nested_subtopics=[]
        )

        # Check if this page has nested subtopics or questions
        if self.scraper._has_nested_subtopics(html):
            # This page has more subtopics - recursively process them
            logger.info(f"    → {subtopic_name} has nested subtopics")
            nested_subtopic_dicts = self.scraper.scrape_subtopics(subtopic_url, topic_name)

            for nested_dict in nested_subtopic_dicts:
                nested_name = nested_dict['name']
                nested_url = nested_dict['url']
                logger.info(f"      Processing nested subtopic: {nested_name}")

                nested_subtopic = self._process_subtopic_recursive(
                    nested_url, nested_name, topic_name
                )
                if nested_subtopic:
                    subtopic.nested_subtopics.append(nested_subtopic)
        else:
            # This page has questions - extract them
            logger.info(f"    → {subtopic_name} has questions")
            question_list = self.scraper.scrape_questions_list(
                subtopic_url, subtopic_name, topic_name
            )

            # For each question, get full detail
            for question_dict in question_list:
                question_url = question_dict['url']
                detail = self.scraper.scrape_question_detail(question_url)

                if detail:
                    # Parse dates
                    created_at = None
                    updated_at = None
                    try:
                        if detail['created_at']:
                            created_at = datetime.strptime(detail['created_at'], '%d/%m/%Y')
                    except Exception as e:
                        logger.warning(f"Could not parse created_at: {e}")

                    try:
                        if detail['updated_at']:
                            updated_at = datetime.strptime(detail['updated_at'], '%d/%m/%Y')
                    except Exception as e:
                        logger.warning(f"Could not parse updated_at: {e}")

                    question = FAQQuestion(
                        id=detail['id'],
                        question=detail['question'],
                        answer=detail['answer'],
                        subtopic_id=subtopic_url,
                        subtopic_name=subtopic_name,
                        topic_name=topic_name,
                        url=question_url,
                        created_at=created_at,
                        updated_at=updated_at
                    )
                    subtopic.questions.append(question)

        return subtopic

    def extract_all_faqs(self, limit_topics: Optional[int] = None) -> List[FAQTopic]:
        """
        Extract all FAQs from the SII website

        Args:
            limit_topics: Optional limit on number of topics to process (for testing)

        Returns:
            List of FAQTopic objects with full hierarchy
        """
        logger.info("Starting full FAQ extraction...")

        # Step 1: Get main topics
        topic_dicts = self.scraper.scrape_main_topics()
        if limit_topics:
            topic_dicts = topic_dicts[:limit_topics]
            logger.info(f"Limited to {limit_topics} topics for testing")

        topics = []

        # Step 2: For each topic, get subtopics
        for topic_dict in topic_dicts:
            topic_name = topic_dict['name']
            topic_url = topic_dict['url']

            logger.info(f"Processing topic: {topic_name}")
            topic = FAQTopic(name=topic_name, url=topic_url, subtopics=[])

            subtopic_dicts = self.scraper.scrape_subtopics(topic_url, topic_name)

            # Step 3: For each subtopic, recursively process it
            for subtopic_dict in subtopic_dicts:
                subtopic_name = subtopic_dict['name']
                subtopic_url = subtopic_dict['url']

                logger.info(f"  Processing subtopic: {subtopic_name}")
                subtopic = self._process_subtopic_recursive(
                    subtopic_url, subtopic_name, topic_name
                )
                if subtopic:
                    topic.subtopics.append(subtopic)

            topics.append(topic)

        logger.info(f"Extraction complete. {len(topics)} topics processed.")
        return topics

    def extract_topic(self, topic_name: str) -> Optional[FAQTopic]:
        """
        Extract FAQs for a specific topic by name

        Args:
            topic_name: Name of the topic to extract

        Returns:
            FAQTopic object or None if not found
        """
        logger.info(f"Extracting specific topic: {topic_name}")
        topic_dicts = self.scraper.scrape_main_topics()

        # Find matching topic
        topic_dict = None
        for t in topic_dicts:
            if t['name'].lower() == topic_name.lower():
                topic_dict = t
                break

        if not topic_dict:
            logger.error(f"Topic not found: {topic_name}")
            return None

        # Extract just this topic
        topics = self.extract_all_faqs(limit_topics=1)
        return topics[0] if topics else None

    def search_questions(self, query: str, topics: Optional[List[FAQTopic]] = None) -> List[FAQQuestion]:
        """
        Search for questions matching a query string

        Args:
            query: Search query (case-insensitive)
            topics: Optional list of topics to search. If None, will extract all topics first.

        Returns:
            List of matching FAQQuestion objects
        """
        logger.info(f"Searching questions for: {query}")

        if topics is None:
            topics = self.extract_all_faqs()

        query_lower = query.lower()
        results = []

        for topic in topics:
            for question in topic.get_all_questions():
                # Search in question text and answer
                if (query_lower in question.question.lower() or
                    query_lower in question.answer.lower()):
                    results.append(question)

        logger.info(f"Found {len(results)} matching questions")
        return results

    def get_topics_summary(self) -> List[dict]:
        """
        Get a summary of all available topics (without full extraction)

        Returns:
            List of dicts with topic names and URLs
        """
        return self.scraper.scrape_main_topics()

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be used as a filename

        Args:
            name: String to sanitize

        Returns:
            Safe filename string
        """
        # Replace special characters with underscores
        safe = re.sub(r'[^\w\s-]', '', name)
        # Replace spaces with underscores
        safe = re.sub(r'[-\s]+', '_', safe)
        # Limit length
        safe = safe[:200]
        return safe.lower()

    def _create_version_directory(self) -> Path:
        """
        Create a versioned output directory

        Returns:
            Path to the versioned directory
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_dir = Path(self.output_dir) / timestamp
        version_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created version directory: {version_dir}")
        return version_dir

    def _export_subtopic_to_markdown(self, subtopic: FAQSubtopic, output_path: Path):
        """
        Export a subtopic with all its questions to a Markdown file.
        Includes questions from nested subtopics if present.

        Args:
            subtopic: FAQSubtopic object to export
            output_path: Path where to save the .md file
        """
        # Get all questions including nested subtopics
        all_questions = subtopic.get_all_questions()

        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# {subtopic.topic_name}\n\n")
            f.write(f"## {subtopic.name}\n\n")
            f.write(f"**URL:** {subtopic.url}\n\n")
            f.write(f"**Total de preguntas:** {len(all_questions)}\n\n")
            f.write("---\n\n")

            # Questions
            for i, question in enumerate(all_questions, 1):
                f.write(f"### {i}. {question.question}\n\n")

                # Metadata (compact format with single line breaks)
                f.write(f"ID: {question.id}  \n")
                if question.created_at:
                    f.write(f"Fecha de creación: {question.created_at.strftime('%d/%m/%Y')}  \n")
                if question.updated_at:
                    f.write(f"Fecha de actualización: {question.updated_at.strftime('%d/%m/%Y')}  \n")
                f.write(f"URL: {question.url}\n\n")

                # Answer
                f.write(f"#### Respuesta\n\n")
                f.write(f"{question.answer}\n\n")
                f.write("---\n\n")

        logger.debug(f"Exported subtopic to {output_path}")

    def export_to_markdown(self, topics: List[FAQTopic], version_dir: Optional[Path] = None) -> Path:
        """
        Export all topics to Markdown files organized by subtopic

        Args:
            topics: List of FAQTopic objects to export
            version_dir: Optional version directory. If None, creates a new one.

        Returns:
            Path to the version directory where files were exported
        """
        if version_dir is None:
            version_dir = self._create_version_directory()

        logger.info(f"Exporting {len(topics)} topics to Markdown...")

        # Create index file
        index_path = version_dir / "INDEX.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# SII FAQs - Índice\n\n")
            f.write(f"**Fecha de extracción:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total de temas:** {len(topics)}\n\n")

            total_subtopics = sum(len(t.subtopics) for t in topics)
            total_questions = sum(len(t.get_all_questions()) for t in topics)
            f.write(f"**Total de subtemas:** {total_subtopics}\n\n")
            f.write(f"**Total de preguntas:** {total_questions}\n\n")
            f.write("---\n\n")

            # Table of contents
            f.write("## Tabla de Contenidos\n\n")

            for topic in topics:
                f.write(f"### {topic.name}\n\n")
                f.write(f"**URL:** {topic.url}\n\n")
                f.write(f"**Subtemas:** {len(topic.subtopics)}\n\n")

                for subtopic in topic.subtopics:
                    # Generate filename for this subtopic
                    topic_safe = self._sanitize_filename(topic.name)
                    subtopic_safe = self._sanitize_filename(subtopic.name)
                    filename = f"{topic_safe}_{subtopic_safe}.md"

                    # Count all questions including nested subtopics
                    question_count = len(subtopic.get_all_questions())
                    f.write(f"- [{subtopic.name}]({filename}) ({question_count} preguntas)\n")

                f.write("\n")

        logger.info(f"Created index file: {index_path}")

        # Export each subtopic to its own file (skip empty subtopics)
        # Handle nested subtopics by flattening them
        file_count = 0
        for topic in topics:
            topic_safe = self._sanitize_filename(topic.name)

            # Process all subtopics (including nested ones) recursively
            def export_subtopic_recursive(subtopic: FAQSubtopic, prefix: str = ""):
                nonlocal file_count

                # If this subtopic has questions, export it
                all_questions = subtopic.get_all_questions()
                if len(all_questions) > 0:
                    subtopic_safe = self._sanitize_filename(subtopic.name)
                    filename = f"{topic_safe}_{prefix}{subtopic_safe}.md"
                    output_path = version_dir / filename

                    self._export_subtopic_to_markdown(subtopic, output_path)
                    file_count += 1
                elif len(subtopic.nested_subtopics) == 0:
                    # Empty subtopic with no nested subtopics
                    logger.debug(f"Skipping empty subtopic: {subtopic.name}")

                # Process nested subtopics
                for nested in subtopic.nested_subtopics:
                    nested_prefix = f"{prefix}{self._sanitize_filename(subtopic.name)}_"
                    export_subtopic_recursive(nested, nested_prefix)

            for subtopic in topic.subtopics:
                export_subtopic_recursive(subtopic)

        logger.info(f"Exported {file_count} subtopic files to {version_dir}")
        return version_dir

    def close(self):
        """Close the scraper session"""
        self.scraper.close()
