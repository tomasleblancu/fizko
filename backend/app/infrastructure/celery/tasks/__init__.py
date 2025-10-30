"""
Celery tasks registry.

This module serves as a central registry for all Celery tasks,
organized by entity/domain.

Structure:
    tasks/
    ├── __init__.py          # This file (registry)
    ├── sii/                 # SII-related tasks
    │   ├── __init__.py
    │   └── sync_tasks.py    # Document synchronization
    ├── documents/           # Document processing tasks
    │   └── __init__.py
    └── whatsapp/            # WhatsApp messaging tasks
        └── __init__.py

Import your task modules here to ensure they're discovered by Celery.
"""

# Import task modules to register them with Celery
from . import sii
from . import documents
from . import whatsapp

__all__ = [
    "sii",
    "documents",
    "whatsapp",
]
