"""Global constants and configuration for Backend V2."""

# Timezone configuration
TIMEZONE = "America/Santiago"  # Chile (UTC-3 / UTC-4 with DST)

# OpenAI models configuration
# Multi-agent system models
SUPERVISOR_MODEL = "gpt-4o-mini"  # Fast and cheap for routing
SPECIALIZED_MODEL = "gpt-4o-mini"  # Fast and cheap for specialized tasks

# Model settings for reasoning models (gpt-5*)
REASONING_EFFORT = "medium"  # Options: "low", "medium", "high"
