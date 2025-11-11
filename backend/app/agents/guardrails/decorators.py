"""Decorators for defining guardrail functions."""

from __future__ import annotations

import functools
from typing import Any, Callable

from agents import Agent, RunContextWrapper, InputGuardrailResult, OutputGuardrailResult

from .core import GuardrailFunctionOutput


# Type for guardrail functions
GuardrailFunction = Callable[
    [RunContextWrapper, Agent, Any],
    GuardrailFunctionOutput
]


class GuardrailWrapper:
    """
    Wrapper class to make guardrail functions compatible with OpenAI Agents SDK.

    The SDK expects guardrails to have a get_name() method.
    """

    def __init__(self, func: Callable, name: str, description: str, is_input: bool = True):
        self.func = func
        self.name = name
        self.description = description
        self.is_input = is_input

        # Preserve original function attributes
        functools.update_wrapper(self, func)

    def get_name(self) -> str:
        """Return the guardrail name (required by Agents SDK)."""
        return self.name

    async def run(self, agent: Agent, input_data: Any, context: RunContextWrapper):
        """
        Run the guardrail (required by Agents SDK).

        This is the method that the SDK calls to execute the guardrail.
        Returns an InputGuardrailResult or OutputGuardrailResult wrapping the output.
        """
        output = await self.func(context, agent, input_data)

        # Wrap output in appropriate result type
        if self.is_input:
            return InputGuardrailResult(guardrail=self, output=output)
        else:
            return OutputGuardrailResult(guardrail=self, output=output)

    async def __call__(self, *args, **kwargs):
        """Make wrapper callable (for direct invocation)."""
        return await self.func(*args, **kwargs)

    def __repr__(self):
        return f"<Guardrail '{self.name}' ({'input' if self.is_input else 'output'})>"


def input_guardrail(func: GuardrailFunction) -> GuardrailWrapper:
    """
    Decorator to mark a function as an input guardrail.

    Input guardrails run on user input before agent execution.

    Example:
        @input_guardrail
        async def check_abuse(
            ctx: RunContextWrapper,
            agent: Agent,
            input: str | list
        ) -> GuardrailFunctionOutput:
            if "malicious" in str(input).lower():
                return GuardrailFunctionOutput(
                    output_info={"reason": "Abusive content"},
                    tripwire_triggered=True
                )
            return GuardrailFunctionOutput(
                output_info={"status": "ok"},
                tripwire_triggered=False
            )

    Args:
        func: Async function that receives (ctx, agent, input) and returns GuardrailFunctionOutput

    Returns:
        GuardrailWrapper instance compatible with Agents SDK
    """
    return GuardrailWrapper(
        func=func,
        name=func.__name__,
        description=func.__doc__ or "No description",
        is_input=True,
    )


def output_guardrail(func: GuardrailFunction) -> GuardrailWrapper:
    """
    Decorator to mark a function as an output guardrail.

    Output guardrails run on agent output before returning to user.

    Example:
        @output_guardrail
        async def check_pii(
            ctx: RunContextWrapper,
            agent: Agent,
            output: Any
        ) -> GuardrailFunctionOutput:
            # Check for PII in output
            output_text = str(output)
            if contains_pii(output_text):
                return GuardrailFunctionOutput(
                    output_info={"reason": "PII detected in output"},
                    tripwire_triggered=True
                )
            return GuardrailFunctionOutput(
                output_info={"status": "ok"},
                tripwire_triggered=False
            )

    Args:
        func: Async function that receives (ctx, agent, output) and returns GuardrailFunctionOutput

    Returns:
        GuardrailWrapper instance compatible with Agents SDK
    """
    return GuardrailWrapper(
        func=func,
        name=func.__name__,
        description=func.__doc__ or "No description",
        is_input=False,
    )
