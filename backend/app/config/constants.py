"""Global constants and configuration.

NOTE: Agent instructions have been moved to app/agents/instructions/
Import them from there instead of this file.
"""

# Timezone configuration
# All datetime operations in the application use this timezone
TIMEZONE = "America/Santiago"  # Chile (UTC-3 / UTC-4 with DST)

# OpenAI models configuration
# Multi-agent system models
SUPERVISOR_MODEL = "gpt-4.1-mini"  # Very fast and cheap for routing
SPECIALIZED_MODEL = "gpt-5-mini"  # Very fast and cheap for specialized tasks

# Model settings for reasoning models (gpt-5*)
REASONING_EFFORT = None  # Options: "low", "medium", "high"
