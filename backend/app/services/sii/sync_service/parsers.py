"""
Módulo de parseo de documentos tributarios del SII

Contiene funciones compartidas para parsear y mapear documentos tributarios
desde el formato del SII al formato de la base de datos.
"""
import logging
from datetime import datetime
from typing import Dict, Optional
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)


def parse_date(date_str: Optional[str]) -> datetime.date:
    """
    Parsea fecha del SII a datetime.date

    Formatos soportados:
    - DD/MM/YYYY
    - DD-MM-YYYY (usado por API de boletas de honorarios)
    - DD-MM-YYYY HH:MM (con hora, se ignora el componente de tiempo)
    - YYYY-MM-DD
    - YYYYMMDD (para períodos)

    Raises:
        ValueError: Si la fecha no puede ser parseada
    """
    if not date_str:
        raise ValueError("Fecha no puede ser None o vacía")

    date_str = date_str.strip()

    try:
        # Si tiene espacio, puede tener componente de tiempo - extraer solo la fecha
        if ' ' in date_str:
            date_str = date_str.split(' ')[0].strip()

        # Intentar formato DD/MM/YYYY
        if '/' in date_str:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        # Intentar formato con guiones
        elif '-' in date_str:
            # Detectar si es DD-MM-YYYY o YYYY-MM-DD
            parts = date_str.split('-')
            if len(parts) == 3:
                # Si el primer elemento tiene 4 dígitos, es YYYY-MM-DD
                if len(parts[0]) == 4:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                # Si el primer elemento tiene 1-2 dígitos, es DD-MM-YYYY
                else:
                    return datetime.strptime(date_str, "%d-%m-%Y").date()
            else:
                raise ValueError(f"Formato de fecha con guiones no reconocido: {date_str}")
        # Intentar formato YYYYMMDD (para períodos como "20251001")
        elif len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, "%Y%m%d").date()
        else:
            raise ValueError(f"Formato de fecha no reconocido: {date_str}")
    except ValueError as e:
        logger.error(f"❌ Error parsing date '{date_str}': {e}")
        raise ValueError(f"No se pudo parsear la fecha '{date_str}': {str(e)}")


def get_purchase_document_type_name(tipo_doc: str) -> str:
    """
    Mapea código de tipo de documento de COMPRA a nombre descriptivo

    Args:
        tipo_doc: Código del tipo de documento

    Returns:
        Nombre del tipo de documento de compra
    """
    tipo_map = {
        "33": "factura_compra",
        "34": "factura_exenta_compra",
        "39": "boleta",  # Boletas de compra
        "43": "liquidacion_factura",
        "46": "factura_compra",  # Factura de compra electrónica
        "48": "comprobante_pago",  # Comprobantes de compra
        "56": "nota_debito_compra",
        "61": "nota_credito_compra"
    }
    return tipo_map.get(tipo_doc, "factura_compra")  # Default a factura_compra


def get_sales_document_type_name(tipo_doc: str) -> str:
    """
    Mapea código de tipo de documento de VENTA a nombre descriptivo

    Args:
        tipo_doc: Código del tipo de documento

    Returns:
        Nombre del tipo de documento de venta
    """
    tipo_map = {
        "33": "factura_venta",
        "34": "factura_exenta",
        "39": "boleta",
        "41": "boleta_exenta",
        "43": "liquidacion_factura",
        "48": "comprobante_pago",
        "56": "nota_debito_venta",
        "61": "nota_credito_venta"
    }
    return tipo_map.get(tipo_doc, "factura_venta")  # Default a factura_venta


