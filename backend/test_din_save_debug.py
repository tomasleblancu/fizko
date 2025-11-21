"""
Debug script to check if DIN documents are being parsed and saved correctly
"""
import asyncio
import logging
from app.config.supabase import get_supabase_client
from app.services.sii_service import SIIService

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_din_save():
    """Test DIN save process with detailed logging"""
    company_id = "7deadc51-adec-4c5c-84a7-0465839adec1"

    supabase = get_supabase_client()
    service = SIIService(supabase)

    logger.info("🚀 Starting DIN-focused sync for October 2025...")

    # Sync only October (month_offset=1)
    result = await service.sync_documents(
        company_id=company_id,
        months=1,
        month_offset=1
    )

    logger.info(f"\n{'='*60}")
    logger.info("FINAL RESULTS:")
    logger.info(f"{'='*60}")
    logger.info(f"Compras total: {result['compras']['total']}")
    logger.info(f"  - Nuevos: {result['compras']['nuevos']}")
    logger.info(f"  - Actualizados: {result['compras']['actualizados']}")

    # Check DB directly for DIN
    logger.info(f"\n{'='*60}")
    logger.info("CHECKING DATABASE...")
    logger.info(f"{'='*60}")

    response = supabase._client.table('purchase_documents').select('*').eq(
        'company_id', company_id
    ).eq('document_type', 'declaracion_ingreso').gte(
        'issue_date', '2025-10-01'
    ).lt('issue_date', '2025-11-01').execute()

    din_docs = response.data
    logger.info(f"DIN in database: {len(din_docs)}")

    if din_docs:
        for doc in din_docs:
            logger.info(f"  Folio: {doc['folio']} - {doc['sender_name']}")
    else:
        logger.error("❌ NO DIN DOCUMENTS IN DATABASE!")


if __name__ == "__main__":
    asyncio.run(test_din_save())
