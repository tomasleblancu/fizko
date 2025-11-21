"""
Test sync for company with DIN documents
"""
import asyncio
import logging
from app.config.supabase import get_supabase_client
from app.services.sii_service import SIIService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_sync():
    """Test sync for company with DIN"""
    company_id = "7deadc51-adec-4c5c-84a7-0465839adec1"

    supabase = get_supabase_client()
    service = SIIService(supabase)

    logger.info("🚀 Starting sync for October 2025...")

    # Sync documents with month_offset=1 (October = 1 month ago from November)
    result = await service.sync_documents(
        company_id=company_id,
        months=1,
        month_offset=1  # October 2025
    )

    logger.info(f"\n{'='*60}")
    logger.info("SYNC RESULTS:")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Success: {result.get('success')}")
    logger.info(f"📊 Compras: {result.get('compras')}")
    logger.info(f"📊 Ventas: {result.get('ventas')}")
    logger.info(f"📊 Honorarios: {result.get('honorarios', {})}")
    logger.info(f"⏱️  Duration: {result.get('duration_seconds')}s")
    logger.info(f"❌ Errors: {result.get('errors', 0)}")

    # Now check if DIN was saved
    logger.info(f"\n{'='*60}")
    logger.info("CHECKING DATABASE FOR DIN...")
    logger.info(f"{'='*60}")

    # Query for DIN documents (tipo 914) directly from database
    response = supabase._client.table('purchase_documents').select('*').eq(
        'company_id', company_id
    ).eq('document_type', 'declaracion_ingreso').eq(
        'period', '202510'
    ).execute()

    din_docs = response.data
    logger.info(f"📋 Found {len(din_docs)} DIN documents in database")

    if din_docs:
        for doc in din_docs:
            logger.info(f"   • Folio: {doc.get('folio')}")
            logger.info(f"     Tipo: {doc.get('document_type')}")
            logger.info(f"     Proveedor: {doc.get('sender_name')}")
            logger.info(f"     Monto: ${doc.get('total_amount'):,.0f}")
    else:
        logger.error("❌ NO DIN DOCUMENTS IN DATABASE!")


if __name__ == "__main__":
    asyncio.run(test_sync())
