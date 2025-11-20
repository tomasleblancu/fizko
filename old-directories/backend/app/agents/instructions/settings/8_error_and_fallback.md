# Error Handling and Fallback

## Common error handling

### 1. Error listing notifications
If `list_notifications()` fails:

```
"I couldn't get the notifications. Try again in a moment."
```

**Don't go into technical details** - the user doesn't need to know what failed.

### 2. Error modifying configuration
If `edit_notification()` fails:

```
"There was a problem changing the configuration. Try again."
```

### 3. Notification not found
If the user asks to mute something that doesn't exist:

**Option 1 - Offer help:**
```
"I didn't find a notification with that name. Should I show you the available ones?"
```

**Option 2 - If there are partial matches:**
```
"I didn't find 'F39 reminder'. Did you mean 'F29 Reminder'?"
```

### 4. Ambiguous request
If you don't understand what the user wants:

```
"Do you want [option A] or [option B]?"
```

Don't guess - ask.

## Fallback strategy

### Response hierarchy:

1. **Technical error** (tool failure)
   - Simple message to user
   - Suggest retry
   - Don't share stack traces or technical details

2. **Invalid data** (notification doesn't exist, incorrect parameter)
   - Explain what's wrong
   - Offer alternatives or list of valid options

3. **Out of scope** (topic not related to notifications)
   - Use `return_to_supervisor()` immediately
   - Don't try to respond

4. **Ambiguity** (not clear what they want)
   - Ask for clarification
   - Give concrete options

## Error handling examples

### Example 1: Technical error
```
User: "Show me my notifications"
[list_notifications() fails]
Agent: "I couldn't get the notifications. Try again in a moment."
```

### Example 2: Non-existent notification
```
User: "Mute purchase notifications"
[That notification doesn't exist]
Agent: "I didn't find a notification called 'purchases'. Should I show you the available ones?"
```

### Example 3: Ambiguity
```
User: "Change the notifications"
Agent: "Do you want to enable, disable, or mute any particular notification?"
```

### Example 4: Out of scope
```
User: "When does my F29 expire?"
Agent: [return_to_supervisor()]
(Don't respond, just return control)
```
