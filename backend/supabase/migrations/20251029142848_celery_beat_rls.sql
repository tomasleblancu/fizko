-- ============================================================================
-- Row Level Security (RLS) for Celery Beat Tables
-- ============================================================================
--
-- This migration adds RLS policies to protect Celery Beat tables.
-- Only authenticated users with valid sessions can manage scheduled tasks.
--
-- Security Model:
-- - Users can only manage tasks for companies they have access to
-- - Access is validated via sessions table (user_id -> company_id)
-- - Schedule tables (interval/crontab) are protected but shared
-- - Task results are visible only to task owners
--
-- ============================================================================

-- ============================================================================
-- Enable RLS on all Celery tables
-- ============================================================================

ALTER TABLE celery_interval_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE celery_crontab_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE celery_periodic_task ENABLE ROW LEVEL SECURITY;
ALTER TABLE celery_periodic_task_changed ENABLE ROW LEVEL SECURITY;
ALTER TABLE celery_task_result ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Add company_id to periodic tasks for multi-tenancy
-- ============================================================================

-- Add company_id column to link tasks to companies
ALTER TABLE celery_periodic_task
ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE CASCADE;

-- Add index for company filtering
CREATE INDEX IF NOT EXISTS idx_celery_periodic_task_company_id
ON celery_periodic_task (company_id);

COMMENT ON COLUMN celery_periodic_task.company_id IS
'Company that owns this scheduled task (NULL for system-level tasks)';

-- ============================================================================
-- Helper function: Check if user has access to company
-- ============================================================================

