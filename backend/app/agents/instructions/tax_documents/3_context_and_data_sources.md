## AVAILABLE TOOLS

### 1. get_documents_summary(month, year)
Get summaries and totals for a period.

Returns:
- Total sales and purchases for the period
- VAT calculations (tax debits, tax credits, VAT payable)

If month/year not specified, uses current month.

### 2. get_documents(document_type, rut, folio, start_date, end_date, limit)
Search for specific documents.

All parameters are optional:
- `document_type`: "sales" (sales), "purchases" (purchases), "both" (both)
- `rut`: Search by provider or client RUT
- `folio`: Search by folio number
- `start_date` / `end_date`: Date range (YYYY-MM-DD format)
- `limit`: Maximum documents (default 20)

### 3. FileSearchTool (when PDFs uploaded)
Search through uploaded PDF documents with up to 5 results.

## DATA SOURCES

- Company purchase documents (database)
- Company sales documents (database)
- Honorarios receipts (database)
- Uploaded PDF documents (when provided by user)
