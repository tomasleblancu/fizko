"""
SII Service Layer for Backend V2.

This service handles all business logic for SII integration:
- Document synchronization (purchases and sales)
- F29 form synchronization
- Authentication and session management

Uses:
- SIIClient for web scraping
- Supabase repositories for database operations

IMPORTANT: All methods are async to work with Supabase async repositories.
Celery tasks wrap these with asyncio.run() since Celery tasks are synchronous.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from dateutil.relativedelta import relativedelta

from app.config.supabase import SupabaseClient
from app.integrations.sii import SIIClient
from app.integrations.sii.exceptions import AuthenticationError, ExtractionError
from app.utils.encryption import decrypt_password
from app.utils.rut import normalize_rut
from app.services.sii.parsers import (
    parse_purchase_document,
    parse_sales_document,
    parse_daily_purchase_document,
    parse_daily_sales_document,
    parse_honorarios_receipt,
)

logger = logging.getLogger(__name__)


class SIIService:
    """
    Service for SII integration operations.

    Handles document and form synchronization with the SII portal.
    All methods are async to work with Supabase async repositories.
    """

    def __init__(self, supabase: SupabaseClient):
        """
        Initialize SII service.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase

    async def _upsert_contact_and_link_documents(
        self,
        company_id: str,
        documents: List[Dict[str, Any]],
        contact_type: str
    ) -> List[Dict[str, Any]]:
        """
        Upsert contacts for documents and link them via contact_id.

        Args:
            company_id: Company UUID
            documents: List of document dicts (purchase or sales)
            contact_type: Type of contact ('provider' for purchases, 'client' for sales)

        Returns:
            List of documents with contact_id added
        """
        # Determine which RUT field to use based on document type
        rut_field = "sender_rut" if contact_type == "provider" else "recipient_rut"
        name_field = "sender_name" if contact_type == "provider" else "recipient_name"

        for doc in documents:
            rut = doc.get(rut_field)
            name = doc.get(name_field)

            # Skip if no RUT (e.g., daily summaries)
            if not rut or not name:
                continue

            try:
                # Upsert contact
                contact = await self.supabase.contacts.upsert_contact(
                    company_id=company_id,
                    rut=rut,
                    business_name=name,
                    contact_type=contact_type
                )

                # Link document to contact
                if contact and contact.get("id"):
                    doc["contact_id"] = contact["id"]

            except Exception as e:
                logger.warning(f"⚠️  Failed to upsert contact for {name} ({rut}): {e}")
                # Continue without linking contact (contact_id will be None)
                continue

        return documents

    async def sync_documents(
        self,
        company_id: str,
        months: int = 1,
        month_offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Synchronize tax documents (purchases and sales) for a company.

        Args:
            company_id: UUID of the company
            months: Number of months to sync (1-12)
            month_offset: Number of months to skip from current month

        Returns:
            Dict with sync results

        Raises:
            ValueError: If company not found or credentials missing
            AuthenticationError: If SII authentication fails
        """
        start_time = datetime.now()

        # Get company info (async)
        company = await self.supabase.companies.get_by_id(company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        if not company.get("sii_password"):
            raise ValueError(f"Company {company_id} has no SII credentials configured")

        rut = company["rut"]

        # Decrypt SII password (stored encrypted in database)
        encrypted_password = company["sii_password"]
        try:
            sii_password = decrypt_password(encrypted_password)
            if not sii_password:
                raise ValueError(f"Company {company_id} has invalid encrypted SII password")
        except Exception as e:
            logger.error(f"Failed to decrypt SII password for company {company_id}: {e}")
            raise ValueError(f"Company {company_id} has corrupted SII credentials")

        # Calculate periods to sync
        base_date = datetime.now() - relativedelta(months=month_offset)
        periods = []
        for i in range(months):
            period_date = base_date - relativedelta(months=i)
            period = period_date.strftime("%Y%m")
            periods.append(period)

        logger.info(f"📅 Syncing periods: {periods} for company {company.get('business_name')}")

        compras_stats = {"total": 0, "nuevos": 0, "actualizados": 0}
        ventas_stats = {"total": 0, "nuevos": 0, "actualizados": 0}
        honorarios_stats = {"total": 0, "nuevos": 0, "actualizados": 0}
        errors = 0

        # Use SIIClient to extract documents
        with SIIClient(tax_id=rut, password=sii_password) as client:
            for period in periods:
                try:
                    logger.info(f"📥 Processing period {period}...")

                    # Step 1: Get summary to know what document types exist
                    try:
                        resumen_result = client.get_resumen(periodo=period)
                        resumen_data = resumen_result.get("data", {})
                    except ExtractionError as e:
                        logger.warning(f"⚠️  Could not get resumen for {period}: {e}")
                        errors += 1
                        continue

                    # Process purchases (compras)
                    compras_result = await self._sync_purchases_for_period(
                        client, company_id, period, resumen_data
                    )
                    compras_stats["nuevos"] += compras_result["nuevos"]
                    compras_stats["actualizados"] += compras_result["actualizados"]
                    compras_stats["total"] += compras_result["total"]

                    # Process sales (ventas)
                    ventas_result = await self._sync_sales_for_period(
                        client, company_id, period, resumen_data
                    )
                    ventas_stats["nuevos"] += ventas_result["nuevos"]
                    ventas_stats["actualizados"] += ventas_result["actualizados"]
                    ventas_stats["total"] += ventas_result["total"]

                    # Process honorarios receipts
                    try:
                        logger.info(f"   💼 Extracting honorarios receipts...")
                        mes = period[4:6]  # Extract month from YYYYMM
                        anio = period[:4]  # Extract year

                        honorarios_result = client.get_boletas_honorarios_todas_paginas(
                            mes=mes,
                            anio=anio
                        )

                        boletas = honorarios_result.get("boletas", [])
                        logger.info(f"   📋 Honorarios: {len(boletas)} receipts")

                        parsed_honorarios = []
                        for boleta in boletas:
                            try:
                                receipt_data = parse_honorarios_receipt(
                                    company_id=company_id,
                                    boleta=boleta,
                                    period=period,
                                    company_rut=rut,
                                    company_name=company.get('business_name')
                                )
                                if receipt_data.get("folio") is not None:
                                    parsed_honorarios.append(receipt_data)
                            except Exception as e:
                                logger.error(f"❌ Error parsing honorarios receipt: {e}")
                                continue

                        if parsed_honorarios:
                            h_nuevos, h_actualizados = await self.supabase.honorarios.upsert_honorarios_receipts(
                                parsed_honorarios
                            )
                            logger.info(f"   💾 Saved honorarios: {h_nuevos} nuevos, {h_actualizados} actualizados")
                            honorarios_stats["nuevos"] += h_nuevos
                            honorarios_stats["actualizados"] += h_actualizados
                            honorarios_stats["total"] += len(parsed_honorarios)

                    except ExtractionError as e:
                        logger.warning(f"⚠️  Honorarios extraction error for {period}: {e}")
                    except Exception as e:
                        logger.error(f"❌ Error processing honorarios for {period}: {e}")

                except Exception as e:
                    logger.error(f"❌ Error processing period {period}: {e}")
                    errors += 1

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "success": True,
            "company_id": company_id,
            "compras": compras_stats,
            "ventas": ventas_stats,
            "honorarios": honorarios_stats,
            "duration_seconds": duration,
            "errors": errors,
        }

    async def _sync_purchases_for_period(
        self,
        client: SIIClient,
        company_id: str,
        period: str,
        resumen_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Sync purchases for a specific period based on resumen data.

        Handles:
        - Boletas (39) and Comprobantes (48) as daily summaries
        - Other document types as individual documents

        Returns:
            Dict with total, nuevos, actualizados counts
        """
        stats = {"total": 0, "nuevos": 0, "actualizados": 0}

        resumen_compras = resumen_data.get("resumen_compras", {})
        resumen_items = resumen_compras.get("data", []) if isinstance(resumen_compras, dict) else []

        if not resumen_items:
            logger.info("   ℹ️  No compras in resumen")
            return stats

        for item in resumen_items:
            try:
                tipo_doc = str(item.get("rsmnTipoDocInteger", ""))
                if not tipo_doc:
                    continue

                cantidad_docs = item.get("rsmnTotDoc", 0)
                nombre_tipo = item.get("dcvNombreTipoDoc", f"Tipo {tipo_doc}")

                logger.info(f"   📋 Compras {nombre_tipo} (Tipo {tipo_doc}): {cantidad_docs} docs")

                # Check if it's a monthly summary without detail
                es_resumen = (
                    item.get("dcvTipoIngresoDoc") == "RESUMEN" or
                    item.get("rsmnLink") is False
                )

                # For boletas (39) and comprobantes (48), extract daily detail
                if es_resumen and tipo_doc in ["39", "48"]:
                    logger.info(f"   🔄 Processing DAILY detail for tipo {tipo_doc}")
                    result = await self._extract_daily_purchases(client, company_id, period, tipo_doc)
                    stats["nuevos"] += result["nuevos"]
                    stats["actualizados"] += result["actualizados"]
                    stats["total"] += result["total"]

                elif not es_resumen:
                    # Has individual detail - extract each document
                    result = await self._extract_individual_purchases(client, company_id, period, tipo_doc)
                    stats["nuevos"] += result["nuevos"]
                    stats["actualizados"] += result["actualizados"]
                    stats["total"] += result["total"]

                # Note: We skip monthly summaries for other document types (not implemented yet)

            except Exception as e:
                logger.error(f"❌ Error processing compras tipo {item.get('rsmnTipoDocInteger')}: {e}")
                continue

        return stats

    async def _sync_sales_for_period(
        self,
        client: SIIClient,
        company_id: str,
        period: str,
        resumen_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Sync sales for a specific period based on resumen data.

        Handles:
        - Boletas (39) and Comprobantes (48) as daily summaries
        - Other document types as individual documents

        Returns:
            Dict with total, nuevos, actualizados counts
        """
        stats = {"total": 0, "nuevos": 0, "actualizados": 0}

        resumen_ventas = resumen_data.get("resumen_ventas", {})
        resumen_items = resumen_ventas.get("data", []) if isinstance(resumen_ventas, dict) else []

        if not resumen_items:
            logger.info("   ℹ️  No ventas in resumen")
            return stats

        for item in resumen_items:
            try:
                tipo_doc = str(item.get("rsmnTipoDocInteger", ""))
                if not tipo_doc:
                    continue

                cantidad_docs = item.get("rsmnTotDoc", 0)
                nombre_tipo = item.get("dcvNombreTipoDoc", f"Tipo {tipo_doc}")

                logger.info(f"   📋 Ventas {nombre_tipo} (Tipo {tipo_doc}): {cantidad_docs} docs")

                # Check if it's a monthly summary without detail
                es_resumen = (
                    item.get("dcvTipoIngresoDoc") == "RESUMEN" or
                    item.get("rsmnLink") is False
                )

                # For boletas (39) and comprobantes (48), extract daily detail
                if es_resumen and tipo_doc in ["39", "48"]:
                    logger.info(f"   🔄 Processing DAILY detail for tipo {tipo_doc}")
                    result = await self._extract_daily_sales(client, company_id, period, tipo_doc)
                    stats["nuevos"] += result["nuevos"]
                    stats["actualizados"] += result["actualizados"]
                    stats["total"] += result["total"]

                elif not es_resumen:
                    # Has individual detail - extract each document
                    result = await self._extract_individual_sales(client, company_id, period, tipo_doc)
                    stats["nuevos"] += result["nuevos"]
                    stats["actualizados"] += result["actualizados"]
                    stats["total"] += result["total"]

                # Note: We skip monthly summaries for other document types (not implemented yet)

            except Exception as e:
                logger.error(f"❌ Error processing ventas tipo {item.get('rsmnTipoDocInteger')}: {e}")
                continue

        return stats

    async def _extract_daily_purchases(
        self,
        client: SIIClient,
        company_id: str,
        period: str,
        tipo_doc: str
    ) -> Dict[str, int]:
        """Extract daily purchase summaries (boletas/comprobantes)."""
        try:
            result = client.get_boletas_diarias(periodo=period, tipo_doc=tipo_doc)
            daily_documents = result.get("data", [])

            logger.info(f"      ✅ Extracted {len(daily_documents)} daily totals")

            parsed_docs = []
            for daily_doc in daily_documents:
                try:
                    doc_data = parse_daily_purchase_document(
                        company_id=company_id,
                        period=period,
                        tipo_doc=tipo_doc,
                        daily_doc=daily_doc
                    )
                    parsed_docs.append(doc_data)
                except Exception as e:
                    logger.error(f"❌ Error parsing daily purchase doc: {e}")
                    continue

            if parsed_docs:
                nuevos, actualizados = await self.supabase.documents.upsert_purchase_documents(
                    parsed_docs
                )
                logger.info(f"      💾 Saved: {nuevos} nuevos, {actualizados} actualizados")
                return {"total": len(parsed_docs), "nuevos": nuevos, "actualizados": actualizados}

            return {"total": 0, "nuevos": 0, "actualizados": 0}

        except ExtractionError as e:
            logger.warning(f"⚠️  Error extracting daily purchases for tipo {tipo_doc}: {e}")
            return {"total": 0, "nuevos": 0, "actualizados": 0}

    async def _extract_daily_sales(
        self,
        client: SIIClient,
        company_id: str,
        period: str,
        tipo_doc: str
    ) -> Dict[str, int]:
        """Extract daily sales summaries (boletas/comprobantes)."""
        try:
            result = client.get_boletas_diarias(periodo=period, tipo_doc=tipo_doc)
            daily_documents = result.get("data", [])

            logger.info(f"      ✅ Extracted {len(daily_documents)} daily totals")

            parsed_docs = []
            for daily_doc in daily_documents:
                try:
                    doc_data = parse_daily_sales_document(
                        company_id=company_id,
                        period=period,
                        tipo_doc=tipo_doc,
                        daily_doc=daily_doc
                    )
                    parsed_docs.append(doc_data)
                except Exception as e:
                    logger.error(f"❌ Error parsing daily sales doc: {e}")
                    continue

            if parsed_docs:
                nuevos, actualizados = await self.supabase.documents.upsert_sales_documents(
                    parsed_docs
                )
                logger.info(f"      💾 Saved: {nuevos} nuevos, {actualizados} actualizados")
                return {"total": len(parsed_docs), "nuevos": nuevos, "actualizados": actualizados}

            return {"total": 0, "nuevos": 0, "actualizados": 0}

        except ExtractionError as e:
            logger.warning(f"⚠️  Error extracting daily sales for tipo {tipo_doc}: {e}")
            return {"total": 0, "nuevos": 0, "actualizados": 0}

    async def _extract_individual_purchases(
        self,
        client: SIIClient,
        company_id: str,
        period: str,
        tipo_doc: str
    ) -> Dict[str, int]:
        """Extract individual purchase documents."""
        try:
            compras_result = client.get_compras(
                periodo=period,
                tipo_doc=tipo_doc,
                estado_contab="REGISTRO"
            )
            compras = compras_result.get("data", [])
            logger.info(f"      ✅ Extracted {len(compras)} individual documents")

            parsed_compras = []
            for doc in compras:
                try:
                    doc_data = parse_purchase_document(
                        company_id=company_id,
                        doc=doc,
                        tipo_doc=tipo_doc,
                        estado_contab="REGISTRO"
                    )
                    if doc_data.get("folio") is not None:
                        parsed_compras.append(doc_data)
                except Exception as e:
                    logger.error(f"❌ Error parsing purchase doc: {e}")
                    continue

            if parsed_compras:
                # Upsert contacts and link to documents
                parsed_compras = await self._upsert_contact_and_link_documents(
                    company_id, parsed_compras, contact_type="provider"
                )

                nuevos, actualizados = await self.supabase.documents.upsert_purchase_documents(
                    parsed_compras
                )
                logger.info(f"      💾 Saved: {nuevos} nuevos, {actualizados} actualizados")
                return {"total": len(parsed_compras), "nuevos": nuevos, "actualizados": actualizados}

            return {"total": 0, "nuevos": 0, "actualizados": 0}

        except ExtractionError as e:
            logger.warning(f"⚠️  Error extracting individual purchases for tipo {tipo_doc}: {e}")
            return {"total": 0, "nuevos": 0, "actualizados": 0}

    async def _extract_individual_sales(
        self,
        client: SIIClient,
        company_id: str,
        period: str,
        tipo_doc: str
    ) -> Dict[str, int]:
        """Extract individual sales documents."""
        try:
            ventas_result = client.get_ventas(periodo=period, tipo_doc=tipo_doc)
            ventas = ventas_result.get("data", [])
            logger.info(f"      ✅ Extracted {len(ventas)} individual documents")

            parsed_ventas = []
            for doc in ventas:
                try:
                    doc_data = parse_sales_document(
                        company_id=company_id,
                        doc=doc,
                        tipo_doc=tipo_doc
                    )
                    if doc_data.get("folio") is not None:
                        parsed_ventas.append(doc_data)
                except Exception as e:
                    logger.error(f"❌ Error parsing sales doc: {e}")
                    continue

            if parsed_ventas:
                # Upsert contacts and link to documents
                parsed_ventas = await self._upsert_contact_and_link_documents(
                    company_id, parsed_ventas, contact_type="client"
                )

                nuevos, actualizados = await self.supabase.documents.upsert_sales_documents(
                    parsed_ventas
                )
                logger.info(f"      💾 Saved: {nuevos} nuevos, {actualizados} actualizados")
                return {"total": len(parsed_ventas), "nuevos": nuevos, "actualizados": actualizados}

            return {"total": 0, "nuevos": 0, "actualizados": 0}

        except ExtractionError as e:
            logger.warning(f"⚠️  Error extracting individual sales for tipo {tipo_doc}: {e}")
            return {"total": 0, "nuevos": 0, "actualizados": 0}

    async def sync_documents_all_companies(
        self,
        months: int = 1,
        month_offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Sync documents for all companies with active subscriptions.

        Args:
            months: Number of months to sync per company
            month_offset: Month offset from current date

        Returns:
            Dict with batch sync summary
        """
        # Get all companies (async)
        # TODO: Filter by active subscriptions when subscription system is implemented
        companies = await self.supabase.companies.list_all()

        if not companies:
            logger.info("⏭️  No companies found")
            return {
                "success": True,
                "total_companies": 0,
                "synced": 0,
                "failed": 0,
                "results": []
            }

        logger.info(f"📊 Found {len(companies)} companies")

        synced = 0
        failed = 0
        results = []

        for company in companies:
            try:
                company_id = company["id"]
                company_name = company.get("business_name", "Unknown")

                logger.info(f"🔄 Syncing documents for company: {company_name}")

                # Await the async sync_documents call
                result = await self.sync_documents(
                    company_id,
                    months=months,
                    month_offset=month_offset
                )

                if result.get("success"):
                    synced += 1
                    logger.info(
                        f"✅ Company {company_name}: "
                        f"compras={result['compras']['total']}, "
                        f"ventas={result['ventas']['total']}"
                    )
                else:
                    failed += 1

                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    **result
                })

            except Exception as e:
                failed += 1
                logger.error(f"❌ Company {company.get('business_name', 'Unknown')} failed: {e}")
                results.append({
                    "company_id": company["id"],
                    "company_name": company.get("business_name", "Unknown"),
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": True,
            "total_companies": len(companies),
            "synced": synced,
            "failed": failed,
            "results": results
        }

    async def sync_f29(
        self,
        company_id: str,
        year: str = None,
    ) -> Dict[str, Any]:
        """
        Synchronize F29 forms for a company.

        Args:
            company_id: UUID of the company
            year: Year to sync (YYYY format). Defaults to current year.

        Returns:
            Dict with sync results

        Raises:
            ValueError: If company not found or credentials missing
            AuthenticationError: If SII authentication fails
        """
        if year is None:
            year = str(datetime.now().year)

        start_time = datetime.now()

        # Get company info (async)
        company = await self.supabase.companies.get_by_id(company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        if not company.get("sii_password"):
            raise ValueError(f"Company {company_id} has no SII credentials configured")

        rut = company["rut"]

        # Decrypt SII password (stored encrypted in database)
        encrypted_password = company["sii_password"]
        try:
            sii_password = decrypt_password(encrypted_password)
            if not sii_password:
                raise ValueError(f"Company {company_id} has invalid encrypted SII password")
        except Exception as e:
            logger.error(f"Failed to decrypt SII password for company {company_id}: {e}")
            raise ValueError(f"Company {company_id} has corrupted SII credentials")

        logger.info(f"📄 Syncing F29 forms for {company.get('business_name')} - Year {year}")

        stats = {"total": 0, "nuevos": 0, "actualizados": 0}

        # Use SIIClient to extract F29 forms
        with SIIClient(tax_id=rut, password=sii_password) as client:
            try:
                # Get F29 list for the year
                logger.info(f"   📥 Fetching F29 list...")
                f29_list = client.get_f29_lista(anio=year)
                logger.info(f"   📋 Found {len(f29_list)} F29 forms")

                if not f29_list:
                    logger.info("   ⏭️  No F29 forms found")
                    duration = (datetime.now() - start_time).total_seconds()
                    return {
                        "success": True,
                        "company_id": company_id,
                        "year": year,
                        **stats,
                        "duration_seconds": duration,
                    }

            except ExtractionError as e:
                raise ValueError(f"Failed to get F29 list: {e}")

        # Build F29 forms list for bulk upsert (outside SIIClient context)
        f29_forms = []
        for f29_summary in f29_list:
            folio = f29_summary.get("folio")
            if not folio:
                logger.warning("   ⚠️  F29 without folio, skipping")
                continue

            # Validate required fields
            period_year = f29_summary.get("period_year")
            period_month = f29_summary.get("period_month")
            period_display = f29_summary.get("period")

            if not period_year or not period_month:
                logger.warning(f"   ⚠️  F29 folio {folio} missing period components, skipping")
                continue

            # Get contributor_rut (from extraction or fallback to company RUT)
            # Normalize to remove hyphens and convert to lowercase (e.g., "77745293-2" -> "777452932")
            contributor_rut_raw = f29_summary.get("contributor_rut") or rut
            contributor_rut = normalize_rut(contributor_rut_raw)

            # Parse submission_date from DD/MM/YYYY to ISO format (YYYY-MM-DD)
            submission_date_str = f29_summary.get("submission_date")
            submission_date = None
            if submission_date_str:
                try:
                    # Parse DD/MM/YYYY format
                    parts = submission_date_str.split("/")
                    if len(parts) == 3:
                        day, month, year = parts
                        submission_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except Exception as e:
                    logger.warning(f"   ⚠️  Failed to parse submission_date '{submission_date_str}': {e}")

            # Transform to match form29_sii_downloads schema
            f29_data = {
                "company_id": company_id,
                "sii_folio": folio,
                "sii_id_interno": f29_summary.get("id_interno_sii"),  # Nullable
                "period_year": period_year,
                "period_month": period_month,
                "period_display": period_display,
                "contributor_rut": contributor_rut,  # Normalized (no hyphen)
                "submission_date": submission_date,  # ISO format: YYYY-MM-DD
                "status": f29_summary.get("status", "Vigente"),  # Capital first letter
                "amount_cents": 0,  # Not extracted yet, default to 0
                "pdf_download_status": "pending" if f29_summary.get("id_interno_sii") else "error",
            }
            f29_forms.append(f29_data)

        # Bulk upsert all F29 forms in a single operation (outside SIIClient context)
        if f29_forms:
            nuevos, actualizados = await self.supabase.f29.upsert_f29_forms(
                f29_forms
            )
            logger.info(f"   💾 Saved: {nuevos} nuevos, {actualizados} actualizados")
            stats["total"] = len(f29_forms)
            stats["nuevos"] = nuevos
            stats["actualizados"] = actualizados

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "success": True,
            "company_id": company_id,
            "year": year,
            **stats,
            "duration_seconds": duration,
        }

    async def sync_f29_all_companies(
        self,
        year: str = None,
    ) -> Dict[str, Any]:
        """
        Sync F29 forms for all companies with active subscriptions.

        Args:
            year: Year to sync (YYYY format). Defaults to current year.

        Returns:
            Dict with batch sync summary
        """
        if year is None:
            year = str(datetime.now().year)

        # Get all companies (async)
        # TODO: Filter by active subscriptions when subscription system is implemented
        companies = await self.supabase.companies.list_all()

        if not companies:
            logger.info("⏭️  No companies found")
            return {
                "success": True,
                "total_companies": 0,
                "synced": 0,
                "failed": 0,
                "year": year,
                "results": []
            }

        logger.info(f"📊 Found {len(companies)} companies")

        synced = 0
        failed = 0
        results = []

        for company in companies:
            try:
                company_id = company["id"]
                company_name = company.get("business_name", "Unknown")

                logger.info(f"🔄 Syncing F29 for company: {company_name}")

                # Await the async sync_f29 call
                result = await self.sync_f29(company_id, year=year)

                if result.get("success"):
                    synced += 1
                    logger.info(
                        f"✅ Company {company_name}: "
                        f"{result.get('total', 0)} F29 forms synced"
                    )
                else:
                    failed += 1

                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    **result
                })

            except Exception as e:
                failed += 1
                logger.error(f"❌ Company {company.get('business_name', 'Unknown')} failed: {e}")
                results.append({
                    "company_id": company["id"],
                    "company_name": company.get("business_name", "Unknown"),
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": True,
            "total_companies": len(companies),
            "synced": synced,
            "failed": failed,
            "year": year,
            "results": results
        }

    async def download_f29_pdf(
        self,
        company_id: str,
        folio: str,
        id_interno_sii: str
    ) -> dict:
        """
        Descarga el PDF de un F29 y lo guarda en Supabase Storage con extracción de datos

        Args:
            company_id: ID de la empresa
            folio: Folio del formulario
            id_interno_sii: ID interno del SII (codInt)

        Returns:
            Dict con resultado de la descarga:
            {
                "success": bool,
                "storage_url": str (si éxito),
                "extracted_data": dict (si éxito),
                "error": str (si falla)
            }
        """
        from app.utils.pdf_validator import is_valid_f29_pdf, get_pdf_size_mb
        from app.services.f29_pdf_extractor import extract_f29_data_from_pdf
        import asyncio

        try:
            # 1. Obtener empresa y RUT
            company = await self.supabase.companies.get_by_id(company_id)
            if not company:
                return {"success": False, "error": f"Company {company_id} not found"}

            rut = company["rut"]
            sii_password_encrypted = company.get("sii_password")

            if not sii_password_encrypted:
                return {"success": False, "error": "No SII credentials configured"}

            # 2. Decrypt password
            sii_password = decrypt_password(sii_password_encrypted)
            if not sii_password:
                return {"success": False, "error": "Invalid encrypted SII password"}

            # 3. Descargar PDF usando SIIClient (sync en thread)
            def _download_pdf():
                with SIIClient(tax_id=rut, password=sii_password) as client:
                    client.login()  # Ensure logged in

                    # Use SIIClient method to download PDF (uses F29Extractor internally)
                    return client.get_f29_compacto(
                        folio=folio,
                        id_interno_sii=id_interno_sii
                    )

            pdf_bytes = await asyncio.to_thread(_download_pdf)

            if not pdf_bytes:
                return {"success": False, "error": "Failed to download PDF"}

            # 4. Validar PDF
            is_valid, validation_msg = is_valid_f29_pdf(pdf_bytes)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Invalid PDF: {validation_msg}"
                }

            pdf_size_mb = get_pdf_size_mb(pdf_bytes)
            logger.info(f"✅ PDF válido descargado: {pdf_size_mb:.2f} MB")

            # 5. Extraer datos del PDF
            extracted_data = None
            try:
                extracted_data = extract_f29_data_from_pdf(pdf_bytes)
                if extracted_data.get('extraction_success'):
                    logger.info(f"✅ Datos extraídos: {extracted_data.get('codes_extracted', 0)} códigos")
                else:
                    logger.warning(f"⚠️ Extracción parcial: {extracted_data.get('error')}")
            except Exception as e:
                logger.warning(f"⚠️ Error extrayendo datos del PDF: {e}")

            # 6. Actualizar registro con datos extraídos
            # TODO: Subir PDF a Supabase Storage
            storage_url = None  # Pendiente: implementar upload a Supabase Storage

            if extracted_data and extracted_data.get('extraction_success'):
                # Actualizar extra_data con datos extraídos
                # pdf_download_status can be: pending, downloaded, error
                self.supabase._client.table('form29_sii_downloads').update({
                    'extra_data': {'f29_data': extracted_data},
                    'pdf_download_status': 'downloaded',  # Mark as downloaded even if not uploaded to storage
                    'pdf_storage_url': storage_url
                }).eq('company_id', company_id).eq('sii_folio', folio).execute()

                logger.info(f"✅ F29 data saved to database: {len(extracted_data.get('codes', {}))} codes")

            return {
                "success": True,
                "storage_url": storage_url,
                "extracted_data": extracted_data,
                "pdf_size_mb": pdf_size_mb
            }

        except Exception as e:
            logger.error(f"❌ Error downloading F29 PDF: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
