# Guardrail Instructions

This directory contains instructions for AI-based guardrail checks.

## Purpose

These instructions are used by small, fast AI models (like gpt-4.1-nano) to classify whether user requests are appropriate for the Fizko platform.

## Files

### ABUSE_DETECTION_AI_CHECK.md

Instructions for the abuse detection AI check that runs in `abuse_detection_guardrail`.

**Used by:** `app/agents/guardrails/implementations/abuse_detection.py`

**Purpose:** Classify user requests as APPROPRIATE or ABUSIVE to block:
- Off-topic requests (programming, homework, entertainment, etc.)
- Malicious usage (prompt injection, manipulation attempts)

## How to Update

To modify what the guardrail blocks or allows:

1. **Edit the instructions file** (e.g., `ABUSE_DETECTION_AI_CHECK.md`)
2. **Update categories** as needed based on your available agents and features
3. **Add edge cases** with examples to improve accuracy
4. **Deploy** - the guardrail will automatically load the updated instructions

## Best Practices

### Writing Good Instructions

✅ **DO:**
- Use clear categories (APPROPRIATE vs ABUSIVE)
- Provide specific examples with ✅/❌ markers
- Include edge cases that are ambiguous
- Explain the platform's purpose and scope
- Use "Key principle" statements for clarity

❌ **DON'T:**
- Use vague language like "might be" or "could be"
- Forget to mention platform-specific features
- Create overly complex rules
- Ignore false positive scenarios

### Updating for New Features

When you add new agents or features to Fizko, update the APPROPRIATE section:

```markdown
## APPROPRIATE requests are about:

**Business & Financial topics that our platform supports:**
- Tax questions...
- Accounting...
- [NEW] Invoice generation and management  ← Add your new feature here
```

## Performance Considerations

- Instructions are loaded from file on each guardrail execution
- File I/O is fast (~1ms) compared to AI inference (~200ms)
- Consider caching if you see performance issues (not needed currently)

## Testing

After updating instructions, test with edge cases:

```bash
cd backend
.venv/bin/python

# In Python REPL:
from app.agents.guardrails.implementations import abuse_detection_guardrail
from agents import Agent, RunContextWrapper, Runner

# Test with your specific edge case
# See test_guardrail_simple.py for examples
```

## Related Documentation

- [abuse_detection.py](../implementations/abuse_detection.py) - Implementation
- [CONFIGURACION_OFF_TOPIC.md](../CONFIGURACION_OFF_TOPIC.md) - Configuration guide
- [GUARDRAILS_IMPLEMENTATION.md](../../../../GUARDRAILS_IMPLEMENTATION.md) - System overview
