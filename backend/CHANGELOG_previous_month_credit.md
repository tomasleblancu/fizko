# Form29 Previous Month Credit Implementation

## Summary

Implemented previous month credit (remanente de crédito fiscal) functionality in Form29 draft generation. This ensures that negative IVA balances from previous months are properly carried forward as credits.

## Changes Made

### 1. Form29Service (`app/services/form29/service.py`)

**Lines 70, 81, 87, 101, 121, 167, 175**

- Extract `previous_month_credit` from TaxSummary
- Apply credit to net_iva calculation: `net_iva = iva_collected - iva_paid - previous_month_credit`
- Include `previous_month_credit` in returned dictionary for transparency
- Log previous month credit application
- Filter out `previous_month_credit` before passing to Form29 model (not stored as separate field)

**Before:**
```python
net_iva = iva_collected - iva_paid
```

**After:**
```python
previous_month_credit = Decimal(str(summary.previous_month_credit or 0))
net_iva = iva_collected - iva_paid - previous_month_credit
```

### 2. TaxSummaryRepository (`app/repositories/tax/tax_summary.py`)

**Lines 12, 290-368**

- Added Form29 import
- Extended `_get_previous_month_credit()` method to search both Form29 and Form29SIIDownload tables
- **Priority logic**:
  1. First checks Form29 table for confirmed/submitted/paid drafts with negative net_iva
  2. Falls back to Form29SIIDownload for real SII forms (código 077)

**Before:**
```python
# Only searched Form29SIIDownload table
f29_stmt = select(Form29SIIDownload).where(...)
```

**After:**
```python
# FIRST: Check Form29 drafts
draft_stmt = select(Form29).where(
    Form29.status.in_(['confirmed', 'submitted', 'paid'])
)
if draft_f29 and draft_f29.net_iva < 0:
    return abs(float(draft_f29.net_iva))

# FALLBACK: Query Form29SIIDownload
f29_stmt = select(Form29SIIDownload).where(...)
```

## How It Works

### Credit Calculation Flow

1. **TaxSummaryRepository** calculates tax summary for current period (e.g., January 2025)
2. Calls `_get_previous_month_credit()` to find December 2024 credit
3. Searches Form29 table first for any confirmed/submitted/paid drafts
   - If found and `net_iva < 0`, uses `abs(net_iva)` as credit
4. If no draft found, searches Form29SIIDownload for código 077
5. Returns credit amount (or None if not found)

### Credit Application

1. **Form29Service** uses TaxSummary to get all values including `previous_month_credit`
2. Calculates net_iva: `iva_collected - iva_paid - previous_month_credit`
3. Returns calculated values with `previous_month_credit` for transparency
4. When creating Form29 draft, filters out `previous_month_credit` (not a model field)
5. The credit is reflected in the lower `net_iva` value

### Example

**Scenario: December 2024 had negative net_iva (credit to carry forward)**

```
December 2024:
  IVA Collected: $1,000,000
  IVA Paid: $1,500,000
  Net IVA: -$500,000  (negative = credit)

January 2025 (with credit applied):
  IVA Collected: $2,000,000
  IVA Paid: $1,200,000
  Previous Month Credit: $500,000
  Net IVA: $2,000,000 - $1,200,000 - $500,000 = $300,000
```

## Testing

Created two test scripts:

### `scripts/test_previous_month_credit.py`
- Tests TaxSummaryRepository credit lookup
- Tests Form29Service credit application
- Verifies calculation logic
- Tests months with no credit

### `scripts/test_form29_generation.py`
- Tests full F29 draft generation for all companies
- Verifies skip logic for existing drafts
- Confirms previous month credit is applied in logs

Both tests pass successfully:
```bash
.venv/bin/python scripts/test_previous_month_credit.py
# ✅ All tests completed successfully!

.venv/bin/python scripts/test_form29_generation.py service --year 2025 --month 1
# Created: 2, Skipped: 0, Errors: 0
```

## Database Schema

### Migration: `20250110120000_add_previous_month_credit_to_form29.sql`

Added explicit `previous_month_credit` field to Form29 model:

```sql
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS previous_month_credit NUMERIC(15, 2) DEFAULT 0 NOT NULL;

CREATE INDEX IF NOT EXISTS idx_form29_previous_month_credit
ON form29(previous_month_credit)
WHERE previous_month_credit > 0;
```

**Benefits of storing the field:**
1. **Traceability**: Explicit record of credit applied to each F29
2. **Auditability**: Can verify calculations months/years later
3. **Debugging**: Easier to identify issues with credit application
4. **Reporting**: Can query forms by credit amount

The credit is:
1. **Calculated** from previous period's net_iva (if Form29 draft)
2. **Extracted** from código 077 (if Form29SIIDownload)
3. **Stored** in `previous_month_credit` field
4. **Applied** to current period's net_iva calculation

## Logging

Enhanced logging to show credit application:

```
Calculated F29 for company <id>, period 2025-01:
  Revenue=1000000, IVA collected=190000, IVA paid=114000,
  Previous month credit=50000, Net IVA=26000

Calculated F29 values for 2025-01:
  Net IVA = $26,000, Previous month credit applied = $50,000
```

## Compatibility

- Maintains homogeneity with `/api/tax-summary` endpoint (uses same TaxSummaryRepository)
- Works with both Form29 drafts and Form29SIIDownload records
- Backwards compatible (credit defaults to 0 if not found)
- No breaking changes to existing code

## Related Files

- `backend/app/services/form29/service.py` - Form29 business logic (lines 70, 81, 87, 101, 121, 167, 174-180)
- `backend/app/repositories/tax/tax_summary.py` - Tax calculation repository (lines 12, 290-368)
- `backend/app/db/models/form29.py` - Form29 model (line 71: added previous_month_credit field)
- `backend/app/db/models/form29_sii_download.py` - Form29SIIDownload model
- `backend/app/infrastructure/celery/tasks/forms/form29.py` - Celery task for batch generation
- `backend/supabase/migrations/20250110120000_add_previous_month_credit_to_form29.sql` - Migration file

## Example Output

From test run on Feb 2025 with Jan 2025 credit:

```
Calculated F29 for company a5cd89cf-38e5-48bb-ace0-52e65c56eee0, period 2025-02:
  Revenue=0, IVA collected=0, IVA paid=0,
  Previous month credit=2,415,904, Net IVA=-2,415,904

Database verification:
{
  "company_id": "a5cd89cf-38e5-48bb-ace0-52e65c56eee0",
  "period_year": 2025,
  "period_month": 2,
  "previous_month_credit": "2415904.00",
  "iva_to_pay": "0.00",
  "iva_credit": "0.00",
  "net_iva": "-2415904.00",
  "status": "draft"
}
```

## Date

2025-11-10
