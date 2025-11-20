"""Supervisor Agent - Routes user queries to specialized agents (Stub for Backend V2)."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI

from app.config.constants import SUPERVISOR_MODEL

logger = logging.getLogger(__name__)


# Simplified supervisor instructions for backend-v2
SUPERVISOR_INSTRUCTIONS = """
Eres un supervisor que analiza consultas de usuarios y las dirige al agente especializado apropiado.

IMPORTANTE: Tu única tarea es ANALIZAR la intención del usuario y TRANSFERIR inmediatamente al agente correcto.
NO generes respuestas de texto - solo llama a funciones de handoff.

Agentes disponibles:
- general_knowledge: Preguntas generales sobre impuestos, contabilidad, leyes chilenas
- tax_documents: Consultas sobre facturas, boletas, DTEs, documentos tributarios
- f29: Preguntas sobre Formulario 29, impuestos mensuales
- payroll: Consultas sobre nómina, sueldos, trabajadores
- settings: Configuración de cuenta, notificaciones
- expense: Gestión de gastos
- feedback: Comentarios y sugerencias

REGLAS:
1. Analiza la consulta del usuario
2. Identifica el agente más apropiado
3. Transfiere INMEDIATAMENTE usando handoff
4. NO generes texto adicional
"""


def create_supervisor_agent(
    db=None,  # Stub parameter for compatibility
    openai_client: AsyncOpenAI = None,
) -> Agent:
    """
    Create the Supervisor Agent that routes to specialized agents (simplified for backend-v2).

    The Supervisor Agent:
    1. Analyzes user intent (using gpt-4o-mini for speed)
    2. Routes IMMEDIATELY to the appropriate specialized agent
    3. Does NOT generate text responses - only function calls (handoffs)

    This is a pure router agent - it delegates all actual work to specialists.

    Args:
        db: Stub parameter for compatibility (not used in backend-v2)
        openai_client: OpenAI client (not used in simplified version)
    """

    agent = Agent(
        name="supervisor_agent",
        model=SUPERVISOR_MODEL,  # gpt-4o-mini (fast routing)
        instructions=SUPERVISOR_INSTRUCTIONS,
        tools=[],  # No tools in simplified version
        # No guardrails in backend-v2 simplified version
    )

    return agent
