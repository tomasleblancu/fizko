-- Allow service_role and postgres to bypass RLS for Celery Beat scheduler tables
-- This is necessary because Celery Beat doesn't have user context

-- Grant permissions to service_role
GRANT ALL ON celery_periodic_task TO service_role;
GRANT ALL ON celery_interval_schedule TO service_role;
GRANT ALL ON celery_crontab_schedule TO service_role;
GRANT ALL ON celery_periodic_task_changed TO service_role;
GRANT ALL ON celery_task_result TO service_role;

-- Create policies for service_role to access all tasks
CREATE POLICY "Service role can manage all periodic tasks"
ON celery_periodic_task
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role can manage all interval schedules"
ON celery_interval_schedule
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role can manage all crontab schedules"
ON celery_crontab_schedule
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role can manage periodic task changes"
ON celery_periodic_task_changed
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role can manage all task results"
ON celery_task_result
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Also grant to postgres role (database owner)
GRANT ALL ON celery_periodic_task TO postgres;
GRANT ALL ON celery_interval_schedule TO postgres;
GRANT ALL ON celery_crontab_schedule TO postgres;
GRANT ALL ON celery_periodic_task_changed TO postgres;
GRANT ALL ON celery_task_result TO postgres;