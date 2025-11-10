# Expenses Implementation - Phase 1: Database Models

## ✅ Completed

### 1. Database Model (`Expense`)
**File:** `backend/app/db/models/expenses.py`

**Features:**
- Complete expense tracking model with all fields
- Enums for categories and statuses
- Financial fields with auto-calculation of tax (via trigger)
- Approval workflow (draft → pending_approval → approved/rejected)
- OCR support (future)
- Flexible metadata (JSONB)
- File attachments support
- Reimbursement tracking

**Key Fields:**
- `expense_category`: Enum (transport, parking, meals, etc.)
- `total_amount`, `net_amount`, `tax_amount`: Auto-calculated
- `status`: Workflow states
- `receipt_file_url`: For photo/PDF attachments
- `metadata`: JSONB for flexible data

### 2. Pydantic Schemas
**File:** `backend/app/schemas/expenses.py`

**Schemas:**
- `ExpenseCreate` - Creating new expenses
- `ExpenseUpdate` - Updating expenses
- `ExpenseApproval` - Approve/reject workflow
- `ExpenseSubmit` - Submit for approval
- `ExpenseReimbursement` - Mark as reimbursed
- `Expense` - Response schema
- `ExpenseListResponse` - List with pagination
- `ExpenseSummary` - Statistics

### 3. Database Migration
**File:** `backend/supabase/migrations/20251110071509_create_expenses_table.sql`

**Features:**
- Table creation with all constraints
- Check constraints for categories, statuses, currencies
- Indexes for efficient queries
- **Automatic triggers:**
  - Auto-calculate tax amounts (`calculate_expense_tax_trigger`)
  - Auto-update `updated_at` timestamp
  - Auto-set `submitted_at` when status → pending_approval
  - Auto-set `approved_at` when status → approved
- Row Level Security (RLS) policies
- Comments for documentation

### 4. Model Relationships
**Updated files:**
- `backend/app/db/models/__init__.py` - Added Expense exports
- `backend/app/db/models/company.py` - Added `expenses` relationship
- `backend/app/db/models/user.py` - Added `expenses_created` and `expenses_approved`
- `backend/app/db/models/contact.py` - Added `expenses` relationship

---

## ✅ Phase 2: Backend API & Agent Tools (Completed)

### 1. Repository Layer ✅
**File:** [backend/app/repositories/expenses.py](backend/app/repositories/expenses.py)

**Implemented methods:**
- `create()` - Create new expense with all fields
- `get()` - Get expense by ID
- `list()` - List with filters (status, category, date range, search, pagination)
- `update()` - Update draft/requires_info expenses
- `delete()` - Delete draft expenses only
- `submit_for_approval()` - Submit draft → pending_approval
- `approve()` - Approve pending → approved
- `reject()` - Reject pending → rejected
- `request_info()` - Request more info pending → requires_info
- `mark_reimbursed()` - Mark approved expense as reimbursed
- `get_summary()` - Get aggregated statistics

### 2. API Endpoints ✅
**File:** [backend/app/routers/expenses.py](backend/app/routers/expenses.py)

**Implemented endpoints:**
```python
POST   /api/expenses                  # Create expense
GET    /api/expenses                  # List expenses (with filters)
GET    /api/expenses/{id}             # Get expense detail
PUT    /api/expenses/{id}             # Update expense
DELETE /api/expenses/{id}             # Delete expense
POST   /api/expenses/{id}/submit      # Submit for approval
POST   /api/expenses/{id}/approve     # Approve expense
POST   /api/expenses/{id}/reject      # Reject expense
POST   /api/expenses/{id}/request-info # Request more information
POST   /api/expenses/{id}/reimburse   # Mark as reimbursed
GET    /api/expenses/summary/stats    # Get expense summary
```

**Features:**
- Full CRUD with workflow state management
- Multi-field filtering (status, category, dates, search)
- Pagination support
- Company-level authorization
- Comprehensive error handling
- Auto-resolved company_id from user session

**Router registered in:** [backend/app/main.py](backend/app/main.py:128)

### 3. Agent Tools ✅
**File:** [backend/app/agents/tools/tax/expense_tools.py](backend/app/agents/tools/tax/expense_tools.py)

**Implemented tools:**

