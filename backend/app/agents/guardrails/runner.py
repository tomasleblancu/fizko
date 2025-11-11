"""GuardrailRunner - Executes guardrails in parallel with agents."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from agents import Agent, RunContextWrapper

from .core import (
    GuardrailFunctionOutput,
    InputGuardrailResult,
    OutputGuardrailResult,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

logger = logging.getLogger(__name__)


class GuardrailRunner:
    """
    Runner for executing guardrails.

    This class handles:
    - Running multiple guardrails in parallel
    - Timing guardrail execution
    - Raising exceptions when tripwires are triggered
    - Logging guardrail results
    """

    @staticmethod
    async def run_input_guardrails(
        ctx: RunContextWrapper,
        agent: Agent,
        input_data: Any,
    ) -> list[InputGuardrailResult]:
        """
        Run all input guardrails for an agent.

        Args:
            ctx: Run context wrapper
            agent: Agent instance with guardrails
            input_data: User input to validate

        Returns:
            List of guardrail results

        Raises:
            InputGuardrailTripwireTriggered: If any guardrail tripwire is triggered
        """
        if not hasattr(agent, "input_guardrails") or not agent.input_guardrails:
            return []

        logger.info(f"🛡️  Running {len(agent.input_guardrails)} input guardrails for {agent.name}")

        # Run all guardrails in parallel
        tasks = []
        for guardrail_func in agent.input_guardrails:
            task = GuardrailRunner._run_single_guardrail(
                guardrail_func=guardrail_func,
                ctx=ctx,
                agent=agent,
                data=input_data,
                is_input=True,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        guardrail_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Guardrail failed with exception: {result}")
                continue

            guardrail_results.append(result)

            # Check if tripwire triggered
            if result.output.tripwire_triggered:
                logger.warning(
                    f"🚨 Input guardrail tripwire triggered: {result.guardrail_name} | "
                    f"Reason: {result.output.output_info}"
                )
                raise InputGuardrailTripwireTriggered(
                    guardrail_name=result.guardrail_name,
                    result=result,
                )

        logger.info(f"✅ All input guardrails passed ({len(guardrail_results)} checks)")
        return guardrail_results

    @staticmethod
    async def run_output_guardrails(
        ctx: RunContextWrapper,
        agent: Agent,
        output_data: Any,
    ) -> list[OutputGuardrailResult]:
        """
        Run all output guardrails for an agent.

        Args:
            ctx: Run context wrapper
            agent: Agent instance with guardrails
            output_data: Agent output to validate

        Returns:
            List of guardrail results

        Raises:
            OutputGuardrailTripwireTriggered: If any guardrail tripwire is triggered
        """
        if not hasattr(agent, "output_guardrails") or not agent.output_guardrails:
            return []

        logger.info(f"🛡️  Running {len(agent.output_guardrails)} output guardrails for {agent.name}")

        # Run all guardrails in parallel
        tasks = []
        for guardrail_func in agent.output_guardrails:
            task = GuardrailRunner._run_single_guardrail(
                guardrail_func=guardrail_func,
                ctx=ctx,
                agent=agent,
                data=output_data,
                is_input=False,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        guardrail_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Guardrail failed with exception: {result}")
                continue

            guardrail_results.append(result)

            # Check if tripwire triggered
            if result.output.tripwire_triggered:
                logger.warning(
                    f"🚨 Output guardrail tripwire triggered: {result.guardrail_name} | "
                    f"Reason: {result.output.output_info}"
                )
                raise OutputGuardrailTripwireTriggered(
                    guardrail_name=result.guardrail_name,
                    result=result,
                )

        logger.info(f"✅ All output guardrails passed ({len(guardrail_results)} checks)")
        return guardrail_results

    @staticmethod
    async def _run_single_guardrail(
        guardrail_func: Any,
        ctx: RunContextWrapper,
        agent: Agent,
        data: Any,
        is_input: bool,
    ) -> InputGuardrailResult | OutputGuardrailResult:
        """
        Run a single guardrail and time its execution.

        Args:
            guardrail_func: Guardrail function to execute
            ctx: Run context wrapper
            agent: Agent instance
            data: Data to validate (input or output)
            is_input: Whether this is an input guardrail

        Returns:
            Guardrail result with timing info
        """
        guardrail_name = getattr(guardrail_func, "_guardrail_name", guardrail_func.__name__)

        start_time = time.perf_counter()
        try:
            output: GuardrailFunctionOutput = await guardrail_func(ctx, agent, data)
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            logger.debug(
                f"{'🔍' if is_input else '📤'} Guardrail '{guardrail_name}' completed | "
                f"{execution_time_ms:.2f}ms | "
                f"Tripwire: {output.tripwire_triggered}"
            )

            result_class = InputGuardrailResult if is_input else OutputGuardrailResult
            return result_class(
                guardrail_name=guardrail_name,
                output=output,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"❌ Guardrail '{guardrail_name}' failed | "
                f"{execution_time_ms:.2f}ms | "
                f"Error: {e}"
            )
            raise
