"""Tools for F29 Agent - Chilean Form 29 (monthly tax declaration) calculations."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal

from agents import RunContextWrapper, function_tool

from ...config.database import AsyncSessionLocal
from ...core import FizkoContext

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
async def calculate_f29_iva(
    ctx: RunContextWrapper[FizkoContext],
    debito_fiscal: float,
    credito_fiscal: float,
    remanente_anterior: float = 0,
) -> dict[str, Any]:
    """
    Calculate IVA (Value Added Tax) for Form 29.

    Args:
        debito_fiscal: IVA charged on sales
        credito_fiscal: IVA paid on purchases
        remanente_anterior: IVA credit balance from previous period

    Returns:
        IVA calculation breakdown for F29
    """
    debito = Decimal(str(debito_fiscal))
    credito = Decimal(str(credito_fiscal))
    remanente = Decimal(str(remanente_anterior))

    # Total credits available
    total_credito = credito + remanente

    # Calculate IVA to pay or credit
    if debito > total_credito:
        iva_a_pagar = debito - total_credito
        remanente_siguiente = Decimal("0")
    else:
        iva_a_pagar = Decimal("0")
        remanente_siguiente = total_credito - debito

    return {
        "debito_fiscal": float(debito.quantize(Decimal("0.01"))),
        "credito_fiscal": float(credito.quantize(Decimal("0.01"))),
        "remanente_anterior": float(remanente.quantize(Decimal("0.01"))),
        "total_credito": float(total_credito.quantize(Decimal("0.01"))),
        "iva_a_pagar": float(iva_a_pagar.quantize(Decimal("0.01"))),
        "remanente_siguiente": float(remanente_siguiente.quantize(Decimal("0.01"))),
        "explanation": (
            f"Débito Fiscal (IVA ventas): ${debito:,.0f}\n"
            f"Crédito Fiscal (IVA compras): ${credito:,.0f}\n"
            f"Remanente período anterior: ${remanente:,.0f}\n"
            f"Total créditos disponibles: ${total_credito:,.0f}\n"
            f"IVA a pagar: ${iva_a_pagar:,.0f}\n"
            f"Remanente para próximo período: ${remanente_siguiente:,.0f}"
        ),
    }


@function_tool(strict_mode=False)
async def calculate_ppm(
    ctx: RunContextWrapper[FizkoContext],
    ingresos_brutos: float,
    tasa_ppm: float = 1.0,
) -> dict[str, Any]:
    """
    Calculate PPM (Pago Provisional Mensual - Monthly Provisional Payment).

    Args:
        ingresos_brutos: Gross income for the month
        tasa_ppm: PPM rate percentage (default 1%)

    Returns:
        PPM calculation breakdown
    """
    ingresos = Decimal(str(ingresos_brutos))
    tasa = Decimal(str(tasa_ppm)) / Decimal("100")

    ppm = ingresos * tasa

    return {
        "ingresos_brutos": float(ingresos.quantize(Decimal("0.01"))),
        "tasa_ppm": float(tasa * Decimal("100")),
        "ppm_a_pagar": float(ppm.quantize(Decimal("0.01"))),
        "explanation": (
            f"Ingresos brutos del mes: ${ingresos:,.0f}\n"
            f"Tasa PPM: {tasa * 100}%\n"
            f"PPM a pagar: ${ppm:,.0f}\n\n"
            "El PPM es un anticipo del impuesto a la renta que se paga mensualmente."
        ),
    }


@function_tool(strict_mode=False)
async def explain_f29_completion(
    ctx: RunContextWrapper[FizkoContext],
) -> dict[str, Any]:
    """
    Explain how to complete Form 29 (monthly tax declaration).

    Returns:
        Step-by-step guide for completing F29
    """
    guide = {
        "title": "Guía para completar el Formulario 29",
        "sections": [
            {
                "section": "1. Información del Contribuyente",
                "steps": [
                    "Ingresar RUT de la empresa",
                    "Verificar razón social",
                    "Seleccionar período tributario (mes y año)",
                ],
            },
            {
                "section": "2. IVA (Impuesto al Valor Agregado)",
                "steps": [
                    "Línea 501: Débito Fiscal (IVA de ventas)",
                    "Línea 505: Crédito Fiscal (IVA de compras)",
                    "Línea 511: Remanente mes anterior",
                    "Línea 515: IVA a pagar (o remanente para próximo mes)",
                ],
            },
            {
                "section": "3. PPM (Pago Provisional Mensual)",
                "steps": [
                    "Línea 601: Ingresos brutos del mes",
                    "Línea 605: Tasa PPM (generalmente 1%)",
                    "Línea 610: PPM a pagar",
                ],
            },
            {
                "section": "4. Retenciones",
                "steps": [
                    "Línea 701: Retenciones de segunda categoría (trabajadores)",
                    "Línea 705: Otras retenciones",
                ],
            },
            {
                "section": "5. Resumen y Pago",
                "steps": [
                    "Línea 901: Total a pagar",
                    "Verificar todos los cálculos",
                    "Enviar declaración antes del día 12 del mes siguiente",
                    "Pagar en banco o en línea",
                ],
            },
        ],
        "important_notes": [
            "La declaración debe presentarse aunque no haya movimiento",
            "El plazo es hasta el día 12 del mes siguiente",
            "Se pueden hacer declaraciones rectificatorias si hay errores",
            "Mantener respaldo de facturas y documentos por 6 años",
        ],
    }

    return guide


@function_tool(strict_mode=False)
async def calculate_f29_summary(
    ctx: RunContextWrapper[FizkoContext],
    iva_a_pagar: float = 0,
    ppm_a_pagar: float = 0,
    retenciones: float = 0,
) -> dict[str, Any]:
    """
    Calculate total F29 payment summary.

    Args:
        iva_a_pagar: IVA to pay
        ppm_a_pagar: PPM to pay
        retenciones: Withholdings to pay

    Returns:
        Complete F29 payment summary
    """
    iva = Decimal(str(iva_a_pagar))
    ppm = Decimal(str(ppm_a_pagar))
    ret = Decimal(str(retenciones))

    total = iva + ppm + ret

    return {
        "components": {
            "iva": float(iva.quantize(Decimal("0.01"))),
            "ppm": float(ppm.quantize(Decimal("0.01"))),
            "retenciones": float(ret.quantize(Decimal("0.01"))),
        },
        "total_a_pagar": float(total.quantize(Decimal("0.01"))),
        "summary": (
            "RESUMEN FORMULARIO 29\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"IVA a pagar:           ${iva:>12,.0f}\n"
            f"PPM a pagar:           ${ppm:>12,.0f}\n"
            f"Retenciones:           ${ret:>12,.0f}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"TOTAL A PAGAR:         ${total:>12,.0f}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
        ),
    }
