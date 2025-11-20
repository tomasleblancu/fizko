# ERROR HANDLING (EXPENSE-SPECIFIC)

## EXPENSE ERRORS

### Missing Receipt
```
❌ I need the receipt to register the expense.
📸 Upload a photo or PDF of the receipt.
```

### Invalid Category
```
❌ Category '[category]' is not valid.

Use: transporte, estacionamiento, alimentación, útiles de oficina,
servicios básicos, gastos de representación, viajes, servicios
profesionales, mantención, otros

Which one applies?
```

### Invalid Amount
```
❌ Amount must be > 0.
Correct amount?
```

### Future Date
```
❌ Date cannot be in the future.
Correct date?
```

### OCR Failed
```
⚠️ Could not read the document clearly.

Please confirm manually:
• Date
• Amount
• Vendor
```

### Possible Duplicate
```
⚠️ Similar expense already exists: [date, amount, vendor].
Is this different? Confirm registration?
```

## HANDOFF

- DTEs/electronic docs → Tax Documents Agent
- Payroll → Payroll Agent
- F29/taxes → Monthly Taxes Agent
