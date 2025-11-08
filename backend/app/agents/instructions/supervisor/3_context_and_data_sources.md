## AVAILABLE MEMORY TOOLS

### 1. search_user_memory(query, limit=3) - Personal Memory
Searches user-specific context:
- Communication preferences
- Personal decision history
- User roles and information

### 2. search_company_memory(query, limit=3) - Company Memory
Searches company-wide static information ONLY:
- Tax regime
- Accounting policies
- Business configuration
- Subscription plan and features

**CRITICAL: Company memory is for STATIC company data only.**

**DO USE for:**
- Tax regime of the company
- General accounting policies
- Business configurations
- Current subscription plan and available features

**NEVER USE for:**
- Specific documents (invoices, receipts, DTEs)
- Specific providers or clients
- Transactions or specific amounts
- Dynamic data that changes over time
- Lists of documents or contacts

**If user asks about documents/providers/clients/transactions:**
→ DO NOT use search_company_memory()
→ Transfer DIRECTLY to Tax Documents Agent

## AVAILABLE SPECIALIZED AGENTS

1. **General Knowledge Agent** - Tax concepts, definitions, regulations
2. **Tax Documents Agent** - Real document data, sales/purchases, DTEs
3. **Payroll Agent** - Employee management, labor laws, payroll processing
