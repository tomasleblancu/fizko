# Services Layer

This directory contains the business logic layer for the Next.js frontend, following the Service Layer pattern used in the FastAPI backend.

## Architecture

```
services/
├── sii/                  # SII integration services
│   ├── sii-auth.service.ts          # Main orchestrator for SII authentication
│   └── sii-backend-client.ts        # HTTP client for backend-v2 API
├── company/              # Company management services
│   ├── company.service.ts           # Company CRUD operations
│   └── company-tax-info.service.ts  # Tax information management
├── session/              # Session management services
│   └── session.service.ts           # User-company session operations
└── celery/               # Celery task management
    └── celery-task.service.ts       # Launch and monitor background tasks
```

## Design Principles

### Separation of Concerns
- **API Routes** (`app/api/*`) - HTTP handling only (validation, auth, error responses)
- **Services** (`services/*`) - Business logic, data manipulation, orchestration
- **Lib** (`lib/*`) - Low-level utilities (formatters, encryption, clients)

### Benefits
✅ **Testability** - Services can be tested without HTTP layer
✅ **Reusability** - Services can be used from:
  - API routes
  - Server actions
  - Server components
  - CLI scripts
✅ **Maintainability** - Logic is centralized and well-organized
✅ **Consistency** - Same pattern as FastAPI backend

## Usage Example

### Before (All logic in route):
```typescript
// app/api/sii/auth/route.ts - 285 lines
export async function POST(request: NextRequest) {
  // Validation
  // Backend call
  // Company creation
  // Tax info update
  // Credential encryption
  // Session creation
  // Settings check
}
```

### After (Service layer):
```typescript
// app/api/sii/auth/route.ts - 57 lines
export async function POST(request: NextRequest) {
  const { rut, password } = await request.json();

  // Validate input
  if (!rut || !password) {
    return NextResponse.json({ error: '...' }, { status: 400 });
  }

  // Get authenticated user
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  // Delegate to service
  const result = await SIIAuthService.authenticateAndSync(
    user.id,
    rut,
    password
  );

  return NextResponse.json(result);
}
```

## Service Documentation

### SIIAuthService
Main orchestrator for SII authentication flow.

**Methods:**
- `authenticateAndSync(userId, userEmail, rut, password)` - Complete authentication flow

**Flow:**
1. Normalize RUT format
2. Call backend SII API
3. Upsert company data
4. Save encrypted credentials
5. Launch document sync task (new companies only)
6. Create/update session
7. Check setup status

### CompanyService
Handles company CRUD operations.

**Methods:**
- `upsertFromSII(normalizedRut, contribInfo)` - Create/update from SII data (returns `{ company, isNew }`)
- `saveCredentials(companyId, password)` - Encrypt and save SII password
- `needsSetup(companyId)` - Check if initial setup is required

### CompanyTaxInfoService
Manages company tax information.

**Methods:**
- `upsert(companyId, contribInfo)` - Create/update tax info with all SII data

**Features:**
- Stores complete SII data in `extra_data` JSONB field
- Extracts key fields for structured queries
- Parses dates from SII format

### SessionService
Manages user-company sessions.

**Methods:**
- `createOrUpdate(userId, companyId, cookies, userEmail)` - Upsert session with SII cookies
- Automatically creates user profile if it doesn't exist (prevents foreign key errors)

### CeleryTaskService
Manages Celery background tasks.

**Methods:**
- `launchTask(request)` - Generic task launcher
- `syncSIIDocuments(companyId, months, monthOffset)` - Sync tax documents
- `syncSIIForm29(companyId, period)` - Sync Form29 declaration
- `getTaskStatus(taskId)` - Check task status
- `waitForTaskCompletion(taskId, pollIntervalMs, timeoutMs)` - Poll until completion
- `cancelTask(taskId)` - Cancel running task

**Features:**
- Automatic task status polling
- Timeout handling
- Task cancellation support
- Specialized methods for common tasks

### SIIBackendClient
HTTP client for backend-v2 communication.

**Methods:**
- `login(rutBody, dv, password)` - Authenticate with SII via backend

## Types

All SII-related types are defined in `types/sii.types.ts`:
- `SIILoginResponse` - Backend login response
- `ContribuyenteInfo` - Complete contributor data from SII
- `SIIAuthResult` - Service authentication result
- Supporting types for addresses, activities, representatives, etc.

## Backend Communication

All communication with backend-v2 (FastAPI) should use the centralized `BackendClient`:

```typescript
import { BackendClient } from '@/lib/backend-client';

// GET request
const data = await BackendClient.get<ResponseType>('/api/endpoint');

// POST request
const result = await BackendClient.post<ResponseType>('/api/endpoint', {
  key: 'value'
});

// PUT, PATCH, DELETE also available
```

**Benefits:**
- ✅ Centralized URL configuration
- ✅ Consistent error handling
- ✅ Automatic logging
- ✅ Type-safe responses
- ✅ Easy to mock for testing

See `lib/backend-client.example.ts` for comprehensive usage examples.

## Adding New Services

When adding new services, follow these guidelines:

1. **Create service file** in appropriate domain folder
2. **Define types** in `types/` directory
3. **Use static methods** for stateless operations
4. **Inject dependencies** (like Supabase client) when needed
5. **Use BackendClient** for all backend-v2 API calls
6. **Document public methods** with JSDoc
7. **Use descriptive logging** with service name prefix
8. **Throw errors** with descriptive messages
9. **Keep routes thin** - delegate to services

## Example: Adding New Service

```typescript
// services/invoice/invoice.service.ts
import { createServiceClient } from '@/lib/supabase/server';

export class InvoiceService {
  /**
   * Create invoice from DTE data
   */
  static async createFromDTE(companyId: string, dteData: any) {
    const client = createServiceClient();
    console.log('[Invoice Service] Creating invoice');

    // Business logic here

    return invoice;
  }
}
```

```typescript
// app/api/invoices/route.ts
import { InvoiceService } from '@/services/invoice/invoice.service';

export async function POST(request: NextRequest) {
  const data = await request.json();
  const result = await InvoiceService.createFromDTE(data.companyId, data.dte);
  return NextResponse.json(result);
}
```
