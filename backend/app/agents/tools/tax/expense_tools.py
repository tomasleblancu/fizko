"""Tools for manual expense registration - for non-electronic expenses (boletas, receipts)."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any
from decimal import Decimal

from agents import RunContextWrapper, function_tool

from app.agents.core import FizkoContext
from app.agents.tools.decorators import require_subscription_tool
from app.agents.tools.utils import get_supabase

logger = logging.getLogger(__name__)


@function_tool(strict_mode=False)
@require_subscription_tool("create_expense")
async def create_expense(
    ctx: RunContextWrapper[FizkoContext],
    category: str,
    description: str,
    amount: float,
    expense_date: str | None = None,
    vendor_name: str | None = None,
    vendor_rut: str | None = None,
    receipt_number: str | None = None,
    has_tax: bool = True,
    is_reimbursable: bool = False,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Register a manual expense ONLY after the user has uploaded a receipt document.

    **IMPORTANT REQUIREMENT:**
    This tool can ONLY be used AFTER:
    1. User has uploaded a receipt/document (image or PDF) in the conversation
    2. You have analyzed the document and extracted information
    3. User has confirmed or complemented the extracted information

    **Workflow:**
    1. User uploads receipt → You analyze it with vision/OCR
    2. You present extracted data → User confirms/corrects
    3. ONLY THEN you can call this tool to register the expense

    **DO NOT use this tool if:**
    - No document has been uploaded in this conversation
    - You haven't analyzed any receipt yet
    - User is just asking hypothetically about expenses

    Use this tool when the user wants to register an expense from a receipt that doesn't have
    a DTE (electronic tax document). Common examples:
    - Taxi/Uber receipts (boletas)
    - Parking tickets
    - Meals at restaurants
    - Small office supplies
    - Any expense without electronic invoice

    Args:
        category: Expense category (required). You can use Spanish or English terms:
            - "transporte" / "transport" = Taxi, Uber, bus, transporte público
            - "estacionamiento" / "parking" = Estacionamiento, parking
            - "alimentación" / "comida" / "meals" = Restaurant, almuerzo, comida
            - "útiles de oficina" / "artículos de oficina" / "office_supplies" = Papelería, útiles
            - "servicios básicos" / "utilities" = Luz, agua, internet
            - "gastos de representación" / "representation" = Representación, cliente
            - "viajes" / "travel" = Viajes de negocio
            - "servicios profesionales" / "professional_services" = Asesorías, servicios
            - "mantención" / "maintenance" = Reparaciones, mantención
            - "otros" / "other" = Otros gastos no categorizados
        description: Brief description of the expense (required)
            Examples: "Taxi al cliente ABC", "Almuerzo reunión", "Estacionamiento oficina"
        amount: Total amount paid in CLP (required)
            The net amount and IVA will be calculated automatically
        expense_date: Date of expense (YYYY-MM-DD). Defaults to today if not provided
        vendor_name: Name of vendor/provider (e.g., "Taxi Seguro", "Restaurant ABC")
        vendor_rut: RUT of vendor if available (format: 12345678-9)
        receipt_number: Receipt/ticket number if available
        has_tax: Whether the amount includes 19% IVA (default: true)
            Set to false for tax-exempt expenses
        is_reimbursable: Whether this expense should be reimbursed to employee (default: false)
        notes: Additional notes or context about the expense

    Returns:
        Dictionary with created expense details or error if no document uploaded

    Examples:
        ❌ WRONG - No document uploaded:
        User: "Quiero registrar un gasto de taxi por $10,000"
        You: "Por favor, primero sube una foto del recibo para poder registrar el gasto."

        ✅ CORRECT - After document analysis:
        User: [uploads receipt photo]
        You: "Veo que es un recibo de taxi por $10,000. ¿Es correcto?"
        User: "Sí, regístralo"
        You: create_expense(category="transport", description="Taxi", amount=10000)

    Note:
        - The expense is created in "draft" status
        - Net amount and IVA are calculated automatically based on has_tax flag
        - Receipt file URL from uploaded document is automatically attached
        - All expenses are tracked for tax deduction purposes
    """
    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    # VALIDATE: Check if there's an uploaded document in the conversation context
    attachments = ctx.context.request_context.get("attachments", [])

    if not attachments or len(attachments) == 0:
        return {
            "error": "No se puede registrar el gasto sin un documento",
            "message": (
                "❌ Para registrar un gasto, primero debes subir una foto o PDF del recibo.\n\n"
                "📸 Por favor, sube el recibo y luego podremos registrar el gasto.\n\n"
                "Una vez que analice el documento, confirmarás la información y "
                "procederé a registrarlo en el sistema."
            ),
            "requires_document": True,
        }

    # Get the most recent attachment (the receipt being processed)
    latest_attachment = attachments[-1]
    receipt_file_url = latest_attachment.get("upload_url") or latest_attachment.get("url")
    receipt_file_name = latest_attachment.get("name")
    receipt_mime_type = latest_attachment.get("mime_type")

    logger.info(f"Creating expense with attachment: {receipt_file_name}")

    # Category mapping: Spanish -> English
    category_mapping = {
        # English (already valid)
        "transport": "transport",
        "parking": "parking",
        "meals": "meals",
        "office_supplies": "office_supplies",
        "utilities": "utilities",
        "representation": "representation",
        "travel": "travel",
        "professional_services": "professional_services",
        "maintenance": "maintenance",
        "other": "other",
        # Spanish terms
        "transporte": "transport",
        "estacionamiento": "parking",
        "alimentacion": "meals",
        "alimentación": "meals",
        "comida": "meals",
        "utiles de oficina": "office_supplies",
        "útiles de oficina": "office_supplies",
        "articulos de oficina": "office_supplies",
        "artículos de oficina": "office_supplies",
        "oficina": "office_supplies",
        "servicios basicos": "utilities",
        "servicios básicos": "utilities",
        "gastos de representacion": "representation",
        "gastos de representación": "representation",
        "representacion": "representation",
        "representación": "representation",
        "viajes": "travel",
        "viaje": "travel",
        "servicios profesionales": "professional_services",
        "mantencion": "maintenance",
        "mantención": "maintenance",
        "otros": "other",
        "otro": "other",
    }

    # Normalize category
    category_normalized = category.lower().strip()
    category_english = category_mapping.get(category_normalized)

    if not category_english:
        return {
            "error": "Categoría no reconocida",
            "message": (
                f"❌ No reconozco la categoría '{category}'.\n\n"
                "Usa una de estas categorías:\n"
                "• transporte / transport\n"
                "• estacionamiento / parking\n"
                "• alimentación / meals\n"
                "• útiles de oficina / office_supplies\n"
                "• servicios básicos / utilities\n"
                "• gastos de representación / representation\n"
                "• viajes / travel\n"
                "• servicios profesionales / professional_services\n"
                "• mantención / maintenance\n"
                "• otros / other"
            ),
        }

    category = category_english

    # Parse expense date
    try:
        if expense_date:
            expense_date_obj = datetime.strptime(expense_date, "%Y-%m-%d").date()
        else:
            expense_date_obj = date.today()
    except ValueError:
        return {"error": "Formato de fecha inválido. Use YYYY-MM-DD"}

    # Validate amount
    if amount <= 0:
        return {"error": "El monto debe ser mayor a 0"}

    try:
        # Get Supabase client
        supabase = get_supabase()

        # Create expense using repository
        expense = await supabase.expenses.create(
            company_id=company_id,
            created_by_user_id=user_id,
            expense_category=category,
            expense_date=expense_date_obj,
            description=description,
            vendor_name=vendor_name,
            vendor_rut=vendor_rut,
            receipt_number=receipt_number,
            total_amount=Decimal(str(amount)),
            has_tax=has_tax,
            is_reimbursable=is_reimbursable,
            notes=notes,
            receipt_file_url=receipt_file_url,
            receipt_file_name=receipt_file_name,
            receipt_mime_type=receipt_mime_type,
        )

        if not expense:
            return {"error": "Error al crear el gasto en la base de datos"}

        # Category labels for response
        category_labels = {
            "transport": "Transporte",
            "parking": "Estacionamiento",
            "meals": "Alimentación",
            "office_supplies": "Útiles de oficina",
            "utilities": "Servicios básicos",
            "representation": "Gastos de representación",
            "travel": "Viajes",
            "professional_services": "Servicios profesionales",
            "maintenance": "Mantención",
            "other": "Otros",
        }

        return {
            "success": True,
            "expense_id": expense.get("id"),
            "category": category,
            "category_label": category_labels.get(category, category),
            "description": expense.get("description"),
            "expense_date": expense.get("expense_date"),
            "vendor_name": expense.get("vendor_name"),
            "total_amount": float(expense.get("total_amount", 0)),
            "net_amount": float(expense.get("net_amount", 0)),
            "tax_amount": float(expense.get("tax_amount", 0)),
            "has_tax": expense.get("has_tax"),
            "is_reimbursable": expense.get("is_reimbursable"),
            "status": expense.get("status"),
            "receipt_file_name": receipt_file_name,
            "message": (
                f"✅ Gasto registrado exitosamente:\n"
                f"- Categoría: {category_labels.get(category, category)}\n"
                f"- Monto total: ${expense.get('total_amount', 0):,.0f}\n"
                f"- Monto neto: ${expense.get('net_amount', 0):,.0f}\n"
                f"- IVA: ${expense.get('tax_amount', 0):,.0f}\n"
                f"- Estado: Borrador (draft)\n"
                f"- Recibo adjunto: {receipt_file_name}\n\n"
                f"El gasto fue registrado y está en estado borrador. "
                f"Puedes editarlo o enviarlo para aprobación cuando estés listo."
            ),
        }

    except Exception as e:
        logger.error(f"Error creating expense: {e}", exc_info=True)
        return {"error": f"Error al crear gasto: {str(e)}"}


