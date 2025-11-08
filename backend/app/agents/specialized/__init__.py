"""Specialized agents for the multi-agent system."""

from .general_knowledge_agent import create_general_knowledge_agent
from .tax_documents_agent import create_tax_documents_agent
from .payroll_agent import create_payroll_agent
from .settings_agent import create_settings_agent

__all__ = [
    "create_general_knowledge_agent",
    "create_tax_documents_agent",
    "create_payroll_agent",
    "create_settings_agent",
]
