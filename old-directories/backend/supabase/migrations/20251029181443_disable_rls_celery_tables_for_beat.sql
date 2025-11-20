-- Temporarily disable RLS on Celery Beat tables to allow scheduler access
-- These tables are internal infrastructure, not user data
-- Beat needs unrestricted access to manage scheduled tasks

-- Disable RLS on Celery Beat tables
ALTER TABLE celery_periodic_task DISABLE ROW LEVEL SECURITY;
ALTER TABLE celery_interval_schedule DISABLE ROW LEVEL SECURITY;
ALTER TABLE celery_crontab_schedule DISABLE ROW LEVEL SECURITY;
ALTER TABLE celery_periodic_task_changed DISABLE ROW LEVEL SECURITY;
ALTER TABLE celery_task_result DISABLE ROW LEVEL SECURITY;

-- Note: We're disabling RLS because:
-- 1. Celery Beat is infrastructure, not user-facing
-- 2. Access control is already handled at the API level (backend routes check company_id)
-- 3. Beat needs to see all tasks regardless of company to schedule them
-- 4. Task results should be accessible for monitoring

-- Security note: The API layer (FastAPI) still enforces company_id filtering
-- via dependencies.get_user_company_id(), so users can only see their own tasks
-- through the web interface.