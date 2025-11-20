-- =====================================================================
-- Fizko Database Migration - Enhanced Form29 Draft Tracking
-- =====================================================================
-- Description: Enhance form29 table to support full draft lifecycle tracking
-- Version: 1.0
-- Date: 2025-01-10
--
-- Purpose:
-- - Track draft creation, validation, confirmation, and payment
-- - Support multiple revisions of the same period
-- - Link to SII submitted forms for reconciliation
-- - Enable audit trail for form submissions
-- =====================================================================

-- =====================================================================
-- ADD NEW COLUMNS FOR DRAFT TRACKING
-- =====================================================================

-- User tracking
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS confirmed_by_user_id UUID REFERENCES auth.users(id);

-- Draft revision tracking (for multiple drafts of the same period)
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS revision_number INTEGER DEFAULT 1 NOT NULL;

-- Validation tracking
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS validation_status TEXT DEFAULT 'pending'::text NOT NULL,
ADD COLUMN IF NOT EXISTS validation_errors JSONB DEFAULT '[]'::jsonb;

-- Confirmation tracking
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS confirmation_notes TEXT;

-- Payment tracking
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'unpaid'::text NOT NULL,
ADD COLUMN IF NOT EXISTS payment_date DATE,
ADD COLUMN IF NOT EXISTS payment_reference TEXT,
ADD COLUMN IF NOT EXISTS payment_amount_cents INTEGER;

-- Link to SII download (when form is submitted and downloaded)
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS sii_download_id UUID REFERENCES form29_sii_downloads(id);

-- Metadata for additional tracking needs
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- =====================================================================
-- UPDATE EXISTING CONSTRAINTS
-- =====================================================================

-- Drop old status constraint
ALTER TABLE form29 DROP CONSTRAINT IF EXISTS form29_status_check;

-- Add new status constraint with more states
ALTER TABLE form29 ADD CONSTRAINT form29_status_check
    CHECK (status = ANY (ARRAY[
        'draft'::text,           -- Initial state, being edited
        'validated'::text,       -- Passed validation checks
        'confirmed'::text,       -- User confirmed, ready to submit
        'submitted'::text,       -- Submitted to SII
        'paid'::text,            -- Payment confirmed
        'cancelled'::text        -- Cancelled/superseded by newer revision
    ]));

-- Add validation status constraint
ALTER TABLE form29 ADD CONSTRAINT form29_validation_status_check
    CHECK (validation_status = ANY (ARRAY[
        'pending'::text,         -- Not yet validated
        'valid'::text,           -- Passed all validations
        'invalid'::text,         -- Has validation errors
        'warning'::text          -- Has warnings but can proceed
    ]));

-- Add payment status constraint
ALTER TABLE form29 ADD CONSTRAINT form29_payment_status_check
    CHECK (payment_status = ANY (ARRAY[
        'unpaid'::text,          -- No payment made
        'pending'::text,         -- Payment initiated but not confirmed
        'paid'::text,            -- Payment confirmed
        'partially_paid'::text,  -- Partial payment made
        'overdue'::text          -- Payment overdue
    ]));

-- Update unique constraint to include revision number
ALTER TABLE form29 DROP CONSTRAINT IF EXISTS form29_company_period_unique;
ALTER TABLE form29 ADD CONSTRAINT form29_company_period_revision_unique
    UNIQUE (company_id, period_year, period_month, revision_number);

-- =====================================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================================

-- Index for active drafts (most common query)
CREATE INDEX IF NOT EXISTS ix_form29_active_drafts
    ON form29(company_id, period_year, period_month)
    WHERE status = 'draft';

-- Index for validated forms ready for submission
CREATE INDEX IF NOT EXISTS ix_form29_ready_for_submission
    ON form29(company_id, status)
    WHERE status IN ('validated', 'confirmed');

-- Index for payment tracking
CREATE INDEX IF NOT EXISTS ix_form29_payment_status
    ON form29(company_id, payment_status)
    WHERE payment_status IN ('unpaid', 'pending', 'overdue');

-- Index for user activity tracking
CREATE INDEX IF NOT EXISTS ix_form29_created_by
    ON form29(created_by_user_id, created_at);

-- Index for SII reconciliation
CREATE INDEX IF NOT EXISTS ix_form29_sii_link
    ON form29(sii_download_id)
    WHERE sii_download_id IS NOT NULL;

-- =====================================================================
-- UPDATE EXISTING RECORDS
-- =====================================================================

