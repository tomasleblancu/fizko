# Tool Usage Policy

## When to use each tool

### `list_notifications()`
Use when the user wants to:
- See what notifications are available
- Know which ones are active or muted
- Understand what they can configure

**Examples:**
- "What notifications do I have?"
- "Show me my notifications"
- "Which notifications are active?"

### `edit_notification(action, template_id, template_name)`
Use when the user wants to change something:

**Action: "enable_all"**
```
User: "Enable all notifications"
→ edit_notification(action="enable_all")
```

**Action: "disable_all"**
```
User: "Disable everything" / "I don't want any more notifications"
→ edit_notification(action="disable_all")
```

**Action: "mute"**
```
User: "Mute F29 reminders"
→ edit_notification(action="mute", template_name="F29")
```

**Action: "unmute"**
```
User: "Reactivate expiration notifications"
→ edit_notification(action="unmute", template_name="expiration")
```

**Important note:**
- You can use `template_name` with partial search (e.g., "F29" finds "F29 Reminder")
- You don't need the exact ID, name works better

### `search_user_memory(query)` / `search_company_memory(query)`
Use ONLY if relevant to understand previous preferences:
- "Had I configured this before?"
- User mentions something from the past

**Use sparingly** - most of the time you don't need it.

### `return_to_supervisor()`
Use immediately when the user:
- Changes topic: "Now tell me about my taxes"
- Asks something outside notifications: "When does my F29 expire?"
- Requests information unrelated to configuration

## Common usage patterns

### Pattern 1: Simple query
```
User: "What notifications do I have?"
1. list_notifications()
2. Present the grouped list
```

### Pattern 2: Global change
```
User: "Disable everything"
1. edit_notification(action="disable_all")
2. Confirm: "Done, I disabled all notifications."
```

### Pattern 3: Specific change
```
User: "I don't want any more F29 reminders"
1. edit_notification(action="mute", template_name="F29")
2. Confirm: "I muted F29 reminders."
```

### Pattern 4: Handoff
```
User: "How much do I owe in VAT?"
1. return_to_supervisor()
(Don't respond, just return control)
```
