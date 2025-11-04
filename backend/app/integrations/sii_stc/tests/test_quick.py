#!/usr/bin/env python
"""
Script de prueba rápida para STC Integration

Uso:
    python -m app.integrations.sii_stc.tests.test_quick

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
    """Ejecuta prueba rápida"""

    # Importar después de configurar logging
    from app.integrations.sii_stc import STCClient
    from app.integrations.sii_stc.exceptions import (
        STCException,
        STCRecaptchaError,
        STCQueryError,
        STCTimeoutError
    )

    # Obtener parámetros de test
    rut = os.getenv("STC_TEST_RUT", "77794858")
    dv = os.getenv("STC_TEST_DV", "K")
    headless = os.getenv("STC_HEADLESS", "true").lower() == "true"

    print("=" * 80)
    print("SII STC INTEGRATION - QUICK TEST")
    print("=" * 80)
    print(f"RUT: {rut}-{dv}")
    print(f"Headless: {headless}")
    print("=" * 80)
    print()

    try:
        # Test 1: Inicialización del cliente
        print("🔧 TEST 1: Client Initialization")
        client = STCClient(headless=headless)
        print("   ✅ Client created")
        print()

        # Test 2: Context manager
        print("🔧 TEST 2: Context Manager")
        with client:
            print("   ✅ Context manager entered")

            # Test 3: Preparación (navegación, cookies, token)
            print("🚀 TEST 3: Client Preparation")
            prep_result = client.prepare(recaptcha_timeout=20)
            print(f"   ✅ Preparation successful")
            print(f"   📊 Cookies: {prep_result['cookies_count']}")
            print(f"   🔑 Token: {prep_result['recaptcha_token']}")
            print()

            # Test 4: Consulta de documento
            print("🔍 TEST 4: Document Query")
            result = client.consultar_documento(
                rut=rut,
                dv=dv,
                auto_prepare=False,
                timeout=15
            )
            print(f"   ✅ Query successful")
            print(f"   📄 Result type: {type(result)}")
            print()

            # Mostrar resultado
            print("📊 TEST 5: Result Details")
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
        print("- reCAPTCHA no se cargó a tiempo")
        print("- Aumentar recaptcha_timeout o query_timeout")
        sys.exit(1)

    except STCRecaptchaError as e:
        print()
        print("=" * 80)
        print("🤖 RECAPTCHA ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("Posibles causas:")
        print("- No se pudo interceptar el token de reCAPTCHA")
        print("- El formato de respuesta de reCAPTCHA cambió")
        print("- selenium-wire no está instalado correctamente")
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
        print("- El token reCAPTCHA expiró")
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
