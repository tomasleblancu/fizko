#!/usr/bin/env python3
"""
Script de prueba para get_propuesta_f29

Uso:
    python scripts/test_get_propuesta_f29.py

Este script:
1. Obtiene las credenciales SII de la empresa desde Supabase
2. Usa el SIIClient para llamar a get_propuesta_f29
3. Muestra el resultado completo
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config.supabase import get_supabase_client
from app.integrations.sii import SIIClient
from app.utils.encryption import decrypt_password


async def main():
    # Configuración
    COMPANY_ID = "4dd964b5-7718-452a-8c41-39d993de5d6d"
    PERIODO = "202511"  # Octubre 2025

    print("=" * 80)
    print("🔍 Script de prueba: get_propuesta_f29")
    print("=" * 80)
    print(f"Company ID: {COMPANY_ID}")
    print(f"Período: {PERIODO}")
    print()

    # 1. Conectar a Supabase
    print("📡 Conectando a Supabase...")
    supabase = get_supabase_client()

    # 2. Obtener empresa
    print(f"🏢 Obteniendo información de la empresa...")
    company = await supabase.companies.get_by_id(COMPANY_ID)

    if not company:
        print(f"❌ Error: Empresa con ID {COMPANY_ID} no encontrada")
        return

    print(f"✅ Empresa encontrada: {company.get('business_name')}")
    print(f"   RUT: {company.get('rut')}")

    # 3. Verificar credenciales SII
    if not company.get("sii_password"):
        print("❌ Error: La empresa no tiene credenciales SII configuradas")
        return

    print("🔐 Desencriptando contraseña SII...")
    encrypted_password = company["sii_password"]
    sii_password = decrypt_password(encrypted_password)

    if not sii_password:
        print("❌ Error: No se pudo desencriptar la contraseña SII")
        return

    print("✅ Contraseña desencriptada correctamente")
    print()

    # 4. Usar SIIClient para obtener propuesta F29
    print("🚀 Iniciando SIIClient...")
    print(f"   RUT: {company['rut']}")
    print(f"   Período: {PERIODO}")
    print()

    rut = company["rut"]

    try:
        with SIIClient(tax_id=rut, password=sii_password, headless=True) as client:
            print("🔐 Autenticando en el SII...")
            client.login()
            print("✅ Autenticación exitosa")
            print()

            print(f"📥 Obteniendo propuesta F29 para período {PERIODO}...")
            propuesta = client.get_propuesta_f29(periodo=PERIODO)
            print("✅ Propuesta F29 obtenida exitosamente")
            print()

            # 5. Mostrar resultados
            print("=" * 80)
            print("📊 RESULTADO")
            print("=" * 80)
            print()

            # Mostrar estructura general
            if isinstance(propuesta, dict):
                print(f"Claves principales: {list(propuesta.keys())}")
                print()

                # Mostrar metadata si existe
                if "metaData" in propuesta:
                    print("📋 Metadata:")
                    metadata = propuesta["metaData"]
                    for key, value in metadata.items():
                        if key != "errors":  # Skip errors si están vacíos
                            print(f"   {key}: {value}")
                    print()

                # Mostrar data si existe
                if "data" in propuesta:
                    data = propuesta["data"]
                    print("📦 Data:")

                    if isinstance(data, dict):
                        # Mostrar claves del data
                        print(f"   Claves: {list(data.keys())}")
                        print()

                        # Mostrar algunos campos importantes si existen
                        if "listCodPropuestos" in data:
                            codigos = data["listCodPropuestos"]
                            print(f"   💰 Códigos propuestos: {len(codigos) if isinstance(codigos, list) else 'N/A'}")
                            if isinstance(codigos, list) and len(codigos) > 0:
                                print(f"   Primeros 5 códigos:")
                                for i, codigo in enumerate(codigos[:5]):
                                    print(f"      {i+1}. {codigo}")
                            print()

                        if "periodo" in data:
                            print(f"   📅 Período: {data['periodo']}")

                        if "formCodigo" in data:
                            print(f"   📝 Formulario: {data['formCodigo']}")

                        if "rutCntr" in data:
                            print(f"   🏢 RUT Contribuyente: {data['rutCntr']}-{data.get('dvCntr', '')}")

                        print()

                # Mostrar JSON completo (pretty-printed)
                print("=" * 80)
                print("📄 JSON COMPLETO")
                print("=" * 80)
                print()
                print(json.dumps(propuesta, indent=2, ensure_ascii=False))

            else:
                print(f"Tipo de respuesta: {type(propuesta)}")
                print(propuesta)

            print()
            print("=" * 80)
            print("✅ Script completado exitosamente")
            print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR")
        print("=" * 80)
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
