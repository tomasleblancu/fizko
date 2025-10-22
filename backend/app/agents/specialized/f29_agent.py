"""F29 Agent - Expert in Chilean Form 29 (monthly tax declaration)."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal
from datetime import date, datetime

from agents import Agent, RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID

from ...config.constants import MODEL, F29_INSTRUCTIONS
from ..context import FizkoContext

logger = logging.getLogger(__name__)


def create_f29_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the F29 Agent.

    This agent helps with:
    - Understanding Form 29 (monthly tax declaration)
    - Calculating IVA (debito fiscal - credito fiscal)
    - Calculating PPM (provisional monthly payment)
    - Explaining employee tax withholdings
    - Step-by-step F29 completion guide
    """

    @function_tool(strict_mode=False)
    async def calculate_f29_iva(
        ctx: RunContextWrapper[FizkoContext],
        company_id: str,
        month: int,
        year: int,
    ) -> dict[str, Any]:
        """
        Calculate IVA (Value Added Tax) for Form 29 based on company documents.

        Args:
            company_id: Company UUID
            month: Month (1-12)
            year: Year

        Returns:
            IVA calculation breakdown (debito fiscal, credito fiscal, IVA to pay)
        """
        from ...db.models import PurchaseDocument, SalesDocument

        user_id = ctx.context.request_context.get("user_id")
        if not user_id:
            return {"error": "Usuario no autenticado"}

        try:
            # Date range for the month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)

            # Get sales documents (Debito Fiscal)
            sales_stmt = select(SalesDocument).where(
                and_(
                    SalesDocument.company_id == UUID(company_id),
                    SalesDocument.issue_date >= start_date,
                    SalesDocument.issue_date < end_date,
                )
            )
            sales_result = await db.execute(sales_stmt)
            sales_docs = sales_result.scalars().all()

            # Get purchase documents (Credito Fiscal)
            purchase_stmt = select(PurchaseDocument).where(
                and_(
                    PurchaseDocument.company_id == UUID(company_id),
                    PurchaseDocument.issue_date >= start_date,
                    PurchaseDocument.issue_date < end_date,
                )
            )
            purchase_result = await db.execute(purchase_stmt)
            purchase_docs = purchase_result.scalars().all()

            # Calculate debito fiscal (IVA charged on sales)
            debito_fiscal = sum(float(doc.tax_amount) for doc in sales_docs)

            # Calculate credito fiscal (IVA paid on purchases)
            credito_fiscal = sum(float(doc.tax_amount) for doc in purchase_docs)

            # Calculate IVA to pay (or refund)
            iva_determinado = debito_fiscal - credito_fiscal

            return {
                "period": f"{year}-{month:02d}",
                "libro_ventas": {
                    "total_documents": len(sales_docs),
                    "total_net": float(sum(doc.net_amount for doc in sales_docs)),
                    "debito_fiscal_iva": debito_fiscal,
                },
                "libro_compras": {
                    "total_documents": len(purchase_docs),
                    "total_net": float(sum(doc.net_amount for doc in purchase_docs)),
                    "credito_fiscal_iva": credito_fiscal,
                },
                "iva_calculation": {
                    "debito_fiscal": debito_fiscal,
                    "credito_fiscal": credito_fiscal,
                    "iva_determinado": iva_determinado,
                    "status": "A PAGAR" if iva_determinado > 0 else "SALDO A FAVOR",
                },
                "f29_line": "Línea 30 del F29: IVA Determinado",
                "deadline": f"{year}-{month + 1 if month < 12 else 1:02d}-12 (día 12 del mes siguiente)",
            }

        except Exception as e:
            logger.error(f"Error calculating F29 IVA: {e}")
            return {"error": str(e)}

    @function_tool(strict_mode=False)
    async def calculate_ppm(
        ctx: RunContextWrapper[FizkoContext],
        gross_income: float,
        tax_regime: str,
    ) -> dict[str, Any]:
        """
        Calculate PPM (Pago Provisional Mensual) for Form 29.

        Args:
            gross_income: Gross monthly income
            tax_regime: Tax regime ("regimen_general", "14_ter", "pro_pyme")

        Returns:
            PPM calculation based on tax regime
        """
        try:
            income = Decimal(str(gross_income))
            ppm_rate = Decimal("0")
            explanation = ""

            if tax_regime == "regimen_general":
                # Régimen General (14 A): 0.25% sobre ingresos brutos
                ppm_rate = Decimal("0.0025")
                explanation = "Régimen General (14 A): 0.25% sobre ingresos brutos"

            elif tax_regime == "14_ter":
                # 14 TER: Tasa variable según tramo de ingresos
                if income <= 5000000:  # Ejemplo simplificado
                    ppm_rate = Decimal("0.0025")
                    explanation = "14 TER: 0.25% (tramo bajo)"
                else:
                    ppm_rate = Decimal("0.01")
                    explanation = "14 TER: 1% (tramo alto)"

            elif tax_regime == "pro_pyme":
                # Pro-Pyme: Similar a 14 TER
                ppm_rate = Decimal("0.0025")
                explanation = "Pro-Pyme: 0.25% sobre ingresos brutos"

            else:
                return {
                    "error": f"Régimen tributario no reconocido: '{tax_regime}'",
                    "available_regimes": ["regimen_general", "14_ter", "pro_pyme"]
                }

            ppm_amount = income * ppm_rate

            return {
                "gross_income": float(income.quantize(Decimal("0.01"))),
                "tax_regime": tax_regime,
                "ppm_rate": float(ppm_rate * Decimal("100")),  # As percentage
                "ppm_amount": float(ppm_amount.quantize(Decimal("0.01"))),
                "explanation": explanation,
                "f29_line": "Línea 75 del F29: PPM",
                "note": "El PPM es un pago a cuenta del Impuesto a la Renta anual",
            }

        except Exception as e:
            logger.error(f"Error calculating PPM: {e}")
            return {"error": str(e)}

    @function_tool(strict_mode=False)
    async def explain_f29_completion(
        ctx: RunContextWrapper[FizkoContext],
    ) -> dict[str, Any]:
        """
        Provide step-by-step guide to completing Form 29.

        Returns:
            Detailed F29 completion guide
        """
        return {
            "form_29_guide": {
                "name": "Formulario 29 - Declaración Mensual y Pago Simultáneo de Impuestos",
                "frequency": "Mensual",
                "deadline": "Día 12 del mes siguiente",
                "filing_method": "Online en www.sii.cl",
            },
            "main_sections": {
                "section_1_iva": {
                    "name": "IVA (Impuesto al Valor Agregado)",
                    "steps": [
                        {
                            "line": "Código 10-15",
                            "description": "Ventas y Servicios (Debito Fiscal)",
                            "source": "Libro de Ventas del mes"
                        },
                        {
                            "line": "Código 20-25",
                            "description": "Compras (Credito Fiscal)",
                            "source": "Libro de Compras del mes"
                        },
                        {
                            "line": "Código 30",
                            "description": "IVA Determinado (Debito - Credito)",
                            "calculation": "Línea 15 - Línea 25"
                        },
                    ]
                },
                "section_2_ppm": {
                    "name": "PPM (Pago Provisional Mensual)",
                    "steps": [
                        {
                            "line": "Código 75",
                            "description": "Pago Provisional por Utilidades Absorbidas (PPM)",
                            "calculation": "Depende del régimen tributario (generalmente 0.25% a 1% de ingresos brutos)"
                        },
                    ]
                },
                "section_3_retenciones": {
                    "name": "Retenciones de Segunda Categoría",
                    "steps": [
                        {
                            "line": "Código 155",
                            "description": "Retenciones a trabajadores dependientes",
                            "source": "Suma de retenciones en liquidaciones de sueldo"
                        },
                    ]
                },
                "section_4_total": {
                    "name": "Total a Pagar",
                    "calculation": "IVA Determinado + PPM + Retenciones - Remanentes anteriores",
                }
            },
            "important_tips": [
                "Verifica que todos los documentos del mes estén incluidos",
                "Revisa que los montos coincidan con tus libros auxiliares",
                "Guarda el comprobante de pago como respaldo",
                "Si tienes saldo a favor de IVA, puedes arrastrarlo al mes siguiente",
                "Pagar fuera de plazo genera multas e intereses",
            ],
            "common_errors": [
                "No incluir todas las facturas del mes",
                "Errores de digitación en montos",
                "No considerar notas de crédito/débito",
                "Usar crédito fiscal de periodos anteriores sin derecho",
            ],
            "payment_methods": [
                "Pago online en sitio del SII (con tarjeta o PAT)",
                "Convenio PAC (Pago Automático de Cotizaciones)",
                "Pago en bancos autorizados",
            ]
        }

    @function_tool(strict_mode=False)
    async def calculate_f29_summary(
        ctx: RunContextWrapper[FizkoContext],
        debito_fiscal: float,
        credito_fiscal: float,
        ppm: float,
        retenciones: float = 0,
        remanente_anterior: float = 0,
    ) -> dict[str, Any]:
        """
        Calculate total F29 payment summary.

        Args:
            debito_fiscal: IVA charged on sales
            credito_fiscal: IVA paid on purchases
            ppm: Provisional monthly payment
            retenciones: Employee tax withholdings
            remanente_anterior: Previous month's credit balance

        Returns:
            Complete F29 payment summary
        """
        try:
            debito = Decimal(str(debito_fiscal))
            credito = Decimal(str(credito_fiscal))
            ppm_amount = Decimal(str(ppm))
            ret = Decimal(str(retenciones))
            remanente = Decimal(str(remanente_anterior))

            # Calculate IVA
            iva_determinado = debito - credito

            # If IVA is negative (credit balance), it can offset other taxes
            iva_to_pay = max(iva_determinado, Decimal("0"))
            iva_credit = abs(min(iva_determinado, Decimal("0")))

            # Total before credits
            subtotal = iva_to_pay + ppm_amount + ret

            # Apply previous credit balance
            total_to_pay = max(subtotal - remanente - iva_credit, Decimal("0"))
            new_credit_balance = max(remanente + iva_credit - subtotal, Decimal("0"))

            return {
                "iva_section": {
                    "debito_fiscal": float(debito.quantize(Decimal("0.01"))),
                    "credito_fiscal": float(credito.quantize(Decimal("0.01"))),
                    "iva_determinado": float(iva_determinado.quantize(Decimal("0.01"))),
                    "iva_to_pay": float(iva_to_pay.quantize(Decimal("0.01"))),
                    "iva_credit": float(iva_credit.quantize(Decimal("0.01"))),
                },
                "other_taxes": {
                    "ppm": float(ppm_amount.quantize(Decimal("0.01"))),
                    "retenciones": float(ret.quantize(Decimal("0.01"))),
                },
                "credits": {
                    "remanente_anterior": float(remanente.quantize(Decimal("0.01"))),
                },
                "summary": {
                    "subtotal_before_credits": float(subtotal.quantize(Decimal("0.01"))),
                    "total_to_pay": float(total_to_pay.quantize(Decimal("0.01"))),
                    "new_credit_balance": float(new_credit_balance.quantize(Decimal("0.01"))),
                },
                "payment_deadline": "Día 12 del mes siguiente",
                "note": "Revisa que todos los montos estén correctos antes de presentar el F29"
            }

        except Exception as e:
            logger.error(f"Error calculating F29 summary: {e}")
            return {"error": str(e)}

    agent = Agent(
        name="f29_agent",
        model=MODEL,
        instructions=F29_INSTRUCTIONS,
        tools=[
            calculate_f29_iva,
            calculate_ppm,
            explain_f29_completion,
            calculate_f29_summary,
        ],
    )

    return agent
