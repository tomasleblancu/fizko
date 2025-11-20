"""Specialized agents for the multi-agent system."""

from .general_knowledge_agent import create_general_knowledge_agent
from .tax_documents_agent import create_tax_documents_agent
from .monthly_taxes_agent import create_monthly_taxes_agent
from .payroll_agent import create_payroll_agent
from .settings_agent import create_settings_agent
from .expense_agent import create_expense_agent
from .feedback_agent import create_feedback_agent

__all__ = [
    "create_general_knowledge_agent",
    "create_tax_documents_agent",
    "create_monthly_taxes_agent",
    "create_payroll_agent",
    "create_settings_agent",
    "create_expense_agent",
    "create_feedback_agent",
]
