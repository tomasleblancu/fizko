"""
Test script to debug DIN (tipo 914) extraction for company ebb912c8-c444-4e9d-8cf6-ec4b73ca00e7
Expected folio: 801732057 in October 2024
"""
import asyncio
import logging
from app.config.supabase import get_supabase_client
from app.integrations.sii import SIIClient
from app.utils.encryption import decrypt_password

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_din_extraction():
    """Test DIN extraction for specific company"""
    company_id = "7deadc51-adec-4c5c-84a7-0465839adec1"
    periodo = "202510"  # October 2025

    # Get company info
    supabase = get_supabase_client()
    company = await supabase.companies.get_by_id(company_id)

    if not company:
        logger.error(f"❌ Company {company_id} not found")
        return

    logger.info(f"✅ Company found: {company.get('business_name')}")
    logger.info(f"   RUT: {company['rut']}")

    # Decrypt password
    encrypted_password = company.get("sii_password")
    if not encrypted_password:
        logger.error("❌ No SII credentials configured")
        return

    sii_password = decrypt_password(encrypted_password)
    if not sii_password:
        logger.error("❌ Failed to decrypt password")
        return

    logger.info("✅ Credentials decrypted")

    # Test extraction
    with SIIClient(tax_id=company['rut'], password=sii_password) as client:
        logger.info(f"\n{'='*60}")
        logger.info("STEP 1: Get resumen to see what document types exist")
        logger.info(f"{'='*60}")

        resumen_result = client.get_resumen(periodo=periodo)
        resumen_data = resumen_result.get("data", {})
        resumen_compras = resumen_data.get("resumen_compras", {})
        resumen_items = resumen_compras.get("data", []) if isinstance(resumen_compras, dict) else []

        logger.info(f"\n📊 Resumen for {periodo}:")
        for item in resumen_items:
            tipo_doc = item.get("rsmnTipoDocInteger")
            nombre_tipo = item.get("dcvNombreTipoDoc")
            cantidad = item.get("rsmnTotDoc", 0)
            tipo_ingreso = item.get("dcvTipoIngresoDoc")
            tiene_link = item.get("rsmnLink")

            logger.info(f"   • Tipo {tipo_doc} ({nombre_tipo}): {cantidad} docs")
            logger.info(f"     - Tipo ingreso: {tipo_ingreso}")
            logger.info(f"     - Tiene link: {tiene_link}")

        # Find DIN entry
        din_item = next((item for item in resumen_items if str(item.get("rsmnTipoDocInteger")) == "914"), None)

        if not din_item:
            logger.warning("⚠️ No DIN (914) found in resumen")
            return

        logger.info(f"\n{'='*60}")
        logger.info("STEP 2: Extract DIN (914) documents")
        logger.info(f"{'='*60}")
        logger.info(f"DIN entry in resumen: {din_item}")

        # Try to extract DIN documents
        try:
            compras_result = client.get_compras(
                periodo=periodo,
                tipo_doc="914",
                estado_contab="REGISTRO"
            )

            logger.info(f"\n📥 API Response for DIN (914):")
            logger.info(f"   Status: {compras_result.get('status')}")

            data = compras_result.get("data", [])
            logger.info(f"   Documents returned: {len(data)}")

            if data:
                logger.info(f"\n✅ DIN documents found:")
                for idx, doc in enumerate(data, 1):
                    folio = doc.get("detNroDoc") or doc.get("folio")
                    rut_emisor = doc.get("detRutDoc")
                    razon_social = doc.get("detRznSoc")
                    monto = doc.get("detMntTotal")

                    logger.info(f"   {idx}. Folio: {folio}")
                    logger.info(f"      RUT Emisor: {rut_emisor}")
                    logger.info(f"      Razón Social: {razon_social}")
                    logger.info(f"      Monto Total: {monto}")

                    # Check if this is our expected folio
                    if str(folio) == "801732057":
                        logger.info(f"      ⭐ FOUND EXPECTED FOLIO!")
            else:
                logger.warning(f"⚠️ No documents returned for tipo 914")
                logger.warning(f"   Full response: {compras_result}")

        except Exception as e:
            logger.error(f"❌ Error extracting DIN: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_din_extraction())
