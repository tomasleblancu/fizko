# Company Setup Edge Function

Edge function that completes initial company setup after SII authentication.

## Overview

This function is called when a user completes the onboarding wizard after authenticating with SII. It performs two main operations:

1. **Save Company Settings** - Stores answers from the setup questionnaire
2. **Initialize Calendar** - Creates company_events for mandatory tax events

## Flow

```
User completes setup form
    ↓
POST /functions/v1/company-setup
    ↓
1. Verify user authentication
2. Verify user has access to company
3. Save company settings (upsert)
4. Mark setup as complete
5. Initialize calendar (create company_events)
    ↓
Return success + created events count
```

## Request

```typescript
POST /functions/v1/company-setup

Headers:
  Authorization: Bearer <supabase_jwt_token>
  Content-Type: application/json

Body:
{
  "company_id": "uuid",
  "settings": {
    "has_formal_employees": true | false | null,
    "has_lease_contracts": true | false | null,
    "has_imports": true | false | null,
    "has_exports": true | false | null,
    "has_bank_loans": true | false | null,
    "business_description": "string | null"
  },
  "selected_template_ids": ["uuid1", "uuid2"] // Optional: additional templates to enable
}
```

## Response

**Success (200):**
```json
{
  "success": true,
  "settings_id": "uuid",
  "company_events_created": 5,
  "message": "Setup completado exitosamente"
}
```

**Error (400/401/403/500):**
```json
{
  "success": false,
  "error": "Error message"
}
```

## What it does

### 1. Save Company Settings

- Checks if settings already exist for the company
- If exists: Updates existing record
- If new: Creates new record
- Always sets:
  - `is_initial_setup_complete = true`
  - `initial_setup_completed_at = <current timestamp>`

### 2. Initialize Calendar

- Fetches all mandatory event templates (`is_mandatory = true`)
- Optionally includes additional templates from `selected_template_ids`
- Checks for existing company_events to avoid duplicates
- Creates company_events for all templates that don't have one yet
- Each company_event is created with `is_enabled = true`

## Database Tables

### company_settings

Stores company configuration from setup wizard:

```sql
company_settings (
  id uuid PRIMARY KEY,
  company_id uuid REFERENCES companies(id),
  has_formal_employees boolean,
  has_lease_contracts boolean,
  has_imports boolean,
  has_exports boolean,
  has_bank_loans boolean,
  business_description text,
  is_initial_setup_complete boolean,
  initial_setup_completed_at timestamptz,
  created_at timestamptz,
  updated_at timestamptz
)
```

### company_events

Links companies to event templates:

```sql
company_events (
  id uuid PRIMARY KEY,
  company_id uuid REFERENCES companies(id),
  event_template_id uuid REFERENCES event_templates(id),
  is_enabled boolean,
  created_at timestamptz
)
```

### event_templates

Master table of tax event types:

```sql
event_templates (
  id uuid PRIMARY KEY,
  code text UNIQUE,
  name text,
  is_mandatory boolean,  -- Auto-enabled for all companies if true
  ...
)
```

## Example Usage (Frontend)

```typescript
import { createClient } from '@/lib/supabase/client';

const supabase = createClient();

// Get session token
const { data: { session } } = await supabase.auth.getSession();

// Call edge function
const response = await fetch(
  `${supabaseUrl}/functions/v1/company-setup`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      company_id: 'uuid',
      settings: {
        has_formal_employees: true,
        has_lease_contracts: false,
        has_imports: false,
        has_exports: false,
        has_bank_loans: true,
        business_description: 'Software development company',
      },
      // Optional: enable specific templates beyond mandatory ones
      selected_template_ids: ['optional-template-uuid'],
    }),
  }
);

const result = await response.json();
console.log(result);
// { success: true, settings_id: "...", company_events_created: 5, ... }
```

## Error Handling

The function handles these error cases:

- **401 Unauthorized** - No auth token or invalid token
- **403 Forbidden** - User doesn't have access to the specified company
- **400 Bad Request** - Missing required fields (company_id)
- **500 Internal Server Error** - Database errors or unexpected exceptions

All errors are logged to console with the `[Company Setup]` prefix.

## Deployment

Deploy using Supabase CLI:

```bash
supabase functions deploy company-setup
```

Or deploy all functions:

```bash
supabase functions deploy
```

## Related Files

- [frontend/src/app/onboarding/setup/page.tsx](../../../../frontend/src/app/onboarding/setup/page.tsx) - Setup wizard UI
- [frontend/src/config/setup-questions.tsx](../../../../frontend/src/config/setup-questions.tsx) - Question definitions
- [frontend/src/services/calendar/calendar.service.ts](../../../../frontend/src/services/calendar/calendar.service.ts) - Calendar service (old direct Supabase implementation)

## Migration Notes

This edge function replaces the direct Supabase calls previously made from the frontend setup page. Benefits:

1. **Security** - Uses service role key, bypasses RLS restrictions
2. **Atomicity** - Settings + calendar initialization in one transaction
3. **Validation** - Server-side validation of company access
4. **Consistency** - Centralized business logic
5. **Auditability** - Server-side logging of setup completion
