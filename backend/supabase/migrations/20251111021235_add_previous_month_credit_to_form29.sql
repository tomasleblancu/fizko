-- Migration: Add previous_month_credit field to form29 table
-- Date: 2025-01-10
-- Description: Adds explicit previous_month_credit field to store the credit
--              carried forward from the previous month's F29.

-- Add previous_month_credit column
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS previous_month_credit NUMERIC(15, 2) DEFAULT 0 NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN form29.previous_month_credit IS 'Credit carried forward from previous month (remanente de crédito fiscal mes anterior). This is the absolute value of the previous month''s negative net_iva, or código 077 from SII downloads.';

-- Add index for queries that filter by previous_month_credit
CREATE INDEX IF NOT EXISTS idx_form29_previous_month_credit
ON form29(previous_month_credit)
WHERE previous_month_credit > 0;