@function_tool(strict_mode=False)
@require_subscription_tool("get_expenses")
async def get_expenses(
    ctx: RunContextWrapper[FizkoContext],
    status: str | None = None,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Get list of expenses with optional filters.

    Use this tool to retrieve and display expense history. All filters are optional.

    Args:
        status: Filter by status:
            - "draft" = Borradores (being edited)
            - "pending_approval" = Pendiente de aprobación
            - "approved" = Aprobados (tax-deductible)
            - "rejected" = Rechazados
            - "requires_info" = Requiere información adicional
        category: Filter by category (transport, parking, meals, etc.)
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        limit: Maximum number of expenses to return (default 20, max 100)

    Returns:
        List of expenses with details and summary statistics

    Examples:
        User: "Muéstrame mis gastos del mes"
        Tool call: get_expenses(start_date="2024-11-01", end_date="2024-11-30")

        User: "¿Qué gastos están pendientes de aprobación?"
        Tool call: get_expenses(status="pending_approval")

        User: "Muestra gastos de transporte"
        Tool call: get_expenses(category="transport")
    """
    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    # Parse dates
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    except ValueError:
        return {"error": "Formato de fecha inválido. Use YYYY-MM-DD"}

    # Validate limit
    limit = min(limit, 100)

    try:
        # Get Supabase client
        supabase = get_supabase()

        # Get expenses using repository
        expenses, total = await supabase.expenses.list(
            company_id=company_id,
            status=status,
            category=category,
            date_from=start_dt,
            date_to=end_dt,
            limit=limit,
            offset=0,
        )

        # Format expenses for response
        formatted_expenses = []
        for expense in expenses:
            formatted_expenses.append({
                "id": expense.get("id"),
                "category": expense.get("expense_category"),
                "description": expense.get("description"),
                "expense_date": expense.get("expense_date"),
                "vendor_name": expense.get("vendor_name"),
                "total_amount": float(expense.get("total_amount", 0)),
                "net_amount": float(expense.get("net_amount", 0)),
                "tax_amount": float(expense.get("tax_amount", 0)),
                "status": expense.get("status"),
                "is_reimbursable": expense.get("is_reimbursable"),
                "created_at": expense.get("created_at"),
            })

        # Get summary
        summary = await supabase.expenses.get_summary(
            company_id=company_id,
            date_from=start_dt,
            date_to=end_dt,
            category=category,
            status=status,
        )

        return {
            "expenses": formatted_expenses,
            "total_count": total,
            "showing": len(formatted_expenses),
            "summary": {
                "total_expenses": summary["total_count"],
                "total_amount": summary["total_amount"],
                "total_net": summary["total_net"],
                "total_tax": summary["total_tax"],
            },
            "filters_applied": {
                "status": status,
                "category": category,
                "date_range": f"{start_date} to {end_date}" if start_date and end_date else None,
            },
        }

    except Exception as e:
        logger.error(f"Error getting expenses: {e}", exc_info=True)
        return {"error": f"Error al obtener gastos: {str(e)}"}


@function_tool(strict_mode=False)
@require_subscription_tool("get_expense_summary")
async def get_expense_summary(
    ctx: RunContextWrapper[FizkoContext],
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = "approved",
) -> dict[str, Any]:
    """
    Get summary statistics for expenses in a period.

    Useful for reporting total expenses, tax deductions, and financial analysis.

    Args:
        start_date: Period start date (YYYY-MM-DD). Defaults to start of current month
        end_date: Period end date (YYYY-MM-DD). Defaults to today
        status: Filter by status (default: "approved" for tax-deductible expenses only)

    Returns:
        Summary with totals and IVA breakdown

    Examples:
        User: "¿Cuánto llevo gastado este mes?"
        Tool call: get_expense_summary()

        User: "Muéstrame el resumen de gastos de octubre"
        Tool call: get_expense_summary(start_date="2024-10-01", end_date="2024-10-31")

        User: "¿Cuánto IVA puedo recuperar de mis gastos aprobados?"
        Tool call: get_expense_summary(status="approved")
    """
    user_id = ctx.context.request_context.get("user_id")
    if not user_id:
        return {"error": "Usuario no autenticado"}

    company_id = ctx.context.request_context.get("company_id")
    if not company_id:
        return {"error": "company_id no disponible en el contexto"}

    # Parse dates
    try:
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            # Default to start of current month
            today = date.today()
            start_dt = date(today.year, today.month, 1)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_dt = date.today()
    except ValueError:
        return {"error": "Formato de fecha inválido. Use YYYY-MM-DD"}

    try:
        # Get Supabase client
        supabase = get_supabase()

        # Get summary using repository
        summary = await supabase.expenses.get_summary(
            company_id=company_id,
            date_from=start_dt,
            date_to=end_dt,
            status=status,
        )

        return {
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
            },
            "status_filter": status,
            "total_expenses": summary["total_count"],
            "total_amount": summary["total_amount"],
            "total_net": summary["total_net"],
            "total_tax": summary["total_tax"],
            "message": (
                f"📊 Resumen de gastos:\n"
                f"Período: {start_dt.strftime('%d/%m/%Y')} - {end_dt.strftime('%d/%m/%Y')}\n"
                f"Total gastos: {summary['total_count']}\n"
                f"Monto total: ${summary['total_amount']:,.0f}\n"
                f"Monto neto: ${summary['total_net']:,.0f}\n"
                f"IVA recuperable: ${summary['total_tax']:,.0f}"
            ),
        }

    except Exception as e:
        logger.error(f"Error getting expense summary: {e}", exc_info=True)
        return {"error": f"Error al obtener resumen: {str(e)}"}