1. **`create_expense()`** - Register manual expenses via conversation with REQUIRED DOCUMENT UPLOAD
   - **CRITICAL WORKFLOW REQUIREMENT:**
     - ✅ User MUST upload receipt (image/PDF) in conversation first
     - ✅ Agent MUST analyze document with vision/OCR
     - ✅ User MUST confirm or complement extracted information
     - ✅ ONLY THEN can expense be registered
   - **Document Validation:**
     - Checks for attachments in conversation context
     - If no attachments: Returns error with instructions to upload receipt
     - Extracts receipt file metadata (URL, name, MIME type)
     - Automatically attaches receipt file to expense record
   - Categories: transport, parking, meals, office_supplies, utilities, etc.
   - Auto-calculates net_amount and tax_amount (19% IVA)
   - Returns formatted Spanish response with receipt filename
   - Examples:
     - ❌ WRONG: User: "Registra un gasto de taxi por $10,000" → Agent: "Sube el recibo primero"
     - ✅ CORRECT: User uploads photo → Agent analyzes → User confirms → Agent registers expense

2. **`get_expenses()`** - List and search expenses
   - Filters: status, category, date range, limit
   - Returns formatted list with summary
   - Example: "Muéstrame mis gastos del mes"

3. **`get_expense_summary()`** - Get statistics
   - Aggregated totals: count, amount, net, tax
   - Period filtering with defaults (current month)
   - Status filtering (default: approved only)
   - Example: "¿Cuánto IVA puedo recuperar de mis gastos?"

**Integrated into Tax Documents Agent:**
[backend/app/agents/specialized/tax_documents_agent.py](backend/app/agents/specialized/tax_documents_agent.py:60-62)

**Exported from:**
[backend/app/agents/tools/tax/__init__.py](backend/app/agents/tools/tax/__init__.py:10-14)

---

## 📋 Next Steps (Phase 3)

### Frontend UI
**Files to create:**

```typescript
// frontend/src/features/expenses/
├── api/
│   └── expensesApi.ts          # API client
├── hooks/
│   ├── useExpensesQuery.ts     # React Query hooks
│   ├── useCreateExpense.ts
│   └── useApproveExpense.ts
├── ui/
│   ├── ExpensesList.tsx        # List view
│   ├── ExpenseForm.tsx         # Create/Edit form
│   ├── ExpenseCard.tsx         # Expense card
│   └── ExpenseApproval.tsx     # Approval UI
└── constants/
    └── expenseCategories.ts    # Category translations
```

**Category translations:**
```typescript
export const EXPENSE_CATEGORIES = {
  transport: {
    value: "transport",
    label: "Transporte",
    icon: "🚗",
  },
  parking: {
    value: "parking",
    label: "Estacionamiento",
    icon: "🅿️",
  },
  meals: {
    value: "meals",
    label: "Alimentación",
    icon: "🍽️",
  },
  // ... etc
};
```

---

## 🗄️ Database Schema

```sql
expenses (
    id UUID PRIMARY KEY,
    company_id UUID → companies(id),
    created_by_user_id UUID → users(id),

    -- Categorization
    expense_category TEXT CHECK(...),
    expense_subcategory TEXT,

    -- Details
    expense_date DATE,
    description TEXT,
    vendor_name TEXT,
    vendor_rut TEXT,
    receipt_number TEXT,

    -- Financial (auto-calculated via trigger)
    total_amount NUMERIC(12,2),
    has_tax BOOLEAN DEFAULT true,
    net_amount NUMERIC(12,2),     -- auto: total / 1.19
    tax_amount NUMERIC(12,2),     -- auto: total - net
    currency TEXT DEFAULT 'CLP',

    -- Business context
    is_business_expense BOOLEAN DEFAULT true,
    is_reimbursable BOOLEAN DEFAULT false,
    reimbursed BOOLEAN DEFAULT false,
    reimbursement_date DATE,

    -- Associations
    contact_id UUID → contacts(id),
    project_code TEXT,

    -- Workflow
    status TEXT CHECK(...) DEFAULT 'draft',
    approved_by_user_id UUID → users(id),
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,

    -- Attachments
    receipt_file_url TEXT,
    receipt_file_name TEXT,
    receipt_file_size INTEGER,
    receipt_mime_type TEXT,

    -- OCR (future)
    ocr_extracted BOOLEAN DEFAULT false,
    ocr_confidence NUMERIC(5,2),
    ocr_data JSONB DEFAULT '{}',

    -- Metadata
    notes TEXT,
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    -- Timestamps (auto-managed)
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    submitted_at TIMESTAMPTZ
)
```

---

## 🔧 Automatic Triggers

### 1. Tax Calculation
```sql
-- Automatically calculates net_amount and tax_amount
-- when total_amount or has_tax changes
CREATE TRIGGER calculate_expense_tax_trigger
    BEFORE INSERT OR UPDATE OF total_amount, has_tax
    ON expenses
```

**Example:**
- User enters: `total_amount = 10000, has_tax = true`
- Trigger calculates:
  - `net_amount = 8403.36` (10000 / 1.19)
  - `tax_amount = 1596.64` (10000 - 8403.36)

