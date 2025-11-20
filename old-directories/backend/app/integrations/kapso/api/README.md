# Kapso API Modules

Modular organization of Kapso WhatsApp Business API client.

## Structure

```
api/
├── __init__.py           # Module exports
├── base.py              # BaseAPI with common HTTP logic
├── messages.py          # Send and search messages
├── conversations.py     # Manage conversations
├── contacts.py          # Contact operations
├── templates.py         # Template operations (Meta API)
├── config.py            # WhatsApp configuration
└── webhooks.py          # Webhook utilities
```

## Usage

### Import the modular client

```python
from app.integrations.kapso import KapsoClient

client = KapsoClient(api_token="your-token")
```

### Messages API

```python
# Send text message
await client.messages.send_text(
    conversation_id="conv-123",
    message="Hello!"
)

# Send media
await client.messages.send_media(
    conversation_id="conv-123",
    media_url="https://example.com/image.jpg",
    media_type="image",
    caption="Check this out!"
)

# Send interactive message
await client.messages.send_interactive(
    conversation_id="conv-123",
    interactive_type="button",
    body_text="Choose an option:",
    buttons=[
        {"id": "1", "title": "Option 1"},
        {"id": "2", "title": "Option 2"}
    ]
)

# Search messages
results = await client.messages.search(
    query="invoice",
    conversation_id="conv-123"
)

# Mark as read
await client.messages.mark_as_read(
    conversation_id="conv-123"
)
```

### Conversations API

```python
# Create conversation
conv = await client.conversations.create(
    phone_number="56912345678",
    whatsapp_config_id="config-123"
)

# Get conversation
conv = await client.conversations.get("conv-123")

# List conversations
convs = await client.conversations.list(
    whatsapp_config_id="config-123",
    limit=50
)

# Update status
await client.conversations.update_status(
    conversation_id="conv-123",
    status="ended",
    reason="Issue resolved"
)
```

### Contacts API

```python
# Search contacts
contacts = await client.contacts.search(
    query="Juan",
    limit=20
)

# Get contact context with recent messages
context = await client.contacts.get_context(
    identifier="56912345678",
    include_recent_messages=True,
    recent_message_limit=30
)

# Add note to contact
note = await client.contacts.add_note(
    contact_identifier="56912345678",
    content="Customer interested in product X",
    name="sales_note"
)
```

### Templates API

```python
# List templates
templates = await client.templates.list(
    whatsapp_config_id="config-123"
)

# Get template structure from Meta API
structure = await client.templates.get_structure(
    template_name="daily_business_summary",
    business_account_id="123456789"
)

print(structure)
# {
#     "template_name": "daily_business_summary",
#     "whatsapp_template_structure": {
#         "header_params": ["day_name"],
#         "body_params": ["sales_count", "sales_total_ft", ...]
#     },
#     "named_parameters": [...]
# }

# Send template
await client.templates.send(
    phone_number_id="647015955153740",
    to="56912345678",
    template_name="welcome_message",
    language_code="es",
    header_params=[{"type": "text", "text": "Juan"}],
    body_params=[
        {"type": "text", "text": "Order #12345"},
        {"type": "text", "text": "$1,500"}
    ]
)

# Send template with pre-built components (used by notification system)
await client.templates.send_with_components(
    phone_number="56912345678",
    template_name="daily_summary",
    phone_number_id="647015955153740",
    components=[
        {
            "type": "header",
            "parameters": [
                {"type": "text", "text": "Lunes", "name": "day_name"}
            ]
        },
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "5", "name": "sales_count"},
                {"type": "text", "text": "$1,500,000", "name": "sales_total_ft"}
            ]
        }
    ]
)

# Create template in Meta
result = await client.templates.create(
    waba_id="1890372408497828",
    name="order_confirmation",
    category="UTILITY",
    language="es",
    components=[{
        "type": "BODY",
        "text": "Hola {{customer_name}}, tu pedido fue confirmado!",
        "example": {
            "body_text_named_params": [
                {"param_name": "customer_name", "example": "Juan"}
            ]
        }
    }]
)
```

### Config API

```python
# List WhatsApp configurations
configs = await client.config.list(
    customer_id="customer-123"
)

# Get inbox for a config
inbox = await client.config.get_inbox(
    whatsapp_config_id="config-123",
    limit=20,
    status="active"
)
```

### Webhooks API

```python
# Validate webhook signature
is_valid = client.webhooks.validate_signature(
    payload=request_body,
    signature=request.headers.get("X-Signature"),
    secret=webhook_secret
)

if not is_valid:
    raise HTTPException(status_code=401, detail="Invalid signature")
```

## Architecture Benefits

### 1. Separation of Concerns
Each module handles one domain:
- **messages.py**: Only message operations
- **templates.py**: Only template operations
- **contacts.py**: Only contact operations
- etc.

### 2. Easy to Test
Each module can be tested independently:
```python
from app.integrations.kapso.api import TemplatesAPI

api = TemplatesAPI(api_token="test-token", base_url="http://mock")
# Test only template operations
```

### 3. Easy to Extend
Add new functionality by creating a new module:
```python
# api/analytics.py
class AnalyticsAPI(BaseAPI):
    async def get_metrics(self, ...):
        ...
```

### 4. Clear Documentation
Each module is self-contained with docstrings.

### 5. Backward Compatible
The old monolithic client is still available:
```python
from app.integrations.kapso import LegacyKapsoClient

client = LegacyKapsoClient(api_token="token")
# Works exactly like before
```

## Migration Guide

### Before (Monolithic Client)
```python
from app.integrations.kapso import KapsoClient

client = KapsoClient(api_token="token")

# All methods at top level
await client.send_text_message(...)
await client.send_template_message(...)
await client.search_contacts(...)
await client.get_template_structure(...)
```

### After (Modular Client)
```python
from app.integrations.kapso import KapsoClient

client = KapsoClient(api_token="token")

# Methods organized by domain
await client.messages.send_text(...)
await client.templates.send(...)
await client.contacts.search(...)
await client.templates.get_structure(...)
```

## Meta API Integration

The `templates` module uses Meta API endpoints directly through Kapso:

- **List/Get Templates**: `https://api.kapso.ai/meta/whatsapp/v23.0/{business_account_id}/message_templates`
- **Send Templates**: `https://api.kapso.ai/meta/whatsapp/v21.0/{phone_number_id}/messages`

This provides:
- Direct access to latest WhatsApp features
- Named parameters support
- Better template management
- Consistent with Meta's documentation

## Error Handling

All modules raise the same exceptions:

```python
from app.integrations.kapso import (
    KapsoAPIError,
    KapsoNotFoundError,
    KapsoValidationError,
    KapsoAuthenticationError,
    KapsoTimeoutError
)

try:
    await client.templates.get_structure("template_name", "waba_id")
except KapsoNotFoundError:
    # Template doesn't exist
    pass
except KapsoAPIError as e:
    # Other API error
    print(e.status_code, e.response_data)
```
