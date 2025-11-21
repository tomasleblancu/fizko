"""
Document parsers for SII data.

Maps SII document format to database schema.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


# Exported parser functions
__all__ = [
    "parse_purchase_document",
    "parse_sales_document",
    "parse_daily_purchase_document",
    "parse_daily_sales_document",
    "parse_honorarios_receipt",
    "parse_date",
    "parse_amount",
    "get_document_type_name",
]


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parse SII date to ISO format (YYYY-MM-DD).

    Supported formats:
    - DD/MM/YYYY
    - DD-MM-YYYY
    - DD-MM-YYYY HH:MM (with time, time component ignored)
    - YYYY-MM-DD
    - YYYYMMDD (for periods)

    Returns:
        ISO formatted date string (YYYY-MM-DD) or None if parsing fails
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    try:
        # If contains space, may have time component - extract only date
        if ' ' in date_str:
            date_str = date_str.split(' ')[0].strip()

        # Try DD/MM/YYYY format
        if '/' in date_str:
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")

        # Try formats with dashes
        elif '-' in date_str:
            parts = date_str.split('-')
            if len(parts) == 3:
                # If first element has 4 digits, it's YYYY-MM-DD (already ISO)
                if len(parts[0]) == 4:
                    return date_str
                # If first element has 1-2 digits, it's DD-MM-YYYY
                else:
                    dt = datetime.strptime(date_str, "%d-%m-%Y")
                    return dt.strftime("%Y-%m-%d")

        # Try YYYYMMDD format (for periods like "20251001")
        elif len(date_str) == 8 and date_str.isdigit():
            dt = datetime.strptime(date_str, "%Y%m%d")
            return dt.strftime("%Y-%m-%d")

        logger.warning(f"⚠️ Unrecognized date format: {date_str}")
        return None

    except ValueError as e:
        logger.error(f"❌ Error parsing date '{date_str}': {e}")
        return None


def get_document_type_name(tipo_doc: str, is_purchase: bool = True) -> str:
    """
    Map SII document type code to descriptive name.

    Args:
        tipo_doc: Document type code from SII
        is_purchase: True for purchase documents, False for sales

    Returns:
        Document type name for database
    """
    if is_purchase:
        tipo_map = {
            "33": "factura_compra",
            "34": "factura_exenta_compra",
            "39": "boleta",
            "43": "liquidacion_factura",
            "46": "factura_compra",
            "48": "comprobante_pago",
            "56": "nota_debito_compra",
            "61": "nota_credito_compra",
            "914": "declaracion_ingreso"
        }
    else:
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

    default = "factura_compra" if is_purchase else "factura_venta"
    return tipo_map.get(str(tipo_doc), default)


def parse_amount(value: Any) -> float:
    """
    Parse amount value to float, handling various formats.

    Args:
        value: Amount value (could be str, int, float, Decimal, None)

    Returns:
        Float value (0.0 if parsing fails)
    """
    if value is None:
        return 0.0

    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            # Remove thousands separators and convert comma to dot
            clean_value = value.replace(".", "").replace(",", ".")
            return float(clean_value)
        return 0.0
    except (ValueError, TypeError):
        logger.warning(f"⚠️ Could not parse amount: {value}")
        return 0.0


def parse_purchase_document(
    company_id: str,
    doc: Dict[str, Any],
    tipo_doc: str,
    estado_contab: str = "REGISTRO"
) -> Dict[str, Any]:
    """
    Parse purchase document from SII format to database format.

    Args:
        company_id: Company UUID
        doc: Raw document from SII
        tipo_doc: Document type code (33, 56, 61, etc.)
        estado_contab: Accounting state ("PENDIENTE" or "REGISTRO")

    Returns:
        Parsed document ready for database insertion
    """
    # Get folio (document number)
    folio = doc.get('detNroDoc') or doc.get('folio')
    if folio is not None:
        try:
            folio = int(folio)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Invalid folio: {folio}")
            folio = None

    # Get RUT and convert to string
    sender_rut = doc.get('detRutDoc')
    if sender_rut is not None:
        sender_rut = str(sender_rut)

    # Map document type
    document_type = get_document_type_name(tipo_doc, is_purchase=True)

    # Parse dates
    issue_date_str = doc.get('detFchDoc') or doc.get('fecha')
    issue_date = parse_date(issue_date_str)

    reception_date_str = doc.get('detFecRecepcion')
    reception_date = parse_date(reception_date_str)

    # Calculate accounting_date (fecha contable)
    # For DIN documents: use issue_date
    # For all other purchases: use reception_date
    is_din = document_type == 'declaracion_ingreso'
    accounting_date = issue_date if is_din else reception_date

    # Parse amounts
    net_amount = parse_amount(doc.get('detMntNeto', 0))
    tax_amount = parse_amount(doc.get('detMntIVA', 0))
    exempt_amount = parse_amount(doc.get('detMntExento', 0))
    total_amount = parse_amount(doc.get('detMntTotal', 0))
    overdue_iva_credit = parse_amount(doc.get('detIVAFueraPlazo', 0))

    # Parse reference document fields (e.g., credit note referencing invoice)
    reference_document_type = doc.get('detTipoDocRef')
    if reference_document_type is not None:
        reference_document_type = str(reference_document_type)

    reference_folio = doc.get('detFolioDocRef')
    if reference_folio is not None:
        try:
            reference_folio = int(reference_folio)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Invalid reference folio: {reference_folio}")
            reference_folio = None

    return {
        "company_id": company_id,
        "document_type": document_type,
        "document_type_code": str(tipo_doc),  # Numeric SII document type code
        "folio": folio,
        "issue_date": issue_date,  # Changed from emission_date to issue_date
        "reception_date": reception_date,  # Date when document was received at SII
        "accounting_date": accounting_date,  # Date for tax recognition (DIN: issue_date, others: reception_date)
        "sender_rut": sender_rut,
        "sender_name": doc.get('detRznSoc'),
        "net_amount": net_amount,
        "tax_amount": tax_amount,
        "exempt_amount": exempt_amount,
        "total_amount": total_amount,
        "overdue_iva_credit": overdue_iva_credit,
        "status": "pending",
        "accounting_state": estado_contab,
        "reference_document_type": reference_document_type,
        "reference_folio": reference_folio,
        "extra_data": doc  # Store raw data for reference
    }


def parse_sales_document(
    company_id: str,
    doc: Dict[str, Any],
    tipo_doc: str
) -> Dict[str, Any]:
    """
    Parse sales document from SII format to database format.

    Args:
        company_id: Company UUID
        doc: Raw document from SII
        tipo_doc: Document type code (33, 39, 56, 61, etc.)

    Returns:
        Parsed document ready for database insertion
    """
    # Get folio (document number)
    folio = doc.get('detNroDoc') or doc.get('folio')
    if folio is not None:
        try:
            folio = int(folio)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Invalid folio: {folio}")
            folio = None

    # Get RUT and convert to string
    recipient_rut = doc.get('detRutDoc')
    if recipient_rut is not None:
        recipient_rut = str(recipient_rut)

    # Map document type
    document_type = get_document_type_name(tipo_doc, is_purchase=False)

    # Parse dates
    issue_date_str = doc.get('detFchDoc') or doc.get('fecha')
    issue_date = parse_date(issue_date_str)

    reception_date_str = doc.get('detFecRecepcion')
    reception_date = parse_date(reception_date_str)

    # Calculate accounting_date (fecha contable)
    # For ALL sales documents (facturas, boletas, comprobantes de pago): always use issue_date
    accounting_date = issue_date

    # Parse amounts
    net_amount = parse_amount(doc.get('detMntNeto', 0))
    tax_amount = parse_amount(doc.get('detMntIVA', 0))
    exempt_amount = parse_amount(doc.get('detMntExento', 0))
    total_amount = parse_amount(doc.get('detMntTotal', 0))
    overdue_iva_credit = parse_amount(doc.get('detIVAFueraPlazo', 0))

    # Parse reference document fields (e.g., credit note referencing invoice)
    reference_document_type = doc.get('detTipoDocRef')
    if reference_document_type is not None:
        reference_document_type = str(reference_document_type)

    reference_folio = doc.get('detFolioDocRef')
    if reference_folio is not None:
        try:
            reference_folio = int(reference_folio)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Invalid reference folio: {reference_folio}")
            reference_folio = None

    return {
        "company_id": company_id,
        "document_type": document_type,
        "document_type_code": str(tipo_doc),  # Numeric SII document type code
        "folio": folio,
        "issue_date": issue_date,
        "reception_date": reception_date,  # Date when document was received at SII
        "accounting_date": accounting_date,  # Date for tax recognition (always issue_date for sales)
        "recipient_rut": recipient_rut,  # Changed to recipient_rut (correct schema name)
        "recipient_name": doc.get('detRznSoc'),  # Changed to recipient_name (correct schema name)
        "net_amount": net_amount,
        "tax_amount": tax_amount,
        "exempt_amount": exempt_amount,
        "total_amount": total_amount,
        "overdue_iva_credit": overdue_iva_credit,
        "status": "pending",
        "reference_document_type": reference_document_type,
        "reference_folio": reference_folio,
        "extra_data": doc  # Store raw data for reference
    }


def parse_daily_purchase_document(
    company_id: str,
    period: str,
    tipo_doc: str,
    daily_doc: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parse daily purchase document (boletas/comprobantes) from SII to database format.

    Args:
        company_id: Company UUID
        period: Period in format YYYYMM
        tipo_doc: Document type code (39 for boletas, 48 for comprobantes)
        daily_doc: Daily document data from SII

    Returns:
        Parsed daily document ready for database insertion
    """
    # Extract day from daily document
    dia = daily_doc.get('dia')
    if not dia:
        raise ValueError(f"Daily document missing 'dia' field: {daily_doc}")

    # Build full date: YYYYMMDD
    year = period[:4]
    month = period[4:6]
    fecha_str = f"{year}{month}{int(dia):02d}"

    # Parse date to ISO format
    issue_date = parse_date(fecha_str)

    # Generate unique folio: YYYYMMDD + TIPO (e.g., 2025090139)
    folio = int(f"{year}{month}{int(dia):02d}{tipo_doc}")

    # Determine name based on document type
    if tipo_doc == "39":
        sender_name = "Boleta Electrónica"
    elif tipo_doc == "48":
        sender_name = "Venta Electrónica"
    else:
        sender_name = "Total Diario"

    # Parse amounts
    net_amount = parse_amount(daily_doc.get('montoNeto', 0))
    tax_amount = parse_amount(daily_doc.get('montoIva', 0))
    exempt_amount = parse_amount(daily_doc.get('montoExento', 0))
    total_amount = parse_amount(daily_doc.get('montoTotal', 0))

    return {
        "company_id": company_id,
        "document_type": get_document_type_name(tipo_doc, is_purchase=True),
        "document_type_code": str(tipo_doc),  # Numeric SII document type code
        "folio": folio,
        "issue_date": issue_date,
        "reception_date": issue_date,  # For daily summaries, reception_date = issue_date
        "accounting_date": issue_date,  # For purchases (boletas/comprobantes): use issue_date
        "sender_rut": None,
        "sender_name": sender_name,
        "net_amount": net_amount,
        "tax_amount": tax_amount,
        "exempt_amount": exempt_amount,
        "total_amount": total_amount,
        "status": "pending",
        "accounting_state": "REGISTRO",
        "extra_data": {
            "is_daily_summary": True,
            "period": period,
            "tipo_doc": tipo_doc,
            "total_documents": int(daily_doc.get('totalDocumentos', 0)),
            "daily_data": daily_doc
        }
    }


