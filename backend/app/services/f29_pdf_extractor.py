"""
Extractor mejorado para Formulario 29 (F29) del SII

Este extractor captura TODOS los códigos y campos del F29 de forma estructurada,
incluyendo:
- Encabezado (folio, RUT, período, razón social, etc.)
- Todos los códigos de débitos (502, 111, 759, etc.)
- Todos los códigos de créditos (511, 520, 504, etc.)
- Cantidades de documentos (503, 110, 758, etc.)
- Impuestos determinados (089, 062, 547, etc.)
- Totales a pagar

Los datos extraídos se almacenan en un diccionario estructurado que luego
se guarda en el campo extra_data (JSONB) del modelo form29_sii_downloads.
"""

import logging
import re
from decimal import Decimal
from typing import Dict, Any, Optional, List
from io import BytesIO

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

logger = logging.getLogger(__name__)


# Mapeo de códigos del F29 según especificación del SII
# Formato: código -> (nombre_campo, descripción)
F29_CODIGO_MAP = {
    # Encabezado
    "07": ("folio", "Folio"),
    "03": ("rut", "RUT"),
    "15": ("periodo", "Período"),
    "01": ("razon_social", "Razón Social"),
    "06": ("direccion_calle", "Calle"),
    "610": ("direccion_numero", "Número"),
    "08": ("comuna", "Comuna"),
    "09": ("telefono", "Teléfono"),
    "55": ("correo", "Correo Electrónico"),
    "314": ("rut_representante", "RUT Representante"),

    # Cantidades de documentos emitidos
    "503": ("cant_facturas_emitidas", "Cantidad Facturas Emitidas"),
    "110": ("cant_boletas", "Cantidad Boletas"),
    "758": ("cant_recibos_electronicos", "Cantidad Recibos de Pago Medios Electrónicos"),
    "509": ("cant_notas_credito_emitidas", "Cantidad Notas de Crédito Emitidas"),
    "708": ("cant_notas_cred_vales_maq", "Cantidad Notas Crédito Vales Máquinas"),
    "584": ("cant_int_ex_no_grav", "Cantidad Intereses Exentos No Gravados"),

    # Cantidades de documentos recibidos
    "500": ("cant_facturas_recibidas", "Cantidad Facturas Recibidas"),
    "519": ("cant_fact_recibidas_giro", "Cantidad Facturas Recibidas del Giro"),
    "527": ("cant_notas_credito_recibidas", "Cantidad Notas de Crédito Recibidas"),
    "531": ("cant_notas_debito_recibidas", "Cantidad Notas de Débito Recibidas"),
    "534": ("cant_form_pago_imp_giro", "Cantidad Formularios Pago Impuesto del Giro"),

    # DÉBITOS (montos)
    "502": ("debitos_facturas", "Débitos Facturas Emitidas"),
    "111": ("debitos_boletas", "Débitos Boletas"),
    "759": ("debitos_recibos_electronicos", "Débitos Recibos de Pago Medios Electrónicos"),
    "510": ("debitos_notas_credito", "Débitos Notas de Crédito Emitidas"),
    "709": ("debitos_notas_cred_vales", "Débitos Notas Crédito Vales Máquinas IVA"),
    "501": ("liquidacion_facturas", "Liquidación de Facturas"),
    "538": ("total_debitos", "Total Débitos"),
    "562": ("monto_sin_der_cred_fiscal", "Monto Sin Derecho a Crédito Fiscal"),

    # CRÉDITOS (montos)
    "511": ("credito_iva_documentos_electronicos", "Crédito IVA por Documentos Electrónicos"),
    "520": ("credito_facturas_giro", "Crédito Recuperado y Reintegros Facturas del Giro"),
    "528": ("credito_notas_credito", "Crédito Recuperado y Reintegros Notas de Crédito"),
    "532": ("credito_notas_debito", "Crédito Notas de Débito"),
    "535": ("credito_pago_imp_giro", "Crédito Recuperado y Reintegros Pago Impuesto del Giro"),
    "504": ("remanente_mes_anterior", "Remanente Crédito Mes Anterior"),
    "077": ("remanente_credito_fisc", "Remanente de Crédito Fiscal"),
    "544": ("recup_imp_diesel", "Recuperación Impuesto Especial Diesel"),
    "779": ("iva_postergado", "Monto de IVA Postergado 6 o 12 Cuotas"),
    "537": ("total_creditos", "Total Créditos"),

    # Impuestos determinados
    "089": ("iva_determinado", "IVA Determinado"),
    "062": ("ppm_neto", "PPM Neto Determinado"),
    "048": ("retencion_imp_unico", "Retención Impuesto Único Trabajadores Art. 74 N°1 LIR"),
    "151": ("retencion_tasa_ley_21133", "Retención Tasa Ley 21.133 Sobre Rentas"),
    "563": ("base_imponible", "Base Imponible"),
    "115": ("tasa_ppm", "Tasa PPM 1ra Categoría"),
    "595": ("subtotal_imp_determinado", "Sub Total Impuestos Determinado Anverso"),
    "547": ("total_determinado", "Total Determinado"),

    # Totales a pagar
    "91": ("total_pagar_plazo_legal", "Total a Pagar Dentro del Plazo Legal"),
    "92": ("mas_ipc", "Más IPC"),
    "93": ("mas_interes_multas", "Más Intereses y Multas"),
    "795": ("condonacion", "Condonación"),
    "94": ("total_pagar_recargo", "Total a Pagar con Recargo"),

    # Detalles de condonación
    "60": ("codigo_condonacion", "Código de Condonación"),
    "922": ("porc_condonacion", "% Condonación"),
    "915": ("fecha_condonacion", "Fecha de la Condonación"),
}


