"""
Guardrails system for agent input/output validation.

Guardrails run in parallel to agents to perform checks and validations:
- Input guardrails: Validate user input before agent execution
- Output guardrails: Validate agent output before returning to user

If a guardrail tripwire is triggered, execution halts and an exception is raised.

Example usage:

    from app.agents.guardrails import input_guardrail, GuardrailFunctionOutput
    from agents import Agent, RunContextWrapper

    @input_guardrail
    async def abuse_detection_guardrail(
        ctx: RunContextWrapper,
        agent: Agent,
        input: str | list
    ) -> GuardrailFunctionOutput:
        # Check for abusive content
        if "malicious prompt" in str(input).lower():
            return GuardrailFunctionOutput(
                output_info={"reason": "Abusive content detected"},
                tripwire_triggered=True
            )
        return GuardrailFunctionOutput(
            output_info={"status": "ok"},
            tripwire_triggered=False
        )

    # Add to agent
    agent = Agent(
        name="My Agent",
        instructions="...",
        input_guardrails=[abuse_detection_guardrail],
    )
"""

from app.agents.guardrails.core import (
    GuardrailFunctionOutput,
    GuardrailResult,
    InputGuardrailResult,
    OutputGuardrailResult,
    GuardrailTripwireTriggered,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)
from app.agents.guardrails.decorators import (
    input_guardrail,
    output_guardrail,
)
from app.agents.guardrails.runner import GuardrailRunner
from app.agents.guardrails.registry import guardrail_registry

__all__ = [
    # Core types
    "GuardrailFunctionOutput",
    "GuardrailResult",
    "InputGuardrailResult",
    "OutputGuardrailResult",
    "GuardrailTripwireTriggered",
    "InputGuardrailTripwireTriggered",
    "OutputGuardrailTripwireTriggered",
    # Decorators
    "input_guardrail",
    "output_guardrail",
    # Infrastructure
    "GuardrailRunner",
    "guardrail_registry",
]
