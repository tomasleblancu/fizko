# Onboarding Configuration

This directory contains centralized configuration files for the onboarding flow.

## Files

### `setup-questions.tsx`

Centralized configuration for all company setup onboarding questions.

**To modify questions:**

1. Open `setup-questions.tsx`
2. Edit the `setupQuestions` array
3. Questions will automatically appear in the order defined

**Question structure:**

```typescript
{
  key: 'field_name',              // Must match CompanySettingsUpdate interface
  title: 'Question text',          // Main question shown to user
  description: 'Help text',        // Subtext explaining the question
  type: 'boolean' | 'text',        // Optional, defaults to 'boolean'
  placeholder: 'Text...',          // For text questions only
  maxLength: 500,                  // For text questions only
  icon: <svg>...</svg>             // React element for icon
}
```

**Question types:**

- **`boolean`** (default): Shows Sí/No/No estoy seguro buttons
  - Auto-advances to next question after selection
  - Best for yes/no questions

- **`text`**: Shows textarea input
  - Requires manual "Continuar" button click
  - Best for free-form text responses
  - Supports `placeholder` and `maxLength` props

## Examples

### Adding a new boolean question:

```typescript
{
  key: 'has_bank_accounts',
  title: '¿Tiene cuentas bancarias comerciales?',
  description: 'Cuentas corrientes o de ahorro para su negocio.',
  icon: (
    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  ),
}
```

### Adding a new text question:

```typescript
{
  key: 'business_goals',
  title: '¿Cuáles son tus metas para este año?',
  description: 'Comparte tus objetivos de negocio para este período.',
  type: 'text',
  placeholder: 'Escribe tus metas aquí...',
  maxLength: 300,
  icon: (
    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
}
```

### Reordering questions:

Simply change the order of questions in the array:

```typescript
export const setupQuestions: SetupQuestion[] = [
  importExportQuestion,    // Move this first
  employeesQuestion,       // Then this
  leaseQuestion,           // Then this
  descriptionQuestion,     // Last
];
```

## Backend Sync Required

When adding new questions, you must also:

1. **Update the database model**: Add field to `CompanySettings` in `backend/app/db/models/company.py`
2. **Create migration**: Add new column in `backend/supabase/migrations/`
3. **Update API schemas**: Add field to `CompanySettingsUpdate` in `backend/app/routers/companies/settings.py`
4. **Update frontend types**: Add field to `CompanySettingsUpdate` in `frontend/src/shared/hooks/useCompanySettings.ts`

## Tips

- Keep questions short and focused
- Use clear, conversational language
- Provide helpful descriptions
- Order questions from most to least important
- Group related questions together
- Use boolean questions for quick setup
- Use text questions sparingly (they slow down the flow)
