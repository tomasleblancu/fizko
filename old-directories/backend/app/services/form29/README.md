# Form29 Service

Business logic layer for Form29 (Chilean F29 tax form) management.

## Overview

This service provides a complete solution for automatic generation, calculation, validation, and management of Form29 drafts. It handles the entire lifecycle from draft creation to submission preparation.

## Components

### Form29Service

Main service class that provides all business logic for Form29 management.

**File:** [service.py](./service.py)

## Key Features

### 1. Automatic Calculation
Calculates F29 values from tax documents (DTEs) stored in the database:
- Aggregates sales (facturas, boletas) by period
- Aggregates purchases (facturas de compra) by period
- Calculates IVA débito fiscal (sales tax)
- Calculates IVA crédito fiscal (purchase tax)
- Computes net IVA (amount to pay or credit)

### 2. Draft Management
- Create drafts for specific companies and periods
- Support for multiple revisions of the same period
- Automatic revision numbering
- Track who created each draft

### 3. Validation
Validates drafts before confirmation:
- Period not in future
- All values non-negative
- IVA calculations correct
- Stores validation errors for user review

### 4. Batch Processing
Generate drafts for all active companies in a single operation:
- Processes companies sequentially
- Handles errors gracefully per company
- Returns comprehensive summary statistics
- Continues processing even if some companies fail

## Usage Examples

### Create Draft for Single Company

```python
from app.config.database import get_db
from app.services.form29 import Form29Service

async with get_db() as db:
    service = Form29Service(db)

    form29, is_new = await service.create_draft_for_period(
        company_id=company_id,
        period_year=2025,
        period_month=1,
        created_by_user_id=user_id,  # Optional
        auto_calculate=True  # Calculate from tax documents
    )

    print(f"Net IVA: ${form29.net_iva:,.0f}")
```

### Calculate Values from Documents

```python
async with get_db() as db:
    service = Form29Service(db)

    values = await service.calculate_f29_from_documents(
        company_id=company_id,
        period_year=2025,
        period_month=1
    )

    print(f"Total Sales: ${values['total_sales']:,.0f}")
    print(f"Total Purchases: ${values['total_purchases']:,.0f}")
    print(f"Net IVA: ${values['net_iva']:,.0f}")
```

### Validate Draft

```python
async with get_db() as db:
    service = Form29Service(db)

    is_valid, errors = await service.validate_draft(form29_id)

    if is_valid:
        print("✅ Draft is valid!")
    else:
        print("❌ Validation errors:")
        for error in errors:
            print(f"  - {error['field']}: {error['message']}")
```

### Confirm Draft

```python
async with get_db() as db:
    service = Form29Service(db)

    try:
        form29 = await service.confirm_draft(
            form29_id=form29_id,
            confirmed_by_user_id=user_id,
            confirmation_notes="Reviewed and approved for submission"
        )
        print(f"✅ Draft confirmed! Status: {form29.status}")
    except ValueError as e:
        print(f"❌ Cannot confirm: {e}")
```

### Generate Drafts for All Companies

```python
async with get_db() as db:
    service = Form29Service(db)

    summary = await service.create_drafts_for_all_companies(
        period_year=2025,
        period_month=1,
        auto_calculate=True
    )

    print(f"Total companies: {summary['total_companies']}")
    print(f"Created: {summary['created']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Errors: {summary['errors']}")

    if summary['error_details']:
        print("\nErrors:")
        for error in summary['error_details']:
            print(f"  - {error['company_name']}: {error['error']}")
```

## Calculation Logic

### Sales Aggregation

```python
# Documents included:
# - FACTURA_VENTA
# - FACTURA_ELECTRONICA
# - FACTURA_EXENTA
# - BOLETA
# - NOTA_CREDITO_VENTA

for document in sales_documents:
    amount = document.total_amount
    tax = document.tax_amount
    net = amount - tax

    if tax > 0:
        taxable_sales += net
        sales_tax += tax
    else:
        exempt_sales += amount

total_sales = taxable_sales + exempt_sales
iva_to_pay = sales_tax
```

### Purchases Aggregation

```python
# Documents included:
# - FACTURA_COMPRA
# - FACTURA_COMPRA_ELECTRONICA
# - NOTA_CREDITO_COMPRA

for document in purchase_documents:
    amount = document.total_amount
    tax = document.tax_amount
    net = amount - tax

    if tax > 0:
        taxable_purchases += net
        purchases_tax += tax

total_purchases = taxable_purchases
iva_credit = purchases_tax
```

### Net IVA Calculation

```python
net_iva = iva_to_pay - iva_credit

# If net_iva > 0: Company owes IVA to SII
# If net_iva < 0: Company has credit for next period
# If net_iva = 0: No payment needed
```

## Validation Rules

### 1. Period Validation
```python
# Cannot create F29 for future periods
today = date.today()
if period_year > today.year or (
    period_year == today.year and period_month > today.month
):
    raise ValidationError("Cannot create F29 for future periods")
```

### 2. Value Validation
```python
# All values must be non-negative
if total_sales < 0:
    raise ValidationError("Total sales cannot be negative")

if total_purchases < 0:
    raise ValidationError("Total purchases cannot be negative")
```

### 3. IVA Calculation Validation
```python
# IVA to pay must equal sales tax
expected_iva_to_pay = sales_tax
if abs(iva_to_pay - expected_iva_to_pay) > 1:
    raise ValidationError("IVA to pay mismatch")

# IVA credit must equal purchases tax
expected_iva_credit = purchases_tax
if abs(iva_credit - expected_iva_credit) > 1:
    raise ValidationError("IVA credit mismatch")

# Net IVA must equal difference
expected_net_iva = iva_to_pay - iva_credit
if abs(net_iva - expected_net_iva) > 1:
    raise ValidationError("Net IVA mismatch")
```

## Error Handling

The service handles errors gracefully:

### Per-Company Errors
When processing multiple companies, errors in one company don't stop processing:

```python
try:
    form29, is_new = await service.create_draft_for_period(...)
    created += 1
except Exception as e:
    errors += 1
    error_details.append({
        "company_id": str(company.id),
        "company_name": company.name,
        "error": str(e)
    })
    # Continue with next company
```

### Calculation Errors
If calculation fails, creates draft with zero values:

```python
try:
    calculated_values = await service.calculate_f29_from_documents(...)
except Exception as e:
    logger.error(f"Error calculating F29 values: {e}")
    calculated_values = {}  # Continue with zeros
```

## Dependencies

- **Repository:** `Form29Repository` for data access
- **Models:** `Form29`, `TaxDocument`, `Company`
- **Database:** SQLAlchemy async session

## Related Documentation

- [Form29 Generation System](../../docs/FORM29_GENERATION_SYSTEM.md) - Complete system documentation
- [Form29 Draft Tracking](../../docs/FORM29_DRAFT_TRACKING.md) - Database schema
- [Form29 Repository](../../repositories/tax/form29.py) - Data access layer

## Testing

See [test_form29_generation.py](../../../scripts/test_form29_generation.py) for testing utilities.

```bash
# Test service directly
python -m scripts.test_form29_generation service --year 2025 --month 1
```

## Future Enhancements

- [ ] Support for partial recalculation (update specific fields only)
- [ ] Integration with SII submission API
- [ ] Automatic payment tracking
- [ ] Email notifications on draft creation
- [ ] Audit log for all changes
- [ ] Support for F29 corrections (rectificatorias)
