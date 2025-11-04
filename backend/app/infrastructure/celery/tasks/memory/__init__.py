"""
Memory Tasks Module

Tareas de Celery relacionadas con guardado de memorias en Mem0.

Estructura modular:
- company.py: Tareas para memorias de empresa
- user.py: Tareas para memorias de usuario
- onboarding.py: Tarea completa de onboarding (empresa + usuario)

IMPORTANT: Keep tasks simple - delegate to services for business logic.
"""

from .company import save_company_memories_task
from .user import save_user_memories_task
from .onboarding import save_onboarding_memories_task

__all__ = [
    "save_company_memories_task",
    "save_user_memories_task",
    "save_onboarding_memories_task",
]
