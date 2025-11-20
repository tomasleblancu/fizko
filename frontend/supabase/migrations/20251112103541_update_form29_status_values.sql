-- Migration: Update Form29 status values
-- Description: Simplifies Form29 workflow from 6 states to 4 states
-- Old states: draft, validated, confirmed, submitted, paid, cancelled
-- New states: draft (calculado), saved (guardado), paid (pagado), cancelled

-- Step 1: Drop the existing check constraint
ALTER TABLE form29 DROP CONSTRAINT IF EXISTS form29_status_check;

-- Step 2: Update existing records to new status names
-- Map old statuses to new statuses:
-- - 'validated' -> 'saved'
-- - 'confirmed' -> 'saved'
-- - 'submitted' -> 'saved'
-- - 'draft' -> 'draft' (no change)
-- - 'paid' -> 'paid' (no change)
-- - 'cancelled' -> 'cancelled' (no change)

UPDATE form29
SET status = CASE
    WHEN status IN ('validated', 'confirmed', 'submitted') THEN 'saved'
    ELSE status
END
WHERE status IN ('validated', 'confirmed', 'submitted');

-- Step 3: Add new check constraint with updated status values
ALTER TABLE form29
ADD CONSTRAINT form29_status_check
CHECK (status = ANY (ARRAY['draft'::text, 'saved'::text, 'paid'::text, 'cancelled'::text]));

-- Step 4: Drop and recreate the index for ready_for_submission (now ready_for_payment)
DROP INDEX IF EXISTS ix_form29_ready_for_submission;

CREATE INDEX ix_form29_ready_for_payment
ON form29(company_id, status)
WHERE status = 'saved';

-- Step 5: Add comment to document the change
COMMENT ON COLUMN form29.status IS 'Form status: draft (calculado), saved (guardado), paid (pagado), cancelled';