### 2. Workflow Timestamps
```sql
-- Sets submitted_at when status changes to pending_approval
CREATE TRIGGER set_expense_submitted_at_trigger

-- Sets approved_at when status changes to approved
CREATE TRIGGER set_expense_approved_at_trigger
```

---

## 🚀 Usage Examples

### Creating an Expense (API)

```bash
POST /api/expenses
{
  "company_id": "123e4567-...",
  "expense_category": "transport",
  "expense_subcategory": "taxi",
  "expense_date": "2024-11-09",
  "description": "Taxi to client meeting",
  "vendor_name": "Taxi Seguro",
  "total_amount": 10000,
  "has_tax": true,
  "is_reimbursable": true,
  "notes": "Meeting with Cliente ABC",
  "tags": ["urgent", "client-related"],
  "metadata": {
    "attendees": ["Juan Pérez"],
    "meeting_location": "Las Condes"
  }
}
```

**Response:**
```json
{
  "id": "789...",
  "expense_category": "transport",
  "total_amount": 10000,
  "net_amount": 8403.36,  // Auto-calculated
  "tax_amount": 1596.64,  // Auto-calculated
  "status": "draft",
  "created_at": "2024-11-09T..."
}
```

### Creating via Agent (Future)

```
User: "Registra un gasto de taxi por $10,000"

Agent:
✅ Gasto registrado:
- Categoría: Transporte (taxi)
- Monto: $10,000 (IVA incluido)
- Neto: $8,403
- IVA: $1,597
- Estado: Borrador

¿Quieres subirlo para aprobación?
```

---

## 📊 Workflow States

```
draft → pending_approval → approved
                       ↘ rejected
                       ↘ requires_info → pending_approval
```

**State descriptions:**
- `draft` - Being created by user
- `pending_approval` - Submitted, awaiting review
- `approved` - Approved by accountant (included in tax reports)
- `rejected` - Not valid
- `requires_info` - Needs more information

---

## 🔐 Security (RLS Policies)

```sql
-- Users can view expenses from their companies
expenses_view_policy

-- Users can create expenses for their companies
expenses_create_policy

-- Users can update their own draft/requires_info expenses
expenses_update_own_policy

-- Company members can update any expense (for approval)
expenses_update_company_policy
```

---

## 🎯 Integration with Tax System

Approved expenses will be included in:
1. **Monthly tax summaries** - Via `get_documents_summary()` tool
2. **F29 calculations** - Counted in IVA crédito fiscal
3. **Financial reports** - Expense analytics

---

## ✅ Testing Checklist

**Phase 1 (Database) - Complete:**
- [x] Database models created (`expenses.py`)
- [x] Pydantic schemas created (`schemas/expenses.py`)
- [x] Migration created with triggers (`20251110071509_create_expenses_table.sql`)
- [x] Model relationships updated (Company, Profile, Contact)
- [ ] Run migration: `supabase migration up` (pending deployment)
- [ ] Test auto-calculation triggers
- [ ] Test RLS policies

**Phase 2 (Backend API & Agent) - Complete:**
- [x] Repository layer created (`repositories/expenses.py`)
- [x] API endpoints created (`routers/expenses.py`)
- [x] Router registered in main app
- [x] Agent tools created (`agents/tools/tax/expense_tools.py`)
- [x] Tools integrated into Tax Documents Agent
- [x] Document upload requirement implemented (receipt validation)
- [x] Receipt file metadata attached to expenses
- [ ] Test CRUD operations via API
- [ ] Test agent tool integration with document upload workflow
- [ ] Test workflow state transitions

**Phase 3 (Frontend) - Pending:**
- [ ] Create frontend API client
- [ ] Create React Query hooks
- [ ] Create UI components (list, form, card)
- [ ] Create expense category constants with i18n
- [ ] Test full workflow end-to-end

---

## 📚 References

**Backend files:**
- Migration: [backend/supabase/migrations/20251110071509_create_expenses_table.sql](backend/supabase/migrations/20251110071509_create_expenses_table.sql)
- Model: [backend/app/db/models/expenses.py](backend/app/db/models/expenses.py)
- Schema: [backend/app/schemas/expenses.py](backend/app/schemas/expenses.py)
- Repository: [backend/app/repositories/expenses.py](backend/app/repositories/expenses.py)
- Router: [backend/app/routers/expenses.py](backend/app/routers/expenses.py)
- Agent tools: [backend/app/agents/tools/tax/expense_tools.py](backend/app/agents/tools/tax/expense_tools.py)

**Related models:**
- [backend/app/db/models/company.py](backend/app/db/models/company.py) - `expenses` relationship
- [backend/app/db/models/user.py](backend/app/db/models/user.py) - `expenses_created`, `expenses_approved`
- [backend/app/db/models/contact.py](backend/app/db/models/contact.py) - `expenses` relationship
