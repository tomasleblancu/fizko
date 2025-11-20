-- Allow postgres role to bypass RLS on Celery Beat tables
-- This is necessary because Celery Beat connects with postgres credentials

-- Create policies for postgres role to access all tasks
DROP POLICY IF EXISTS "Postgres role can manage all periodic tasks" ON celery_periodic_task;
CREATE POLICY "Postgres role can manage all periodic tasks"
ON celery_periodic_task
FOR ALL
TO postgres
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Postgres role can manage all interval schedules" ON celery_interval_schedule;
CREATE POLICY "Postgres role can manage all interval schedules"
ON celery_interval_schedule
FOR ALL
TO postgres
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Postgres role can manage all crontab schedules" ON celery_crontab_schedule;
CREATE POLICY "Postgres role can manage all crontab schedules"
ON celery_crontab_schedule
FOR ALL
TO postgres
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Postgres role can manage periodic task changes" ON celery_periodic_task_changed;
CREATE POLICY "Postgres role can manage periodic task changes"
ON celery_periodic_task_changed
FOR ALL
TO postgres
USING (true)
WITH CHECK (true);

DROP POLICY IF EXISTS "Postgres role can manage all task results" ON celery_task_result;
CREATE POLICY "Postgres role can manage all task results"
ON celery_task_result
FOR ALL
TO postgres
USING (true)
WITH CHECK (true);