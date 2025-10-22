"""Specialized agents for Fizko tax/accounting platform."""

from .remuneraciones_agent import create_remuneraciones_agent
from .sii_general_agent import create_sii_general_agent
from .documentos_tributarios_agent import create_documentos_tributarios_agent
from .importaciones_agent import create_importaciones_agent
from .contabilidad_agent import create_contabilidad_agent
from .f29_agent import create_f29_agent
from .operacion_renta_agent import create_operacion_renta_agent

__all__ = [
    "create_sii_general_agent",
    "create_remuneraciones_agent",
    "create_documentos_tributarios_agent",
    "create_importaciones_agent",
    "create_contabilidad_agent",
    "create_f29_agent",
    "create_operacion_renta_agent",
]
