"""
Servicio para extraer datos estructurados de PDFs del Formulario 29 (F29)
"""
import logging
import re
from decimal import Decimal
from typing import Dict, Optional, Any, List
from io import BytesIO

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

logger = logging.getLogger(__name__)


class F29PDFExtractor:
    """
    Extractor de datos estructurados desde PDFs del Formulario 29

    Extrae campos clave del F29 como:
    - Ventas y débito fiscal
    - Compras y crédito fiscal
    - IVA determinado
    - Período y folio
    """

    def __init__(self):
        if PdfReader is None:
            raise ImportError(
                "pypdf o PyPDF2 es requerido para extraer datos de PDFs. "
                "Instala con: pip install pypdf"
            )

    def extract_from_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extrae el 100% del contenido estructurado del PDF del F29

        Args:
            pdf_bytes: Contenido del PDF en bytes

        Returns:
            Diccionario con TODO el contenido extraído:
            {
                'period_year': int,
                'period_month': int,
                'folio': str,
                'total_sales': Decimal,
                'taxable_sales': Decimal,
                'exempt_sales': Decimal,
                'sales_tax': Decimal (débito fiscal),
                'total_purchases': Decimal,
                'taxable_purchases': Decimal,
                'purchases_tax': Decimal (crédito fiscal),
                'iva_to_pay': Decimal,
                'iva_credit': Decimal,
                'net_iva': Decimal (IVA determinado),
                'raw_content': {
                    'full_text': str,  # Texto completo extraído
                    'pages': list,     # Texto por página
                    'lines': list,     # Todas las líneas
                    'parsed_fields': dict,  # TODOS los campos parseados
                },
                'extra_data': dict  # Campos adicionales
            }
        """
        try:
            # Leer PDF
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PdfReader(pdf_file)

            # Extraer TODO el texto página por página
            pages_text = []
            full_text = ""
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                pages_text.append({
                    'page_number': i + 1,
                    'text': page_text,
                    'char_count': len(page_text)
                })
                full_text += page_text

            logger.info(f"Texto extraído del PDF: {len(full_text)} caracteres en {len(pages_text)} páginas")

            # Dividir en líneas para análisis completo
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]

            # Parsear datos estructurados
            extracted_data = self._parse_f29_text(full_text)

            # Agregar TODO el contenido raw
            extracted_data['raw_content'] = {
                'full_text': full_text,
                'pages': pages_text,
                'lines': lines,
                'line_count': len(lines),
                'char_count': len(full_text),
                'parsed_fields': self._extract_all_fields(full_text, lines)
            }

            return extracted_data

        except Exception as e:
            logger.error(f"Error extrayendo datos del PDF: {e}")
            raise

    def _parse_f29_text(self, text: str) -> Dict[str, Any]:
        """
        Parsea el texto extraído del PDF para obtener los campos del F29

        Args:
            text: Texto completo extraído del PDF

        Returns:
            Diccionario con datos parseados
        """
        data = {
            'extra_data': {}
        }

        # 1. Extraer período (mes y año)
        period = self._extract_period(text)
        if period:
            data['period_year'] = period['year']
            data['period_month'] = period['month']

        # 2. Extraer folio
        folio = self._extract_folio(text)
        if folio:
            data['folio'] = folio

        # 3. Extraer ventas y débito fiscal
        # Buscar patrones como:
        # - "DEBITO FISCAL" seguido de números
        # - "Total Ventas" o "Ventas Netas"
        # - "IVA Débito"

        sales_data = self._extract_sales_data(text)
        data.update(sales_data)

        # 4. Extraer compras y crédito fiscal
        purchases_data = self._extract_purchases_data(text)
        data.update(purchases_data)

        # 5. Extraer IVA determinado
        iva_data = self._extract_iva_calculation(text)
        data.update(iva_data)

        # 6. Guardar texto completo en extra_data para referencia
        data['extra_data']['full_text_preview'] = text[:500]  # Primeros 500 chars

        return data

    def _extract_period(self, text: str) -> Optional[Dict[str, int]]:
        """Extrae el período (mes y año) del F29"""
        # Patrones comunes:
        # - "PERIODO TRIBUTARIO: 01/2024"
        # - "MES: 01 AÑO: 2024"
        # - "ENERO 2024"

        patterns = [
            r'PERIODO\s+TRIBUTARIO[:\s]+(\d{2})/(\d{4})',
            r'MES[:\s]+(\d{2})\s+A[ÑN]O[:\s]+(\d{4})',
            r'(\d{2})/(\d{4})',  # Formato simple MM/YYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                month = int(match.group(1))
                year = int(match.group(2))
                logger.debug(f"Período extraído: {month}/{year}")
                return {'month': month, 'year': year}

        logger.warning("No se pudo extraer el período del PDF")
        return None

    def _extract_folio(self, text: str) -> Optional[str]:
        """Extrae el número de folio del F29"""
        # Patrones: "FOLIO: 123456789" o "Nº FOLIO: 123456789"
        patterns = [
            r'FOLIO[:\s]+(\d{8,10})',
            r'N[°º]\s*FOLIO[:\s]+(\d{8,10})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                folio = match.group(1)
                logger.debug(f"Folio extraído: {folio}")
                return folio

        logger.warning("No se pudo extraer el folio del PDF")
        return None

    def _extract_sales_data(self, text: str) -> Dict[str, Decimal]:
        """Extrae datos de ventas y débito fiscal"""
        data = {
            'total_sales': Decimal('0'),
            'taxable_sales': Decimal('0'),
            'exempt_sales': Decimal('0'),
            'sales_tax': Decimal('0'),  # Débito fiscal
        }

        # Buscar débito fiscal (IVA de ventas)
        # Patrones: "DEBITO FISCAL" o "IVA DEBITO" seguido de monto
        debito_patterns = [
            r'DEBITO\s+FISCAL[:\s]+\$?\s*([\d.,]+)',
            r'IVA\s+DEBITO[:\s]+\$?\s*([\d.,]+)',
            r'TOTAL\s+DEBITO[:\s]+\$?\s*([\d.,]+)',
        ]

        for pattern in debito_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace('.', '').replace(',', '.')
                data['sales_tax'] = Decimal(amount_str)
                logger.debug(f"Débito fiscal extraído: {data['sales_tax']}")
                break

        # Calcular ventas afectas aproximadas (débito / 0.19)
        if data['sales_tax'] > 0:
            data['taxable_sales'] = (data['sales_tax'] / Decimal('0.19')).quantize(Decimal('0.01'))

        return data

    def _extract_purchases_data(self, text: str) -> Dict[str, Decimal]:
        """Extrae datos de compras y crédito fiscal"""
        data = {
            'total_purchases': Decimal('0'),
            'taxable_purchases': Decimal('0'),
            'purchases_tax': Decimal('0'),  # Crédito fiscal
        }

        # Buscar crédito fiscal (IVA de compras)
        # Patrones: "CREDITO FISCAL" o "IVA CREDITO" seguido de monto
        credito_patterns = [
            r'CREDITO\s+FISCAL[:\s]+\$?\s*([\d.,]+)',
            r'IVA\s+CREDITO[:\s]+\$?\s*([\d.,]+)',
            r'TOTAL\s+CREDITO[:\s]+\$?\s*([\d.,]+)',
        ]

        for pattern in credito_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace('.', '').replace(',', '.')
                data['purchases_tax'] = Decimal(amount_str)
                logger.debug(f"Crédito fiscal extraído: {data['purchases_tax']}")
                break

        # Calcular compras afectas aproximadas (crédito / 0.19)
        if data['purchases_tax'] > 0:
            data['taxable_purchases'] = (data['purchases_tax'] / Decimal('0.19')).quantize(Decimal('0.01'))

        return data

    def _extract_iva_calculation(self, text: str) -> Dict[str, Decimal]:
        """Extrae el cálculo de IVA (determinación)"""
        data = {
            'iva_to_pay': Decimal('0'),
            'iva_credit': Decimal('0'),
            'net_iva': Decimal('0'),
        }

        # Buscar IVA determinado o IVA a pagar
        # Patrones: "IVA DETERMINADO", "IVA A PAGAR", "REMANENTE"
        iva_patterns = [
            r'IVA\s+DETERMINADO[:\s]+\$?\s*([\d.,]+)',
            r'IVA\s+A\s+PAGAR[:\s]+\$?\s*([\d.,]+)',
            r'TOTAL\s+A\s+PAGAR[:\s]+\$?\s*([\d.,]+)',
        ]

        for pattern in iva_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace('.', '').replace(',', '.')
                amount = Decimal(amount_str)

                if amount > 0:
                    data['net_iva'] = amount
                    data['iva_to_pay'] = amount
                else:
                    data['net_iva'] = amount
                    data['iva_credit'] = abs(amount)

                logger.debug(f"IVA determinado extraído: {data['net_iva']}")
                break

        return data

    def _extract_all_fields(self, text: str, lines: List[str]) -> Dict[str, Any]:
        """
        Extrae TODOS los campos posibles del F29 usando múltiples patrones

        Args:
            text: Texto completo del PDF
            lines: Lista de líneas del PDF

        Returns:
            Diccionario con todos los campos encontrados
        """
        all_fields = {}

        # Lista completa de campos del F29 (basado en el formulario oficial)
        # Usaremos patrones genéricos para capturar todo

        # 1. Números de casillas (el F29 tiene casillas numeradas)
        # Patrón: "[número] ... [valor]"
        casilla_pattern = r'\[(\d+)\]\s*([^\[]*?)(?=\[|$)'
        casillas = re.findall(casilla_pattern, text, re.DOTALL)
        if casillas:
            all_fields['casillas'] = {}
            for casilla_num, casilla_valor in casillas:
                all_fields['casillas'][casilla_num] = casilla_valor.strip()

        # 2. Buscar todos los montos (números con formato chileno)
        # Patrón: $123.456 o 123.456
        monto_pattern = r'\$?\s*([\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{2})?)'
        montos = re.findall(monto_pattern, text)
        all_fields['montos_encontrados'] = montos[:50]  # Primeros 50 montos

        # 3. Extraer todas las etiquetas y sus valores
        # Buscar patrones como "ETIQUETA: VALOR" o "ETIQUETA VALOR"
        label_pattern = r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+[A-ZÁÉÍÓÚÑ])\s*[:\-]?\s*\$?\s*([\d.,]+|[A-Z0-9\-]+)'
        labels = re.findall(label_pattern, text)
        if labels:
            all_fields['campos_etiquetados'] = {}
            for label, valor in labels:
                label_clean = label.strip()
                if len(label_clean) > 3:  # Filtrar labels muy cortas
                    all_fields['campos_etiquetados'][label_clean] = valor.strip()

        # 4. Información del contribuyente
        rut_pattern = r'RUT[:\s]+(\d{1,2}\.\d{3}\.\d{3}-[\dK])'
        rut_match = re.search(rut_pattern, text, re.IGNORECASE)
        if rut_match:
            all_fields['rut_contribuyente'] = rut_match.group(1)

        nombre_pattern = r'(?:NOMBRE|RAZ[ÓO]N SOCIAL)[:\s]+([A-ZÁÉÍÓÚÑ\s]+(?:[A-ZÁÉÍÓÚÑ]|S\.A\.|LTDA\.|SPA))'
        nombre_match = re.search(nombre_pattern, text, re.IGNORECASE)
        if nombre_match:
            all_fields['nombre_contribuyente'] = nombre_match.group(1).strip()

        # 5. Fecha de presentación
        fecha_pattern = r'(?:FECHA|PRESENTACI[ÓO]N)[:\s]+(\d{2}/\d{2}/\d{4})'
        fecha_match = re.search(fecha_pattern, text, re.IGNORECASE)
        if fecha_match:
            all_fields['fecha_presentacion'] = fecha_match.group(1)

        # 6. Detectar secciones del formulario
        secciones = {
            'ventas_servicios': r'VENTAS?\s+Y\s+SERVICIOS|D[ÉE]BITO\s+FISCAL',
            'compras': r'COMPRAS?\s+Y\s+SERVICIOS|CR[ÉE]DITO\s+FISCAL',
            'remanente': r'REMANENTE|SALDO\s+A\s+FAVOR',
            'determinacion_iva': r'DETERMINACI[ÓO]N\s+(?:DEL\s+)?IVA|IVA\s+DETERMINADO',
            'otros_impuestos': r'OTROS\s+IMPUESTOS|IMPUESTOS\s+ADICIONALES'
        }

        all_fields['secciones_encontradas'] = {}
        for seccion, pattern in secciones.items():
            if re.search(pattern, text, re.IGNORECASE):
                all_fields['secciones_encontradas'][seccion] = True

        # 7. Capturar tablas (líneas que parecen tener estructura tabular)
        # Buscar líneas con múltiples números separados por espacios
        tabla_lines = []
        for line in lines:
            # Si la línea tiene 2 o más números, podría ser parte de una tabla
            numeros_en_linea = re.findall(r'[\d.,]+', line)
            if len(numeros_en_linea) >= 2:
                tabla_lines.append({
                    'line': line,
                    'values': numeros_en_linea
                })

        if tabla_lines:
            all_fields['posibles_tablas'] = tabla_lines[:20]  # Primeras 20 líneas tabulares

        # 8. Totales y subtotales
        total_patterns = {
            'total_debito_fiscal': r'TOTAL\s+D[ÉE]BITO\s+FISCAL[:\s]+\$?\s*([\d.,]+)',
            'total_credito_fiscal': r'TOTAL\s+CR[ÉE]DITO\s+FISCAL[:\s]+\$?\s*([\d.,]+)',
            'total_a_pagar': r'TOTAL\s+A\s+PAGAR[:\s]+\$?\s*([\d.,]+)',
            'total_remanente': r'TOTAL\s+REMANENTE[:\s]+\$?\s*([\d.,]+)',
        }

        all_fields['totales'] = {}
        for key, pattern in total_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                all_fields['totales'][key] = match.group(1)

        # 9. Códigos de actividad económica
        codigo_actividad_pattern = r'C[ÓO]DIGO\s+ACTIVIDAD[:\s]+(\d+)'
        codigo_match = re.search(codigo_actividad_pattern, text, re.IGNORECASE)
        if codigo_match:
            all_fields['codigo_actividad_economica'] = codigo_match.group(1)

        # 10. Guardar líneas que contienen palabras clave importantes
        keywords = ['IVA', 'DÉBITO', 'CRÉDITO', 'TOTAL', 'SUBTOTAL', 'VENTAS', 'COMPRAS',
                   'EXENTA', 'AFECTA', 'EXPORTACIÓN', 'REMANENTE', 'PAGAR']

        all_fields['lineas_importantes'] = []
        for line in lines:
            if any(keyword in line.upper() for keyword in keywords):
                all_fields['lineas_importantes'].append(line)

        # Limitar a 100 líneas para no saturar
        all_fields['lineas_importantes'] = all_fields['lineas_importantes'][:100]

        return all_fields


# Función helper para uso rápido
def extract_f29_data_from_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Función helper para extraer datos de un PDF F29

    Args:
        pdf_bytes: Contenido del PDF en bytes

    Returns:
        Diccionario con datos extraídos
    """
    extractor = F29PDFExtractor()
    return extractor.extract_from_pdf(pdf_bytes)
