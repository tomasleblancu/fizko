-- Create expenses table for manual expense tracking
-- This table is separate from purchase_documents and specifically designed
-- for non-DTE expenses that require manual entry and approval workflow

CREATE TABLE IF NOT EXISTS expenses (
    -- Identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_by_user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE SET NULL,

    -- Expense categorization
    expense_category TEXT NOT NULL CHECK (
        expense_category IN (
            'transport', 'parking', 'meals', 'office_supplies',
            'utilities', 'representation', 'travel',
            'professional_services', 'maintenance', 'other'
        )
    ),
    expense_subcategory TEXT,

    -- Expense details
    expense_date DATE NOT NULL,
    description TEXT NOT NULL,
    vendor_name TEXT,
    vendor_rut TEXT,
    receipt_number TEXT,

    -- Financial information
    total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount > 0),
    has_tax BOOLEAN NOT NULL DEFAULT true,
    net_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'CLP' CHECK (
        currency IN ('CLP', 'USD', 'EUR')
    ),

    -- Business context
    is_business_expense BOOLEAN NOT NULL DEFAULT true,
    is_reimbursable BOOLEAN NOT NULL DEFAULT false,
    reimbursed BOOLEAN NOT NULL DEFAULT false,
    reimbursement_date DATE,

    -- Optional associations
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    project_code TEXT,

    -- Approval workflow
    status TEXT NOT NULL DEFAULT 'draft' CHECK (
        status IN (
            'draft', 'pending_approval', 'approved',
            'rejected', 'requires_info'
        )
    ),
    approved_by_user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,

    -- Document attachments
    receipt_file_url TEXT,
    receipt_file_name TEXT,
    receipt_file_size INTEGER,
    receipt_mime_type TEXT,

    -- OCR / extraction data (future feature)
    ocr_extracted BOOLEAN NOT NULL DEFAULT false,
    ocr_confidence NUMERIC(5, 2) CHECK (
        ocr_confidence IS NULL OR
        (ocr_confidence >= 0 AND ocr_confidence <= 100)
    ),
    ocr_data JSONB DEFAULT '{}'::jsonb,

    -- Notes and metadata
    notes TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    submitted_at TIMESTAMPTZ
);

-- Indexes for efficient queries
CREATE INDEX idx_expenses_company_id ON expenses(company_id);
CREATE INDEX idx_expenses_created_by ON expenses(created_by_user_id);
CREATE INDEX idx_expenses_expense_date ON expenses(expense_date);
CREATE INDEX idx_expenses_status ON expenses(status);
CREATE INDEX idx_expenses_category ON expenses(expense_category);
CREATE INDEX idx_expenses_company_date ON expenses(company_id, expense_date);
CREATE INDEX idx_expenses_company_status ON expenses(company_id, status);

-- Trigger to auto-calculate tax amounts when has_tax is true
CREATE OR REPLACE FUNCTION calculate_expense_tax()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.has_tax THEN
        -- IVA rate is 19% in Chile
        NEW.net_amount := ROUND(NEW.total_amount / 1.19, 2);
        NEW.tax_amount := NEW.total_amount - NEW.net_amount;
    ELSE
        NEW.net_amount := 0;
        NEW.tax_amount := 0;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_expense_tax_trigger
    BEFORE INSERT OR UPDATE OF total_amount, has_tax ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION calculate_expense_tax();

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_expenses_updated_at
    BEFORE UPDATE ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to set submitted_at when status changes to pending_approval
CREATE OR REPLACE FUNCTION set_expense_submitted_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'pending_approval' AND OLD.status = 'draft' AND NEW.submitted_at IS NULL THEN
        NEW.submitted_at := now();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_expense_submitted_at_trigger
    BEFORE UPDATE OF status ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION set_expense_submitted_at();

-- Trigger to set approved_at when status changes to approved
CREATE OR REPLACE FUNCTION set_expense_approved_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'approved' AND OLD.status != 'approved' AND NEW.approved_at IS NULL THEN
        NEW.approved_at := now();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_expense_approved_at_trigger
    BEFORE UPDATE OF status ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION set_expense_approved_at();

-- Row Level Security (RLS)
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view expenses from their companies
CREATE POLICY expenses_view_policy ON expenses
    FOR SELECT
    USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid()
            AND is_active = true
        )
    );

-- Policy: Users can create expenses for their companies
CREATE POLICY expenses_create_policy ON expenses
    FOR INSERT
    WITH CHECK (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid()
            AND is_active = true
        )
        AND created_by_user_id = auth.uid()
    );

-- Policy: Users can update their own draft/requires_info expenses
CREATE POLICY expenses_update_own_policy ON expenses
    FOR UPDATE
    USING (
        created_by_user_id = auth.uid()
        AND status IN ('draft', 'requires_info')
    );

-- Policy: All users from company can update any expense (for approval workflow)
-- Note: Consider adding role checks if you have an accountant role
CREATE POLICY expenses_update_company_policy ON expenses
    FOR UPDATE
    USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid()
            AND is_active = true
        )
    );

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON expenses TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON expenses TO service_role;

-- Comments for documentation
COMMENT ON TABLE expenses IS 'Manual expense tracking for non-DTE documents with approval workflow';
COMMENT ON COLUMN expenses.expense_category IS 'Category of expense for reporting and classification';
COMMENT ON COLUMN expenses.has_tax IS 'Whether the total_amount includes 19% IVA (Chilean tax)';
COMMENT ON COLUMN expenses.net_amount IS 'Auto-calculated net amount (total / 1.19 if has_tax)';
COMMENT ON COLUMN expenses.tax_amount IS 'Auto-calculated tax amount (total - net if has_tax)';
COMMENT ON COLUMN expenses.status IS 'Workflow status: draft -> pending_approval -> approved/rejected';
COMMENT ON COLUMN expenses.is_reimbursable IS 'Whether this expense should be reimbursed to the employee';
COMMENT ON COLUMN expenses.ocr_data IS 'Raw OCR extraction data for future OCR feature';
COMMENT ON COLUMN expenses.metadata IS 'Flexible JSONB field for additional context (attendees, km, etc)';
