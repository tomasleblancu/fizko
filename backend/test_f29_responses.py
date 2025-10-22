#!/usr/bin/env python3
"""
Script para probar los métodos de F29 y ver las respuestas reales
"""
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.integrations.sii import SIIClient

# Test credentials
TEST_RUT = "77794858-k"
TEST_PASSWORD = "SiiPfufl574@#"

def print_separator(title: str):
    """Print a nice separator"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_f29_lista():
    """Test get_f29_lista and show response structure"""
    print_separator("TEST 1: get_f29_lista()")

    # Use last year to ensure we have data
    test_year = str(datetime.now().year - 1)
    print(f"Testing with year: {test_year}\n")

    try:
        with SIIClient(tax_id=TEST_RUT, password=TEST_PASSWORD, headless=True) as client:
            print("🔐 Logging in...")
            # F29 does login automatically

            print(f"📋 Fetching F29 list for year {test_year}...")
            formularios = client.get_f29_lista(anio=test_year)

            print(f"\n✅ SUCCESS! Retrieved {len(formularios)} formularios\n")

            # Show structure of first item
            if formularios:
                print("📄 First formulario structure:")
                print(json.dumps(formularios[0], indent=2, default=str, ensure_ascii=False))

                print("\n📊 All fields present in first formulario:")
                for key, value in formularios[0].items():
                    print(f"  - {key:20s}: {type(value).__name__:15s} = {value}")

                # Show summary of all formularios
                print(f"\n📋 Summary of all {len(formularios)} formularios:")
                print(f"{'Period':<12} {'Folio':<15} {'Status':<12} {'Amount':>15} {'Has id_interno_sii':<10}")
                print("-" * 75)
                for f in formularios:
                    has_id = '✅ Yes' if 'id_interno_sii' in f else '❌ No'
                    print(f"{f.get('period', 'N/A'):<12} {f.get('folio', 'N/A'):<15} {f.get('status', 'N/A'):<12} {f.get('amount', 0):>15,} {has_id:<10}")

            else:
                print("⚠️ No formularios found for this year")

            return formularios

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_f29_compacto(formularios):
    """Test get_f29_compacto to download PDF"""
    print_separator("TEST 2: get_f29_compacto()")

    if not formularios:
        print("⚠️ Skipping PDF download test - no formularios available")
        return

    # Get first formulario with id_interno_sii
    f29_to_download = None
    for f in formularios:
        if 'id_interno_sii' in f:
            f29_to_download = f
            break

    if not f29_to_download:
        print("⚠️ No formulario found with id_interno_sii - cannot download PDF")
        return

    print(f"📥 Testing PDF download for:")
    print(f"  - Period: {f29_to_download['period']}")
    print(f"  - Folio: {f29_to_download['folio']}")
    print(f"  - ID Interno SII: {f29_to_download['id_interno_sii']}\n")

    try:
        with SIIClient(tax_id=TEST_RUT, password=TEST_PASSWORD, headless=True) as client:
            print("🔐 Logging in...")
            client.login(force_new=True)

            print("📄 Downloading PDF...")
            pdf_bytes = client.get_f29_compacto(
                folio=f29_to_download['folio'],
                id_interno_sii=f29_to_download['id_interno_sii']
            )

            if pdf_bytes:
                print(f"✅ SUCCESS! PDF downloaded: {len(pdf_bytes):,} bytes")
                print(f"   First 50 bytes: {pdf_bytes[:50]}")

                # Save to file for inspection
                filename = f"f29_{f29_to_download['period']}_test.pdf"
                with open(filename, 'wb') as f:
                    f.write(pdf_bytes)
                print(f"   💾 Saved to: {filename}")

            else:
                print("❌ PDF download returned None")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print_separator("F29 RESPONSE TESTING")
    print("This script will test F29 methods and show real response structures\n")

    # Test 1: Get F29 lista
    formularios = test_f29_lista()

    # Test 2: Download PDF (only if we have formularios)
    if formularios:
        test_f29_compacto(formularios)

    print_separator("TESTS COMPLETED")
    print("\nReview the output above to understand the response structures.")
    print("Use this information to design the database models.\n")

if __name__ == "__main__":
    main()
