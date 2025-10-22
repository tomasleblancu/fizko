"""Importaciones Agent - Expert in Chilean imports and DIN (Declaración de Ingreso)."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal

from agents import Agent, RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.constants import MODEL, IMPORTACIONES_INSTRUCTIONS
from ..context import FizkoContext

logger = logging.getLogger(__name__)


def create_importaciones_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Importaciones Agent.

    This agent helps with:
    - Understanding the import process in Chile
    - Explaining DIN (Declaración de Ingreso) documents
    - Calculating total import costs (FOB, freight, insurance, duties, VAT)
    - Explaining accounting treatment of imports
    - Interpreting attached DIN documents (PDF)
    """

    @function_tool(strict_mode=False)
    async def calculate_import_cost(
        ctx: RunContextWrapper[FizkoContext],
        fob_value: float,
        freight: float,
        insurance: float,
        duty_rate: float,
        other_expenses: float = 0,
    ) -> dict[str, Any]:
        """
        Calculate total cost of an import including all duties and taxes.

        Args:
            fob_value: FOB (Free On Board) value in USD or CLP
            freight: International freight cost
            insurance: Insurance cost
            duty_rate: Customs duty rate as percentage (e.g., 6 for 6%)
            other_expenses: Other expenses (customs clearance, storage, local transport)

        Returns:
            Detailed breakdown of import costs
        """
        try:
            # Calculate CIF (Cost, Insurance, Freight)
            cif_value = Decimal(str(fob_value)) + Decimal(str(freight)) + Decimal(str(insurance))

            # Calculate customs duty
            duty = cif_value * (Decimal(str(duty_rate)) / Decimal("100"))

            # Calculate taxable base for IVA (CIF + Duty)
            taxable_base = cif_value + duty

            # Calculate IVA (19%)
            iva = taxable_base * Decimal("0.19")

            # Total import cost
            total_cost = cif_value + duty + iva + Decimal(str(other_expenses))

            return {
                "breakdown": {
                    "fob": float(Decimal(str(fob_value)).quantize(Decimal("0.01"))),
                    "freight": float(Decimal(str(freight)).quantize(Decimal("0.01"))),
                    "insurance": float(Decimal(str(insurance)).quantize(Decimal("0.01"))),
                    "cif": float(cif_value.quantize(Decimal("0.01"))),
                    "customs_duty": float(duty.quantize(Decimal("0.01"))),
                    "duty_rate_percent": duty_rate,
                    "taxable_base_for_iva": float(taxable_base.quantize(Decimal("0.01"))),
                    "iva_19": float(iva.quantize(Decimal("0.01"))),
                    "other_expenses": float(Decimal(str(other_expenses)).quantize(Decimal("0.01"))),
                },
                "totals": {
                    "total_duties_and_taxes": float((duty + iva).quantize(Decimal("0.01"))),
                    "total_import_cost": float(total_cost.quantize(Decimal("0.01"))),
                },
                "accounting_note": "El IVA de importación es un crédito fiscal recuperable en el F29"
            }

        except Exception as e:
            logger.error(f"Error calculating import cost: {e}")
            return {"error": str(e)}

    @function_tool(strict_mode=False)
    async def explain_din_process(
        ctx: RunContextWrapper[FizkoContext],
    ) -> dict[str, Any]:
        """
        Explain the DIN (Declaración de Ingreso) process and its components.

        Returns:
            Detailed explanation of the DIN process
        """
        return {
            "din_overview": {
                "name": "Declaración de Ingreso (DIN)",
                "purpose": "Documento emitido por Aduanas que certifica el ingreso legal de mercadería importada a Chile",
                "issuer": "Servicio Nacional de Aduanas",
            },
            "process_steps": [
                {
                    "step": 1,
                    "name": "Embarque",
                    "description": "Compra internacional y embarque de mercadería"
                },
                {
                    "step": 2,
                    "name": "Llegada a Chile",
                    "description": "Mercadería llega a puerto/aeropuerto chileno"
                },
                {
                    "step": 3,
                    "name": "Declaración Aduanera",
                    "description": "Agente de aduanas presenta documentación y declara la mercadería"
                },
                {
                    "step": 4,
                    "name": "Pago de Derechos",
                    "description": "Pago de aranceles e IVA de importación"
                },
                {
                    "step": 5,
                    "name": "Emisión DIN",
                    "description": "Aduanas emite la DIN certificando el ingreso"
                },
                {
                    "step": 6,
                    "name": "Retiro de Mercadería",
                    "description": "Se autoriza el retiro físico de la mercadería"
                },
            ],
            "din_components": {
                "datos_importador": "RUT y nombre del importador",
                "datos_mercaderia": "Descripción, cantidad, valor FOB",
                "valores_cif": "FOB + Flete + Seguro",
                "arancel": "Tasa arancelaria aplicada y monto",
                "iva_importacion": "19% sobre (CIF + Arancel)",
                "total_pagado": "Suma de todos los tributos",
            },
            "accounting_treatment": {
                "asset_activation": "El costo total de importación se activa como inventario o activo fijo",
                "iva_credit": "El IVA de importación es crédito fiscal recuperable en el F29",
                "purchase_book": "Se registra en el Libro de Compras como factura de importación",
            },
            "fizko_integration": {
                "status": "PENDIENTE - En desarrollo",
                "future_feature": "Próximamente Fizko podrá procesar DIN automáticamente",
                "current_capability": "Por ahora, puedo ayudarte a interpretar una DIN adjunta y explicar sus componentes",
            }
        }

    @function_tool(strict_mode=False)
    async def calculate_iva_credit_import(
        ctx: RunContextWrapper[FizkoContext],
        iva_import_amount: float,
    ) -> dict[str, Any]:
        """
        Explain how to recover IVA paid on imports as tax credit.

        Args:
            iva_import_amount: Amount of IVA paid on import

        Returns:
            Explanation of IVA credit recovery
        """
        try:
            iva = Decimal(str(iva_import_amount))

            return {
                "iva_import": float(iva.quantize(Decimal("0.01"))),
                "treatment": {
                    "tipo_credito": "Crédito Fiscal IVA",
                    "formulario": "Formulario 29 (F29)",
                    "cuando_recuperar": "En el mes en que se paga el IVA de importación",
                    "registro": "Se incluye en el Libro de Compras",
                },
                "example": {
                    "description": f"Si pagas ${float(iva.quantize(Decimal('0.01')))} de IVA en una importación",
                    "book_entry": "Se registra como crédito fiscal en Libro de Compras",
                    "f29_effect": "Se resta del IVA débito fiscal en el F29",
                    "result": "Reduces el IVA a pagar al SII ese mes (o aumentas saldo a favor)",
                },
                "requirements": {
                    "document": "DIN original con timbre de Aduanas",
                    "payment_proof": "Comprobante de pago del IVA de importación",
                    "timing": "Debe registrarse en el periodo en que se pagó",
                },
                "important_note": "El crédito fiscal solo aplica si la empresa está afecta a IVA"
            }

        except Exception as e:
            logger.error(f"Error calculating IVA credit: {e}")
            return {"error": str(e)}

    # TODO: Add function to process DIN attachments when implemented
    # @function_tool(strict_mode=False)
    # async def process_din_attachment(
    #     ctx: RunContextWrapper[FizkoContext],
    #     attachment_id: str,
    # ) -> dict[str, Any]:
    #     """
    #     Process an attached DIN document (PDF) and extract key information.
    #
    #     CURRENTLY NOT IMPLEMENTED - Placeholder for future functionality.
    #     """
    #     return {
    #         "status": "NOT_IMPLEMENTED",
    #         "message": "La funcionalidad de procesamiento automático de DIN está en desarrollo",
    #         "alternative": "Por favor describe el contenido de la DIN y te ayudaré a interpretarla",
    #     }

    agent = Agent(
        name="importaciones_agent",
        model=MODEL,
        instructions=IMPORTACIONES_INSTRUCTIONS,
        tools=[
            calculate_import_cost,
            explain_din_process,
            calculate_iva_credit_import,
        ],
    )

    return agent
