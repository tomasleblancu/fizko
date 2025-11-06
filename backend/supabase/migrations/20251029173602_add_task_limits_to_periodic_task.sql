-- Add max_retries, soft_time_limit, and hard_time_limit columns to celery_periodic_task
ALTER TABLE celery_periodic_task 
ADD COLUMN IF NOT EXISTS max_retries INTEGER,
ADD COLUMN IF NOT EXISTS soft_time_limit INTEGER,
ADD COLUMN IF NOT EXISTS hard_time_limit INTEGER;

-- Add comments
COMMENT ON COLUMN celery_periodic_task.max_retries IS 'Maximum retry attempts';
COMMENT ON COLUMN celery_periodic_task.soft_time_limit IS 'Soft time limit in seconds';
COMMENT ON COLUMN celery_periodic_task.hard_time_limit IS 'Hard time limit in seconds';