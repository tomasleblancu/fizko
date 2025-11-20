"""
Honorarios Repository - Handles honorarios receipts queries.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class HonorariosRepository(BaseRepository):
    """Repository for honorarios receipts data access."""

    async def upsert_honorarios_receipts(
        self, receipts: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """
        Upsert honorarios receipts (insert or update based on company_id + folio).

        Args:
            receipts: List of honorarios receipts to upsert

        Returns:
            Tuple of (newly_created_count, updated_count)
        """
        if not receipts:
            return 0, 0

        try:
            # Get existing folios to count new vs updated
            company_id = receipts[0]["company_id"]
            folios = [receipt["folio"] for receipt in receipts if receipt.get("folio") is not None]

            existing_folios = set()
            if folios:
                response = (
                    self._client
                    .table("honorarios_receipts")
                    .select("folio")
                    .eq("company_id", company_id)
                    .in_("folio", folios)
                    .execute()
                )
                existing_folios = {receipt["folio"] for receipt in response.data}

            # Count new vs updated
            nuevos = sum(1 for receipt in receipts if receipt.get("folio") not in existing_folios)
            actualizados = len(receipts) - nuevos

            # Supabase upsert (inserts or updates based on unique constraint)
            response = (
                self._client
                .table("honorarios_receipts")
                .upsert(receipts, on_conflict="company_id,folio")
                .execute()
            )

            logger.info(
                f"✅ Upserted {len(receipts)} honorarios receipts: "
                f"{nuevos} nuevos, {actualizados} actualizados"
            )
            return nuevos, actualizados

        except Exception as e:
            self._log_error("upsert_honorarios_receipts", e, count=len(receipts))
            return 0, 0
