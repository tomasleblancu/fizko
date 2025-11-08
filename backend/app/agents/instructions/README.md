# Agent Instructions - Modular Structure

This directory contains the instructions for all Fizko agents using a modular, structured approach based on Anthropic's best practices.

## Directory Structure

```
instructions/
├── __init__.py                 # Instruction loader
├── README.md                   # This file
├── shared/                     # Shared sections across all agents
│   ├── 4_interaction_rules.md
│   ├── 8_error_and_fallback.md
│   └── 9_safety_and_limitations.md
├── supervisor/                 # Supervisor agent (routing)
│   ├── 1_system_overview.md
│   ├── 2_objectives_and_responsibilities.md
│   ├── 3_context_and_data_sources.md
│   ├── 4_interaction_rules.md
│   ├── 5_tool_usage_policy.md
│   ├── 6_reasoning_and_workflow.md
│   ├── 7_output_format.md
│   ├── 8_error_and_fallback.md
│   └── 9_safety_and_limitations.md
├── general_knowledge/          # General knowledge agent (tax concepts)
│   └── [9 sections following same structure]
├── tax_documents/              # Tax documents agent (real data)
│   └── [9 sections following same structure]
└── payroll/                    # Payroll agent (employees & labor law)
    └── [9 sections following same structure]
```

## Section Organization

Each agent has 9 numbered sections following Anthropic's recommended structure:

1. **System Overview** - Agent identity and primary function
2. **Objectives & Responsibilities** - Main tasks and expected outcomes
3. **Context & Data Sources** - Available tools, data, and knowledge base
4. **Interaction Rules** - Communication guidelines and principles
5. **Tool Usage Policy** - When and how to use each tool
6. **Reasoning & Workflow** - Decision flows and reasoning steps
7. **Output Format** - Response structure and formatting guidelines
8. **Error & Fallback** - Error handling and fallback behavior
9. **Safety & Limitations** - Scope boundaries and safety guidelines

## Usage

Instructions are automatically loaded by `__init__.py` using the `_load_modular_instruction()` function:

```python
from app.agents.instructions import (
    SUPERVISOR_INSTRUCTIONS,
    GENERAL_KNOWLEDGE_INSTRUCTIONS,
    TAX_DOCUMENTS_INSTRUCTIONS,
    PAYROLL_INSTRUCTIONS
)
```

The loader:
1. Reads all numbered `.md` files from an agent's directory
2. Sorts them by filename (1_*.md, 2_*.md, etc.)
3. Combines them into a single instruction string
4. Returns the complete instruction text

## Benefits of Modular Structure

✅ **Easy to maintain** - Each section is focused and independent
✅ **Easy to update** - Modify specific sections without affecting others
✅ **Consistent structure** - All agents follow the same organization
✅ **Reusable content** - Shared sections can be referenced across agents
✅ **Better version control** - Git diffs are cleaner and more meaningful
✅ **Testable** - Each section can be reviewed and tested independently

## Editing Guidelines

When modifying instructions:

1. **Keep sections focused** - Each file should address one aspect
2. **Use clear headings** - Make structure immediately visible
3. **Be concise** - Remove unnecessary words and repetition
4. **Avoid ambiguity** - Use precise language and clear examples
5. **Test changes** - Verify instructions load correctly after changes

## Shared Content

The `shared/` directory contains sections that are common across multiple agents:
- Communication principles
- Error handling basics
- Safety guidelines

These can be used as reference or copied into agent-specific sections when needed.

## Adding New Agents

To add a new agent:

1. Create a new directory: `instructions/[agent_name]/`
2. Create 9 numbered sections following the structure above
3. Update `__init__.py` to load the new agent:
   ```python
   NEW_AGENT_INSTRUCTIONS = _load_modular_instruction("new_agent")
   ```
4. Add to `__all__` export list
5. Test loading with the instructions module

## Migration Notes

This modular structure was created on 2025-11-07, replacing single-file instructions:
- ~~supervisor.md~~ → `supervisor/` (9 files)
- ~~general_knowledge.md~~ → `general_knowledge/` (9 files)
- ~~tax_documents.md~~ → `tax_documents/` (9 files)
- ~~payroll.md~~ → `payroll/` (9 files)

All legacy single-file instructions have been removed.
