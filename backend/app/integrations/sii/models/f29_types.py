"""
Tipos de datos para formularios F29
"""
from typing import TypedDict
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


class FormularioF29(TypedDict):
    """
    Informacion basica de un formulario F29 encontrado en busquedas

    Attributes:
        folio: Numero de folio del formulario (visible en tabla)
        period: Periodo tributario (formato: MM-YYYY)
        contributor: Nombre del contribuyente
        submission_date: Fecha de presentacion
        status: Estado del formulario (ej: "Vigente", "Rectificado")
        amount: Monto total a pagar/devolver
        id_interno_sii: ID interno del SII (folio de búsqueda GWT-RPC) - opcional
    """
    folio: str
    period: str
    contributor: str
    submission_date: str
    status: str
    amount: int
    id_interno_sii: NotRequired[str]


class ValorExtraido(TypedDict):
    """Valor extraído de un campo"""
    valor: str
    formato: NotRequired[str]


class CampoF29(TypedDict):
    """Campo individual del formulario F29"""
    codigo: str
    nombre: str
    valor: str


class FilaF29(TypedDict):
    """Fila de una subtabla del F29"""
    campos: dict


class SubtablaF29(TypedDict):
    """Subtabla del formulario F29"""
    nombre: str
    filas: list


class FormularioF29Completo(TypedDict):
    """Formulario F29 completo con todos los detalles"""
    folio: str
    periodo: str
    campos_extraidos: list
    subtablas: list
    total_campos: int
    total_subtablas: int
