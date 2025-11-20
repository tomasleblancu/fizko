"""Personnel repositories - Employee and payroll management."""

from .payroll import PayrollRepository
from .person import PersonRepository

__all__ = [
    "PayrollRepository",
    "PersonRepository",
]
