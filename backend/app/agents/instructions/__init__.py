"""Agent instructions loader.

This module loads agent instructions from markdown files for better organization
and maintainability. Each agent has its own instruction directory with modular sections.
"""

from pathlib import Path


def _load_modular_instruction(agent_name: str) -> str:
    """Load modular instruction from agent directory.

    Loads all numbered markdown files in the agent's directory and combines them
    into a single instruction string.

    Args:
        agent_name: Name of the agent directory (e.g., "supervisor")

    Returns:
        Combined instruction text content
    """
    agent_dir = Path(__file__).parent / agent_name
    if not agent_dir.exists():
        raise FileNotFoundError(f"Agent directory not found: {agent_dir}")

    # Get all numbered markdown files and sort them
    md_files = sorted(agent_dir.glob("[0-9]_*.md"))

    if not md_files:
        raise FileNotFoundError(f"No instruction files found in: {agent_dir}")

    # Load and combine all sections
    sections = []
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8").strip()
        if content:
            sections.append(content)

    return "\n\n".join(sections)


# Load all agent instructions using modular structure
SUPERVISOR_INSTRUCTIONS = _load_modular_instruction("supervisor")
GENERAL_KNOWLEDGE_INSTRUCTIONS = _load_modular_instruction("general_knowledge")
TAX_DOCUMENTS_INSTRUCTIONS = _load_modular_instruction("tax_documents")
MONTHLY_TAXES_INSTRUCTIONS = _load_modular_instruction("monthly_taxes")
PAYROLL_INSTRUCTIONS = _load_modular_instruction("payroll")
EXPENSE_INSTRUCTIONS = _load_modular_instruction("expense")

__all__ = [
    "SUPERVISOR_INSTRUCTIONS",
    "GENERAL_KNOWLEDGE_INSTRUCTIONS",
    "TAX_DOCUMENTS_INSTRUCTIONS",
    "MONTHLY_TAXES_INSTRUCTIONS",
    "PAYROLL_INSTRUCTIONS",
    "EXPENSE_INSTRUCTIONS",
]
