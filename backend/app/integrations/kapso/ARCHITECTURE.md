# Kapso Integration Architecture

## 📁 File Structure

```
kapso/
├── __init__.py                    # Main exports (KapsoClient, models, exceptions)
├── client.py                      # ✨ Modular client (MAIN - organized by domain)
├── client_old.py                  # Legacy monolithic client (backward compatibility)
├── models.py                      # Data models (MessageType, ConversationStatus, etc.)
├── exceptions.py                  # Custom exceptions
├── examples.py                    # Usage examples
├── test_modular.py                # Structure tests
├── README.md                      # Main documentation
├── WEBHOOK_TROUBLESHOOTING.md    # Webhook debugging guide
├── ARCHITECTURE.md               # This file
│
└── api/                          # ✨ Modular API modules
    ├── __init__.py               # Module exports
    ├── README.md                 # API modules documentation
    ├── base.py                   # BaseAPI with common HTTP logic
    ├── messages.py               # MessagesAPI - Send and search messages
    ├── conversations.py          # ConversationsAPI - Manage conversations
    ├── contacts.py               # ContactsAPI - Contact operations
    ├── templates.py              # TemplatesAPI - Template operations (Meta API)
    ├── config.py                 # ConfigAPI - WhatsApp configuration
    └── webhooks.py               # WebhooksAPI - Webhook utilities
```

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        KapsoClient (v2)                         │
│                     (client_v2.py)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  messages    │  │conversations │  │   contacts   │         │
│  │   API        │  │     API      │  │     API      │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│  ┌──────────────┐  ┌──────┴───────┐  ┌──────────────┐         │
│  │  templates   │  │   config     │  │   webhooks   │         │
│  │     API      │  │     API      │  │     API      │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                   ┌────────▼────────┐                          │
│                   │    BaseAPI      │                          │
│                   │   (base.py)     │                          │
│                   └────────┬────────┘                          │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │     httpx       │
                    │  AsyncClient    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐    │    ┌─────────▼─────────┐
     │  Kapso API      │    │    │    Meta API       │
     │ app.kapso.ai    │    │    │  api.kapso.ai     │
     │   /api/v1       │    │    │ /meta/whatsapp/   │
     └─────────────────┘    │    └───────────────────┘
                            │
                   ┌────────▼────────┐
                   │  Meta WhatsApp  │
                   │  Business API   │
                   └─────────────────┘
```

## 🔄 Request Flow

### Example: Send Template

```
User Code
   │
   ├─> client.templates.send(...)
   │
   └─> TemplatesAPI.send()
         │
         ├─> Build Meta API payload with components
         │
         └─> BaseAPI._make_request()
               │
               ├─> httpx.AsyncClient.request()
               │     │
               │     └─> https://api.kapso.ai/meta/whatsapp/v21.0/{phone_number_id}/messages
               │           │
               │           └─> Meta WhatsApp Business API
               │
               └─> Handle response / errors
                     │
                     └─> Return result to user
```

### Example: Get Template Structure

```
User Code
   │
   ├─> client.templates.get_structure(...)
   │
   └─> TemplatesAPI.get_structure()
         │
         ├─> Request to Meta API through Kapso
         │     │
         │     └─> https://api.kapso.ai/meta/whatsapp/v23.0/{waba_id}/message_templates?name={template_name}
         │
         ├─> Extract named_parameters from response
         │     ├─> header_text_named_params
         │     └─> body_text_named_params
         │
         ├─> Build whatsapp_template_structure
         │     ├─> header_params: [...]
         │     └─> body_params: [...]
         │
         └─> Return structured data
