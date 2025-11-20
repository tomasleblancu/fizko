-- Add has_bank_loans field to company_settings table
-- This field tracks whether the company has active bank loans/credit

ALTER TABLE company_settings
ADD COLUMN IF NOT EXISTS has_bank_loans BOOLEAN;

COMMENT ON COLUMN company_settings.has_bank_loans IS 'Indicates if the company has active bank loans or credit lines';
