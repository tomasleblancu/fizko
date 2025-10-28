"""Tools for Operación Renta Agent - Chilean annual tax declaration (Formulario 22)."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal

from agents import RunContextWrapper, function_tool

from ...core import FizkoContext

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
async def calculate_annual_income_tax(
    ctx: RunContextWrapper[FizkoContext],
    annual_income: float,
    tax_regime: str,
    ppm_paid: float = 0,
    ppua_paid: float = 0,
    other_credits: float = 0,
) -> dict[str, Any]:
    """
    Calculate annual income tax (Impuesto a la Renta) for a company.

    Args:
        annual_income: Total annual taxable income
        tax_regime: Tax regime (regimen_general, 14_ter, pro_pyme, regimen_simplificado)
        ppm_paid: Total PPM (Pagos Provisionales Mensuales) paid during the year
        ppua_paid: PPUA (Pago Provisional por Utilidades Absorbidas) if applicable
        other_credits: Other tax credits available

    Returns:
        Detailed calculation of annual income tax
    """
    try:
        income = Decimal(str(annual_income))
        ppm = Decimal(str(ppm_paid))
        ppua = Decimal(str(ppua_paid))
        credits = Decimal(str(other_credits))

        # Tax rates by regime
        tax_rates = {
            "regimen_general": Decimal("0.27"),  # 27% (14 A)
            "pro_pyme": Decimal("0.25"),  # 25%
            "14_ter": None,  # Variable rate
            "regimen_simplificado": None,  # Taxed on withdrawals
        }

        if tax_regime == "regimen_general":
            # Régimen General (14 A): 27% flat rate
            tax_rate = tax_rates["regimen_general"]
            gross_tax = income * tax_rate

            result = {
                "tax_regime": "Régimen General (14 A)",
                "annual_income": float(income.quantize(Decimal("0.01"))),
                "tax_rate": "27%",
                "gross_tax": float(gross_tax.quantize(Decimal("0.01"))),
                "credits": {
                    "ppm_paid": float(ppm.quantize(Decimal("0.01"))),
                    "ppua_paid": float(ppua.quantize(Decimal("0.01"))),
                    "other_credits": float(credits.quantize(Decimal("0.01"))),
                    "total_credits": float((ppm + ppua + credits).quantize(Decimal("0.01"))),
                },
                "net_tax": float((gross_tax - ppm - ppua - credits).quantize(Decimal("0.01"))),
            }

        elif tax_regime == "pro_pyme":
            # Pro-Pyme: 25% flat rate
            tax_rate = tax_rates["pro_pyme"]
            gross_tax = income * tax_rate

            result = {
                "tax_regime": "Régimen Pro-Pyme",
                "annual_income": float(income.quantize(Decimal("0.01"))),
                "tax_rate": "25%",
                "gross_tax": float(gross_tax.quantize(Decimal("0.01"))),
                "credits": {
                    "ppm_paid": float(ppm.quantize(Decimal("0.01"))),
                    "ppua_paid": float(ppua.quantize(Decimal("0.01"))),
                    "other_credits": float(credits.quantize(Decimal("0.01"))),
                    "total_credits": float((ppm + ppua + credits).quantize(Decimal("0.01"))),
                },
                "net_tax": float((gross_tax - ppm - ppua - credits).quantize(Decimal("0.01"))),
            }

        elif tax_regime == "14_ter":
            # 14 TER: Progressive rates (simplified example)
            # Actual rates are more complex and depend on UF values
            if income <= Decimal("5000000"):
                tax_rate = Decimal("0.0025")
            elif income <= Decimal("10000000"):
                tax_rate = Decimal("0.005")
            else:
                tax_rate = Decimal("0.0175")

            gross_tax = income * tax_rate

            result = {
                "tax_regime": "Régimen 14 TER",
                "annual_income": float(income.quantize(Decimal("0.01"))),
                "tax_rate": f"{float(tax_rate * 100):.2f}%",
                "note": "Tasa variable según tramo de ingresos",
                "gross_tax": float(gross_tax.quantize(Decimal("0.01"))),
                "credits": {
                    "ppm_paid": float(ppm.quantize(Decimal("0.01"))),
                    "other_credits": float(credits.quantize(Decimal("0.01"))),
                    "total_credits": float((ppm + credits).quantize(Decimal("0.01"))),
                },
                "net_tax": float((gross_tax - ppm - credits).quantize(Decimal("0.01"))),
            }

        elif tax_regime == "regimen_simplificado":
            result = {
                "tax_regime": "Régimen Simplificado (14 B)",
                "annual_income": float(income.quantize(Decimal("0.01"))),
                "note": "En este régimen se tributa sobre retiros efectivos, no sobre utilidades",
                "explanation": "El impuesto se calcula sobre los retiros que realicen los socios, no sobre las utilidades devengadas",
                "recommendation": "Debes declarar los retiros efectivos del año y aplicar la tabla de Global Complementario o Adicional",
            }

        else:
            return {
                "error": f"Régimen tributario no reconocido: '{tax_regime}'",
                "available_regimes": ["regimen_general", "pro_pyme", "14_ter", "regimen_simplificado"]
            }

        # Determine if owes or has refund
        net_tax_value = result.get("net_tax", 0)
        if net_tax_value > 0:
            result["status"] = "IMPUESTO A PAGAR"
            result["action"] = f"Debes pagar ${net_tax_value:,.0f} al SII"
        elif net_tax_value < 0:
            result["status"] = "DEVOLUCIÓN"
            result["action"] = f"Tienes derecho a devolución de ${abs(net_tax_value):,.0f}"
        else:
            result["status"] = "SIN PAGO NI DEVOLUCIÓN"
            result["action"] = "El impuesto anual está completamente cubierto por los PPM"

        return result

    except Exception as e:
        logger.error(f"Error calculating annual income tax: {e}")
        return {"error": str(e)}


@function_tool(strict_mode=False)
async def explain_operacion_renta(
    ctx: RunContextWrapper[FizkoContext],
    year: int | None = None,
) -> dict[str, Any]:
    """
    Explain the Operación Renta process (annual tax declaration).

    Args:
        year: Tax year (defaults to previous year)

    Returns:
        Comprehensive guide to Operación Renta
    """
    import datetime

    if year is None:
        year = datetime.datetime.now().year - 1

    return {
        "operacion_renta_guide": {
            "name": "Operación Renta",
            "year": year,
            "description": "Declaración anual de impuestos a la renta del año tributario anterior",
            "deadline": f"30 de abril de {year + 1}",
            "form": "Formulario 22 (F22) - online en www.sii.cl",
        },
        "who_must_file": [
            "Todas las empresas con actividades el año anterior",
            "Trabajadores independientes con ingresos superiores a 13.5 UF mensuales",
            "Personas con rentas del capital (arriendos, dividendos, etc.)",
            "Trabajadores dependientes con múltiples empleadores",
            "Personas que quieran solicitar devolución de impuestos",
        ],
        "key_concepts": {
            "renta_liquida_imponible": {
                "description": "Base imponible sobre la cual se calcula el impuesto",
                "formula": "Ingresos Brutos - Gastos Aceptados - Pérdidas del Ejercicio",
            },
            "impuesto_primera_categoria": {
                "description": "Impuesto que pagan las empresas sobre sus utilidades",
                "rates": {
                    "regimen_general": "27%",
                    "pro_pyme": "25%",
                    "14_ter": "Variable (0.25% - 1.75%)",
                },
            },
            "global_complementario": {
                "description": "Impuesto personal progresivo sobre retiros/dividendos",
                "applies_to": "Personas naturales (socios, accionistas)",
            },
            "ppm_credits": {
                "description": "Crédito por PPM pagados durante el año",
                "recoverable": "Se descuentan del impuesto anual",
            },
        },
        "process_steps": [
            {
                "step": 1,
                "name": "Cierre Contable",
                "description": "Cerrar libros contables al 31 de diciembre",
                "deadline": "Enero - Febrero",
            },
            {
                "step": 2,
                "name": "Calcular Renta Líquida Imponible",
                "description": "Determinar base imponible (ingresos - gastos)",
                "deadline": "Febrero - Marzo",
            },
            {
                "step": 3,
                "name": "Determinar Impuesto de Primera Categoría",
                "description": "Aplicar tasa según régimen tributario",
                "deadline": "Marzo",
            },
            {
                "step": 4,
                "name": "Rebajar Créditos (PPM, PPUA, otros)",
                "description": "Descontar pagos provisionales del año",
                "deadline": "Marzo",
            },
            {
                "step": 5,
                "name": "Presentar F22 en SII",
                "description": "Declarar online en www.sii.cl",
                "deadline": f"Hasta 30 de abril de {year + 1}",
            },
            {
                "step": 6,
                "name": "Pagar o Solicitar Devolución",
                "description": "Pagar impuesto adeudado o recibir devolución",
                "deadline": f"Mayo de {year + 1}",
            },
        ],
        "required_documents": [
            "Balance General al 31 de diciembre",
            "Estado de Resultados del año",
            "Libro Diario y Mayor",
            "Comprobantes de PPM pagados (F29 mensuales)",
            "Certificados de retenciones",
            "Facturas de compra y venta",
            "Contratos de arriendo, créditos, etc.",
        ],
        "common_deductions": [
            "Gastos operacionales necesarios para producir renta",
            "Depreciación de activos fijos",
            "Pérdidas de ejercicios anteriores",
            "Intereses de préstamos para la actividad",
            "Gastos de personal (sueldos, cotizaciones)",
        ],
        "important_tips": [
            "Mantén tu contabilidad al día durante todo el año",
            "Guarda todos los respaldos de gastos (facturas, boletas)",
            "Revisa que todos los F29 mensuales estén presentados",
            "Verifica que los montos de PPM coincidan con tus registros",
            "Si tienes dudas, consulta con un contador antes del 30 de abril",
            "El SII ofrece una propuesta pre-llenada, revísala cuidadosamente",
        ],
    }


@function_tool(strict_mode=False)
async def calculate_global_complementario(
    ctx: RunContextWrapper[FizkoContext],
    annual_withdrawals: float,
    previous_tax_paid: float = 0,
) -> dict[str, Any]:
    """
    Calculate Global Complementario tax (personal income tax on withdrawals/dividends).

    Args:
        annual_withdrawals: Total withdrawals/dividends received during the year
        previous_tax_paid: Tax already paid (Primera Categoría credit)

    Returns:
        Global Complementario calculation with tax brackets
    """
    try:
        withdrawals = Decimal(str(annual_withdrawals))
        credit = Decimal(str(previous_tax_paid))

        # Global Complementario tax brackets (2024 - simplified)
        # Actual brackets are in UTA (Unidad Tributaria Anual)
        brackets = [
            {"from": Decimal("0"), "to": Decimal("8036832"), "rate": Decimal("0"), "base": Decimal("0")},
            {"from": Decimal("8036832"), "to": Decimal("17859516"), "rate": Decimal("0.04"), "base": Decimal("0")},
            {"from": Decimal("17859516"), "to": Decimal("29766024"), "rate": Decimal("0.08"), "base": Decimal("392907")},
            {"from": Decimal("29766024"), "to": Decimal("41672532"), "rate": Decimal("0.135"), "base": Decimal("1345428")},
            {"from": Decimal("41672532"), "to": Decimal("53579040"), "rate": Decimal("0.23"), "base": Decimal("2954906")},
            {"from": Decimal("53579040"), "to": Decimal("71438724"), "rate": Decimal("0.304"), "base": Decimal("5693403")},
            {"from": Decimal("71438724"), "to": None, "rate": Decimal("0.35"), "base": Decimal("11121018")},
        ]

        # Find applicable bracket and calculate tax
        gross_tax = Decimal("0")
        bracket_info = None

        for bracket in brackets:
            if bracket["to"] is None or withdrawals <= bracket["to"]:
                excess = withdrawals - bracket["from"]
                gross_tax = bracket["base"] + (excess * bracket["rate"])
                bracket_info = {
                    "from": float(bracket["from"]),
                    "to": float(bracket["to"]) if bracket["to"] else "Sin límite",
                    "rate": float(bracket["rate"] * 100),
                    "base_tax": float(bracket["base"]),
                }
                break

        net_tax = gross_tax - credit

        return {
            "annual_withdrawals": float(withdrawals.quantize(Decimal("0.01"))),
            "applicable_bracket": bracket_info,
            "gross_tax": float(gross_tax.quantize(Decimal("0.01"))),
            "tax_credit": float(credit.quantize(Decimal("0.01"))),
            "net_tax": float(net_tax.quantize(Decimal("0.01"))),
            "status": "IMPUESTO A PAGAR" if net_tax > 0 else "DEVOLUCIÓN" if net_tax < 0 else "SIN PAGO",
            "note": "Los tramos de Global Complementario se ajustan anualmente según UTA",
        }

    except Exception as e:
        logger.error(f"Error calculating Global Complementario: {e}")
        return {"error": str(e)}
