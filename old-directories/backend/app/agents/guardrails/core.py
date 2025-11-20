"""Core types and exceptions for guardrails system."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class GuardrailFunctionOutput(BaseModel):
    """
    Output from a guardrail function.

    Attributes:
        output_info: Additional information about the check (reason, confidence, etc.)
        tripwire_triggered: If True, halts execution and raises exception
    """
    output_info: dict[str, Any] | BaseModel | None = None
    tripwire_triggered: bool = False


class GuardrailResult(BaseModel):
    """
    Result from running a guardrail.

    Attributes:
        guardrail_name: Name of the guardrail that ran
        output: Output from the guardrail function
        execution_time_ms: How long the guardrail took to run
    """
    guardrail_name: str
    output: GuardrailFunctionOutput
    execution_time_ms: float


class InputGuardrailResult(GuardrailResult):
    """Result from an input guardrail."""
    pass


class OutputGuardrailResult(GuardrailResult):
    """Result from an output guardrail."""
    pass


# Exceptions
class GuardrailTripwireTriggered(Exception):
    """Base exception for when a guardrail tripwire is triggered."""
    def __init__(self, guardrail_name: str, result: GuardrailResult):
        self.guardrail_name = guardrail_name
        self.result = result
        super().__init__(
            f"Guardrail '{guardrail_name}' triggered: {result.output.output_info}"
        )


class InputGuardrailTripwireTriggered(GuardrailTripwireTriggered):
    """Exception raised when an input guardrail tripwire is triggered."""
    pass


class OutputGuardrailTripwireTriggered(GuardrailTripwireTriggered):
    """Exception raised when an output guardrail tripwire is triggered."""
    pass
