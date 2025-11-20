-- Add sii_password column to companies table
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS sii_password TEXT NULL;

-- Add comment to document the column
COMMENT ON COLUMN companies.sii_password IS 'SII portal password (should be encrypted in production for security)';