def parse_honorarios_receipt(boleta: Dict, company_id: UUID, period: str) -> Dict:
    """
    Parsea boleta de honorarios del formato SII al formato DB

    Args:
        boleta: Dict con datos de la boleta desde el scraper
        company_id: UUID de la compañía
        period: Período en formato YYYYMM

    Returns:
        Dict con datos parseados para insertar en DB

    Formato de entrada (desde scraper):
    {
        'numero_boleta': 12345,
        'estado': 'Vigente',
        'fecha_boleta': '15/10/2025',
        'fecha_emision': '15/10/2025',
        'usuario_emision': 'usuario@email.com',
        'sociedad_profesional': False,
        'rut_receptor': '12345678-9',
        'nombre_receptor': 'Empresa Receptora',
        'honorarios_brutos': 500000,
        'retencion_emisor': 0,
        'retencion_receptor': 50000,
        'honorarios_liquidos': 450000,
        'manual': False
    }
    """
    try:
        # Determinar receipt_type basado en el contexto
        # Si la compañía es el receptor, entonces es una boleta RECIBIDA (paid to provider)
        # Si la compañía es el emisor, entonces es una boleta EMITIDA (received for service)
        # Por ahora asumimos que son boletas RECIBIDAS (pagadas a prestadores de servicios)
        receipt_type = "received"

        # Parsear fechas
        issue_date = None
        if boleta.get('fecha_boleta'):
            try:
                issue_date = parse_date(boleta['fecha_boleta'])
            except ValueError:
                pass

        emission_date = None
        if boleta.get('fecha_emision'):
            try:
                emission_date = parse_date(boleta['fecha_emision'])
            except ValueError:
                pass

        # Si no hay issue_date pero hay emission_date, usar emission_date como issue_date
        if not issue_date and emission_date:
            issue_date = emission_date

        # Si no hay ninguna fecha, usar el período
        if not issue_date:
            year = int(period[:4])
            month = int(period[4:6])
            issue_date = datetime(year, month, 1).date()

        # Parsear montos como Decimal
        gross_amount = Decimal(str(boleta.get('honorarios_brutos', 0) or 0))
        issuer_retention = Decimal(str(boleta.get('retencion_emisor', 0) or 0))
        recipient_retention = Decimal(str(boleta.get('retencion_receptor', 0) or 0))
        net_amount = Decimal(str(boleta.get('honorarios_liquidos', 0) or 0))

        # Mapear estado
        estado_raw = boleta.get('estado', 'pending')
        if isinstance(estado_raw, str):
            estado_lower = estado_raw.lower()
            if 'vigente' in estado_lower:
                status = 'vigente'
            elif 'anulad' in estado_lower:
                status = 'anulada'
            else:
                status = 'pending'
        else:
            status = 'pending'

        # Construir documento parseado
        parsed = {
            "company_id": company_id,
            "receipt_type": receipt_type,
            "folio": boleta.get('numero_boleta'),
            "issue_date": issue_date,
            "emission_date": emission_date,

            # Para boletas RECIBIDAS:
            # - El emisor es quien presta el servicio (proveedor)
            # - El receptor es la compañía
            "issuer_rut": None,  # No disponible en datos actuales
            "issuer_name": None,  # No disponible en datos actuales
            "recipient_rut": boleta.get('rut_receptor'),
            "recipient_name": boleta.get('nombre_receptor'),

            # Montos
            "gross_amount": gross_amount,
            "issuer_retention": issuer_retention,
            "recipient_retention": recipient_retention,
            "net_amount": net_amount,

            # Estado y metadata
            "status": status,
            "is_professional_society": boleta.get('sociedad_profesional', False),
            "is_manual": boleta.get('manual', False),
            "emission_user": boleta.get('usuario_emision'),

            # Extra data (guardar raw data para referencia)
            "extra_data": {
                "raw_data": boleta,
                "sync_period": period,
                "synced_at": datetime.now().isoformat()
            }
        }

        return parsed

    except Exception as e:
        logger.error(
            f"❌ Error parsing boleta de honorarios {boleta.get('numero_boleta', 'unknown')}: {e}",
            exc_info=True
        )
        raise


