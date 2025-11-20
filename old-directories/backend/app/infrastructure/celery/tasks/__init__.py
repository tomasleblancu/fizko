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
    ├── forms/               # Form management tasks (Form29, etc.)
    │   ├── __init__.py
    │   └── form29.py        # Form29 draft generation
    ├── whatsapp/            # WhatsApp messaging tasks
    │   └── __init__.py
    ├── notifications/       # Notification tasks
    │   ├── __init__.py
    │   ├── calendar_notifications.py
    │   └── processing.py
    ├── calendar/            # Calendar synchronization tasks
    │   ├── __init__.py
    │   └── sync.py          # Calendar sync tasks
    └── memory/              # Memory (Mem0) tasks
        └── __init__.py      # Memory save/update tasks

Import your task modules here to ensure they're discovered by Celery.
"""

# Import task modules to register them with Celery
from . import sii
from . import documents
from . import forms
from . import whatsapp
from . import calendar
from . import notifications
from . import memory

__all__ = [
    "sii",
    "documents",
    "forms",
    "whatsapp",
    "calendar",
    "notifications",
    "memory",
]