def parse_daily_sales_document(
    company_id: str,
    period: str,
    tipo_doc: str,
    daily_doc: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parse daily sales document (boletas/comprobantes) from SII to database format.

    Args:
        company_id: Company UUID
        period: Period in format YYYYMM
        tipo_doc: Document type code (39 for boletas, 48 for comprobantes)
        daily_doc: Daily document data from SII

    Returns:
        Parsed daily document ready for database insertion
    """
    # Extract day from daily document
    dia = daily_doc.get('dia')
    if not dia:
        raise ValueError(f"Daily document missing 'dia' field: {daily_doc}")

    # Build full date: YYYYMMDD
    year = period[:4]
    month = period[4:6]
    fecha_str = f"{year}{month}{int(dia):02d}"

    # Parse date to ISO format
    issue_date = parse_date(fecha_str)

    # Generate unique folio: YYYYMMDD + TIPO (e.g., 2025090139)
    folio = int(f"{year}{month}{int(dia):02d}{tipo_doc}")

    # Determine name based on document type
    if tipo_doc == "39":
        recipient_name = "Boleta Electrónica"
    elif tipo_doc == "48":
        recipient_name = "Venta Electrónica"
    else:
        recipient_name = "Total Diario"

    # Parse amounts
    net_amount = parse_amount(daily_doc.get('montoNeto', 0))
    tax_amount = parse_amount(daily_doc.get('montoIva', 0))
    exempt_amount = parse_amount(daily_doc.get('montoExento', 0))
    total_amount = parse_amount(daily_doc.get('montoTotal', 0))

    return {
        "company_id": company_id,
        "document_type": get_document_type_name(tipo_doc, is_purchase=False),
        "document_type_code": str(tipo_doc),  # Numeric SII document type code
        "folio": folio,
        "issue_date": issue_date,
        "reception_date": issue_date,  # For daily summaries, reception_date = issue_date
        "accounting_date": issue_date,  # For sales: always use issue_date
        "recipient_rut": None,
        "recipient_name": recipient_name,
        "net_amount": net_amount,
        "tax_amount": tax_amount,
        "exempt_amount": exempt_amount,
        "total_amount": total_amount,
        "status": "pending",
        "extra_data": {
            "is_daily_summary": True,
            "period": period,
            "tipo_doc": tipo_doc,
            "total_documents": int(daily_doc.get('totalDocumentos', 0)),
            "daily_data": daily_doc
        }
    }


def parse_honorarios_receipt(
    company_id: str,
    boleta: Dict[str, Any],
    period: str,
    company_rut: str = None,
    company_name: str = None
) -> Dict[str, Any]:
    """
    Parse honorarios receipt from SII format to database format.

    Args:
        company_id: Company UUID
        boleta: Receipt data from SII
        period: Period in format YYYYMM
        company_rut: Company RUT (not used, for compatibility)
        company_name: Company name (not used, for compatibility)

    Returns:
        Parsed receipt ready for database insertion
    """
    # Determine receipt_type
    # Assuming these are RECEIVED receipts (paid to service providers)
    # as the SII API doesn't provide clear issuer information
    receipt_type = "received"

    # Parse dates
    issue_date = None
    if boleta.get('fecha_boleta'):
        try:
            issue_date = parse_date(boleta['fecha_boleta'])
        except Exception as e:
            logger.warning(f"⚠️ Error parsing fecha_boleta: {e}")

    emission_date = None
    if boleta.get('fecha_emision'):
        try:
            emission_date = parse_date(boleta['fecha_emision'])
        except Exception as e:
            logger.warning(f"⚠️ Error parsing fecha_emision: {e}")

    # If no issue_date but has emission_date, use emission_date
    if not issue_date and emission_date:
        issue_date = emission_date

    # If still no date, use first day of period
    if not issue_date:
        year = int(period[:4])
        month = int(period[4:6])
        issue_date = f"{year:04d}-{month:02d}-01"

    # Parse folio
    folio = boleta.get('numero_boleta')
    if folio is not None:
        try:
            folio = int(folio)
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Invalid folio: {folio}")
            folio = None

    # Parse amounts
    gross_amount = parse_amount(boleta.get('honorarios_brutos', 0))
    issuer_retention = parse_amount(boleta.get('retencion_emisor', 0))
    recipient_retention = parse_amount(boleta.get('retencion_receptor', 0))
    net_amount = parse_amount(boleta.get('honorarios_liquidos', 0))

    # Map status
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

    return {
        "company_id": company_id,
        "receipt_type": receipt_type,
        "folio": folio,
        "issue_date": issue_date,
        "emission_date": emission_date,
        "issuer_rut": None,  # Not available in SII API
        "issuer_name": None,  # Not available in SII API
        "recipient_rut": boleta.get('rut_receptor'),
        "recipient_name": boleta.get('nombre_receptor'),
        "gross_amount": gross_amount,
        "issuer_retention": issuer_retention,
        "recipient_retention": recipient_retention,
        "net_amount": net_amount,
        "status": status,
        "is_professional_society": boleta.get('sociedad_profesional', False),
        "is_manual": boleta.get('manual', False),
        "emission_user": boleta.get('usuario_emision'),
        "extra_data": {
            "raw_data": boleta,
            "sync_period": period,
            "synced_at": datetime.now().isoformat()
        }
    }
