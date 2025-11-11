"""PII Detection Guardrail - Prevents leaking sensitive information."""

from __future__ import annotations

import logging
import re
from typing import Any

from agents import Agent, RunContextWrapper, output_guardrail

from app.agents.guardrails.core import GuardrailFunctionOutput

logger = logging.getLogger(__name__)


@output_guardrail
async def pii_output_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    output_data: Any,
) -> GuardrailFunctionOutput:
    """
    Detects PII (Personally Identifiable Information) in agent output.

    Checks for:
    - RUT (Chilean national ID) patterns
    - Email addresses
    - Phone numbers
    - Credit card patterns
    - Passwords/API keys

    Note: This is a basic implementation using regex.
    For production, consider using a dedicated PII detection service.
    """
    # Extract text from output
    if isinstance(output_data, str):
        output_text = output_data
    elif hasattr(output_data, "response"):
        output_text = str(output_data.response)
    else:
        output_text = str(output_data)

    pii_patterns = {
        "rut": r"\d{1,2}\.\d{3}\.\d{3}[-\.][\dkK]",  # Chilean RUT format
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\+?56\s?9\s?\d{4}\s?\d{4}",  # Chilean phone format
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "api_key": r"sk-[a-zA-Z0-9]{32,}",  # OpenAI API key pattern
    }

    detected_pii = []
    for pii_type, pattern in pii_patterns.items():
        matches = re.findall(pattern, output_text)
        if matches:
            detected_pii.append({
                "type": pii_type,
                "count": len(matches),
                "samples": matches[:2],  # First 2 examples
            })

    if detected_pii:
        logger.warning(
            f"🚨 PII detected in output: {detected_pii} | "
            f"Agent: {agent.name}"
        )

        # For now, just log - don't block
        # You can change this to tripwire_triggered=True to block output with PII
        return GuardrailFunctionOutput(
            output_info={
                "pii_detected": detected_pii,
                "action": "logged_only",
            },
            tripwire_triggered=False,  # Change to True to block
        )

    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False,
    )