CREATE OR REPLACE FUNCTION public.user_has_company_access(target_company_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Check if user has an active session for this company
    RETURN EXISTS (
        SELECT 1
        FROM sessions s
        WHERE s.user_id = auth.uid()
          AND s.company_id = target_company_id
          AND s.expires_at > NOW()
    );
END;
$$;

COMMENT ON FUNCTION public.user_has_company_access(UUID) IS
'Check if authenticated user has access to a company via active session';

-- ============================================================================
-- RLS Policies: celery_periodic_task
-- ============================================================================

-- SELECT: Users can view tasks for companies they have access to
CREATE POLICY "Users can view tasks for accessible companies"
ON celery_periodic_task
FOR SELECT
USING (
    -- Allow if company_id is NULL (system tasks) OR user has access
    company_id IS NULL OR user_has_company_access(company_id)
);

-- INSERT: Users can create tasks for companies they have access to
CREATE POLICY "Users can create tasks for accessible companies"
ON celery_periodic_task
FOR INSERT
WITH CHECK (
    -- Require company_id to be set and user must have access
    company_id IS NOT NULL AND user_has_company_access(company_id)
);

-- UPDATE: Users can update tasks for companies they have access to
CREATE POLICY "Users can update tasks for accessible companies"
ON celery_periodic_task
FOR UPDATE
USING (
    company_id IS NOT NULL AND user_has_company_access(company_id)
)
WITH CHECK (
    company_id IS NOT NULL AND user_has_company_access(company_id)
);

-- DELETE: Users can delete tasks for companies they have access to
CREATE POLICY "Users can delete tasks for accessible companies"
ON celery_periodic_task
FOR DELETE
USING (
    company_id IS NOT NULL AND user_has_company_access(company_id)
);

-- ============================================================================
-- RLS Policies: celery_interval_schedule
-- ============================================================================

-- SELECT: All authenticated users can view interval schedules (shared resource)
CREATE POLICY "Authenticated users can view interval schedules"
ON celery_interval_schedule
FOR SELECT
USING (auth.uid() IS NOT NULL);

-- INSERT: All authenticated users can create interval schedules
CREATE POLICY "Authenticated users can create interval schedules"
ON celery_interval_schedule
FOR INSERT
WITH CHECK (auth.uid() IS NOT NULL);

-- Note: No UPDATE/DELETE policies - schedules are immutable and shared
-- If you need to change a schedule, create a new one and update the task

-- ============================================================================
-- RLS Policies: celery_crontab_schedule
-- ============================================================================

-- SELECT: All authenticated users can view crontab schedules (shared resource)
CREATE POLICY "Authenticated users can view crontab schedules"
ON celery_crontab_schedule
FOR SELECT
USING (auth.uid() IS NOT NULL);

-- INSERT: All authenticated users can create crontab schedules
CREATE POLICY "Authenticated users can create crontab schedules"
ON celery_crontab_schedule
FOR INSERT
WITH CHECK (auth.uid() IS NOT NULL);

-- Note: No UPDATE/DELETE policies - schedules are immutable and shared

-- ============================================================================
-- RLS Policies: celery_task_result
-- ============================================================================

-- Add company_id to task results for filtering
ALTER TABLE celery_task_result
ADD COLUMN IF NOT EXISTS company_id UUID;

CREATE INDEX IF NOT EXISTS idx_celery_task_result_company_id
ON celery_task_result (company_id);

COMMENT ON COLUMN celery_task_result.company_id IS
'Company that owns the task execution (extracted from task kwargs)';

-- Function to extract company_id from task kwargs
CREATE OR REPLACE FUNCTION public.extract_company_id_from_task()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Try to extract company_id from kwargs JSON
    IF NEW.task_kwargs IS NOT NULL THEN
        BEGIN
            NEW.company_id := (NEW.task_kwargs->>'company_id')::UUID;
        EXCEPTION WHEN OTHERS THEN
            -- If extraction fails, leave as NULL
            NEW.company_id := NULL;
        END;
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger to auto-populate company_id from kwargs
CREATE TRIGGER trigger_extract_company_id
BEFORE INSERT ON celery_task_result
FOR EACH ROW
EXECUTE FUNCTION public.extract_company_id_from_task();

COMMENT ON FUNCTION public.extract_company_id_from_task() IS
'Automatically extracts company_id from task_kwargs for RLS filtering';

-- SELECT: Users can view task results for companies they have access to
CREATE POLICY "Users can view task results for accessible companies"
ON celery_task_result
FOR SELECT
USING (
    -- Allow if company_id is NULL (system tasks) OR user has access
    company_id IS NULL OR user_has_company_access(company_id)
);

-- INSERT: System can insert task results (workers run as service role)
-- Users don't directly insert task results - this is done by Celery workers
CREATE POLICY "Service role can insert task results"
ON celery_task_result
FOR INSERT
WITH CHECK (
    -- Allow service role to insert (Celery workers)
    current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
    OR
    -- Or allow authenticated users (for manual task submission)
    auth.uid() IS NOT NULL
);

-- UPDATE: Service role can update task results
CREATE POLICY "Service role can update task results"
ON celery_task_result
FOR UPDATE
USING (
    current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
);

-- ============================================================================
-- RLS Policies: celery_periodic_task_changed
-- ============================================================================

-- This is a single-row table used by Beat scheduler
-- Allow read access to authenticated users, write access to service role

CREATE POLICY "Authenticated users can view task change tracker"
ON celery_periodic_task_changed
FOR SELECT
USING (auth.uid() IS NOT NULL);

CREATE POLICY "Service role can update task change tracker"
ON celery_periodic_task_changed
FOR UPDATE
USING (
    current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
);

CREATE POLICY "Service role can insert task change tracker"
ON celery_periodic_task_changed
FOR INSERT
WITH CHECK (
    current_setting('request.jwt.claims', true)::json->>'role' = 'service_role'
);

-- ============================================================================
-- Update existing trigger to maintain company_id consistency
-- ============================================================================

-- Ensure company_id is preserved when updating periodic tasks
CREATE OR REPLACE FUNCTION public.validate_periodic_task_company()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Prevent changing company_id after creation (immutable)
    IF TG_OP = 'UPDATE' AND OLD.company_id IS DISTINCT FROM NEW.company_id THEN
        RAISE EXCEPTION 'Cannot change company_id of existing task';
    END IF;

    -- Ensure company_id is set on INSERT
    IF TG_OP = 'INSERT' AND NEW.company_id IS NULL THEN
        RAISE EXCEPTION 'company_id is required for new tasks';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trigger_validate_task_company
BEFORE INSERT OR UPDATE ON celery_periodic_task
FOR EACH ROW
EXECUTE FUNCTION public.validate_periodic_task_company();

COMMENT ON FUNCTION public.validate_periodic_task_company() IS
'Ensures company_id is set and immutable for periodic tasks';

-- ============================================================================
-- Grant necessary permissions
-- ============================================================================

-- Grant service role access to all Celery tables (for workers)
GRANT ALL ON celery_interval_schedule TO service_role;
GRANT ALL ON celery_crontab_schedule TO service_role;
GRANT ALL ON celery_periodic_task TO service_role;
GRANT ALL ON celery_periodic_task_changed TO service_role;
GRANT ALL ON celery_task_result TO service_role;

-- Grant authenticated users access via RLS policies
GRANT SELECT, INSERT, UPDATE, DELETE ON celery_periodic_task TO authenticated;
GRANT SELECT, INSERT ON celery_interval_schedule TO authenticated;
GRANT SELECT, INSERT ON celery_crontab_schedule TO authenticated;
GRANT SELECT ON celery_task_result TO authenticated;
GRANT SELECT ON celery_periodic_task_changed TO authenticated;

-- Grant sequence usage
GRANT USAGE ON SEQUENCE celery_interval_schedule_id_seq TO authenticated, service_role;
GRANT USAGE ON SEQUENCE celery_crontab_schedule_id_seq TO authenticated, service_role;
GRANT USAGE ON SEQUENCE celery_periodic_task_id_seq TO authenticated, service_role;
GRANT USAGE ON SEQUENCE celery_periodic_task_changed_id_seq TO authenticated, service_role;
GRANT USAGE ON SEQUENCE celery_task_result_id_seq TO authenticated, service_role;

-- ============================================================================
-- Migration Data: Update existing tasks
-- ============================================================================

-- If you have existing tasks without company_id, you can set them here
-- Example: UPDATE celery_periodic_task SET company_id = 'uuid-here' WHERE name = 'task-name';

-- For now, we'll leave existing tasks as-is (company_id = NULL)
-- They will be visible to all users but cannot be modified (RLS blocks NULL company_id updates)

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check RLS is enabled:
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE tablename LIKE 'celery_%';

-- List policies:
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
-- FROM pg_policies
-- WHERE tablename LIKE 'celery_%'
-- ORDER BY tablename, policyname;

-- Test user access (run as authenticated user):
-- SELECT name, task, enabled, company_id
-- FROM celery_periodic_task
-- WHERE company_id = 'your-company-uuid';

-- ============================================================================
-- Important Notes
-- ============================================================================

-- 1. SYSTEM TASKS: Tasks with company_id = NULL are system-level tasks
--    - Visible to all users (read-only)
--    - Can only be modified via service role or direct SQL
--    - Use for global background jobs

-- 2. COMPANY TASKS: Tasks with company_id set are company-specific
--    - Only visible to users with access to that company
--    - Users can create/update/delete via API
--    - Use for tenant-specific scheduled tasks

-- 3. WORKERS: Celery workers should use service_role credentials
--    - Set SUPABASE_SERVICE_KEY in worker environment
--    - Workers need full access to read/write task results

-- 4. API ENDPOINTS: The scheduled_tasks router should:
--    - Always set company_id from user's session
--    - Filter tasks by user's accessible companies
--    - Prevent company_id manipulation

-- ============================================================================
