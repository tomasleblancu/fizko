"""Payroll management tools for the Fizko agent system."""

from .payroll_tools import (
    get_people,
    get_person,
    create_person,
    update_person,
)

__all__ = [
    "get_people",
    "get_person",
    "create_person",
    "update_person",
]
