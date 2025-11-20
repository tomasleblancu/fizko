"""
SII FAQ Integration Module

Scraper for extracting FAQs from the Chilean Tax Authority (SII) website
and creating OpenAI vector stores for AI agent file search.
"""

from app.integrations.sii_faq.client import SIIFAQClient
from app.integrations.sii_faq.models import FAQTopic, FAQSubtopic, FAQQuestion
from app.integrations.sii_faq.vectorizer import FAQVectorizer

__all__ = [
    "SIIFAQClient",
    "FAQTopic",
    "FAQSubtopic",
    "FAQQuestion",
    "FAQVectorizer"
]