def parse_purchase_document(company_id: UUID, doc: Dict, tipo_doc: str, estado_contab: str = None) -> Dict:
    """
    Parsea documento de compra del formato SII al formato DB

    Args:
        company_id: ID de la empresa
        doc: Documento raw del SII
        tipo_doc: Tipo de documento SII (33, 56, 61, etc.) - viene del parámetro de extracción
        estado_contab: Estado contable del documento ("PENDIENTE" o "REGISTRO")
    """
    # Obtener RUT y convertir a string si es necesario
    sender_rut = doc.get('detRutDoc')
    if sender_rut is not None:
        sender_rut = str(sender_rut)

    # Usar el tipo_doc del parámetro (ya que detTpoDoc viene null del SII)
    # Fallback a detTpoDoc solo si existe (para compatibilidad futura)
    tipo_doc_sii = str(doc.get('detTpoDoc') or tipo_doc)
    document_type = get_purchase_document_type_name(tipo_doc_sii)

    return {
        "company_id": company_id,
        "document_type": document_type,
        "folio": int(doc.get('detNroDoc') or doc.get('folio', 0)),
        "issue_date": parse_date(doc.get('detFchDoc') or doc.get('fecha')),
        "sender_rut": sender_rut,
        "sender_name": doc.get('detRznSoc'),
        "net_amount": Decimal(str(doc.get('detMntNeto', 0))),
        "tax_amount": Decimal(str(doc.get('detMntIVA', 0))),
        "exempt_amount": Decimal(str(doc.get('detMntExento', 0))),
        "total_amount": Decimal(str(doc.get('detMntTotal', 0))),
        "status": "pending",
        "accounting_state": estado_contab,  # PENDIENTE o REGISTRO
        "extra_data": doc  # Guardar datos completos
    }


def parse_sales_document(company_id: UUID, doc: Dict, tipo_doc: str) -> Dict:
    """
    Parsea documento de venta del formato SII al formato DB

    Args:
        company_id: ID de la empresa
        doc: Documento raw del SII
        tipo_doc: Tipo de documento SII (33, 39, 56, 61, etc.) - viene del parámetro de extracción
    """
    # Obtener RUT y convertir a string si es necesario
    recipient_rut = doc.get('detRutDoc')
    if recipient_rut is not None:
        recipient_rut = str(recipient_rut)

    # Usar el tipo_doc del parámetro (ya que detTpoDoc viene null del SII)
    # Fallback a detTpoDoc solo si existe (para compatibilidad futura)
    tipo_doc_sii = str(doc.get('detTpoDoc') or tipo_doc)
    document_type = get_sales_document_type_name(tipo_doc_sii)

    return {
        "company_id": company_id,
        "document_type": document_type,
        "folio": int(doc.get('detNroDoc') or doc.get('folio', 0)),
        "issue_date": parse_date(doc.get('detFchDoc') or doc.get('fecha')),
        "recipient_rut": recipient_rut,
        "recipient_name": doc.get('detRznSoc'),
        "net_amount": Decimal(str(doc.get('detMntNeto', 0))),
        "tax_amount": Decimal(str(doc.get('detMntIVA', 0))),
        "exempt_amount": Decimal(str(doc.get('detMntExento', 0))),
        "total_amount": Decimal(str(doc.get('detMntTotal', 0))),
        "status": "pending",
        "extra_data": doc  # Guardar datos completos
    }


