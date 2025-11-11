# Form29 Draft Tracking System

## Overview

The Form29 model has been enhanced to support full lifecycle tracking of F29 tax form drafts, from creation through validation, confirmation, submission, and payment.

## Database Schema Changes

### New Fields

#### User Tracking
- `created_by_user_id` (UUID, nullable) - References `auth.users.id`
- `confirmed_by_user_id` (UUID, nullable) - References `auth.users.id`

#### Revision System
- `revision_number` (INTEGER, default: 1) - Allows multiple drafts of the same period
- **Unique constraint updated**: `(company_id, period_year, period_month, revision_number)`

#### Validation
- `validation_status` (TEXT, default: 'pending') - Values: `pending`, `valid`, `invalid`, `warning`
- `validation_errors` (JSONB, default: `[]`) - Array of validation error objects

#### Confirmation
- `confirmed_at` (TIMESTAMPTZ, nullable) - When user confirmed the draft
- `confirmation_notes` (TEXT, nullable) - Optional user notes

#### Payment Tracking
- `payment_status` (TEXT, default: 'unpaid') - Values: `unpaid`, `pending`, `paid`, `partially_paid`, `overdue`
- `payment_date` (DATE, nullable) - When payment was made
- `payment_reference` (TEXT, nullable) - SII payment reference number
- `payment_amount_cents` (INTEGER, nullable) - Actual amount paid (may differ from calculated)

#### SII Reconciliation
- `sii_download_id` (UUID, nullable) - References `form29_sii_downloads.id`

#### Additional Metadata
- `metadata` (JSONB, default: `{}`) - For future extensibility

### Updated Status Values

The `status` field now supports:
- `draft` - Initial state, being edited
- `validated` - Passed validation checks
- `confirmed` - User confirmed, ready to submit
- `submitted` - Submitted to SII
- `paid` - Payment confirmed
- `cancelled` - Superseded by newer revision

## Draft Lifecycle

```
1. draft → User creates/edits form
   ↓
2. validated → System validates calculations
   ↓
3. confirmed → User confirms for submission
   ↓
4. submitted → Form submitted to SII
   ↓
5. paid → Payment confirmed
```

## Helper Functions (PostgreSQL)

### `get_latest_form29_revision(company_id, year, month)`
Returns the latest non-cancelled revision for a given period.

```sql
SELECT * FROM get_latest_form29_revision(
    'company-uuid'::uuid,
    2025,
    1
);
```

### `create_form29_revision(form29_id, user_id)`
Creates a new revision by copying an existing form and marking the old one as cancelled.

```sql
SELECT create_form29_revision(
    'form29-uuid'::uuid,
    'user-uuid'::uuid
);
```

Returns the UUID of the newly created revision.

## SQLAlchemy Model Properties

The Form29 model includes helpful properties:

### Status Checks
- `is_draft` - Check if form is still a draft
- `is_validated` - Check if form has been validated
- `is_confirmed` - Check if form has been confirmed
- `is_submitted` - Check if form has been submitted to SII
- `is_paid` - Check if payment has been completed
- `is_cancelled` - Check if form has been cancelled

### Permission Checks
- `can_be_edited` - Check if form can still be edited
- `can_be_confirmed` - Check if form is ready to be confirmed
- `can_be_submitted` - Check if form is ready to be submitted to SII

### Data Checks
- `has_validation_errors` - Check if form has validation errors
- `is_linked_to_sii` - Check if form is linked to an SII download

### Utilities
- `period_display` - Get period in display format (YYYY-MM)

## Relationships

### Form29 Model
- `company` - Link to Company
- `sii_download_link` - New: Form29 → Form29SIIDownload (via `sii_download_id`)
- `sii_download_legacy` - Legacy: Form29SIIDownload → Form29 (via `form29_id`)

### Form29SIIDownload Model
- `company` - Link to Company
- `form29` - Legacy: Points to Form29 via `form29_id`
- `linked_form29` - New: Form29 points to this SII download via `sii_download_id`

## Indexes

Performance indexes have been added for common queries:
- `ix_form29_active_drafts` - Active drafts by company/period
- `ix_form29_ready_for_submission` - Forms ready for submission
- `ix_form29_payment_status` - Payment tracking queries
- `ix_form29_created_by` - User activity tracking
- `ix_form29_sii_link` - SII reconciliation queries

## Usage Examples

### Create a new draft
```python
form29 = Form29(
    company_id=company_id,
    period_year=2025,
    period_month=1,
    revision_number=1,
    created_by_user_id=user_id,
    status="draft",
    validation_status="pending",
    payment_status="unpaid",
    # ... other fields
)
db.add(form29)
await db.commit()
```

### Validate a draft
```python
# Run validation logic
errors = validate_form29(form29)

if errors:
    form29.validation_status = "invalid"
    form29.validation_errors = errors
else:
    form29.validation_status = "valid"
    form29.status = "validated"

await db.commit()
```

### Confirm a draft
```python
if form29.can_be_confirmed:
    form29.status = "confirmed"
    form29.confirmed_by_user_id = user_id
    form29.confirmed_at = datetime.now(timezone.utc)
    form29.confirmation_notes = "Ready for submission"
    await db.commit()
```

### Submit to SII
```python
if form29.can_be_submitted:
    # Submit to SII...
    folio = await submit_to_sii(form29)

    form29.status = "submitted"
    form29.folio = folio
    form29.submission_date = datetime.now(timezone.utc)
    await db.commit()
```

### Record payment
```python
form29.payment_status = "paid"
form29.payment_date = date.today()
form29.payment_reference = "SII-REF-12345"
form29.payment_amount_cents = 150000  # $150.000 CLP
form29.status = "paid"
await db.commit()
```

### Link to SII download
```python
# After downloading from SII
sii_download = await get_sii_download_by_folio(folio)
form29.sii_download_id = sii_download.id
await db.commit()
```

### Create a new revision
```python
# Using SQL function
new_id = await db.scalar(
    text("SELECT create_form29_revision(:form29_id, :user_id)"),
    {"form29_id": form29.id, "user_id": user_id}
)

# Or manually
latest_revision = await db.scalar(
    select(func.max(Form29.revision_number))
    .where(
        Form29.company_id == company_id,
        Form29.period_year == year,
        Form29.period_month == month
    )
)

new_form29 = Form29(
    company_id=company_id,
    period_year=year,
    period_month=month,
    revision_number=(latest_revision or 0) + 1,
    created_by_user_id=user_id,
    # Copy other fields from previous revision...
)
```

## Migration Applied

Migration file: `20250110000000_enhance_form29_draft_tracking.sql`
- Applied to staging: ✅
- Applied to production: ⏳ (pending)

## Next Steps

1. Update Form29 service layer to use new fields
2. Add validation logic for Form29 drafts
3. Create API endpoints for:
   - Creating drafts
   - Validating drafts
   - Confirming drafts
   - Creating revisions
4. Update frontend to support draft workflow
5. Add tests for draft lifecycle
