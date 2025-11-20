"""
Cliente modular del SII

Este módulo exporta el SIIClient completo con todos los métodos organizados
en una estructura modular:

- base.py: Inicialización, autenticación, cookies
- contribuyente_methods.py: Información del contribuyente
- dte_methods.py: Documentos tributarios (compras, ventas, resumen)
- f29_methods.py: Formularios F29, propuestas, declaraciones, mensajes
- boletas_methods.py: Boletas de honorarios

Uso:
    from app.integrations.sii.client import SIIClient

    with SIIClient(tax_id="12345678-9", password="secret") as client:
        # Todos los métodos disponibles
        client.login()
        client.get_contribuyente()
        client.get_compras("202501")
        client.get_f29_lista("2025")
        client.get_boletas_honorarios("10", "2025")
"""

from .boletas_methods import BoletasMethods

# SIIClient es el alias final que hereda de todo
class SIIClient(BoletasMethods):
    """
    Cliente completo del SII con todos los métodos.

    Cadena de herencia:
    SIIClient -> BoletasMethods -> F29Methods -> DTEMethods -> ContribuyenteMethods -> SIIClientBase

    Métodos disponibles:

    **Autenticación y Cookies:**
    - login(force_new=False)
    - get_cookies()
    - is_authenticated()

    **Contribuyente:**
    - get_contribuyente()

    **Documentos Tributarios (DTEs):**
    - get_compras(periodo, tipo_doc="33")
    - get_ventas(periodo, tipo_doc="33")
    - get_resumen(periodo)
    - get_boletas_diarias(periodo, tipo_doc)

    **Formulario 29:**
    - get_f29_lista(anio, folio=None)
    - get_f29_compacto(folio, id_interno_sii)
    - get_propuesta_f29(periodo)
    - get_tasa_ppmo(periodo, categoria_tributaria=1, tipo_formulario="FMNINT")
    - get_declaraciones_con_estados(mes, anio, form_id="2", max_retries=3)
    - get_mensajes_contribuyente(periodo, form_id="2", tipo="IP", max_retries=3)
    - guardar_propuesta_f29(mes, anio, tipo_propuesta_inicial=44, form_codigo="29", max_retries=3)
    - enviar_datos_flujo(mes, anio, tipo=44, form="29", max_retries=3)

    **Boletas de Honorarios:**
    - get_boletas_honorarios(mes, anio, max_retries=3)
    - get_boletas_honorarios_todas_paginas(mes, anio, max_retries=3)

    Example:
        >>> with SIIClient(tax_id="12345678-9", password="secret") as client:
        ...     client.login()
        ...     info = client.get_contribuyente()
        ...     compras = client.get_compras("202501")
        ...     boletas = client.get_boletas_honorarios("10", "2025")
    """
    pass


# Para compatibilidad, también exportar las clases base por si alguien quiere usarlas
__all__ = [
    'SIIClient',
]
