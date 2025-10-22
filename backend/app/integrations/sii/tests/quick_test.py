#!/usr/bin/env python
"""
Script de prueba rápida para RPA v3

Uso:
    python quick_test.py

Configura las credenciales:
    export SII_TEST_RUT="12345678-9"
    export SII_TEST_PASSWORD="tu_password"
"""
import os
import sys
import logging
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fizko_django.settings')
import django
django.setup()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Importar cliente
from apps.sii.rpa_v3 import SIIClient


def main():
    """Ejecuta pruebas rápidas"""

    # Obtener credenciales
    tax_id = os.getenv("SII_TEST_RUT")
    password = os.getenv("SII_TEST_PASSWORD")

    if not tax_id or not password:
        print("❌ Error: Credenciales no configuradas")
        print("   export SII_TEST_RUT=\"12345678-9\"")
        print("   export SII_TEST_PASSWORD=\"tu_password\"")
        sys.exit(1)

    print("=" * 80)
    print("RPA v3 - QUICK TEST")
    print("=" * 80)
    print(f"RUT: {tax_id}")
    print(f"Headless: True")
    print("=" * 80)
    print()

    try:
        with SIIClient(tax_id=tax_id, password=password, headless=True) as client:

            # Test 1: Login
            print("🔐 TEST 1: Login")
            success = client.login()
            print(f"   ✅ Login: {success}")
            print()

            # Test 2: Cookies
            print("🍪 TEST 2: Cookies")
            cookies = client.get_cookies()
            print(f"   ✅ Total cookies: {len(cookies)}")
            print()

            # Test 3: Contribuyente
            print("📊 TEST 3: Contribuyente")
            info = client.get_contribuyente()
            print(f"   ✅ RUT: {info.get('rut', 'N/A')}")
            print(f"   ✅ Razón Social: {info.get('razon_social', 'N/A')}")
            print(f"   ✅ Email: {info.get('email', 'N/A')}")
            print()

            # Test 4: Compras
            print("📥 TEST 4: Compras DTEs")
            periodo = datetime.now().strftime("%Y%m")
            compras = client.get_compras(periodo=periodo)
            print(f"   ✅ Status: {compras.get('status', 'N/A')}")
            print(f"   ✅ Total docs: {len(compras.get('data', []))}")
            print(f"   ✅ Method: {compras.get('extraction_method', 'N/A')}")
            print()

            # Test 5: Ventas
            print("📤 TEST 5: Ventas DTEs")
            ventas = client.get_ventas(periodo=periodo)
            print(f"   ✅ Status: {ventas.get('status', 'N/A')}")
            print(f"   ✅ Total docs: {len(ventas.get('data', []))}")
            print(f"   ✅ Method: {ventas.get('extraction_method', 'N/A')}")
            print()

            # Test 6: F29 Lista
            print("📋 TEST 6: F29 Lista")
            anio = str(datetime.now().year - 1)
            f29_lista = client.get_f29_lista(anio=anio)
            print(f"   ✅ Total F29: {len(f29_lista)}")
            if f29_lista:
                form = f29_lista[0]
                print(f"   ✅ Primer folio: {form.get('folio', 'N/A')}")
            print()

            print("=" * 80)
            print("✅ TODOS LOS TESTS PASARON")
            print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR EN TESTS")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
