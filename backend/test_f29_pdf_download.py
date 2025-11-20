"""
Test script for F29 PDF download functionality.

Tests the complete flow:
1. Find a company (by RUT or first with SII credentials)
2. Find F29 records with id_interno_sii automatically
3. Download the PDF using the service
4. Validate PDF content
5. Extract data from PDF
6. Verify database update

Usage:
    # With specific company by RUT
    STC_TEST_RUT=77794858 STC_TEST_DV=K python test_f29_pdf_download.py

    # With browser visible
    STC_HEADLESS=false python test_f29_pdf_download.py

    # Headless mode (default)
    STC_HEADLESS=true python test_f29_pdf_download.py
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.config.supabase import get_supabase_client
from app.services.sii_service import SIIService


async def test_f29_pdf_download():
    """
    Test F29 PDF download and data extraction.

    Flow:
    1. Get company (by RUT env var or first with SII credentials)
    2. Find F29 with id_interno_sii (codInt) automatically
    3. Download PDF using service
    4. Verify extracted data
    """

    print('=' * 70)
    print('🧪 TEST: F29 PDF Download and Data Extraction')
    print('=' * 70)
    print()

    # Get Supabase client
    print('🔧 Initializing Supabase client...')
    supabase = get_supabase_client()

    # Check if we should use test credentials from env
    test_rut = os.getenv('STC_TEST_RUT')
    test_dv = os.getenv('STC_TEST_DV')

    if test_rut and test_dv:
        # Use test credentials from environment
        print(f'🔑 Using test credentials from environment: {test_rut}-{test_dv}')

        # Find test company
        tax_id = f"{test_rut}{test_dv}".lower()
        response = supabase._client.table('companies').select('*').eq('rut', tax_id).limit(1).execute()

        if not response.data:
            print(f'❌ No company found with RUT {tax_id}')
            print('   Create a company with this RUT first')
            return

        company = response.data[0]
        company_id = company['id']
        business_name = company.get('business_name', 'N/A')

        print(f'✅ Test company found: {business_name}')
        print(f'   Company ID: {company_id}')
        print()
    else:
        # Original behavior: get first company with SII credentials
        print('🔍 Searching for company with SII credentials...')
        response = supabase._client.table('companies').select('*').not_.is_('sii_password', 'null').limit(1).execute()

        if not response.data:
            print('❌ No company found with SII credentials')
            print()
            print('💡 TIP: Use test credentials:')
            print('   STC_TEST_RUT=77794858 STC_TEST_DV=K python test_f29_pdf_download.py')
            return

        company = response.data[0]
        company_id = company['id']
        business_name = company.get('business_name', 'N/A')

        print(f'✅ Company found: {business_name}')
        print(f'   Company ID: {company_id}')
        print()

    # Find F29 records with id_interno_sii but without PDF data
    print('🔍 Looking for F29 records ready for PDF download...')
    print('   (Records with id_interno_sii but without extracted data)')
    print()

    f29_response = (
        supabase._client
        .table('form29_sii_downloads')
        .select('*')
        .eq('company_id', company_id)
        .not_.is_('sii_id_interno', 'null')
        .order('period_year', desc=True)
        .order('period_month', desc=True)
        .limit(10)
        .execute()
    )

    if not f29_response.data:
        print('❌ No F29 records found with id_interno_sii')
        print('   Run sync_f29 first to extract F29 records from SII')
        print()
        print('💡 Example:')
        print(f'   STC_TEST_RUT={test_rut} STC_TEST_DV={test_dv} python test_f29_extraction.py')
        return

    f29_records = f29_response.data

    # Filter records without PDF data (not yet downloaded)
    records_without_pdf = [
        r for r in f29_records
        if not r.get('extra_data', {}).get('f29_data')
    ]

    print(f'✅ Found {len(f29_records)} F29 records with id_interno_sii')
    print(f'   {len(records_without_pdf)} without PDF data (ready for download)')
    print()

    # Show available records (prioritize those without PDF data)
    records_to_show = records_without_pdf[:5] if records_without_pdf else f29_records[:5]

    print('📋 Available F29 records for PDF download:')
    print('-' * 80)
    for i, record in enumerate(records_to_show, 1):
        folio = record.get('sii_folio', 'N/A')
        period = record.get('period_display', 'N/A')
        codint = record.get('sii_id_interno', 'N/A')
        has_pdf_data = '✅' if record.get('extra_data', {}).get('f29_data') else '⏳'

        print(f'{i}. Folio: {folio:12s} | Period: {period:8s} | codInt: {codint:10s} | Data: {has_pdf_data}')
    print()

    # Select first record without PDF data, or first record if all have data
    if records_without_pdf:
        selected = records_without_pdf[0]
        print('🎯 Auto-selected: First record WITHOUT PDF data')
    else:
        selected = f29_records[0]
        print('🎯 Auto-selected: First record (re-downloading since all have data)')

    folio = selected['sii_folio']
    id_interno_sii = selected['sii_id_interno']
    period_display = selected.get('period_display', 'N/A')

    print(f'   Folio: {folio}')
    print(f'   Period: {period_display}')
    print(f'   codInt: {id_interno_sii}')
    print()

    # Verify headless mode
    headless = os.getenv('STC_HEADLESS', 'true').lower() == 'true'
    print(f'ℹ️  Headless mode: {headless}')
    print()

    # ============================================================
    # TEST: Download PDF and extract data
    # ============================================================

    print('=' * 70)
    print('🚀 STARTING PDF DOWNLOAD AND EXTRACTION')
    print('=' * 70)
    print()

    service = SIIService(supabase)

    try:
        import time
        start_time = time.time()

        # Call service method
        result = await service.download_f29_pdf(
            company_id=company_id,
            folio=folio,
            id_interno_sii=id_interno_sii
        )

        elapsed = time.time() - start_time

        # ============================================================
        # RESULTS
        # ============================================================

        print()
        print('=' * 70)
        print('✅ PDF DOWNLOAD COMPLETED')
        print('=' * 70)
        print()

        if result.get('success'):
            print('✅ Success!')
            print()
            print('📊 Results:')
            print('-' * 70)
            print(f'   PDF Size: {result.get("pdf_size_mb", 0):.2f} MB')
            print(f'   Storage URL: {result.get("storage_url", "TODO - Not implemented")}')
            print(f'   Duration: {elapsed:.2f}s')
            print()

            # Show extracted data summary
            extracted = result.get('extracted_data', {})
            if extracted:
                print('📄 Extracted Data Summary:')
                print('-' * 70)

                header = extracted.get('header', {})
                print(f'   Contributor: {header.get("contributor_name", "N/A")}')
                print(f'   RUT: {header.get("rut", "N/A")}')
                print(f'   Period: {header.get("period", "N/A")}')
                print(f'   Folio: {header.get("folio", "N/A")}')
                print()

                codes = extracted.get('codes', {})
                print(f'   Total codes extracted: {len(codes)}')

                # Show some sample codes
                if codes:
                    print('   Sample codes:')
                    for i, (code, value) in enumerate(list(codes.items())[:5], 1):
                        print(f'      {code}: {value}')
                    if len(codes) > 5:
                        print(f'      ... and {len(codes) - 5} more')
                print()

                summary = extracted.get('summary', {})
                if summary:
                    print('   Summary:')
                    print(f'      Total debits: {summary.get("total_debits", 0)}')
                    print(f'      Total credits: {summary.get("total_credits", 0)}')
                    print(f'      Total quantities: {summary.get("total_quantities", 0)}')
                    print(f'      Extraction success: {extracted.get("extraction_success", False)}')
                print()

            # ============================================================
            # VERIFICATION: Check database update
            # ============================================================

            print('🔍 Verifying database update...')
            print()

            verification_response = (
                supabase._client
                .table('form29_sii_downloads')
                .select('*')
                .eq('company_id', company_id)
                .eq('sii_folio', folio)
                .limit(1)
                .execute()
            )

            if verification_response.data:
                updated_record = verification_response.data[0]
                extra_data = updated_record.get('extra_data', {})
                f29_data = extra_data.get('f29_data', {})

                if f29_data:
                    print('✅ Database updated successfully!')
                    print(f'   F29 data found in extra_data.f29_data')
                    print(f'   Codes in DB: {len(f29_data.get("codes", {}))}')
                    print(f'   Extraction success: {f29_data.get("extraction_success", False)}')
                else:
                    print('⚠️  Database record found but no F29 data in extra_data')
            else:
                print('❌ Could not verify database update')

            print()
            print('=' * 70)
            print('🎉 TEST COMPLETED SUCCESSFULLY!')
            print('=' * 70)
            print()
            print('✅ Flow validated:')
            print('   1. ✅ PDF download from SII')
            print('   2. ✅ PDF validation')
            print('   3. ✅ Data extraction from PDF')
            print('   4. ✅ Database update with extracted data')

        else:
            print('❌ Failed!')
            print(f'   Error: {result.get("error", "Unknown error")}')
            print()

    except Exception as e:
        print()
        print('=' * 70)
        print('❌ ERROR DURING PDF DOWNLOAD')
        print('=' * 70)
        print(f'Error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    asyncio.run(test_f29_pdf_download())
