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
    │   └── forms.py         # Form processing (F29 from SII)
    ├── form29/              # Form29 draft generation tasks
    │   ├── __init__.py
    │   └── drafts.py        # Draft generation from tax documents
    ├── calendar/            # Calendar-related tasks
    │   ├── __init__.py
    │   └── events.py        # Calendar event generation
    └── memory/              # Memory-related tasks
        ├── __init__.py
        └── load.py          # Memory loading from existing data

Import your task modules here to ensure they're discovered by Celery.
"""

# Import task modules to register them with Celery
from . import sii
from . import form29
from . import calendar
from . import memory

__all__ = [
    "sii",
    "form29",
    "calendar",
    "memory",
]
