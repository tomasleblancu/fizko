#!/usr/bin/env python3
"""
Test de integración completo para F29 SII Downloads
Verifica que toda la cadena funcione: SII → Servicio → DB
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.db.models import Company, Session as SessionModel, Form29SIIDownload
from app.services.sii.service import SIIService

# Test credentials
TEST_RUT = "77794858-k"
TEST_PASSWORD = "SiiPfufl574@#"


async def test_full_integration():
    """Test completo de integración F29"""
    print("="*80)
    print("  TEST DE INTEGRACIÓN COMPLETO - F29 SII DOWNLOADS")
    print("="*80)

    async with AsyncSessionLocal() as db:
        try:
            # 1. Buscar o crear empresa de prueba
            print("\n1️⃣  Buscando empresa en DB...")
            stmt = select(Company).where(Company.rut == TEST_RUT.replace('-', '').lower())
            result = await db.execute(stmt)
            company = result.scalar_one_or_none()

            if not company:
                print("   ⚠️  Empresa no encontrada, creando...")
                company = Company(
                    rut=TEST_RUT,
                    business_name="EMPRESA DE PRUEBA F29",
                    sii_password=TEST_PASSWORD
                )
                db.add(company)
                await db.commit()
                await db.refresh(company)
                print(f"   ✅ Empresa creada: {company.id}")
            else:
                print(f"   ✅ Empresa encontrada: {company.id}")

            # 2. Buscar o crear sesión
            print("\n2️⃣  Buscando sesión en DB...")
            # Para simplificar, buscar cualquier sesión activa de la empresa
            stmt = select(SessionModel).where(
                SessionModel.company_id == company.id,
                SessionModel.is_active == True
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()

            if not session:
                print("   ⚠️  Sesión no encontrada. Se requiere una sesión válida con user_id.")
                print("   💡 Por favor, crea una sesión manualmente en la DB primero.")
                return

            print(f"   ✅ Sesión encontrada: {session.id}")

            # 3. Extraer F29 del SII
            print("\n3️⃣  Extrayendo F29 del SII...")
            service = SIIService(db)

            test_year = str(datetime.now().year - 1)
            print(f"   📅 Año de prueba: {test_year}")

            formularios = await service.extract_f29_lista(
                session_id=session.id,
                anio=test_year
            )

            print(f"   ✅ {len(formularios)} formularios extraídos del SII")

            # 4. Guardar en DB
            print("\n4️⃣  Guardando formularios en DB...")
            saved_downloads = await service.save_f29_downloads(
                company_id=str(company.id),
                formularios=formularios
            )

            print(f"   ✅ {len(saved_downloads)} registros guardados en form29_sii_downloads")

            # 5. Verificar en DB
            print("\n5️⃣  Verificando registros en DB...")
            stmt = select(Form29SIIDownload).where(
                Form29SIIDownload.company_id == company.id
            ).order_by(Form29SIIDownload.period_year, Form29SIIDownload.period_month)

            result = await db.execute(stmt)
            db_records = result.scalars().all()

            print(f"   ✅ {len(db_records)} registros encontrados en DB")

            # 6. Mostrar resumen
            print("\n6️⃣  Resumen de registros:")
            print(f"   {'Period':<12} {'Folio':<15} {'Status':<12} {'Amount':>15} {'PDF ID':>10}")
            print("   " + "-"*70)

            for record in db_records:
                has_id = '✅' if record.sii_id_interno else '❌'
                print(f"   {record.period_display:<12} {record.sii_folio:<15} {record.status:<12} {record.amount_cents:>15,} {has_id:>10}")

            # 7. Estadísticas
            print("\n7️⃣  Estadísticas:")
            total_amount = sum(r.amount_cents for r in db_records)
            with_pdf_id = sum(1 for r in db_records if r.sii_id_interno)
            without_pdf_id = len(db_records) - with_pdf_id

            print(f"   📊 Total registros: {len(db_records)}")
            print(f"   💰 Suma total montos: ${total_amount:,}")
            print(f"   ✅ Con id_interno_sii: {with_pdf_id}")
            print(f"   ❌ Sin id_interno_sii: {without_pdf_id}")

            # 8. Verificar campos específicos del primer registro
            if db_records:
                print("\n8️⃣  Detalle del primer registro:")
                first = db_records[0]
                print(f"   ID: {first.id}")
                print(f"   Company ID: {first.company_id}")
                print(f"   SII Folio: {first.sii_folio}")
                print(f"   SII ID Interno: {first.sii_id_interno or 'N/A'}")
                print(f"   Período: {first.period_year}-{first.period_month:02d} ({first.period_display})")
                print(f"   Contribuyente: {first.contributor_rut}")
                print(f"   Fecha envío: {first.submission_date}")
                print(f"   Estado: {first.status}")
                print(f"   Monto: ${first.amount_cents:,}")
                print(f"   Estado descarga PDF: {first.pdf_download_status}")
                print(f"   Puede descargar PDF: {'✅ Sí' if first.can_download_pdf else '❌ No'}")
                print(f"   Vinculado a F29 local: {'✅ Sí' if first.is_linked_to_local_form else '❌ No'}")
                print(f"   Creado: {first.created_at}")

            print("\n" + "="*80)
            print("  ✅ TEST DE INTEGRACIÓN COMPLETADO EXITOSAMENTE")
            print("="*80)

        except Exception as e:
            print(f"\n❌ ERROR durante el test: {e}")
            import traceback
            traceback.print_exc()
            raise


async def test_query_performance():
    """Test de performance de queries comunes"""
    print("\n" + "="*80)
    print("  TEST DE PERFORMANCE - QUERIES COMUNES")
    print("="*80)

    async with AsyncSessionLocal() as db:
        import time

        # Query 1: Buscar por período
        print("\n📊 Query 1: Buscar F29 por período (2024-01)")
        start = time.time()
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.period_year == 2024,
            Form29SIIDownload.period_month == 1
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        elapsed = (time.time() - start) * 1000
        print(f"   ✅ Encontrados: {len(records)} registros en {elapsed:.2f}ms")

        # Query 2: Buscar sin id_interno_sii
        print("\n📊 Query 2: Buscar F29 sin id_interno_sii (no pueden descargar PDF)")
        start = time.time()
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.sii_id_interno.is_(None)
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        elapsed = (time.time() - start) * 1000
        print(f"   ✅ Encontrados: {len(records)} registros en {elapsed:.2f}ms")

        # Query 3: Buscar por estado
        print("\n📊 Query 3: Buscar F29 por estado (Vigente)")
        start = time.time()
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.status == "Vigente"
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        elapsed = (time.time() - start) * 1000
        print(f"   ✅ Encontrados: {len(records)} registros en {elapsed:.2f}ms")


async def main():
    """Run all tests"""
    print("\n🚀 Iniciando tests de integración F29...\n")

    # Test 1: Integración completa
    await test_full_integration()

    # Test 2: Performance de queries
    await test_query_performance()

    print("\n✅ Todos los tests completados\n")


if __name__ == "__main__":
    asyncio.run(main())
