-- Make company_id optional for periodic tasks
-- System-level tasks (like celery.backend_cleanup) don't belong to any company

-- Drop the trigger that enforces company_id
DROP TRIGGER IF EXISTS trigger_validate_task_company ON celery_periodic_task;

-- Drop the function
DROP FUNCTION IF EXISTS validate_periodic_task_company();

-- Note: company_id is still in the table and nullable, but no longer required
-- API layer will still set company_id for user-created tasks
-- But system tasks and Celery built-ins can have NULL company_id