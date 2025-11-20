-- Change args and kwargs from JSONB to TEXT
-- sqlalchemy-celery-beat expects JSON strings, not JSONB objects

ALTER TABLE celery_schema.celery_periodictask 
ALTER COLUMN args TYPE TEXT USING args::text,
ALTER COLUMN kwargs TYPE TEXT USING kwargs::text;

-- Update existing rows to ensure they are valid JSON strings
UPDATE celery_schema.celery_periodictask
SET 
    args = CASE 
        WHEN args IS NULL THEN '[]'
        WHEN args::text = '[]' THEN '[]'
        ELSE args::text
    END,
    kwargs = CASE
        WHEN kwargs IS NULL THEN '{}'
        WHEN kwargs::text = '{}' THEN '{}'
        ELSE kwargs::text
    END;