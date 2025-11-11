"""Abuse Detection Guardrail - Detects malicious usage patterns."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent, RunContextWrapper, Runner, input_guardrail
from pydantic import BaseModel

from app.agents.guardrails.core import GuardrailFunctionOutput

from agents.model_settings import ModelSettings, Reasoning

logger = logging.getLogger(__name__)


class AbuseCheckOutput(BaseModel):
    """Output from abuse detection check."""
    is_abusive: bool
    reason: str
    confidence: float  # 0.0 to 1.0


@input_guardrail
async def abuse_detection_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input_data: str | list[dict[str, Any]],
) -> GuardrailFunctionOutput:
    """
    Detects malicious usage patterns like:
    - Requests to help with homework/exams (for tax platform)
    - Attempts to manipulate the model
    - Prompt injection attempts
    - Off-topic requests (e.g., creative writing, coding help)

    This uses a fast model (gpt-4o-mini) to quickly classify the request.
    """
    # Extract text from input
    if isinstance(input_data, str):
        input_text = input_data
    else:
        # Extract text from message format
        text_parts = []
        for item in input_data:
            if isinstance(item, dict) and "content" in item:
                for part in item["content"]:
                    if isinstance(part, dict) and part.get("type") == "input_text":
                        text_parts.append(part.get("text", ""))
        input_text = " ".join(text_parts)

    # Quick heuristic checks (fast path)
    # 1. Prompt injection patterns
    prompt_injection_patterns = [
        "ignore previous instructions",
        "disregard your instructions",
        "act as if you are",
        "pretend to be",
        "you are now",
        "new instructions:",
    ]

    for pattern in prompt_injection_patterns:
        if pattern in input_text.lower():
            logger.warning(f"🚨 Abuse detection: Prompt injection pattern detected: '{pattern}'")
            return GuardrailFunctionOutput(
                output_info={
                    "reason": f"Prompt injection attempt detected (pattern: {pattern})",
                    "confidence": 0.9,
                },
                tripwire_triggered=True,
            )

    # 2. Off-topic / Out-of-scope patterns
    # Keywords that indicate the request is NOT about taxes/accounting/Chile
    off_topic_keywords = [
        # Homework/Academic
        ("homework", "exam", "examen", "exámenes"),
        # Math/Science (unless tax-related)
        ("ecuación", "ecuaciones", "equation", "equations", "álgebra", "algebra", "matemática", "matemáticas", "mathematics"),
        # Entertainment
        ("película", "películas", "movie", "movies", "serie", "series", "juego", "juegos", "game", "games", "videojuego", "videojuegos"),
        # Creative writing
        ("poema", "poemas", "poem", "poems", "cuento", "cuentos", "story", "stories", "novela", "novelas", "novel", "novels"),
        # Programming (unless about Fizko integration)
        ("código python", "codigo python", "código java", "codigo java", "python code", "java code", "javascript", "programar", "programación", "programacion", "programming"),
        # General knowledge unrelated to business
        ("quién fue", "quien fue", "who was", "quiénes fueron", "who were"),
        # Recipes/Cooking
        ("receta", "recetas", "recipe", "recipes", "cocinar", "cocina", "cooking", "cook", "preparar comida", "ingredientes", "ingredients"),
    ]

    input_lower = input_text.lower()

    # Check for off-topic keywords
    off_topic_matches = []
    for keyword_group in off_topic_keywords:
        for keyword in keyword_group:
            if keyword in input_lower:
                off_topic_matches.append(keyword)
                break  # One match per group is enough

    # If keywords detected, block immediately (no need to call AI)
    if len(off_topic_matches) >= 1:
        logger.warning(f"🚨 Abuse detection: Off-topic request detected: {off_topic_matches}")
        return GuardrailFunctionOutput(
            output_info={
                "reason": f"Off-topic request (keywords: {off_topic_matches})",
                "confidence": 0.9,  # High confidence when keywords match
            },
            tripwire_triggered=True,
        )

    # AI check - FALLBACK layer for cases without obvious keywords
    # Only runs if NO keywords were detected
    USE_AI_CHECK = True  # ⚠️ Adds ~200ms latency but catches edge cases keywords miss

    if USE_AI_CHECK:
        try:
            # Create a simple agent to classify the request
            from openai import AsyncOpenAI
            import os
            from pathlib import Path

            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Load instructions from file
            # __file__ is in: app/agents/guardrails/implementations/abuse_detection.py
            # Need to go up to: app/agents/instructions/guardrails/ABUSE_DETECTION_AI_CHECK.md
            instructions_path = Path(__file__).parent.parent.parent / "instructions" / "guardrails" / "ABUSE_DETECTION_AI_CHECK.md"
            with open(instructions_path, "r", encoding="utf-8") as f:
                instructions = f.read()

            abuse_check_agent = Agent(
                name="Abuse Detection",
                instructions=instructions,
                model="gpt-5-nano",
                model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
                output_type=AbuseCheckOutput,
            )

            result = await Runner.run(
                abuse_check_agent,
                input_text,
                context=ctx.context,
            )

            abuse_check: AbuseCheckOutput = result.final_output

            if abuse_check.is_abusive:
                logger.warning(
                    f"🚨 Abuse detection (AI): {abuse_check.reason} | "
                    f"Confidence: {abuse_check.confidence:.2f}"
                )
                return GuardrailFunctionOutput(
                    output_info={
                        "reason": abuse_check.reason,
                        "confidence": abuse_check.confidence,
                    },
                    tripwire_triggered=True,
                )

        except Exception as e:
            logger.error(f"❌ Abuse detection AI check failed: {e}")
            # Don't block on guardrail failure - allow request through
            pass

    # All checks passed
    return GuardrailFunctionOutput(
        output_info={"status": "ok"},
        tripwire_triggered=False,
    )
