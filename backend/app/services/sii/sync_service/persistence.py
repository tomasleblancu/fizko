"""
Módulo de persistencia para documentos tributarios

Contiene funciones compartidas para guardar y actualizar documentos
en la base de datos usando bulk upsert.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Contact, PurchaseDocument, SalesDocument, HonorariosReceipt

logger = logging.getLogger(__name__)


async def get_or_create_contact(
    db: AsyncSession,
    company_id: UUID,
    rut: Optional[str],
    name: Optional[str],
    contact_type: str  # 'provider' or 'client'
) -> Optional[UUID]:
    """
    Busca o crea un contacto basado en el RUT

    Args:
        db: Sesión de base de datos
        company_id: ID de la compañía
        rut: RUT del contacto
        name: Nombre del contacto
        contact_type: Tipo de contacto ('provider' o 'client')

    Returns:
        UUID del contacto o None si no se puede crear
    """
    if not rut or not name:
        return None

    # Normalizar RUT (eliminar puntos, guiones, etc)
    rut = rut.strip().replace(".", "").replace("-", "").upper()

    # Buscar contacto existente
    stmt = select(Contact).where(
        Contact.company_id == company_id,
        Contact.rut == rut
    )
    result = await db.execute(stmt)
    existing_contact = result.scalar_one_or_none()

    if existing_contact:
        # Verificar si necesitamos actualizar el tipo
        if existing_contact.contact_type != 'both':
            # Si es proveedor y ahora es cliente (o viceversa), cambiar a 'both'
            if (existing_contact.contact_type == 'provider' and contact_type == 'client') or \
               (existing_contact.contact_type == 'client' and contact_type == 'provider'):
                existing_contact.contact_type = 'both'
                existing_contact.updated_at = datetime.utcnow()
                logger.info(f"📝 Updated contact {rut} type to 'both'")

        return existing_contact.id

    # Crear nuevo contacto
    try:
        new_contact = Contact(
            company_id=company_id,
            rut=rut,
            business_name=name,
            contact_type=contact_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_contact)
        await db.flush()  # Flush para obtener el ID sin commit

        logger.info(f"✨ Created new {contact_type}: {name} ({rut})")
        return new_contact.id

    except Exception as e:
        logger.error(f"❌ Error creating contact {rut}: {e}")
        return None


async def bulk_upsert_purchases(
    db: AsyncSession,
    company_id: UUID,
    documents: List[Dict[str, Any]]
) -> Tuple[int, int]:
    """
    Guarda documentos de compra en DB usando bulk upsert

    Args:
        db: Sesión de base de datos
        company_id: ID de la compañía
        documents: Lista de documentos preparados para insertar

    Returns:
        (nuevos, actualizados)
    """
    if not documents:
        return 0, 0

    # Obtener folios existentes para contar nuevos vs actualizados
    folios = [doc['folio'] for doc in documents]
    stmt = select(PurchaseDocument.folio).where(
        PurchaseDocument.company_id == company_id,
        PurchaseDocument.folio.in_(folios)
    )
    result = await db.execute(stmt)
    existing_folios = set(row[0] for row in result.fetchall())

    nuevos = sum(1 for doc in documents if doc['folio'] not in existing_folios)
    actualizados = len(documents) - nuevos

    # Usar PostgreSQL INSERT ... ON CONFLICT para upsert en batch
    stmt = insert(PurchaseDocument).values(documents)
    stmt = stmt.on_conflict_do_update(
        index_elements=['company_id', 'folio'],
        set_={
            'document_type': stmt.excluded.document_type,
            'issue_date': stmt.excluded.issue_date,
            'sender_rut': stmt.excluded.sender_rut,
            'sender_name': stmt.excluded.sender_name,
            'contact_id': stmt.excluded.contact_id,
            'net_amount': stmt.excluded.net_amount,
            'tax_amount': stmt.excluded.tax_amount,
            'exempt_amount': stmt.excluded.exempt_amount,
            'total_amount': stmt.excluded.total_amount,
            'status': stmt.excluded.status,
            'extra_data': stmt.excluded.extra_data,
            'updated_at': datetime.utcnow()
        }
    )

    await db.execute(stmt)
    return nuevos, actualizados


async def bulk_upsert_sales(
    db: AsyncSession,
    company_id: UUID,
    documents: List[Dict[str, Any]]
) -> Tuple[int, int]:
    """
    Guarda documentos de venta en DB usando bulk upsert

    Args:
        db: Sesión de base de datos
        company_id: ID de la compañía
        documents: Lista de documentos preparados para insertar

    Returns:
        (nuevos, actualizados)
    """
    if not documents:
        return 0, 0

    # Obtener folios existentes para contar nuevos vs actualizados
    folios = [doc['folio'] for doc in documents]
    stmt = select(SalesDocument.folio).where(
        SalesDocument.company_id == company_id,
        SalesDocument.folio.in_(folios)
    )
    result = await db.execute(stmt)
    existing_folios = set(row[0] for row in result.fetchall())

    nuevos = sum(1 for doc in documents if doc['folio'] not in existing_folios)
    actualizados = len(documents) - nuevos

    # Usar PostgreSQL INSERT ... ON CONFLICT para upsert en batch
    stmt = insert(SalesDocument).values(documents)
    stmt = stmt.on_conflict_do_update(
        index_elements=['company_id', 'folio'],
        set_={
            'document_type': stmt.excluded.document_type,
            'issue_date': stmt.excluded.issue_date,
            'recipient_rut': stmt.excluded.recipient_rut,
            'recipient_name': stmt.excluded.recipient_name,
            'contact_id': stmt.excluded.contact_id,
            'net_amount': stmt.excluded.net_amount,
            'tax_amount': stmt.excluded.tax_amount,
            'exempt_amount': stmt.excluded.exempt_amount,
            'total_amount': stmt.excluded.total_amount,
            'status': stmt.excluded.status,
            'extra_data': stmt.excluded.extra_data,
            'updated_at': datetime.utcnow()
        }
    )

    await db.execute(stmt)
    return nuevos, actualizados


async def upsert_monthly_summary_purchase(
    db: AsyncSession,
    doc_data: Dict[str, Any]
) -> Tuple[int, int]:
    """
    Guarda o actualiza un documento de resumen mensual de compras

    Args:
        db: Sesión de base de datos
        doc_data: Datos del documento preparados

    Returns:
        Tuple (nuevos, actualizados)
    """
    folio = doc_data["folio"]
    company_id = doc_data["company_id"]

    # Buscar documento existente
    stmt = (
        select(PurchaseDocument)
        .where(PurchaseDocument.company_id == company_id)
        .where(PurchaseDocument.folio == folio)
    )
    result = await db.execute(stmt)
    existing_doc = result.scalar_one_or_none()

    if existing_doc:
        # Actualizar documento existente
        for key, value in doc_data.items():
            if key != "company_id":  # No actualizar company_id
                setattr(existing_doc, key, value)

        logger.debug(f"♻️  Updated monthly summary (compras): folio={folio}")
        return 0, 1
    else:
        # Crear nuevo documento
        purchase_doc = PurchaseDocument(**doc_data)
        db.add(purchase_doc)
        logger.debug(f"✨ Created monthly summary (compras): folio={folio}")
        return 1, 0


async def upsert_monthly_summary_sales(
    db: AsyncSession,
    doc_data: Dict[str, Any]
) -> Tuple[int, int]:
    """
    Guarda o actualiza un documento de resumen mensual de ventas

    Args:
        db: Sesión de base de datos
        doc_data: Datos del documento preparados

    Returns:
        Tuple (nuevos, actualizados)
    """
    folio = doc_data["folio"]
    company_id = doc_data["company_id"]

    # Buscar documento existente
    stmt = (
        select(SalesDocument)
        .where(SalesDocument.company_id == company_id)
        .where(SalesDocument.folio == folio)
    )
    result = await db.execute(stmt)
    existing_doc = result.scalar_one_or_none()

    if existing_doc:
        # Actualizar documento existente
        for key, value in doc_data.items():
            if key != "company_id":  # No actualizar company_id
                setattr(existing_doc, key, value)

        logger.debug(f"♻️  Updated monthly summary (ventas): folio={folio}")
        return 0, 1
    else:
        # Crear nuevo documento
        sales_doc = SalesDocument(**doc_data)
        db.add(sales_doc)
        logger.debug(f"✨ Created monthly summary (ventas): folio={folio}")
        return 1, 0


async def bulk_upsert_honorarios(
    db: AsyncSession,
    honorarios_list: List[Dict[str, Any]],
    company_id: UUID
) -> Dict[str, int]:
    """
    Guarda boletas de honorarios en DB usando bulk upsert

    Args:
        db: Sesión de base de datos
        honorarios_list: Lista de boletas preparadas para insertar
        company_id: ID de la compañía

    Returns:
        {"nuevos": int, "actualizados": int}
    """
    if not honorarios_list:
        return {"nuevos": 0, "actualizados": 0}

    # Filtrar boletas que tienen folio (las sin folio no se pueden hacer upsert)
    boletas_con_folio = [b for b in honorarios_list if b.get('folio')]
    boletas_sin_folio = [b for b in honorarios_list if not b.get('folio')]

    if boletas_sin_folio:
        logger.warning(f"⚠️ {len(boletas_sin_folio)} boletas sin folio serán insertadas sin validación de duplicados")

    # Contar nuevos vs actualizados para boletas CON folio
    nuevos = 0
    actualizados = 0

    if boletas_con_folio:
        folios = [doc['folio'] for doc in boletas_con_folio]
        stmt = select(HonorariosReceipt.folio).where(
            HonorariosReceipt.company_id == company_id,
            HonorariosReceipt.folio.in_(folios)
        )
        result = await db.execute(stmt)
        existing_folios = set(row[0] for row in result.fetchall())

        nuevos = sum(1 for doc in boletas_con_folio if doc['folio'] not in existing_folios)
        actualizados = len(boletas_con_folio) - nuevos

        # Usar PostgreSQL INSERT ... ON CONFLICT para upsert en batch
        stmt = insert(HonorariosReceipt).values(boletas_con_folio)
        stmt = stmt.on_conflict_do_update(
            index_elements=['company_id', 'folio'],
            set_={
                'receipt_type': stmt.excluded.receipt_type,
                'issue_date': stmt.excluded.issue_date,
                'emission_date': stmt.excluded.emission_date,
                'issuer_rut': stmt.excluded.issuer_rut,
                'issuer_name': stmt.excluded.issuer_name,
                'recipient_rut': stmt.excluded.recipient_rut,
                'recipient_name': stmt.excluded.recipient_name,
                'gross_amount': stmt.excluded.gross_amount,
                'issuer_retention': stmt.excluded.issuer_retention,
                'recipient_retention': stmt.excluded.recipient_retention,
                'net_amount': stmt.excluded.net_amount,
                'status': stmt.excluded.status,
                'is_professional_society': stmt.excluded.is_professional_society,
                'is_manual': stmt.excluded.is_manual,
                'emission_user': stmt.excluded.emission_user,
                'extra_data': stmt.excluded.extra_data,
                'updated_at': datetime.utcnow()
            }
        )

        await db.execute(stmt)

    # Insertar boletas sin folio directamente (sin upsert)
    if boletas_sin_folio:
        for boleta in boletas_sin_folio:
            receipt = HonorariosReceipt(**boleta)
            db.add(receipt)
        nuevos += len(boletas_sin_folio)

    return {"nuevos": nuevos, "actualizados": actualizados}