class F29PDFExtractor:
    """
    Extractor mejorado que captura TODOS los códigos del F29
    """

    def __init__(self):
        if PdfReader is None:
            raise ImportError(
                "pypdf o PyPDF2 es requerido. Instala con: pip install pypdf"
            )

    def extract_from_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extrae TODOS los datos estructurados del PDF del F29

        Args:
            pdf_bytes: Contenido del PDF en bytes

        Returns:
            Diccionario completo con todos los datos extraídos:
            {
                'header': {  # Información del encabezado
                    'folio': str,
                    'rut': str,
                    'periodo': str,
                    'razon_social': str,
                    'direccion': str,
                    'tipo_declaracion': str,
                    'fecha_presentacion': str,
                    'banco': str,
                    'medio_pago': str
                },
                'codes': {  # Todos los códigos con sus valores
                    '502': {'value': float, 'glosa': str, 'field_name': str},
                    '503': {'value': int, 'glosa': str, 'field_name': str},
                    ...
                },
                'grouped': {  # Datos agrupados por categoría
                    'debitos': {...},
                    'creditos': {...},
                    'cantidades': {...},
                    'impuestos': {...}
                },
                'summary': {  # Resumen con totales principales
                    'total_debitos': float,
                    'total_creditos': float,
                    'iva_determinado': float,
                    'total_pagar': float
                },
                'raw_text': str  # Texto completo para referencia
            }
        """
        try:
            # 1. Extraer texto del PDF
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PdfReader(pdf_file)

            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()

            logger.info(f"📄 Texto extraído: {len(full_text)} caracteres")

            # 2. Extraer encabezado
            header = self._extract_header(full_text)

            # 3. Extraer todos los códigos con sus valores
            codes = self._extract_all_codes(full_text)

            # 4. Agrupar códigos por categoría
            grouped = self._group_codes(codes)

            # 5. Calcular resumen con totales principales
            summary = self._calculate_summary(codes)

            # 6. Compilar resultado final
            result = {
                'header': header,
                'codes': codes,
                'grouped': grouped,
                'summary': summary,
                'raw_text': full_text[:1000],  # Primeros 1000 chars para referencia
                'extraction_success': True,
                'codes_extracted': len(codes)
            }

            logger.info(f"✅ Extracción completada: {len(codes)} códigos extraídos")
            return result

        except Exception as e:
            logger.error(f"❌ Error extrayendo datos del PDF: {e}", exc_info=True)
            return {
                'extraction_success': False,
                'error': str(e),
                'codes': {},
                'header': {},
                'grouped': {},
                'summary': {}
            }

    def _extract_header(self, text: str) -> Dict[str, Any]:
        """Extrae información del encabezado del F29"""
        header = {}

        # Folio
        folio_match = re.search(r'FOLIO\s+\[07\]\s+(\d+)', text)
        if folio_match:
            header['folio'] = folio_match.group(1)

        # RUT
        rut_match = re.search(r'RUT\s+\[03\]\s+([\d.-K]+)', text)
        if rut_match:
            header['rut'] = rut_match.group(1)

        # Período
        period_match = re.search(r'PERIODO\s+\[15\]\s+(\d{6})', text)
        if period_match:
            period = period_match.group(1)
            header['periodo'] = period
            header['periodo_year'] = int(period[:4])
            header['periodo_month'] = int(period[4:6])
            header['periodo_display'] = f"{period[:4]}-{period[4:6]}"

        # Razón Social
        razon_match = re.search(r'01\s+Apellido.*?02\s+Apellido.*?05\s+Nombres\s+(.+?)\s+06', text, re.DOTALL)
        if razon_match:
            header['razon_social'] = razon_match.group(1).strip()

        # Dirección
        dir_match = re.search(r'06\s+Calle\s+610\s+Número\s+08\s+Comuna\s+(.+?)\s+09', text, re.DOTALL)
        if dir_match:
            header['direccion'] = dir_match.group(1).strip().replace('\n', ' ')

        # Tipo de declaración
        tipo_match = re.search(r'Tipo de Declaración\s+Corrige a Folio.*?\s+Banco.*?\s+Medio de Pago.*?\s+Fecha de Presentación\s+(\w+)', text)
        if tipo_match:
            header['tipo_declaracion'] = tipo_match.group(1)

        # Fecha de presentación
        fecha_match = re.search(r'Fecha de Presentación\s+(\d{2}/\d{2}/\d{4})', text)
        if fecha_match:
            header['fecha_presentacion'] = fecha_match.group(1)

        # Banco
        banco_match = re.search(r'Banco\s+Medio de Pago\s+Fecha\s+\w+\s+(\w+)', text)
        if banco_match:
            header['banco'] = banco_match.group(1)

        # Medio de pago
        medio_match = re.search(r'Medio de Pago\s+Fecha.*?\s+(\w+)\s+\d{2}/\d{2}/\d{4}', text)
        if medio_match:
            header['medio_pago'] = medio_match.group(1)

        return header

    def _clean_numeric_value(self, value_str: str) -> str:
        """
        Limpia un valor numérico distinguiendo entre puntos decimales y separadores de miles

        Reglas:
        - Comas siempre son decimales (formato chileno alternativo)
        - Múltiples puntos son separadores de miles (1.234.567)
        - Un solo punto: determinar por contexto
          * Si empieza con 0 o un dígito < 10 y tiene 3 decimales -> es decimal (0.250, 1.500)
          * Si tiene 3 decimales y primer número > 9 -> es miles (123.456)
          * Si tiene != 3 decimales -> es decimal (0.25, 123.5)

        Ejemplos:
        - "0.250" -> "0.250" (decimal)
        - "1.234.567" -> "1234567" (miles)
        - "123.456" -> "123456" (miles)
        - "16.959" -> "16959" (miles)
        """
        # Si tiene coma decimal, convertirla a punto
        if ',' in value_str:
            value_str = value_str.replace(',', '.')

        # Si tiene punto, determinar si es decimal o miles
        if '.' in value_str:
            parts = value_str.split('.')

            # Múltiples puntos: definitivamente miles (1.234.567)
            if len(parts) > 2:
                return value_str.replace('.', '')

            # Un solo punto: verificar contexto
            elif len(parts) == 2:
                first_part = parts[0]
                second_part = parts[1]

                # Si la última parte tiene 3 dígitos
                if len(second_part) == 3:
                    # Si primera parte es "0" o un solo dígito pequeño, es decimal
                    if first_part == '0' or (len(first_part) == 1 and int(first_part) < 10):
                        # Es decimal: 0.250, 1.500, 2.125
                        return value_str
                    else:
                        # Es miles: 123.456, 16.959
                        return value_str.replace('.', '')
                else:
                    # No tiene 3 dígitos: definitivamente decimal (0.25, 123.5, 16.9)
                    return value_str

        return value_str

    def _extract_all_codes(self, text: str) -> Dict[str, Any]:
        """
        Extrae TODOS los códigos del F29 con sus valores

        Soporta dos formatos:
        Formato 1 (código al inicio): 503 CANTIDAD FACTURAS EMITIDAS 49
        Formato 2 (código al final):  Más IPC 92 0 +
        """
        codes = {}

        # Patrón 1: Código al inicio + glosa + valor
        pattern1 = r'^(\d{2,3})\s+(.+?)\s+([\d.,]+)(?:\s*[+\-=])?$'

        # Patrón 2: Glosa + código + valor (para sección de totales)
        pattern2 = r'^(.+?)\s+(\d{2,3})\s+([\d.,]+)(?:\s*[+\-=])?$'

        # Patrón 3: Glosa específica para códigos de pago (más flexible)
        pattern3 = r'(Más\s+IPC|Más\s+Interes(?:es)?\s+y\s+Multas|CONDONACIÓN|Condonación|TOTAL\s+A\s+PAGAR\s+CON\s+RECARGO|Total\s+a\s+Pagar\s+con\s+Recargo)\s+(\d{2,3})\s+([\d.,]+)'

        # Patrón 4: Códigos de pago sin valor (cuando está vacío)
        pattern4 = r'(Más\s+IPC|Más\s+Interes(?:es)?\s+y\s+Multas|CONDONACIÓN|Condonación|TOTAL\s+A\s+PAGAR\s+CON\s+RECARGO|Total\s+a\s+Pagar\s+con\s+Recargo)\s+(\d{2,3})\s*[+\-=]'

        for line in text.split('\n'):
            line = line.strip()

            # Primero intentar detectar códigos de la sección de pagos (92, 93, 795, 94)
            special_match = re.search(pattern3, line, re.IGNORECASE)
            if special_match:
                glosa = special_match.group(1).strip()
                code = special_match.group(2)
                value_str = special_match.group(3)

                # Normalizar glosa
                if 'IPC' in glosa.upper():
                    glosa = 'Más IPC'
                elif 'INTERES' in glosa.upper() or 'MULTAS' in glosa.upper():
                    glosa = 'Más Intereses y Multas'
                elif 'CONDONACIÓN' in glosa.upper() or 'CONDONACION' in glosa.upper():
                    glosa = 'Condonación'
                elif 'PAGAR CON RECARGO' in glosa.upper():
                    glosa = 'Total a Pagar con Recargo'
            else:
                # Intentar detectar códigos de pago sin valor (vacíos)
                empty_match = re.search(pattern4, line, re.IGNORECASE)
                if empty_match:
                    glosa = empty_match.group(1).strip()
                    code = empty_match.group(2)
                    value_str = '0'  # Asignar 0 cuando no hay valor

                    # Normalizar glosa
                    if 'IPC' in glosa.upper():
                        glosa = 'Más IPC'
                    elif 'INTERES' in glosa.upper() or 'MULTAS' in glosa.upper():
                        glosa = 'Más Intereses y Multas'
                    elif 'CONDONACIÓN' in glosa.upper() or 'CONDONACION' in glosa.upper():
                        glosa = 'Condonación'
                    elif 'PAGAR CON RECARGO' in glosa.upper():
                        glosa = 'Total a Pagar con Recargo'
                else:
                    # Intentar con patrón 1 (código al inicio)
                    match = re.match(pattern1, line, re.IGNORECASE)
                    if match:
                        code = match.group(1)
                        glosa = match.group(2).strip()
                        value_str = match.group(3)
                    else:
                        # Intentar con patrón 2 (código al final)
                        match = re.match(pattern2, line, re.IGNORECASE)
                        if match:
                            glosa = match.group(1).strip()
                            code = match.group(2)
                            value_str = match.group(3)
                        else:
                            # No match con ningún patrón
                            continue

            # Limpiar el valor con lógica mejorada para distinguir decimales de miles
            clean_value = self._clean_numeric_value(value_str)

            # Intentar convertir a número
            try:
                # Si tiene decimales, usar float (JSON-serializable)
                if '.' in clean_value:
                    value = float(clean_value)
                else:
                    # Si es entero, mantener como int
                    value = int(clean_value)

                codes[code] = {
                    'value': value,
                    'glosa': glosa,
                    'field_name': F29_CODIGO_MAP.get(code, (f"codigo_{code}", glosa))[0]
                }

                logger.debug(f"Código {code}: {glosa} = {value}")

            except (ValueError, Decimal.InvalidOperation):
                logger.warning(f"No se pudo convertir valor para código {code}: {value_str}")

        # Extraer códigos de tabla de condonación (formato especial)
        self._extract_condonacion_table(text, codes)

        return codes

    def _extract_condonacion_table(self, text: str, codes: Dict[str, Any]) -> None:
        """
        Extrae códigos de la tabla de condonación (formato especial con múltiples columnas)

        Formato en el PDF:
        60 | % Condonación | 922 | Número de la Resolución | 915 | Fecha de la Condonación
           |      70       |     |       013-2015          |     |      31/12/2025
        """
        # Buscar línea con "% Condonación" y "Número de la Resolución"
        for i, line in enumerate(text.split('\n')):
            if '% Condonación' in line or '% Condonacion' in line:
                # Extraer código 60 si está en el encabezado
                header_match = re.search(r'(\d{2,3})\s+%\s+Condonaci[oó]n', line)
                if header_match and '60' not in codes:
                    codes['60'] = {
                        'value': None,  # Código 60 es solo indicador de sección
                        'glosa': 'Código de Condonación',
                        'field_name': 'codigo_condonacion'
                    }
                    logger.debug("Código 60: Código de Condonación (sección detectada)")
                # Buscar la siguiente línea con los valores
                lines = text.split('\n')
                if i + 1 < len(lines):
                    value_line = lines[i + 1].strip()

                    # Extraer valores usando regex más flexible
                    parts = value_line.split()

                    # Intentar extraer valores en orden
                    for part in parts:
                        part = part.strip()

                        # Código 60 o 922: porcentaje de condonación (número simple)
                        if part.isdigit() and len(part) <= 3:
                            valor = int(part)
                            # Si es un porcentaje razonable, asignarlo al código 922
                            if 1 <= valor <= 100 and '922' not in codes:
                                codes['922'] = {
                                    'value': valor,
                                    'glosa': '% Condonación',
                                    'field_name': 'porc_condonacion'
                                }
                                logger.debug(f"Código 922: % Condonación = {valor}")

                        # Código 915: número de resolución (formato: XXX-XXXX)
                        elif re.match(r'\d{3}-\d{4}', part):
                            codes['915'] = {
                                'value': part,
                                'glosa': 'Número de la Resolución',
                                'field_name': 'numero_resolucion'
                            }
                            logger.debug(f"Código 915: Número de la Resolución = {part}")

                        # Código 915 (fecha): formato DD/MM/YYYY
                        elif re.match(r'\d{2}/\d{2}/\d{4}', part):
                            if '915' in codes and isinstance(codes['915']['value'], str) and '-' in codes['915']['value']:
                                # Ya tenemos el número de resolución, esto es la fecha de condonación
                                pass

                break

    def _group_codes(self, codes: Dict[str, Any]) -> Dict[str, Dict]:
        """Agrupa códigos por categoría para facilitar acceso"""

        # Códigos de cantidades (documentos)
        cantidad_codes = ['503', '110', '758', '509', '708', '584', '500', '519', '527', '531', '534']

        # Códigos de débitos (montos)
        debito_codes = ['502', '111', '759', '510', '709', '501', '538', '562']

        # Códigos de créditos (montos)
        credito_codes = ['511', '520', '528', '532', '535', '504', '077', '544', '779', '537']

        # Códigos de impuestos
        impuesto_codes = ['089', '062', '048', '563', '115', '595', '547', '151']

        # Códigos de totales a pagar
        pago_codes = ['91', '92', '93', '795', '94', '60', '922', '915']

        grouped = {
            'cantidades': {},
            'debitos': {},
            'creditos': {},
            'impuestos': {},
            'pagos': {}
        }

        for code, data in codes.items():
            if code in cantidad_codes:
                grouped['cantidades'][code] = data
            elif code in debito_codes:
                grouped['debitos'][code] = data
            elif code in credito_codes:
                grouped['creditos'][code] = data
            elif code in impuesto_codes:
                grouped['impuestos'][code] = data
            elif code in pago_codes:
                grouped['pagos'][code] = data

        return grouped

    def _calculate_summary(self, codes: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula resumen con los totales más importantes"""
        summary = {}

        # Total débitos (código 538)
        if '538' in codes:
            summary['total_debitos'] = codes['538']['value']

        # Total créditos (código 537)
        if '537' in codes:
            summary['total_creditos'] = codes['537']['value']

        # IVA determinado (código 089)
        if '089' in codes:
            summary['iva_determinado'] = codes['089']['value']

        # PPM neto (código 062)
        if '062' in codes:
            summary['ppm_neto'] = codes['062']['value']

        # Total determinado (código 547)
        if '547' in codes:
            summary['total_determinado'] = codes['547']['value']

        # Total a pagar (código 91)
        if '91' in codes:
            summary['total_pagar'] = codes['91']['value']

        # Calcular diferencia débito-crédito
        if 'total_debitos' in summary and 'total_creditos' in summary:
            summary['diferencia_debito_credito'] = summary['total_debitos'] - summary['total_creditos']

        return summary


def extract_f29_data_from_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Función helper para extraer datos del F29 desde PDF

    Esta es la función principal que se llama desde otros servicios.

    Args:
        pdf_bytes: Contenido del PDF en bytes

    Returns:
        Diccionario con todos los datos extraídos
    """
    extractor = F29PDFExtractor()
    return extractor.extract_from_pdf(pdf_bytes)
