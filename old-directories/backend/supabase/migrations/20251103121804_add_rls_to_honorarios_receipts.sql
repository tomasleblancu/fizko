-- Migration: Add RLS policies to honorarios_receipts table
-- Description: Enable Row Level Security and add policies for honorarios_receipts

-- Enable RLS on honorarios_receipts table
ALTER TABLE honorarios_receipts ENABLE ROW LEVEL SECURITY;

-- Policy: Allow authenticated users to SELECT their company's honorarios receipts
-- Users can only see receipts for companies they have an active session with
CREATE POLICY "Users can view their company's honorarios receipts"
    ON honorarios_receipts
    FOR SELECT
    TO authenticated
    USING (
        company_id IN (
            SELECT company_id
            FROM sessions
            WHERE user_id = auth.uid()
            AND is_active = true
        )
    );

-- Policy: Allow authenticated users to INSERT honorarios receipts for their companies
CREATE POLICY "Users can create honorarios receipts for their companies"
    ON honorarios_receipts
    FOR INSERT
    TO authenticated
    WITH CHECK (
        company_id IN (
            SELECT company_id
            FROM sessions
            WHERE user_id = auth.uid()
            AND is_active = true
        )
    );

-- Policy: Allow authenticated users to UPDATE their company's honorarios receipts
CREATE POLICY "Users can update their company's honorarios receipts"
    ON honorarios_receipts
    FOR UPDATE
    TO authenticated
    USING (
        company_id IN (
            SELECT company_id
            FROM sessions
            WHERE user_id = auth.uid()
            AND is_active = true
        )
    )
    WITH CHECK (
        company_id IN (
            SELECT company_id
            FROM sessions
            WHERE user_id = auth.uid()
            AND is_active = true
        )
    );

-- Policy: Allow authenticated users to DELETE their company's honorarios receipts
CREATE POLICY "Users can delete their company's honorarios receipts"
    ON honorarios_receipts
    FOR DELETE
    TO authenticated
    USING (
        company_id IN (
            SELECT company_id
            FROM sessions
            WHERE user_id = auth.uid()
            AND is_active = true
        )
    );

-- Add comment explaining the RLS policies
COMMENT ON TABLE honorarios_receipts IS 'Boletas de honorarios recibidas y emitidas por la empresa. RLS enabled: users can only access receipts for companies they have active sessions with.';
