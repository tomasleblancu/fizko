-- Migration: Add sii_password column to companies table
-- Description: Adds a field to store SII portal password for each company
-- Date: 2025-10-21

-- Add sii_password column to companies table
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS sii_password TEXT NULL;

-- Add comment to document the column
COMMENT ON COLUMN companies.sii_password IS 'SII portal password (should be encrypted in production for security)';

-- Note: Passwords should be encrypted using pgcrypto or application-level encryption in production
-- Example for future encryption implementation:
-- UPDATE companies SET sii_password = pgp_sym_encrypt(sii_password, 'encryption_key') WHERE sii_password IS NOT NULL;
