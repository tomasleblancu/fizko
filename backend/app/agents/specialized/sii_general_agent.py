"""SII General Agent - Expert in Chilean tax authority (SII) regulations."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal

from agents import Agent, RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from ...config.constants import MODEL, SII_GENERAL_INSTRUCTIONS
from ..context import FizkoContext

logger = logging.getLogger(__name__)


def create_sii_general_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the SII General Agent.

    This agent helps with:
    - General tax questions about Chilean SII
    - Tax filing deadlines
    - Tax regime explanations
    - Business tax obligations
    """

    @function_tool(strict_mode=False)
    async def get_tax_regime_info(
        ctx: RunContextWrapper[FizkoContext],
        regime: str,
    ) -> dict[str, Any]:
        """
        Get information about a specific Chilean tax regime.

        Args:
            regime: The tax regime (regimen_general, regimen_simplificado, pro_pyme, 14_ter)

        Returns:
            Information about the tax regime
        """
        regimes = {
            "regimen_general": {
                "name": "Régimen General (14 A)",
                "description": "Régimen tributario general para empresas. Tributa sobre renta efectiva.",
                "tax_rate": "27%",
                "ideal_for": "Empresas grandes y medianas con contabilidad completa",
                "requirements": [
                    "Contabilidad completa",
                    "Declaración mensual de IVA",
                    "Declaración anual de renta"
                ],
            },
            "regimen_simplificado": {
                "name": "Régimen Simplificado (14 B)",
                "description": "Régimen para pequeñas empresas basado en retiros efectivos.",
                "tax_rate": "Variable según retiros",
                "ideal_for": "Pequeñas empresas y profesionales independientes",
                "requirements": [
                    "Ingresos menores a 75.000 UF anuales",
                    "Contabilidad simplificada",
                    "Declaración mensual de IVA"
                ],
            },
            "pro_pyme": {
                "name": "Régimen Pro-Pyme",
                "description": "Régimen especial para micro, pequeñas y medianas empresas.",
                "tax_rate": "25% sobre renta efectiva",
                "ideal_for": "PYMEs con ingresos hasta 75.000 UF anuales",
                "requirements": [
                    "Ingresos menores a 75.000 UF anuales",
                    "Contabilidad simplificada o completa",
                    "Declaración mensual de IVA"
                ],
            },
            "14_ter": {
                "name": "Régimen 14 Ter",
                "description": "Régimen simplificado para micro y pequeñas empresas.",
                "tax_rate": "Variable según ingresos (0.25% a 1.75%)",
                "ideal_for": "Microempresas con ingresos hasta 50.000 UF anuales",
                "requirements": [
                    "Ingresos menores a 50.000 UF anuales",
                    "Contabilidad simplificada",
                    "Declaración mensual de IVA"
                ],
            },
        }

        regime_info = regimes.get(regime)
        if not regime_info:
            return {
                "error": f"Régimen '{regime}' no encontrado",
                "available_regimes": list(regimes.keys())
            }

        return regime_info

    @function_tool(strict_mode=False)
    async def get_tax_deadlines(
        ctx: RunContextWrapper[FizkoContext],
        month: int | None = None,
    ) -> dict[str, Any]:
        """
        Get tax filing deadlines for a specific month.

        Args:
            month: Month number (1-12). If None, returns current month deadlines.

        Returns:
            Tax deadlines for the specified month
        """
        import datetime

        if month is None:
            month = datetime.datetime.now().month

        if month < 1 or month > 12:
            return {"error": "El mes debe estar entre 1 y 12"}

        # Standard deadlines (these are typical, may vary)
        deadlines = {
            "iva_mensual": {
                "name": "Declaración Mensual de IVA (F29)",
                "deadline_day": 12,
                "description": "Declaración de IVA del mes anterior"
            },
            "ppm": {
                "name": "Pago Provisional Mensual (F29)",
                "deadline_day": 12,
                "description": "Pago a cuenta del impuesto a la renta"
            },
            "remuneraciones": {
                "name": "Retenciones de Segunda Categoría",
                "deadline_day": 12,
                "description": "Retención de impuesto a trabajadores dependientes"
            },
        }

        # Annual deadline (April for previous year)
        if month == 4:
            deadlines["renta_anual"] = {
                "name": "Declaración Anual de Renta (F22)",
                "deadline_day": 30,
                "description": "Declaración de impuesto a la renta del año anterior"
            }

        return {
            "month": month,
            "year": datetime.datetime.now().year,
            "deadlines": deadlines
        }

    @function_tool(strict_mode=False)
    async def calculate_iva(
        ctx: RunContextWrapper[FizkoContext],
        net_amount: float,
        include_iva: bool = False,
    ) -> dict[str, Any]:
        """
        Calculate IVA (Chilean VAT at 19%).

        Args:
            net_amount: The net amount (without IVA) or gross amount (with IVA)
            include_iva: If True, net_amount includes IVA and needs to be separated

        Returns:
            IVA calculation breakdown
        """
        IVA_RATE = Decimal("0.19")

        if include_iva:
            # Separate IVA from gross amount
            gross = Decimal(str(net_amount))
            net = gross / (Decimal("1") + IVA_RATE)
            iva = gross - net
        else:
            # Calculate IVA on net amount
            net = Decimal(str(net_amount))
            iva = net * IVA_RATE
            gross = net + iva

        return {
            "net_amount": float(net.quantize(Decimal("0.01"))),
            "iva_19": float(iva.quantize(Decimal("0.01"))),
            "gross_amount": float(gross.quantize(Decimal("0.01"))),
            "calculation_type": "with_iva" if include_iva else "add_iva"
        }

    @function_tool(strict_mode=False)
    async def get_company_info(
        ctx: RunContextWrapper[FizkoContext],
    ) -> dict[str, Any]:
        """
        Get information about the user's company/companies.

        Returns:
            List of companies registered for the user
        """
        from ...db.models import Company

        user_id = ctx.context.request_context.get("user_id")
        if not user_id:
            return {"error": "Usuario no autenticado"}

        try:
            stmt = select(Company).where(Company.user_id == UUID(user_id))
            result = await db.execute(stmt)
            companies = result.scalars().all()

            if not companies:
                return {"message": "No hay empresas registradas", "companies": []}

            return {
                "companies": [
                    {
                        "id": str(c.id),
                        "rut": c.rut,
                        "business_name": c.business_name,
                        "trade_name": c.trade_name,
                        "tax_regime": c.tax_regime,
                        "activity_code": c.sii_activity_code,
                    }
                    for c in companies
                ]
            }
        except Exception as e:
            logger.error(f"Error getting company info: {e}")
            return {"error": str(e)}

    agent = Agent(
        name="sii_general_agent",
        model=MODEL,
        instructions=SII_GENERAL_INSTRUCTIONS,
        tools=[
            get_tax_regime_info,
            get_tax_deadlines,
            calculate_iva,
            get_company_info,
        ],
    )

    return agent
