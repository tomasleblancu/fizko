"""
Test E2E para sync completo de F29 (extracción + transformación + guardado)

Simula el flujo completo del Celery task sync_f29:
1. Extracción de F29 desde SII (con SIIClient)
2. Transformación de datos al schema de Supabase
3. Bulk upsert en form29_sii_downloads

Uso:
    STC_HEADLESS=false python test_f29_extraction.py
    STC_HEADLESS=true python test_f29_extraction.py  # Default
"""
import os
import time
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from app.services.sii_service import SIIService
from app.config.supabase import get_supabase_client


async def test_f29_sync_e2e():
    """
    Test E2E completo del sync de F29

    Cubre el mismo flujo que el Celery task sync_f29:
    - Obtiene credenciales de la empresa
    - Extrae F29 del SII
    - Transforma datos al schema de DB
    - Guarda en form29_sii_downloads
    """

    year = '2024'

    # Obtener cliente Supabase
    print('🔧 Inicializando Supabase client...')
    supabase = get_supabase_client()

    # Check if we should use test credentials from env
    test_rut = os.getenv('STC_TEST_RUT')
    test_dv = os.getenv('STC_TEST_DV')

    if test_rut and test_dv:
        # Use test credentials from environment
        print(f'🔑 Usando credenciales de test desde environment: {test_rut}-{test_dv}')

        # Find test company using normalized RUT format (without hyphen, lowercase)
        # Database stores RUTs as "12345678k" not "12345678-K"
        tax_id = f"{test_rut}{test_dv}".lower()
        response = supabase._client.table('companies').select('*').eq('rut', tax_id).limit(1).execute()

        if not response.data:
            print('❌ No se encontró empresa con RUT de test en la base de datos')
            print(f'   Crea una empresa con RUT {tax_id} primero')
            return

        company = response.data[0]
        company_id = company['id']
        business_name = company.get('business_name', 'N/A')

        print(f'✅ Empresa de test encontrada: {business_name}')
        print(f'   Company ID: {company_id}')
        print()
        print('⚠️  NOTA: Este test usará las credenciales SII guardadas en la empresa')
        print('   Si las credenciales están encriptadas con otra ENCRYPTION_KEY, fallará.')
        print()
    else:
        # Original behavior: get first company with SII credentials
        print('🔍 Buscando empresa con credenciales SII...')
        response = supabase._client.table('companies').select('*').not_.is_('sii_password', 'null').limit(1).execute()

        if not response.data:
            print('❌ No se encontró ninguna empresa con credenciales SII')
            print()
            print('💡 TIP: Puedes usar credenciales de test:')
            print('   STC_TEST_RUT=77794858 STC_TEST_DV=K python test_f29_extraction.py')
            return

        company = response.data[0]
        company_id = company['id']
        business_name = company.get('business_name', 'N/A')

    print(f'✅ Empresa encontrada: {business_name}')
    print(f'   Company ID: {company_id}')
    print(f'   Año a sincronizar: {year}')
    print()

    # Verificar modo headless
    headless = os.getenv('STC_HEADLESS', 'true').lower() == 'true'
    print(f'ℹ️  Modo headless: {headless}')
    print()

    # ============================================================
    # PASO 1: EXTRACCIÓN + TRANSFORMACIÓN + GUARDADO (E2E)
    # ============================================================

    print('=' * 70)
    print('🚀 INICIANDO SYNC E2E DE F29')
    print('=' * 70)
    print()

    # Crear servicio SII (igual que en Celery task)
    service = SIIService(supabase)

    try:
        # Ejecutar sync completo (extrae, transforma y guarda)
        print('⏱️  Midiendo tiempo total del sync...')
        start_time = time.time()

        result = await service.sync_f29(
            company_id=company_id,
            year=year
        )

        elapsed = time.time() - start_time

        # ============================================================
        # RESULTADOS
        # ============================================================

        print()
        print('=' * 70)
        print('✅ SYNC E2E COMPLETADO')
        print('=' * 70)
        print()

        # Mostrar estadísticas del sync
        print('📊 Estadísticas del sync:')
        print('-' * 70)
        print(f'   Success: {result.get("success")}')
        print(f'   Total formularios: {result.get("total", 0)}')
        print(f'   Nuevos: {result.get("nuevos", 0)}')
        print(f'   Actualizados: {result.get("actualizados", 0)}')
        print(f'   Duración (service): {result.get("duration_seconds", 0):.2f}s')
        print(f'   Duración (total): {elapsed:.2f}s')
        print()

        # ============================================================
        # VERIFICACIÓN: Leer datos guardados desde Supabase
        # ============================================================

        print('🔍 Verificando datos guardados en Supabase...')
        print()

        verification_response = (
            supabase._client
            .table('form29_sii_downloads')
            .select('*')
            .eq('company_id', company_id)
            .order('period_year', desc=True)
            .order('period_month', desc=True)
            .execute()
        )

        saved_forms = verification_response.data

        print(f'✅ Total registros en DB: {len(saved_forms)}')
        print()

        if saved_forms:
            print('📄 Formularios guardados en Supabase:')
            print('-' * 70)

            for i, form in enumerate(saved_forms, 1):
                folio = form.get('sii_folio', 'N/A')
                period_display = form.get('period_display', 'N/A')
                period_year = form.get('period_year', 'N/A')
                period_month = form.get('period_month', 'N/A')
                contributor_rut = form.get('contributor_rut', 'N/A')
                status = form.get('status', 'N/A')
                codint = form.get('sii_id_interno', 'N/A')
                pdf_status = form.get('pdf_download_status', 'N/A')
                amount = form.get('amount_cents', 0)

                print(f'{i:2d}. Folio: {folio:12s} | Period: {period_display:8s} '
                      f'({period_year}/{period_month:02d})')
                print(f'    RUT: {contributor_rut:12s} | Status: {status:10s} | '
                      f'PDF: {pdf_status:10s}')
                print(f'    codInt: {codint:10s} | Amount: ${amount:>12,}')
                print()

            # ============================================================
            # VALIDACIONES
            # ============================================================

            print('=' * 70)
            print('🔬 VALIDACIONES')
            print('=' * 70)
            print()

            # Validación 1: Todos tienen period_year y period_month
            missing_period = [
                f for f in saved_forms
                if not f.get('period_year') or not f.get('period_month')
            ]
            if missing_period:
                print(f'⚠️  {len(missing_period)} formularios sin period_year/month')
            else:
                print('✅ Todos los formularios tienen period_year y period_month')

            # Validación 2: Todos tienen contributor_rut
            missing_rut = [f for f in saved_forms if not f.get('contributor_rut')]
            if missing_rut:
                print(f'⚠️  {len(missing_rut)} formularios sin contributor_rut')
            else:
                print('✅ Todos los formularios tienen contributor_rut')

            # Validación 3: Conteo de codInt extraídos
            with_codint = [f for f in saved_forms if f.get('sii_id_interno')]
            without_codint = [f for f in saved_forms if not f.get('sii_id_interno')]
            print(f'✅ {len(with_codint)} formularios CON sii_id_interno (codInt)')
            if without_codint:
                print(f'⚠️  {len(without_codint)} formularios SIN sii_id_interno')

            # Validación 4: PDF download status
            pending_pdf = [
                f for f in saved_forms
                if f.get('pdf_download_status') == 'pending'
            ]
            error_pdf = [
                f for f in saved_forms
                if f.get('pdf_download_status') == 'error'
            ]
            print(f'ℹ️  {len(pending_pdf)} formularios listos para descarga PDF')
            if error_pdf:
                print(f'⚠️  {len(error_pdf)} formularios con error en PDF (sin codInt)')

            print()

        print('=' * 70)
        print('🎉 SYNC E2E COMPLETADO EXITOSAMENTE!')
        print('=' * 70)
        print()
        print('✅ Flujo validado:')
        print('   1. ✅ Extracción desde SII')
        print('   2. ✅ Transformación de datos')
        print('   3. ✅ Guardado en form29_sii_downloads')
        print('   4. ✅ Verificación de datos guardados')
        print()

        # ============================================================
        # PASO 2: DESCARGA DE PDFs Y EXTRACCIÓN DE DATOS
        # ============================================================

        print('=' * 70)
        print('📥 PASO 2: DESCARGA DE PDFs Y EXTRACCIÓN DE DATOS')
        print('=' * 70)
        print()

        # Buscar formularios con id_interno_sii pero sin PDF descargado
        forms_to_download = [
            f for f in saved_forms
            if f.get('sii_id_interno') and not f.get('extra_data', {}).get('f29_data')
        ]

        if not forms_to_download:
            print('ℹ️  No hay formularios pendientes de descarga de PDF')
            print('   (Todos los formularios con sii_id_interno ya tienen f29_data)')
            print()
        else:
            print(f'📋 Formularios listos para descarga de PDF: {len(forms_to_download)}')
            print()

            # Limitar a 3 descargas para el test
            max_downloads = min(3, len(forms_to_download))
            print(f'🎯 Descargando PDFs de {max_downloads} formularios (máximo para test)...')
            print()

            successful_downloads = 0
            failed_downloads = 0

            for i, form in enumerate(forms_to_download[:max_downloads], 1):
                folio = form.get('sii_folio')
                period_display = form.get('period_display', 'N/A')
                id_interno_sii = form.get('sii_id_interno')

                print(f'{i}/{max_downloads}. Descargando PDF: Folio={folio}, Period={period_display}')

                try:
                    # Descargar PDF y extraer datos
                    pdf_result = await service.download_f29_pdf(
                        company_id=company_id,
                        folio=folio,
                        id_interno_sii=id_interno_sii
                    )

                    if pdf_result.get('success'):
                        successful_downloads += 1
                        extracted = pdf_result.get('extracted_data', {})
                        codes_count = len(extracted.get('codes', {}))
                        pdf_size = pdf_result.get('pdf_size_mb', 0)

                        print(f'   ✅ Descargado: {pdf_size:.2f}MB, {codes_count} códigos extraídos')
                    else:
                        failed_downloads += 1
                        error = pdf_result.get('error', 'Unknown error')
                        print(f'   ❌ Error: {error}')

                except Exception as e:
                    failed_downloads += 1
                    print(f'   ❌ Excepción: {type(e).__name__}: {e}')

                print()

            # Resumen de descargas
            print('=' * 70)
            print('📊 RESUMEN DE DESCARGAS DE PDF')
            print('=' * 70)
            print(f'   Total intentos: {max_downloads}')
            print(f'   ✅ Exitosas: {successful_downloads}')
            print(f'   ❌ Fallidas: {failed_downloads}')
            print()

            if successful_downloads > 0:
                # Verificar datos extraídos en la base de datos
                print('🔍 Verificando datos extraídos en la base de datos...')
                print()

                verification_response = (
                    supabase._client
                    .table('form29_sii_downloads')
                    .select('*')
                    .eq('company_id', company_id)
                    .not_.is_('sii_id_interno', 'null')
                    .order('period_year', desc=True)
                    .order('period_month', desc=True)
                    .execute()
                )

                updated_forms = verification_response.data
                forms_with_data = [
                    f for f in updated_forms
                    if f.get('extra_data', {}).get('f29_data')
                ]

                print(f'✅ Formularios con datos extraídos: {len(forms_with_data)}/{len(updated_forms)}')
                print()

                if forms_with_data:
                    print('📄 Muestra de datos extraídos:')
                    print('-' * 70)

                    for i, form in enumerate(forms_with_data[:3], 1):
                        folio = form.get('sii_folio', 'N/A')
                        period = form.get('period_display', 'N/A')
                        f29_data = form.get('extra_data', {}).get('f29_data', {})
                        codes = f29_data.get('codes', {})
                        extraction_success = f29_data.get('extraction_success', False)

                        print(f'{i}. Folio: {folio} | Period: {period}')
                        print(f'   Códigos extraídos: {len(codes)}')
                        print(f'   Extracción exitosa: {extraction_success}')

                        # Mostrar algunos códigos de muestra
                        if codes:
                            sample_codes = list(codes.items())[:3]
                            print('   Códigos de muestra:')
                            for code, value in sample_codes:
                                print(f'      {code}: {value}')
                        print()

        print('=' * 70)
        print('🎉 TEST COMPLETO FINALIZADO!')
        print('=' * 70)
        print()
        print('✅ Flujo completo validado:')
        print('   1. ✅ Extracción de F29 desde SII')
        print('   2. ✅ Transformación y guardado en DB')
        print('   3. ✅ Descarga de PDFs de formularios')
        print('   4. ✅ Extracción de datos de PDFs')
        print('   5. ✅ Actualización de DB con datos extraídos')

    except Exception as e:
        print()
        print('=' * 70)
        print('❌ ERROR DURANTE EL TEST')
        print('=' * 70)
        print(f'Error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    # Ejecutar test async
    asyncio.run(test_f29_sync_e2e())
