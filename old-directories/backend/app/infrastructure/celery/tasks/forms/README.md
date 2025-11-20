# Forms Celery Tasks

This module contains Celery tasks related to tax form management.

## Tasks

### Form29 Draft Generation

**File:** [form29.py](./form29.py)

#### `forms.generate_f29_drafts_all_companies`

Generates Form29 drafts for all active companies for a specific period.

**Parameters:**
- `period_year` (int, optional) - Year for the F29 period (defaults to previous month)
- `period_month` (int, optional) - Month for the F29 period (1-12, defaults to previous month)
- `auto_calculate` (bool, default=True) - Whether to auto-calculate values from tax documents

**Returns:**
```python
{
    "success": bool,
    "period_year": int,
    "period_month": int,
    "total_companies": int,
    "created": int,
    "skipped": int,
    "errors": int,
    "error_details": List[Dict],
    "execution_time_seconds": float
}
```

**Usage:**

```python
from app.infrastructure.celery.tasks.forms import generate_f29_drafts_all_companies

# Generate drafts for January 2025
result = generate_f29_drafts_all_companies.delay(period_year=2025, period_month=1)

# Generate drafts for previous month (auto-detect)
result = generate_f29_drafts_all_companies.delay()
```

**Features:**
- Auto-detects previous month if parameters not provided
- Uses `Form29Service` for business logic
- Auto-calculates from `TaxSummaryRepository` for homogeneity with `/api/tax-summary`
- Handles errors per company gracefully
- Retries on database/connection errors
- Comprehensive logging and error reporting

**See Also:**
- [Form29 Service](../../../services/form29/README.md)
- [Form29 Generation System](../../../../docs/FORM29_GENERATION_SYSTEM.md)
- [Test Script](../../../../scripts/test_form29_generation.py)
