# Backend Client

Centralized HTTP client for communicating with the FastAPI backend (backend-v2).

## Overview

The `BackendClient` provides a consistent, type-safe interface for all API calls to backend-v2. It handles:

- ✅ **URL construction** - Centralized backend URL configuration
- ✅ **HTTP methods** - GET, POST, PUT, PATCH, DELETE
- ✅ **Error handling** - Consistent error messages
- ✅ **Logging** - Automatic request/response logging
- ✅ **Type safety** - Generic type support for responses
- ✅ **Headers** - Automatic Content-Type + custom headers support

## Configuration

The backend URL is configured via environment variable:

```bash
# .env.local
NEXT_PUBLIC_BACKEND_V2_URL=http://localhost:8000
```

If not set, defaults to `http://localhost:8000`.

## Basic Usage

### Import

```typescript
import { BackendClient } from '@/lib/backend-client';
```

### GET Request

```typescript
interface Company {
  id: string;
  rut: string;
  business_name: string;
}

const company = await BackendClient.get<Company>('/api/companies/123');
console.log(company.business_name);
```

### POST Request

```typescript
interface LoginRequest {
  rut: string;
  dv: string;
  password: string;
}

interface LoginResponse {
  success: boolean;
  token: string;
}

const response = await BackendClient.post<LoginResponse>(
  '/api/auth/login',
  {
    rut: '12345678',
    dv: '9',
    password: 'secret',
  }
);

if (response.success) {
  console.log('Token:', response.token);
}
```

### PUT Request

```typescript
const updatedCompany = await BackendClient.put<Company>(
  '/api/companies/123',
  {
    business_name: 'New Name',
    address: 'New Address',
  }
);
```

### PATCH Request

```typescript
const patchedCompany = await BackendClient.patch<Company>(
  '/api/companies/123',
  {
    phone: '+56912345678', // Only update phone
  }
);
```

### DELETE Request

```typescript
interface DeleteResponse {
  success: boolean;
  message: string;
}

const result = await BackendClient.delete<DeleteResponse>(
  '/api/contacts/456'
);
```

## Advanced Usage

### Custom Headers

```typescript
const response = await BackendClient.post<any>(
  '/api/endpoint',
  { data: 'example' },
  {
    headers: {
      'X-Custom-Header': 'value',
      'X-Request-ID': crypto.randomUUID(),
    },
  }
);
```

### Query Parameters

```typescript
// Manual construction
const params = new URLSearchParams({
  period: '202501',
  type: 'compras',
  limit: '50',
});

const documents = await BackendClient.get<any>(
  `/api/tax/documents?${params.toString()}`
);
```

### Error Handling

```typescript
try {
  const data = await BackendClient.get<any>('/api/endpoint');
  return { success: true, data };
} catch (error) {
  if (error instanceof Error) {
    console.error('Backend error:', error.message);
    return { success: false, error: error.message };
  }
  return { success: false, error: 'Unknown error' };
}
```

## Using in Services

The recommended pattern is to use `BackendClient` within service classes:

```typescript
// services/tax/tax-document.service.ts
import { BackendClient } from '@/lib/backend-client';

export class TaxDocumentService {
  static async syncDocuments(companyId: string, period: string) {
    console.log('[Tax Document Service] Syncing documents');

    const response = await BackendClient.post<SyncResponse>(
      '/api/tax/documents/sync',
      {
        company_id: companyId,
        period,
      }
    );

    console.log(`[Tax Document Service] Synced ${response.total} documents`);
    return response;
  }

  static async getDocument(documentId: string) {
    console.log('[Tax Document Service] Fetching document');

    return BackendClient.get<Document>(
      `/api/tax/documents/${documentId}`
    );
  }
}
```

## API Reference

### Static Methods

#### `getBaseUrl(): string`

Returns the configured backend URL.

```typescript
const url = BackendClient.getBaseUrl();
// "http://localhost:8000"
```

#### `getUrl(endpoint: string): string`

Constructs the full URL for an endpoint.

```typescript
const url = BackendClient.getUrl('/api/sii/login');
// "http://localhost:8000/api/sii/login"
```

#### `get<T>(endpoint: string, options?: RequestInit): Promise<T>`

Makes a GET request.

**Parameters:**
- `endpoint` - API endpoint path (e.g., `/api/companies/123`)
- `options` - Optional fetch options (headers, etc.)

**Returns:** Promise of type `T`

**Throws:** Error if request fails

#### `post<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T>`

Makes a POST request.

**Parameters:**
- `endpoint` - API endpoint path
- `body` - Request body (will be JSON stringified)
- `options` - Optional fetch options

**Returns:** Promise of type `T`

**Throws:** Error if request fails

#### `put<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T>`

Makes a PUT request.

#### `patch<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T>`

Makes a PATCH request.

#### `delete<T>(endpoint: string, options?: RequestInit): Promise<T>`

Makes a DELETE request.

## Examples

See `backend-client.example.ts` for comprehensive usage examples including:

1. Simple GET request
2. POST with body
3. PUT for update
4. DELETE request
5. PATCH for partial update
6. GET with query parameters
7. Custom headers
8. Using in service classes
9. Error handling patterns
10. URL debugging

## Logging

All requests are automatically logged:

```
[Backend Client] GET http://localhost:8000/api/companies/123
[Backend Client] POST http://localhost:8000/api/sii/login
```

Errors are also logged:

```
[Backend Client] POST http://localhost:8000/api/sii/login failed: Unauthorized
```

## Error Format

All errors are thrown as `Error` instances with descriptive messages:

```typescript
throw new Error('Backend error: 404 Not Found');
throw new Error('Backend error: 500 Internal Server Error');
```

The error message includes:
- HTTP status code
- Status text
- Original error text from backend (if available)

## Best Practices

1. ✅ **Always use type parameters** for type-safe responses
2. ✅ **Use in services** rather than directly in components/routes
3. ✅ **Handle errors** with try/catch blocks
4. ✅ **Log operations** in service methods
5. ✅ **Use query parameters** for GET requests with filters
6. ✅ **Centralize endpoints** - consider creating endpoint constants
7. ❌ **Don't bypass** - Always use BackendClient for backend-v2 calls
8. ❌ **Don't hardcode URLs** - Use the centralized configuration

## Migration Guide

If you have existing code calling backend-v2 directly:

**Before:**
```typescript
const response = await fetch('http://localhost:8000/api/sii/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ rut, dv, password }),
});
const data = await response.json();
```

**After:**
```typescript
const data = await BackendClient.post<SIILoginResponse>(
  '/api/sii/login',
  { rut, dv, password }
);
```

Benefits:
- 50% less code
- Type-safe response
- Automatic error handling
- Centralized URL configuration
- Automatic logging
