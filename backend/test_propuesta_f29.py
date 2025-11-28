#!/usr/bin/env python3
"""
Script de prueba para verificar el método get_propuesta_f29 del SIIClient.

Este script prueba la obtención de la propuesta de F29 desde el SII
para una empresa específica.

Usage:
    python test_propuesta_f29.py
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_propuesta_f29(company_id: str, periodo: str):
    """
    Prueba el método get_propuesta_f29 para una empresa.

    Args:
        company_id: ID de la empresa
        periodo: Período en formato YYYYMM (ej: "202510")
    """
    from app.integrations.sii.client import SIIClient
    from app.utils.encryption import decrypt_password
    from supabase import create_client

    logger.info("=" * 80)
    logger.info(f"🧪 PRUEBA: get_propuesta_f29 para empresa {company_id}")
    logger.info(f"📅 Período: {periodo}")
    logger.info("=" * 80)

    # 1. Obtener credenciales de la empresa desde Supabase
    logger.info("\n📊 Paso 1: Obteniendo credenciales de la empresa...")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("❌ Variables SUPABASE_URL y SUPABASE_SERVICE_KEY requeridas")
        return

    supabase = create_client(supabase_url, supabase_key)

    try:
        response = (
            supabase
            .table("companies")
            .select("id, business_name, rut, sii_password")
            .eq("id", company_id)
            .maybe_single()
            .execute()
        )

        company = response.data if hasattr(response, 'data') else None

        if not company:
            logger.error(f"❌ Empresa no encontrada: {company_id}")
            return

        logger.info(f"✅ Empresa encontrada: {company.get('business_name')}")
        logger.info(f"   RUT: {company.get('rut')}")

        rut = company.get("rut")
        encrypted_password = company.get("sii_password")

        if not rut or not encrypted_password:
            logger.error("❌ La empresa no tiene RUT o password SII configurado")
            return

        # Desencriptar password
        logger.info("🔓 Desencriptando contraseña SII...")
        try:
            sii_password = decrypt_password(encrypted_password)
            logger.info("✅ Contraseña desencriptada exitosamente")
        except Exception as e:
            logger.error(f"❌ Error desencriptando contraseña: {e}", exc_info=True)
            return

    except Exception as e:
        logger.error(f"❌ Error obteniendo empresa: {e}", exc_info=True)
        return

    # 2. Crear SIIClient y hacer login
    logger.info("\n🔐 Paso 2: Creando cliente SII y haciendo login...")

    try:
        with SIIClient(tax_id=rut, password=sii_password) as client:
            logger.info("✅ SIIClient creado exitosamente")

            # Login
            logger.info("🔑 Iniciando sesión en SII...")
            client.login()
            logger.info("✅ Login exitoso")

            # 3. Obtener propuesta F29
            logger.info(f"\n📋 Paso 3: Obteniendo propuesta F29 para período {periodo}...")

            propuesta = client.get_propuesta_f29(periodo)

            if propuesta:
                logger.info("✅ Propuesta obtenida exitosamente")

                # Extraer información relevante
                data = propuesta.get("data", {})
                metadata = propuesta.get("metaData", {})

                codigos_propuestos = data.get("listCodPropuestos", [])
                codigos_complementar = data.get("listCodComplementar", [])
                condiciones = data.get("listCondiciones", [])

                logger.info("\n" + "=" * 80)
                logger.info("📊 RESULTADO DE LA PROPUESTA F29")
                logger.info("=" * 80)

                logger.info(f"\n📌 Códigos Propuestos: {len(codigos_propuestos)}")
                if codigos_propuestos:
                    for i, codigo in enumerate(codigos_propuestos[:5], 1):  # Mostrar primeros 5
                        # Manejar tanto dict como int
                        if isinstance(codigo, dict):
                            logger.info(f"   {i}. Código {codigo.get('codCasilla')}: {codigo.get('valorCasilla')}")
                        else:
                            logger.info(f"   {i}. Código: {codigo}")
                    if len(codigos_propuestos) > 5:
                        logger.info(f"   ... y {len(codigos_propuestos) - 5} más")

                logger.info(f"\n📝 Códigos a Complementar: {len(codigos_complementar)}")
                if codigos_complementar:
                    for i, codigo in enumerate(codigos_complementar[:5], 1):
                        # Manejar tanto dict como int
                        if isinstance(codigo, dict):
                            logger.info(f"   {i}. Código {codigo.get('codCasilla')}: {codigo.get('valorCasilla')}")
                        else:
                            logger.info(f"   {i}. Código: {codigo}")
                    if len(codigos_complementar) > 5:
                        logger.info(f"   ... y {len(codigos_complementar) - 5} más")

                logger.info(f"\n⚙️ Condiciones del Contribuyente: {len(condiciones)}")
                if condiciones:
                    for condicion in condiciones:
                        logger.info(f"   - {condicion}")

                logger.info(f"\n📄 Metadata:")
                logger.info(f"   Código respuesta: {metadata.get('codigoRespuesta')}")
                logger.info(f"   Descripción: {metadata.get('descripcionRespuesta')}")

                # Guardar JSON completo para inspección
                output_file = f"propuesta_f29_{company_id}_{periodo}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(propuesta, f, indent=2, ensure_ascii=False)
                logger.info(f"\n💾 Propuesta completa guardada en: {output_file}")

                logger.info("\n" + "=" * 80)
                logger.info("✅ PRUEBA COMPLETADA EXITOSAMENTE")
                logger.info("=" * 80)

            else:
                logger.warning("⚠️ No se obtuvo propuesta del SII")

    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {e}", exc_info=True)
        logger.info("\n" + "=" * 80)
        logger.info("❌ PRUEBA FALLIDA")
        logger.info("=" * 80)


if __name__ == "__main__":
    # Configuración de la prueba
    COMPANY_ID = "3ee62c88-db13-4db9-bd74-1367f8c30e66"
    PERIODO = "202510"  # Octubre 2025

    logger.info("\n")
    logger.info("🚀 Iniciando script de prueba de propuesta F29")
    logger.info(f"   Empresa: {COMPANY_ID}")
    logger.info(f"   Período: {PERIODO}")
    logger.info("\n")

    test_propuesta_f29(COMPANY_ID, PERIODO)
