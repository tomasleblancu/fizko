"""Contabilidad Agent - Expert in Chilean accounting principles (PCGA)."""

from __future__ import annotations

import logging
from typing import Any
from decimal import Decimal

from agents import Agent, RunContextWrapper, function_tool
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.constants import MODEL, CONTABILIDAD_INSTRUCTIONS
from ..context import FizkoContext

logger = logging.getLogger(__name__)


def create_contabilidad_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Contabilidad Agent.

    This agent helps with:
    - Understanding Chilean accounting principles (PCGA)
    - Explaining balance sheet, income statement, cash flow
    - Chart of accounts and accounting cycle
    - Double-entry bookkeeping
    - Financial analysis and ratios
    """

    @function_tool(strict_mode=False)
    async def explain_accounting_cycle(
        ctx: RunContextWrapper[FizkoContext],
    ) -> dict[str, Any]:
        """
        Explain the complete accounting cycle used in Chilean accounting.

        Returns:
            Detailed explanation of the accounting cycle steps
        """
        return {
            "accounting_cycle": {
                "description": "Proceso sistemático de registro y cierre contable",
                "frequency": "Se repite cada periodo contable (mensual, trimestral, anual)",
            },
            "steps": [
                {
                    "step": 1,
                    "name": "Identificación de Transacciones",
                    "description": "Identificar eventos económicos que afectan la empresa",
                    "examples": ["Venta de productos", "Compra de insumos", "Pago de sueldos"]
                },
                {
                    "step": 2,
                    "name": "Registro en Libro Diario",
                    "description": "Registrar transacciones en orden cronológico con partida doble",
                    "principle": "Cada transacción afecta al menos dos cuentas (Debe = Haber)"
                },
                {
                    "step": 3,
                    "name": "Traspaso a Libro Mayor",
                    "description": "Trasladar asientos del diario a cada cuenta del mayor",
                    "result": "Saldo actualizado de cada cuenta contable"
                },
                {
                    "step": 4,
                    "name": "Balance de Comprobación",
                    "description": "Verificar que la suma de débitos = suma de créditos",
                    "purpose": "Detectar errores aritméticos"
                },
                {
                    "step": 5,
                    "name": "Ajustes Contables",
                    "description": "Registrar ajustes de periodo (depreciación, provisiones, devengo)",
                    "examples": ["Depreciación mensual", "Provisión incobrables", "Gastos devengados"]
                },
                {
                    "step": 6,
                    "name": "Balance de Comprobación Ajustado",
                    "description": "Balance actualizado después de ajustes"
                },
                {
                    "step": 7,
                    "name": "Estados Financieros",
                    "description": "Preparar estados financieros finales",
                    "statements": [
                        "Balance General (Estado de Situación Financiera)",
                        "Estado de Resultados (Estado de Pérdidas y Ganancias)",
                        "Estado de Flujo de Efectivo",
                        "Estado de Cambios en el Patrimonio"
                    ]
                },
                {
                    "step": 8,
                    "name": "Asientos de Cierre",
                    "description": "Cerrar cuentas de resultado contra patrimonio",
                    "purpose": "Preparar para el siguiente periodo"
                },
            ],
            "principles": {
                "partida_doble": "Toda transacción afecta al menos dos cuentas (Debe = Haber)",
                "devengado": "Registrar ingresos cuando se ganan y gastos cuando se incurren",
                "entidad": "La empresa es independiente de sus dueños",
                "going_concern": "La empresa continuará operando indefinidamente",
            }
        }

    @function_tool(strict_mode=False)
    async def explain_financial_statements(
        ctx: RunContextWrapper[FizkoContext],
        statement_type: str,
    ) -> dict[str, Any]:
        """
        Explain a specific financial statement and its components.

        Args:
            statement_type: Type of statement ("balance", "income", "cash_flow", "equity")

        Returns:
            Detailed explanation of the requested financial statement
        """
        statements = {
            "balance": {
                "name": "Balance General (Estado de Situación Financiera)",
                "formula": "Activos = Pasivos + Patrimonio",
                "purpose": "Muestra la situación financiera de la empresa en un momento específico",
                "components": {
                    "activos": {
                        "corrientes": ["Caja y bancos", "Cuentas por cobrar", "Inventarios", "Gastos anticipados"],
                        "no_corrientes": ["Propiedad, planta y equipo", "Inversiones", "Intangibles", "Activos diferidos"]
                    },
                    "pasivos": {
                        "corrientes": ["Cuentas por pagar", "Impuestos por pagar", "Sueldos por pagar", "Préstamos CP"],
                        "no_corrientes": ["Préstamos LP", "Provisiones LP"]
                    },
                    "patrimonio": ["Capital", "Reservas", "Utilidades retenidas", "Resultado del ejercicio"]
                },
                "key_ratios": {
                    "liquidez_corriente": "Activo Corriente / Pasivo Corriente",
                    "razon_acida": "(Activo Corriente - Inventarios) / Pasivo Corriente",
                    "endeudamiento": "Pasivo Total / Activo Total",
                }
            },
            "income": {
                "name": "Estado de Resultados (Pérdidas y Ganancias)",
                "formula": "Utilidad Neta = Ingresos - Gastos",
                "purpose": "Muestra la rentabilidad de la empresa durante un periodo",
                "structure": [
                    "Ingresos Operacionales",
                    "- Costo de Ventas",
                    "= Margen Bruto",
                    "- Gastos de Administración y Ventas",
                    "= Resultado Operacional (EBIT)",
                    "+ Ingresos No Operacionales",
                    "- Gastos No Operacionales",
                    "= Resultado antes de Impuestos",
                    "- Impuesto a la Renta",
                    "= Utilidad Neta"
                ],
                "key_ratios": {
                    "margen_bruto": "(Margen Bruto / Ingresos) * 100",
                    "margen_operacional": "(EBIT / Ingresos) * 100",
                    "margen_neto": "(Utilidad Neta / Ingresos) * 100",
                }
            },
            "cash_flow": {
                "name": "Estado de Flujo de Efectivo",
                "purpose": "Muestra entradas y salidas de efectivo durante un periodo",
                "sections": {
                    "operacionales": {
                        "description": "Flujos relacionados con la operación del negocio",
                        "examples": ["Cobros a clientes", "Pagos a proveedores", "Pago de sueldos", "Pago de impuestos"]
                    },
                    "inversion": {
                        "description": "Flujos relacionados con activos de largo plazo",
                        "examples": ["Compra de equipos", "Venta de activos fijos", "Inversiones financieras"]
                    },
                    "financiamiento": {
                        "description": "Flujos relacionados con deuda y patrimonio",
                        "examples": ["Préstamos recibidos", "Pago de préstamos", "Aportes de capital", "Dividendos pagados"]
                    }
                },
                "importance": "Clave para analizar la liquidez real de la empresa"
            },
            "equity": {
                "name": "Estado de Cambios en el Patrimonio",
                "purpose": "Muestra los cambios en el patrimonio durante el periodo",
                "components": ["Capital inicial", "Aportes de socios", "Retiros", "Utilidad o pérdida del ejercicio", "Capital final"],
            }
        }

        statement = statements.get(statement_type)
        if not statement:
            return {
                "error": f"Tipo de estado financiero no reconocido: '{statement_type}'",
                "available_types": list(statements.keys())
            }

        return statement

    @function_tool(strict_mode=False)
    async def calculate_financial_ratios(
        ctx: RunContextWrapper[FizkoContext],
        activo_corriente: float,
        pasivo_corriente: float,
        activo_total: float,
        pasivo_total: float,
        patrimonio: float,
        ingresos: float,
        utilidad_neta: float,
        inventarios: float = 0,
    ) -> dict[str, Any]:
        """
        Calculate key financial ratios for analysis.

        Args:
            activo_corriente: Current assets
            pasivo_corriente: Current liabilities
            activo_total: Total assets
            pasivo_total: Total liabilities
            patrimonio: Equity
            ingresos: Revenue
            utilidad_neta: Net income
            inventarios: Inventories (optional)

        Returns:
            Dictionary with calculated financial ratios and their interpretation
        """
        try:
            ratios = {}

            # Liquidity ratios
            if pasivo_corriente > 0:
                liquidez_corriente = Decimal(str(activo_corriente)) / Decimal(str(pasivo_corriente))
                ratios["liquidez_corriente"] = {
                    "value": float(liquidez_corriente.quantize(Decimal("0.01"))),
                    "interpretation": "Ideal > 1.0. Indica capacidad de pagar deudas de corto plazo"
                }

                razon_acida = (Decimal(str(activo_corriente)) - Decimal(str(inventarios))) / Decimal(str(pasivo_corriente))
                ratios["razon_acida"] = {
                    "value": float(razon_acida.quantize(Decimal("0.01"))),
                    "interpretation": "Ideal > 1.0. Liquidez sin contar inventarios"
                }

            # Solvency ratios
            if activo_total > 0:
                endeudamiento = (Decimal(str(pasivo_total)) / Decimal(str(activo_total))) * Decimal("100")
                ratios["endeudamiento"] = {
                    "value": float(endeudamiento.quantize(Decimal("0.01"))),
                    "unit": "%",
                    "interpretation": "Ideal < 60%. Porcentaje de activos financiados con deuda"
                }

            if patrimonio > 0:
                apalancamiento = Decimal(str(pasivo_total)) / Decimal(str(patrimonio))
                ratios["apalancamiento"] = {
                    "value": float(apalancamiento.quantize(Decimal("0.01"))),
                    "interpretation": "Cuántas veces la deuda supera el patrimonio"
                }

            # Profitability ratios
            if ingresos > 0:
                margen_neto = (Decimal(str(utilidad_neta)) / Decimal(str(ingresos))) * Decimal("100")
                ratios["margen_neto"] = {
                    "value": float(margen_neto.quantize(Decimal("0.01"))),
                    "unit": "%",
                    "interpretation": "Porcentaje de utilidad sobre ventas"
                }

            if patrimonio > 0:
                roe = (Decimal(str(utilidad_neta)) / Decimal(str(patrimonio))) * Decimal("100")
                ratios["roe_return_on_equity"] = {
                    "value": float(roe.quantize(Decimal("0.01"))),
                    "unit": "%",
                    "interpretation": "Rentabilidad del patrimonio"
                }

            if activo_total > 0:
                roa = (Decimal(str(utilidad_neta)) / Decimal(str(activo_total))) * Decimal("100")
                ratios["roa_return_on_assets"] = {
                    "value": float(roa.quantize(Decimal("0.01"))),
                    "unit": "%",
                    "interpretation": "Rentabilidad de los activos"
                }

            return {
                "ratios": ratios,
                "summary": "Ratios financieros calculados exitosamente",
                "note": "Compara estos ratios con promedios de tu industria y con periodos anteriores"
            }

        except Exception as e:
            logger.error(f"Error calculating financial ratios: {e}")
            return {"error": str(e)}

    agent = Agent(
        name="contabilidad_agent",
        model=MODEL,
        instructions=CONTABILIDAD_INSTRUCTIONS,
        tools=[
            explain_accounting_cycle,
            explain_financial_statements,
            calculate_financial_ratios,
        ],
    )

    return agent
