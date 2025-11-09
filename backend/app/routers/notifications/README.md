# Notification Routers (Complete)

Modular router structure for ALL notification operations (admin + user-facing).

## Structure

```
notifications/
├── __init__.py           # Main router aggregator (combines admin + user)
├── templates.py          # CRUD endpoints for notification templates (admin)
├── whatsapp_sync.py      # WhatsApp template synchronization (admin)
├── subscriptions.py      # Company notification subscriptions (admin)
├── user_operations.py    # User-scoped operations (scheduling, history, preferences)
└── README.md             # This file
```

## Endpoints

### Admin Operations (require `require_auth`)

#### Template Management (`templates.py`)

All endpoints prefixed with `/api/notifications/notification-templates`:

- **GET** `/` - List notification templates (with filters)
- **GET** `/{template_id}` - Get template details
- **POST** `/` - Create new template
- **PUT** `/{template_id}` - Update template
- **DELETE** `/{template_id}` - Delete template

#### WhatsApp Synchronization (`whatsapp_sync.py`)

- **POST** `/api/notifications/notification-templates/sync-whatsapp/{template_name}` - Sync WhatsApp template structure from Meta API

#### Company Subscriptions (`subscriptions.py`)

All endpoints prefixed with `/api/notifications/company/{company_id}/notification-subscriptions`:

- **GET** `/` - List all subscriptions for a company
- **POST** `/` - Create new subscription
- **PUT** `/{subscription_id}` - Update subscription
- **DELETE** `/{subscription_id}` - Delete subscription

### User Operations (`user_operations.py`)

Scoped to current user's company (uses `get_user_company_id()`):

#### Scheduling
- **POST** `/api/notifications/schedule` - Schedule a notification
- **POST** `/api/notifications/process` - Process pending notifications (admin TODO)

#### History
- **GET** `/api/notifications/history` - View notification history

#### Preferences
- **GET** `/api/notifications/preferences` - Get user notification preferences
- **PUT** `/api/notifications/preferences` - Update user notification preferences

## Architecture

All routers follow the service layer pattern:

```
Router (HTTP layer)
    ↓ delegates to
NotificationService (business logic)
    ↓ uses
NotificationTemplateRepository (data access)
    ↓ queries
Database (PostgreSQL via SQLAlchemy)
```

### Key Benefits

1. **Separation of concerns**: HTTP handling separated from business logic
2. **No SQL in routers**: All database operations in repositories
3. **Testability**: Services and repositories can be tested independently
4. **Maintainability**: Changes to logic don't affect HTTP layer

## Dependencies

- **Service**: [app/services/notifications/](../../../services/notifications/)
- **Repository**: [app/repositories/core/notifications.py](../../../repositories/core/notifications.py)
- **Schemas**: [app/schemas/notifications.py](../../../schemas/notifications.py)

## Usage Example

```python
from app.routers.admin.notifications import router as notifications_router

app.include_router(notifications_router)
```

## Related Documentation

- [Notification Service README](../../../services/notifications/README.md)
- [Repository Pattern](../../../repositories/README.md)
