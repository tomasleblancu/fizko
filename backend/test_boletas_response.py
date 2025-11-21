"""
Test script to check complete response from SII boletas honorarios API
"""

import asyncio
import json
import logging
from app.config.database import get_db
from app.repositories.core.profile import ProfileRepository
from app.integrations.sii import SIIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test company with honorarios receipts
TEST_COMPANY_ID = "4ee048a7-8fb1-43ac-bbb0-0c6a9c7c8e97"  # ZANEK LIMITADA - has 31 honorarios

async def test_boletas_response():
    """Test boletas honorarios response to see all fields"""

    logger.info("=" * 80)
    logger.info("TESTING BOLETAS HONORARIOS RESPONSE")
    logger.info("=" * 80)

    async with get_db() as db:
        # Get company SII credentials
        profile_repo = ProfileRepository(db)
        profile = await profile_repo.get_company_profile(TEST_COMPANY_ID)

        if not profile or not profile.get('sii_rut') or not profile.get('sii_password'):
            logger.error("❌ Company has no SII credentials")
            return

        sii_rut = profile['sii_rut']
        sii_password = profile['sii_password']

        logger.info(f"📋 Company RUT: {sii_rut}")

        # Initialize SII client
        async with SIIClient(rut=sii_rut, password=sii_password, db=db, company_id=TEST_COMPANY_ID) as client:
            # Login
            logger.info("🔐 Logging in to SII...")
            await client.login()
            logger.info("✅ Logged in successfully")

            # Get boletas honorarios for current month
            logger.info("\n📥 Fetching boletas honorarios...")
            result = await client.get_boletas_honorarios(period="202510")

            logger.info("\n" + "=" * 80)
            logger.info("FULL RESPONSE STRUCTURE")
            logger.info("=" * 80)

            # Print full structure
            logger.info(f"\nKeys in response: {list(result.keys())}")

            if 'boletas' in result and result['boletas']:
                logger.info(f"\nTotal boletas: {len(result['boletas'])}")
                logger.info("\n" + "=" * 80)
                logger.info("FIRST BOLETA COMPLETE DATA:")
                logger.info("=" * 80)

                first_boleta = result['boletas'][0]
                logger.info(json.dumps(first_boleta, indent=2, ensure_ascii=False))

                logger.info("\n" + "=" * 80)
                logger.info("BOLETA FIELDS:")
                logger.info("=" * 80)
                for key, value in first_boleta.items():
                    logger.info(f"  {key}: {value} (type: {type(value).__name__})")

                # Check if there's any RUT-related field
                logger.info("\n" + "=" * 80)
                logger.info("RUT-RELATED FIELDS:")
                logger.info("=" * 80)
                rut_fields = {k: v for k, v in first_boleta.items() if 'rut' in k.lower()}
                if rut_fields:
                    for key, value in rut_fields.items():
                        logger.info(f"  ✓ {key}: {value}")
                else:
                    logger.info("  ❌ No RUT fields found for issuer")

                # Check for emisor-related fields
                logger.info("\n" + "=" * 80)
                logger.info("EMISOR-RELATED FIELDS:")
                logger.info("=" * 80)
                emisor_fields = {k: v for k, v in first_boleta.items() if 'emis' in k.lower()}
                if emisor_fields:
                    for key, value in emisor_fields.items():
                        logger.info(f"  ✓ {key}: {value}")
                else:
                    logger.info("  ❌ No emisor fields found")
            else:
                logger.warning("⚠️ No boletas found in response")

            if 'totales' in result:
                logger.info("\n" + "=" * 80)
                logger.info("TOTALES:")
                logger.info("=" * 80)
                logger.info(json.dumps(result['totales'], indent=2, ensure_ascii=False))

            if 'paginacion' in result:
                logger.info("\n" + "=" * 80)
                logger.info("PAGINACION:")
                logger.info("=" * 80)
                logger.info(json.dumps(result['paginacion'], indent=2, ensure_ascii=False))

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETED")
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_boletas_response())