-- Set validation status for existing drafts
UPDATE form29
SET validation_status = 'pending'
WHERE validation_status IS NULL;

-- Set payment status for existing forms
UPDATE form29
SET payment_status = CASE
    WHEN status = 'submitted' THEN 'paid'::text  -- Assume submitted forms were paid
    ELSE 'unpaid'::text
END
WHERE payment_status IS NULL OR payment_status = 'unpaid';

-- =====================================================================
-- HELPER FUNCTIONS
-- =====================================================================

-- Function to get the latest revision for a period
CREATE OR REPLACE FUNCTION get_latest_form29_revision(
    p_company_id UUID,
    p_period_year INTEGER,
    p_period_month INTEGER
)
RETURNS form29 AS $$
    SELECT *
    FROM form29
    WHERE company_id = p_company_id
      AND period_year = p_period_year
      AND period_month = p_period_month
      AND status != 'cancelled'
    ORDER BY revision_number DESC
    LIMIT 1;
$$ LANGUAGE SQL STABLE;

-- Function to create a new revision (copy from existing)
CREATE OR REPLACE FUNCTION create_form29_revision(
    p_form29_id UUID,
    p_user_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_new_id UUID;
    v_new_revision INTEGER;
    v_old_form form29;
BEGIN
    -- Get the existing form
    SELECT * INTO v_old_form
    FROM form29
    WHERE id = p_form29_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Form29 not found: %', p_form29_id;
    END IF;

    -- Get the next revision number
    SELECT COALESCE(MAX(revision_number), 0) + 1
    INTO v_new_revision
    FROM form29
    WHERE company_id = v_old_form.company_id
      AND period_year = v_old_form.period_year
      AND period_month = v_old_form.period_month;

    -- Cancel the old form
    UPDATE form29
    SET status = 'cancelled',
        updated_at = NOW()
    WHERE id = p_form29_id;

    -- Create new revision
    INSERT INTO form29 (
        company_id,
        period_year,
        period_month,
        revision_number,
        total_sales,
        taxable_sales,
        exempt_sales,
        sales_tax,
        total_purchases,
        taxable_purchases,
        purchases_tax,
        iva_to_pay,
        iva_credit,
        net_iva,
        status,
        created_by_user_id,
        extra_data
    )
    VALUES (
        v_old_form.company_id,
        v_old_form.period_year,
        v_old_form.period_month,
        v_new_revision,
        v_old_form.total_sales,
        v_old_form.taxable_sales,
        v_old_form.exempt_sales,
        v_old_form.sales_tax,
        v_old_form.total_purchases,
        v_old_form.taxable_purchases,
        v_old_form.purchases_tax,
        v_old_form.iva_to_pay,
        v_old_form.iva_credit,
        v_old_form.net_iva,
        'draft',
        p_user_id,
        v_old_form.extra_data
    )
    RETURNING id INTO v_new_id;

    RETURN v_new_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- COMMENTS (Documentation)
-- =====================================================================

COMMENT ON COLUMN form29.created_by_user_id IS 'User who created this draft';
COMMENT ON COLUMN form29.confirmed_by_user_id IS 'User who confirmed this draft for submission';
COMMENT ON COLUMN form29.revision_number IS 'Revision number for this period (1-indexed, increments for corrections)';
COMMENT ON COLUMN form29.validation_status IS 'Status of validation: pending, valid, invalid, warning';
COMMENT ON COLUMN form29.validation_errors IS 'Array of validation errors/warnings (JSON array)';
COMMENT ON COLUMN form29.confirmed_at IS 'When the draft was confirmed by user';
COMMENT ON COLUMN form29.confirmation_notes IS 'Optional notes from user at confirmation time';
COMMENT ON COLUMN form29.payment_status IS 'Payment status: unpaid, pending, paid, partially_paid, overdue';
COMMENT ON COLUMN form29.payment_date IS 'Date when payment was made to SII';
COMMENT ON COLUMN form29.payment_reference IS 'Payment reference number from SII';
COMMENT ON COLUMN form29.payment_amount_cents IS 'Actual amount paid in Chilean pesos (may differ from calculated net_iva)';
COMMENT ON COLUMN form29.sii_download_id IS 'Link to form29_sii_downloads when form is submitted and downloaded from SII';
COMMENT ON COLUMN form29.metadata IS 'Additional metadata for future extensibility (JSONB)';

-- =====================================================================
-- END OF MIGRATION
-- =====================================================================
