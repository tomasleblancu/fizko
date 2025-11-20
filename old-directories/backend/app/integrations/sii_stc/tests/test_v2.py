#!/usr/bin/env python
"""
Test para STCClientV2 - Workaround con llenado de formulario

Uso:
    python -m app.integrations.sii_stc.tests.test_v2

Variables de entorno opcionales:
    STC_TEST_RUT - RUT a consultar (default: 77794858)
    STC_TEST_DV - DV del RUT (default: K)
    STC_HEADLESS - Modo headless (default: true)
"""
import os
import sys
import logging
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Ejecuta prueba del cliente V2"""

    # Importar después de configurar logging
    from app.integrations.sii_stc import STCClientV2
    from app.integrations.sii_stc.exceptions import (
        STCException,
        STCQueryError,
        STCTimeoutError
    )

    # Obtener parámetros de test
    rut = os.getenv("STC_TEST_RUT", "77794858")
    dv = os.getenv("STC_TEST_DV", "K")
    headless = os.getenv("STC_HEADLESS", "true").lower() == "true"

    print("=" * 80)
    print("SII STC CLIENT V2 - TEST (Form Fill Workaround)")
    print("=" * 80)
    print(f"RUT: {rut}-{dv}")
    print(f"Headless: {headless}")
    print("=" * 80)
    print()

    try:
        # Test 1: Inicialización del cliente
        print("🔧 TEST 1: Client Initialization")
        client = STCClientV2(headless=headless)
        print("   ✅ Client created")
        print()

        # Test 2: Context manager
        print("🔧 TEST 2: Context Manager")
        with client:
            print("   ✅ Context manager entered")

            # Test 3: Consulta directa (llena formulario y captura POST)
            print("🔍 TEST 3: Query Document (Fill Form + Intercept POST)")
            result = client.consultar_documento(
                rut=rut,
                dv=dv,
                timeout=30
            )
            print(f"   ✅ Query successful")
            print(f"   📄 Result type: {type(result)}")
            print()

            # Mostrar resultado
            print("📊 TEST 4: Result Details")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()

        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)

    except STCTimeoutError as e:
        print()
        print("=" * 80)
        print("⏰ TIMEOUT ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("Posibles causas:")
        print("- El portal STC está lento")
        print("- El formulario no se cargó a tiempo")
        print("- El POST a la API no se completó")
        print("- Aumentar timeout parameter")
        sys.exit(1)

    except STCQueryError as e:
        print()
        print("=" * 80)
        print("❌ QUERY ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("Posibles causas:")
        print("- El RUT no existe o es inválido")
        print("- El formulario cambió (actualizar selectores CSS)")
        print("- La API del SII cambió")
        sys.exit(1)

    except STCException as e:
        print()
        print("=" * 80)
        print("❌ STC ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ UNEXPECTED ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
