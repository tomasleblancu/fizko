"""
Celery tasks registry for Backend V2.

This module serves as a central registry for all Celery tasks,
organized by entity/domain.

Structure:
    tasks/
    ├── __init__.py          # This file (registry)
    ├── sii/                 # SII-related tasks
    │   ├── __init__.py
    │   ├── documents.py     # Document synchronization
    │   └── forms.py         # Form processing (F29)
    └── calendar/            # Calendar-related tasks
        ├── __init__.py
        └── events.py        # Calendar event generation

Import your task modules here to ensure they're discovered by Celery.
"""

# Import task modules to register them with Celery
from . import sii
from . import calendar

__all__ = [
    "sii",
    "calendar",
]
