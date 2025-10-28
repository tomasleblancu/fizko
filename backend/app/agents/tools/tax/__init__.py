"""Tax-related tools for agents."""

from .documentos_tributarios_tools import (
    get_documentos_tributarios_tools,
    get_documento_tributario_tool,
    list_documentos_tributarios_tool,
)
from .f29_tools import get_f29_tools, get_f29_tool, list_f29_tool
from .operacion_renta_tools import (
    get_operacion_renta_tools,
    get_operacion_renta_tool,
    list_operaciones_renta_tool,
)
from .remuneraciones_tools import (
    get_remuneraciones_tools,
    get_remuneracion_tool,
    list_remuneraciones_tool,
)
from .sii_general_tools import get_sii_general_tools

__all__ = [
    # Documentos Tributarios
    "get_documentos_tributarios_tools",
    "get_documento_tributario_tool",
    "list_documentos_tributarios_tool",
    # F29
    "get_f29_tools",
    "get_f29_tool",
    "list_f29_tool",
    # Operación Renta
    "get_operacion_renta_tools",
    "get_operacion_renta_tool",
    "list_operaciones_renta_tool",
    # Remuneraciones
    "get_remuneraciones_tools",
    "get_remuneracion_tool",
    "list_remuneraciones_tool",
    # SII General
    "get_sii_general_tools",
]
