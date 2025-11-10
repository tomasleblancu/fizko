"""
Data models for SII FAQ
"""

from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FAQQuestion:
    """
    Represents a single FAQ question and answer
    """
    id: str  # e.g., "001.100.7893.004"
    question: str
    answer: str
    subtopic_id: str
    subtopic_name: str
    topic_name: str
    url: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class FAQSubtopic:
    """
    Represents a subtopic within a FAQ topic.
    Can contain either questions OR nested subtopics (but not both).
    """
    name: str
    url: str
    topic_name: str
    questions: List[FAQQuestion] = field(default_factory=list)
    # Support nested subtopics for multi-level hierarchy
    nested_subtopics: List['FAQSubtopic'] = field(default_factory=list)

    def get_all_questions(self) -> List[FAQQuestion]:
        """Get all questions from this subtopic and any nested subtopics"""
        all_questions = list(self.questions)
        for nested in self.nested_subtopics:
            all_questions.extend(nested.get_all_questions())
        return all_questions


@dataclass
class FAQTopic:
    """
    Represents a main FAQ topic
    """
    name: str
    url: str
    subtopics: List[FAQSubtopic] = field(default_factory=list)

    def get_all_questions(self) -> List[FAQQuestion]:
        """Get all questions from all subtopics"""
        questions = []
        for subtopic in self.subtopics:
            questions.extend(subtopic.questions)
        return questions
