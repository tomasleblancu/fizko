-- Remove the CHECK constraint that requires either interval_id or crontab_id
-- With the generic FK pattern (discriminator + schedule_id), this constraint is too restrictive
ALTER TABLE celery_schema.celery_periodictask 
DROP CONSTRAINT IF EXISTS check_schedule;