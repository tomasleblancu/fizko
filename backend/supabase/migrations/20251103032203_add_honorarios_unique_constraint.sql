-- Add unique constraint on (company_id, folio) for honorarios_receipts
-- This constraint is required for ON CONFLICT handling during bulk upsert operations

-- First, check if any duplicates exist and handle them
-- We'll keep the most recent record (by created_at) if there are duplicates
WITH duplicates AS (
    SELECT
        company_id,
        folio,
        array_agg(id ORDER BY created_at DESC) as ids
    FROM honorarios_receipts
    WHERE folio IS NOT NULL
    GROUP BY company_id, folio
    HAVING COUNT(*) > 1
),
to_delete AS (
    SELECT unnest(ids[2:]) as id
    FROM duplicates
)
DELETE FROM honorarios_receipts
WHERE id IN (SELECT id FROM to_delete);

-- Now add the unique constraint
-- Note: This constraint allows NULL folios (multiple records can have NULL folio for same company)
ALTER TABLE honorarios_receipts
ADD CONSTRAINT honorarios_receipts_company_folio_key
UNIQUE (company_id, folio);

-- Add comment explaining the constraint
COMMENT ON CONSTRAINT honorarios_receipts_company_folio_key ON honorarios_receipts IS
'Ensures that each folio number is unique within a company. NULL folios are allowed (not considered duplicates).';
