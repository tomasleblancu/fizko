-- =====================================================================
-- Fizko Database Migration - Form 29 SII Downloads
-- =====================================================================
-- Description: Creates table to track F29 forms downloaded from SII portal
-- Version: 1.0
-- Date: 2025-01-22
--
-- Purpose:
-- - Store F29 forms as they appear in the SII portal
-- - Track PDF download status and storage
-- - Separate from locally calculated F29 forms
-- - Enable reconciliation between SII and local data
-- =====================================================================

-- =====================================================================
-- FORM 29 SII DOWNLOADS TABLE
-- =====================================================================

CREATE TABLE IF NOT EXISTS form29_sii_downloads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Optional link to local F29 (for reconciliation)
    form29_id UUID REFERENCES form29(id) ON DELETE SET NULL,

    -- SII data (as returned from API)
    sii_folio TEXT NOT NULL,
    sii_id_interno TEXT,  -- NULLABLE - not always available from SII

    -- Period
    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,
    period_display TEXT NOT NULL,  -- "YYYY-MM" format from SII

    -- Form information
    contributor_rut TEXT NOT NULL,
    submission_date DATE,  -- Converted from "DD/MM/YYYY" format
    status TEXT NOT NULL,  -- Vigente, Rectificado, Anulado
    amount_cents INTEGER DEFAULT 0 NOT NULL,  -- Amount in Chilean pesos (integer, no decimals)

    -- PDF download tracking
    pdf_storage_url TEXT,  -- URL to PDF file in storage (e.g., Supabase Storage)
    pdf_download_status TEXT DEFAULT 'pending'::text NOT NULL,  -- pending, downloaded, error
    pdf_download_error TEXT,
    pdf_downloaded_at TIMESTAMPTZ,

    -- Additional flexible data
    extra_data JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Unique constraint: one download record per company per folio
    CONSTRAINT form29_sii_downloads_company_folio_unique
        UNIQUE (company_id, sii_folio),

    -- Constraints
    CONSTRAINT form29_sii_downloads_period_month_check
        CHECK (period_month >= 1 AND period_month <= 12),
    CONSTRAINT form29_sii_downloads_status_check
        CHECK (status = ANY (ARRAY['Vigente'::text, 'Rectificado'::text, 'Anulado'::text])),
    CONSTRAINT form29_sii_downloads_pdf_status_check
        CHECK (pdf_download_status = ANY (ARRAY['pending'::text, 'downloaded'::text, 'error'::text]))
);

-- =====================================================================
-- INDEXES
-- =====================================================================

-- Composite index for efficient period queries
CREATE INDEX IF NOT EXISTS ix_form29_sii_downloads_company_period
    ON form29_sii_downloads(company_id, period_year, period_month);

-- Index for folio lookups
CREATE INDEX IF NOT EXISTS ix_form29_sii_downloads_folio
    ON form29_sii_downloads(sii_folio);

-- Index for status queries
CREATE INDEX IF NOT EXISTS ix_form29_sii_downloads_status
    ON form29_sii_downloads(company_id, status);

-- Index for PDF download status (useful for batch processing)
CREATE INDEX IF NOT EXISTS ix_form29_sii_downloads_pdf_status
    ON form29_sii_downloads(company_id, pdf_download_status)
    WHERE pdf_download_status = 'pending';

-- Index for reconciliation (forms not yet linked to local F29)
CREATE INDEX IF NOT EXISTS ix_form29_sii_downloads_unlinked
    ON form29_sii_downloads(company_id, period_year, period_month)
    WHERE form29_id IS NULL;

-- =====================================================================
-- TRIGGERS
-- =====================================================================

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_form29_sii_downloads_updated_at
    BEFORE UPDATE ON form29_sii_downloads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================================

ALTER TABLE form29_sii_downloads ENABLE ROW LEVEL SECURITY;

-- Users can view form29_sii_downloads for companies they have sessions for
CREATE POLICY "Users can view form29 sii downloads via sessions"
    ON form29_sii_downloads FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = form29_sii_downloads.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- Users can insert form29_sii_downloads for companies they have sessions for
CREATE POLICY "Users can insert form29 sii downloads via sessions"
    ON form29_sii_downloads FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- Users can update form29_sii_downloads for companies they have sessions for
CREATE POLICY "Users can update form29 sii downloads via sessions"
    ON form29_sii_downloads FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = form29_sii_downloads.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- Users can delete form29_sii_downloads for companies they have sessions for
CREATE POLICY "Users can delete form29 sii downloads via sessions"
    ON form29_sii_downloads FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = form29_sii_downloads.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- =====================================================================
-- COMMENTS (Documentation)
-- =====================================================================

COMMENT ON TABLE form29_sii_downloads IS 'F29 forms downloaded from SII portal (separate from locally calculated F29)';
COMMENT ON COLUMN form29_sii_downloads.sii_folio IS 'Folio number from SII (unique per form)';
COMMENT ON COLUMN form29_sii_downloads.sii_id_interno IS 'Internal SII ID required for PDF download (may be null for some forms)';
COMMENT ON COLUMN form29_sii_downloads.form29_id IS 'Optional link to locally calculated F29 form (for reconciliation)';
COMMENT ON COLUMN form29_sii_downloads.amount_cents IS 'Amount in Chilean pesos (integer, no decimals)';
COMMENT ON COLUMN form29_sii_downloads.pdf_storage_url IS 'URL to PDF file in storage (e.g., Supabase Storage)';
COMMENT ON COLUMN form29_sii_downloads.pdf_download_status IS 'Status of PDF download: pending, downloaded, or error';

-- =====================================================================
-- END OF MIGRATION
-- =====================================================================
