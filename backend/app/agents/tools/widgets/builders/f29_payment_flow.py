"""F29 Payment Flow Widget - Step-by-step guide to pay F29 on SII.

Based on flujo_pago_f29.widget template.
"""

from __future__ import annotations

from typing import Any

try:
    from chatkit.widgets import WidgetRoot, Card, Col, Title, Text, Row, Button, Divider, Badge
    from chatkit.actions import ActionConfig
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    WidgetRoot = Any  # type: ignore
    Card = Any  # type: ignore
    Col = Any  # type: ignore
    Title = Any  # type: ignore
    Text = Any  # type: ignore
    Row = Any  # type: ignore
    Button = Any  # type: ignore
    Divider = Any  # type: ignore
    Badge = Any  # type: ignore
    ActionConfig = Any  # type: ignore


def create_f29_payment_flow_widget(
    title: str = "Paso a paso: pago en SII",
    url: str = "https://zeusr.sii.cl/AUT2000/InicioAutenticacion/IngresoRutClave.html?https://www4.sii.cl/propuestaf29ui/#/default",
) -> WidgetRoot | None:
    """
    Create a widget displaying the step-by-step flow to pay F29 on SII.

    Uses JSON dict structure for maximum compatibility with ChatKit.

    Args:
        title: Title of the payment flow widget
        url: URL to the SII F29 payment page

    Returns:
        Card widget with the payment flow steps, or None if widgets not available
    """
    if not WIDGETS_AVAILABLE:
        return None

    # Define payment steps (from flujo_pago_f29.widget)
    steps = [
        {"id": "1", "num": 1, "text": "Visita el enlace inicial."},
        {"id": "2", "num": 2, "text": "Ingresa tus credenciales."},
        {"id": "3", "num": 3, "text": "Haz clic en \"Aceptar\"."},
        {"id": "4", "num": 4, "text": "Haz clic en \"Continuar desde declaración guardada\"."},
        {"id": "5", "num": 5, "text": "Haz clic en \"Continuar desde datos guardados\"."},
        {"id": "6", "num": 6, "text": "Haz clic en \"Enviar declaración\"."},
        {"id": "7", "num": 7, "text": "Haz clic en \"Continuar\"."},
        {"id": "8", "num": 8, "text": "Elige tu método de pago y paga."},
    ]

    # Build step rows with better styling - each step in a Box
    step_rows = []
    for step in steps:
        step_rows.append({
            "type": "Box",
            "padding": 2,
            "background": "subtle",
            "radius": "md",
            "children": [
                {
                    "type": "Row",
                    "gap": 2,
                    "align": "start",
                    "children": [
                        {
                            "type": "Badge",
                            "label": str(step['num']),
                            "color": "info"
                        },
                        {
                            "type": "Text",
                            "value": step["text"],
                            "size": "sm"
                        }
                    ]
                }
            ]
        })

    # Build widget structure - using Col instead of ListView
    widget_dict = {
        "type": "Card",
        "size": "sm",
        "children": [
            # Header section
            {
                "type": "Col",
                "gap": 1,
                "children": [
                    {
                        "type": "Title",
                        "value": title,
                        "size": "sm"
                    },
                    {
                        "type": "Text",
                        "value": f"Sigue estos {len(steps)} pasos.",
                        "size": "sm",
                        "color": "secondary"
                    }
                ]
            },
            # Button-styled Markdown link (best option for external URLs)
            {
                "type": "Row",
                "children": [
                    {
                        "type": "Box",
                        "padding": 2,
                        "children": [
                            {
                                "type": "Markdown",
                                "value": f"**[🔗 Abrir SII]({url})**"
                            }
                        ]
                    }
                ]
            },
            # Divider
            {
                "type": "Divider",
                "flush": True
            },
            # Steps in Col with better spacing
            {
                "type": "Col",
                "gap": 3,
                "children": step_rows
            }
        ]
    }

    return widget_dict  # type: ignore


def f29_payment_flow_widget_copy_text(
    title: str = "Paso a paso: pago en SII",
    url: str = "https://zeusr.sii.cl/AUT2000/InicioAutenticacion/IngresoRutClave.html?https://www4.sii.cl/propuestaf29ui/#/default",
) -> str:
    """
    Generate human-readable fallback text for the F29 payment flow widget.

    Returns:
        Formatted text representation of the payment flow
    """
    lines = [
        title,
        "=" * len(title),
        "",
        "Sigue estos 8 pasos:",
        "",
        "1. Visita el enlace inicial.",
        "2. Ingresa tus credenciales.",
        "3. Haz clic en \"Aceptar\".",
        "4. Haz clic en \"Continuar desde declaración guardada\".",
        "5. Haz clic en \"Continuar desde datos guardados\".",
        "6. Haz clic en \"Enviar declaración\".",
        "7. Haz clic en \"Continuar\".",
        "8. Elige tu método de pago y paga.",
        "",
        f"🔗 Enlace: {url}",
    ]

    return "\n".join(lines)
