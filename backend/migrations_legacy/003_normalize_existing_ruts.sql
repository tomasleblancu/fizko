-- Migration: Normalize existing RUTs in companies table
-- Description: Updates all RUTs to normalized format (lowercase, no hyphens)
-- Date: 2025-10-21

-- Create a temporary function to normalize RUTs
CREATE OR REPLACE FUNCTION normalize_rut_temp(rut TEXT) RETURNS TEXT AS $$
BEGIN
    IF rut IS NULL THEN
        RETURN NULL;
    END IF;

    -- Remove all non-alphanumeric characters and convert to lowercase
    RETURN lower(regexp_replace(rut, '[^0-9kK]', '', 'g'));
END;
$$ LANGUAGE plpgsql;

-- Update all existing RUTs to normalized format
UPDATE companies
SET rut = normalize_rut_temp(rut)
WHERE rut IS NOT NULL
  AND rut != normalize_rut_temp(rut);

-- Drop the temporary function
DROP FUNCTION normalize_rut_temp(TEXT);

-- Log the change
DO $$
BEGIN
    RAISE NOTICE 'RUT normalization completed. All RUTs are now in lowercase without hyphens.';
END $$;
