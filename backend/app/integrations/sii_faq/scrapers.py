"""
Scrapers for extracting FAQ data from SII website
"""

import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

from app.integrations.sii_faq.config import (
    BASE_URL,
    MAIN_FAQ_URL,
    REQUEST_TIMEOUT,
    USER_AGENT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from app.integrations.sii_faq.models import FAQTopic, FAQSubtopic, FAQQuestion

logger = logging.getLogger(__name__)


class SIIFAQScraper:
    """
    Scraper for SII FAQ pages using requests + BeautifulSoup
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL with retries

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if failed
        """
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{MAX_RETRIES})")
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                response.encoding = 'utf-8'  # Ensure proper encoding for Spanish chars
                return response.text
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return None
        return None

    def scrape_main_topics(self) -> List[Dict[str, str]]:
        """
        Scrape main topics from the FAQ landing page

        Returns:
            List of dicts with 'name' and 'url' keys
        """
        logger.info("Scraping main FAQ topics...")
        html = self._fetch_html(MAIN_FAQ_URL)
        if not html:
            logger.error("Failed to fetch main FAQ page")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        topics = []

        # Find all topic boxes
        # Pattern 1: <div class="caja-item" onclick="window.location='...'">
        for div in soup.find_all('div', class_='caja-item'):
            onclick = div.get('onclick', '')
            if 'window.location' in onclick:
                # Extract URL from onclick="window.location='path/file.htm'"
                start = onclick.find("'") + 1
                end = onclick.rfind("'")
                if start > 0 and end > start:
                    relative_url = onclick[start:end]
                    url = urljoin(BASE_URL + "/", relative_url)

                    # Get topic name from span.titulo-item
                    span = div.find('span', class_='titulo-item')
                    if span:
                        name = span.get_text(strip=True)
                        topics.append({'name': name, 'url': url})
                        logger.debug(f"Found topic: {name}")

        # Pattern 2: Collapsible sections with subtopics (e.g., "Impuestos Mensuales", "Declaraciones Juradas")
        # These have <a role="button" data-toggle="collapse"> with nested <ul><li><a> for subtopics
        for collapse_div in soup.find_all('div', class_='panel-collapse collapse'):
            panel_body = collapse_div.find('div', class_='panel-body')
            if panel_body:
                # Find the parent section to get the main topic name
                parent_caja = collapse_div.find_previous('div', class_='caja-item')
                if parent_caja:
                    titulo_acordeon = parent_caja.find('span', class_='titulo-acordeon')
                    if titulo_acordeon:
                        main_topic_name = titulo_acordeon.get_text(strip=True)

                        # Now extract subtopics from the <ul><li><a> structure
                        for link in panel_body.find_all('a', href=True):
                            relative_url = link['href']
                            url = urljoin(BASE_URL + "/", relative_url)
                            subtopic_name = link.get_text(strip=True)
                            # Use full name: "Main Topic - Subtopic"
                            full_name = f"{main_topic_name} - {subtopic_name}"
                            topics.append({'name': full_name, 'url': url})
                            logger.debug(f"Found nested topic: {full_name}")

        logger.info(f"Found {len(topics)} main topics")
        return topics

    def scrape_subtopics(self, topic_url: str, topic_name: str) -> List[Dict[str, str]]:
        """
        Scrape subtopics from a topic page

        Args:
            topic_url: URL of the topic page
            topic_name: Name of the parent topic

        Returns:
            List of dicts with 'name', 'url', and 'topic_name' keys
        """
        logger.info(f"Scraping subtopics from {topic_name}...")
        html = self._fetch_html(topic_url)
        if not html:
            logger.error(f"Failed to fetch topic page: {topic_url}")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        subtopics = []

        # Find subtopics list: <div id="listado_subtemas"><ol><li><a>
        listado = soup.find('div', id='listado_subtemas')
        if listado:
            for link in listado.find_all('a', href=True):
                relative_url = link['href']
                # Build full URL relative to topic page directory
                base_dir = topic_url.rsplit('/', 1)[0]
                url = urljoin(base_dir + "/", relative_url)
                name = link.get_text(strip=True)
                subtopics.append({
                    'name': name,
                    'url': url,
                    'topic_name': topic_name
                })
                logger.debug(f"Found subtopic: {name}")

        logger.info(f"Found {len(subtopics)} subtopics in {topic_name}")
        return subtopics

    def _has_nested_subtopics(self, html: str) -> bool:
        """
        Check if a page contains nested subtopics (not just questions)

        Args:
            html: HTML content of the page

        Returns:
            True if page has listado_subtemas div, False otherwise
        """
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find('div', id='listado_subtemas') is not None

    def scrape_questions_list(self, subtopic_url: str, subtopic_name: str, topic_name: str) -> List[Dict[str, str]]:
        """
        Scrape list of questions from a subtopic page

        Args:
            subtopic_url: URL of the subtopic page
            subtopic_name: Name of the subtopic
            topic_name: Name of the parent topic

        Returns:
            List of dicts with 'question', 'url', 'subtopic_name', 'topic_name' keys
        """
        logger.info(f"Scraping questions from subtopic: {subtopic_name}...")
        html = self._fetch_html(subtopic_url)
        if not html:
            logger.error(f"Failed to fetch subtopic page: {subtopic_url}")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        questions = []

        # Find questions list: <div id="listado-preguntas-por-tema"><ul><li><a>
        listado = soup.find('div', id='listado-preguntas-por-tema')
        if listado:
            for link in listado.find_all('a', href=True):
                relative_url = link['href']
                # Build full URL relative to subtopic page directory
                base_dir = subtopic_url.rsplit('/', 1)[0]
                url = urljoin(base_dir + "/", relative_url)
                question_text = link.get_text(strip=True)
                questions.append({
                    'question': question_text,
                    'url': url,
                    'subtopic_name': subtopic_name,
                    'topic_name': topic_name
                })
                logger.debug(f"Found question: {question_text[:50]}...")

        logger.info(f"Found {len(questions)} questions in subtopic {subtopic_name}")
        return questions

    def scrape_question_detail(self, question_url: str) -> Optional[Dict[str, str]]:
        """
        Scrape detailed information for a single question

        Args:
            question_url: URL of the question detail page

        Returns:
            Dict with 'id', 'question', 'answer', 'created_at', 'updated_at' keys or None if failed
        """
        logger.info(f"Scraping question detail from {question_url}...")
        html = self._fetch_html(question_url)
        if not html:
            logger.error(f"Failed to fetch question page: {question_url}")
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Extract question
        question_div = soup.find('div', id='div-pregunta')
        question = question_div.find('h2').get_text(strip=True) if question_div and question_div.find('h2') else ""

        # Extract answer
        answer_div = soup.find('div', id='div-respuesta')
        answer = answer_div.get_text(strip=True) if answer_div else ""

        # Extract ID
        id_div = soup.find('div', id='div-id')
        faq_id = id_div.get_text(strip=True).replace('ID:', '').strip() if id_div else ""

        # Extract dates
        created_div = soup.find('div', id='div-fec-creacion')
        created_at = created_div.get_text(strip=True).replace('Fecha de creación:', '').strip() if created_div else None

        updated_div = soup.find('div', id='div-fec-actualizacion')
        updated_at = updated_div.get_text(strip=True).replace('Fecha de actualización:', '').strip() if updated_div else None

        result = {
            'id': faq_id,
            'question': question,
            'answer': answer,
            'created_at': created_at,
            'updated_at': updated_at,
            'url': question_url
        }

        logger.debug(f"Extracted question detail: ID={faq_id}")
        return result

    def close(self):
        """Close the requests session"""
        self.session.close()