```

## 📦 Module Responsibilities

### BaseAPI (base.py)
- Common HTTP request logic
- Error handling and exception mapping
- Status code processing
- Timeout management
- Shared headers configuration

### MessagesAPI (messages.py)
- `send_text()` - Send text messages
- `send_media()` - Send images, videos, documents
- `send_interactive()` - Send buttons and lists
- `search()` - Search messages by content
- `mark_as_read()` - Mark messages as read

### ConversationsAPI (conversations.py)
- `create()` - Create new conversation
- `get()` - Get conversation details
- `list()` - List conversations
- `update_status()` - Update conversation status (active/ended)

### ContactsAPI (contacts.py)
- `search()` - Search contacts by name/phone
- `get_context()` - Get contact with recent messages
- `add_note()` - Add notes to contacts

### TemplatesAPI (templates.py)
- `list()` - List available templates
- `get_structure()` - Get template structure from Meta API
- `create()` - Create template in Meta
- `send()` - Send template with parameters
- `send_with_components()` - Send with pre-built components

### ConfigAPI (config.py)
- `list()` - List WhatsApp configurations
- `get_inbox()` - Get inbox for a configuration

### WebhooksAPI (webhooks.py)
- `validate_signature()` - Validate webhook HMAC signature
- `health_check()` - Health check utility

## 🔌 Integration Points

### 1. Notification System
```python
# backend/app/services/notifications/modules/sending_service.py
kapso_client = KapsoClient(api_token=api_token)

# Send template via WhatsApp
await kapso_client.templates.send_with_components(
    phone_number=phone,
    template_name=template_id,
    phone_number_id=phone_number_id,
    components=components
)
```

### 2. WhatsApp Service
```python
# backend/app/services/whatsapp/service.py
kapso_client = KapsoClient(api_token=api_token)

# Send text message
await kapso_client.messages.send_text(
    conversation_id=conv_id,
    message=text
)

# Get contact context
context = await kapso_client.contacts.get_context(
    identifier=phone_number
)
```

### 3. Admin Endpoints
```python
# backend/app/routers/admin/notifications.py
kapso_client = KapsoClient(api_token=api_token)

# Sync template structure from Meta
structure = await kapso_client.templates.get_structure(
    template_name=name,
    business_account_id=waba_id
)
```

## 🚀 Migration Path

### Phase 1: ✅ COMPLETED
- Created modular API modules in `api/` directory
- Implemented modular client with domain-specific APIs
- Renamed `client_v2.py` → `client.py` (modular is now the main client)
- Renamed old `client.py` → `client_old.py` (legacy backup)
- Updated `__init__.py` to export modular client as default
- Legacy client available as `LegacyKapsoClient` for backward compatibility

### Phase 2: In Progress
- ✅ Updated `backend/app/routers/admin/notifications.py` to use modular client
- TODO: Update services to use modular client
- TODO: Update Celery tasks to use modular client

### Phase 3: Future
- Deprecate legacy client (add warnings)
- Remove `client_old.py` after full migration
- Add more specialized modules as needed

## 🎯 Design Principles

### 1. Single Responsibility
Each API module handles one domain of functionality.

### 2. Composition over Inheritance
`KapsoClient` composes multiple API modules rather than inheriting a massive base class.

### 3. Explicit is Better than Implicit
Clear naming: `client.templates.send()` is more explicit than `client.send_template_message()`.

### 4. Don't Repeat Yourself (DRY)
Common HTTP logic lives in `BaseAPI`, shared by all modules.

### 5. Open/Closed Principle
Easy to extend with new modules without modifying existing code.

## 📊 Benefits Summary

| Aspect | Before (Monolithic) | After (Modular) |
|--------|-------------------|----------------|
| **File size** | 1,081 lines | ~200 lines/module |
| **Testability** | Hard to isolate | Easy to test each domain |
| **Discoverability** | Scroll through huge file | Browse by domain |
| **Extensibility** | Modify huge class | Add new module |
| **IDE support** | Poor autocomplete | Excellent autocomplete |
| **Documentation** | One huge docstring | Per-module docs |
| **Collaboration** | Merge conflicts | Work on separate modules |

## 🔐 Environment Variables

Required for template operations:
- `KAPSO_API_TOKEN` - Kapso API authentication token
- `WHATSAPP_BUSINESS_ACCOUNT_ID` - Meta WABA ID (for template structure sync)
- `WHATSAPP_PHONE_NUMBER_ID` - Meta phone number ID (for sending templates)

## 📚 See Also

- [API Modules README](api/README.md) - Detailed API documentation
- [Main README](README.md) - General Kapso integration info
- [Webhook Troubleshooting](WEBHOOK_TROUBLESHOOTING.md) - Debug webhooks
