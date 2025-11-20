-- Add business_description field to company_settings table
-- This field stores a free-form description of the business (max 100 words)

ALTER TABLE company_settings
ADD COLUMN IF NOT EXISTS business_description TEXT;

COMMENT ON COLUMN company_settings.business_description IS 'Free-form description of the business provided during onboarding (max 100 words recommended)';
