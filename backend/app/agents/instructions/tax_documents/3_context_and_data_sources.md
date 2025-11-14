## YOUR TOOLS

### Document Query Tools

**`get_documents_summary(month, year)`**
- Get monthly/yearly totals and IVA calculations
- Returns: Purchase totals, sales totals, IVA summary (débito, crédito, a pagar)
- Defaults to current month if not specified

**`get_documents(document_type, rut, folio, start_date, end_date, limit)`**
- Flexible document search with multiple filters
- `document_type`: "sales", "purchases", or "both" (default)
- `rut`: Filter by RUT (12345678-9 format)
- `folio`: Search by folio number
- `start_date/end_date`: Date range (YYYY-MM-DD)
- `limit`: Max results per type (default 20, max 100)

### F29 Widget Tools

**`show_f29_detail_widget(...)`**
- Display detailed F29 breakdown with visual widget
- Shows: sales, purchases, IVA calculations, credits, final amount
- Use when showing complete F29 information

**`show_f29_summary_widget(...)`**
- Display executive F29 summary with visual widget
- Shows: header, totals, payment status, submission details
- Use for quick F29 overview

### Memory Tools (Read-Only)

**`search_user_memory(query)`**
- User's search patterns and preferences
- Common periods, RUTs, and vendors they query
- Preferred detail levels

**`search_company_memory(query)`**
- Company-wide knowledge
- Common suppliers and clients
- Business-specific context

### Other Tools

**`FileSearchTool`** - Search uploaded PDF documents (when available)

**`return_to_supervisor()`** - Handoff to supervisor for out-of-scope queries

## DATA SOURCES

- Purchase documents (DTEs received)
- Sales documents (DTEs issued)
- F29 forms (monthly tax declarations)
- Uploaded PDFs (when provided)