def parse_daily_purchase_document(
    company_id: UUID,
    period: str,
    tipo_doc: str,
    daily_doc: Dict
) -> Dict:
    """
    Parsea total diario de boletas/comprobantes de compra

    Args:
        company_id: ID de la empresa
        period: Período en formato YYYYMM
        tipo_doc: Tipo de documento (39, 48, etc.)
        daily_doc: Documento diario del SII
    """
    # Extraer día del documento diario
    # El SII devuelve 'dia' como número (1, 2, 3, etc.)
    dia = daily_doc.get('dia')
    if not dia:
        raise ValueError(f"Daily document missing 'dia' field: {daily_doc}")

    # Construir fecha completa: YYYYMMDD
    year = period[:4]
    month = period[4:6]
    fecha_str = f"{year}{month}{dia:02d}"

    # Parsear fecha
    issue_date = parse_date(fecha_str)

    # Generar folio único: YYYYMMDD + TIPO (ej: 2025090139)
    folio = int(f"{issue_date.strftime('%Y%m%d')}{tipo_doc}")

    # Determinar nombre según tipo de documento
    # 39 = Boleta Electrónica, 48 = Comprobante de Pago Electrónico
    if tipo_doc == "39":
        sender_name = "Boleta Electrónica"
    elif tipo_doc == "48":
        sender_name = "Venta Electrónica"
    else:
        sender_name = "Total Diario"

    return {
        "company_id": company_id,
        "document_type": get_purchase_document_type_name(tipo_doc),
        "folio": folio,
        "issue_date": issue_date,
        "sender_rut": None,
        "sender_name": sender_name,
        "net_amount": Decimal(str(daily_doc.get('montoNeto', 0))),
        "tax_amount": Decimal(str(daily_doc.get('montoIva', 0))),
        "exempt_amount": Decimal(str(daily_doc.get('montoExento', 0))),
        "total_amount": Decimal(str(daily_doc.get('montoTotal', 0))),
        "status": "pending",
        "extra_data": {
            "is_daily_summary": True,
            "period": period,
            "tipo_doc": tipo_doc,
            "total_documents": int(daily_doc.get('totalDocumentos', 0)),
            "daily_data": daily_doc
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def parse_daily_sales_document(
    company_id: UUID,
    period: str,
    tipo_doc: str,
    daily_doc: Dict
) -> Dict:
    """
    Parsea total diario de boletas/comprobantes de venta

    Args:
        company_id: ID de la empresa
        period: Período en formato YYYYMM
        tipo_doc: Tipo de documento (39, 48, etc.)
        daily_doc: Documento diario del SII
    """
    # Extraer día del documento diario
    # El SII devuelve 'dia' como número (1, 2, 3, etc.)
    dia = daily_doc.get('dia')
    if not dia:
        raise ValueError(f"Daily document missing 'dia' field: {daily_doc}")

    # Construir fecha completa: YYYYMMDD
    year = period[:4]
    month = period[4:6]
    fecha_str = f"{year}{month}{dia:02d}"

    # Parsear fecha
    issue_date = parse_date(fecha_str)

    # Generar folio único: YYYYMMDD + TIPO (ej: 2025090139)
    folio = int(f"{issue_date.strftime('%Y%m%d')}{tipo_doc}")

    # Determinar nombre según tipo de documento
    # 39 = Boleta Electrónica, 48 = Comprobante de Pago Electrónico
    if tipo_doc == "39":
        recipient_name = "Boleta Electrónica"
    elif tipo_doc == "48":
        recipient_name = "Venta Electrónica"
    else:
        recipient_name = "Total Diario"

    return {
        "company_id": company_id,
        "document_type": get_sales_document_type_name(tipo_doc),
        "folio": folio,
        "issue_date": issue_date,
        "recipient_rut": None,
        "recipient_name": recipient_name,
        "net_amount": Decimal(str(daily_doc.get('montoNeto', 0))),
        "tax_amount": Decimal(str(daily_doc.get('montoIva', 0))),
        "exempt_amount": Decimal(str(daily_doc.get('montoExento', 0))),
        "total_amount": Decimal(str(daily_doc.get('montoTotal', 0))),
        "status": "pending",
        "extra_data": {
            "is_daily_summary": True,
            "period": period,
            "tipo_doc": tipo_doc,
            "total_documents": int(daily_doc.get('totalDocumentos', 0)),
            "daily_data": daily_doc
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def parse_monthly_summary(
    company_id: UUID,
    period: str,
    tipo_doc: str,
    resumen_item: Dict,
    document_type_mapper
) -> Dict:
    """
    Parsea resumen mensual de documentos

    Args:
        company_id: ID de la empresa
        period: Período en formato YYYYMM
        tipo_doc: Tipo de documento
        resumen_item: Item del resumen con datos agregados
        document_type_mapper: Función para mapear tipo de documento
    """
    # Generar folio único: PERIODO + TIPO (ej: 20251039)
    folio = int(f"{period}{tipo_doc}")

    return {
        "company_id": company_id,
        "document_type": document_type_mapper(tipo_doc),
        "folio": folio,
        "issue_date": parse_date(f"{period}01"),  # Primer día del mes
        "net_amount": Decimal(str(resumen_item.get('rsmnMntNeto', 0))),
        "tax_amount": Decimal(str(resumen_item.get('rsmnMntIVA', 0))),
        "exempt_amount": Decimal(str(resumen_item.get('rsmnMntExento', 0))),
        "total_amount": Decimal(str(resumen_item.get('rsmnMntTotal', 0))),
        "status": "pending",
        "extra_data": {
            "is_monthly_summary": True,
            "period": period,
            "tipo_doc": tipo_doc,
            "total_documents": resumen_item.get('rsmnTotDoc', 0),
            "resumen_completo": resumen_item
        }
    }
