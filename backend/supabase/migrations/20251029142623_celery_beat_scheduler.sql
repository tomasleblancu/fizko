-- ============================================================================
-- Celery Beat Database Scheduler Tables
-- ============================================================================
--
-- This migration creates tables required by sqlalchemy-celery-beat for storing
-- periodic task schedules in the database. This allows dynamic creation,
-- modification, and deletion of scheduled tasks without worker restarts.
--
-- Tables:
--   1. celery_interval_schedule - Interval-based schedules (every N minutes/hours/days)
--   2. celery_crontab_schedule - Cron-based schedules (cron expressions)
--   3. celery_periodic_task - Main periodic task definitions
--   4. celery_periodic_task_changed - Tracks changes for scheduler reload
--   5. celery_task_result - Optional task execution history
--
-- Usage:
--   - Celery Beat worker reads from these tables every 5 seconds (configured)
--   - Changes are detected via celery_periodic_task_changed timestamp
--   - Tasks can be managed via API or directly in database
--
-- ============================================================================

-- ============================================================================
-- 1. Interval Schedule (every N minutes/hours/days/weeks)
-- ============================================================================
CREATE TABLE IF NOT EXISTS celery_interval_schedule (
    id SERIAL PRIMARY KEY,
    every INTEGER NOT NULL CHECK (every > 0),
    period VARCHAR(24) NOT NULL CHECK (period IN ('days', 'hours', 'minutes', 'seconds', 'microseconds')),

    -- Uniqueness constraint
    UNIQUE (every, period)
);

CREATE INDEX idx_celery_interval_every_period
ON celery_interval_schedule (every, period);

COMMENT ON TABLE celery_interval_schedule IS
'Interval-based schedules for periodic tasks (e.g., every 30 minutes)';
COMMENT ON COLUMN celery_interval_schedule.every IS
'Number of period units (e.g., 30 for "every 30 minutes")';
COMMENT ON COLUMN celery_interval_schedule.period IS
'Time unit: days, hours, minutes, seconds, or microseconds';

-- ============================================================================
-- 2. Crontab Schedule (cron-like expressions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS celery_crontab_schedule (
    id SERIAL PRIMARY KEY,
    minute VARCHAR(64) NOT NULL DEFAULT '*',
    hour VARCHAR(64) NOT NULL DEFAULT '*',
    day_of_week VARCHAR(64) NOT NULL DEFAULT '*',
    day_of_month VARCHAR(64) NOT NULL DEFAULT '*',
    month_of_year VARCHAR(64) NOT NULL DEFAULT '*',
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',

    -- Uniqueness constraint
    UNIQUE (minute, hour, day_of_week, day_of_month, month_of_year, timezone)
);

CREATE INDEX idx_celery_crontab_schedule
ON celery_crontab_schedule (minute, hour, day_of_week, day_of_month, month_of_year);

COMMENT ON TABLE celery_crontab_schedule IS
'Cron-based schedules for periodic tasks (e.g., 0 0 * * * for midnight daily)';
COMMENT ON COLUMN celery_crontab_schedule.minute IS
'Minute (0-59, *, */5, 0-15, etc.)';
COMMENT ON COLUMN celery_crontab_schedule.hour IS
'Hour (0-23, *, */2, 9-17, etc.)';
COMMENT ON COLUMN celery_crontab_schedule.day_of_week IS
'Day of week (0-6 where 0=Sunday, *, mon-fri, etc.)';
COMMENT ON COLUMN celery_crontab_schedule.day_of_month IS
'Day of month (1-31, *, */2, 1,15, etc.)';
COMMENT ON COLUMN celery_crontab_schedule.month_of_year IS
'Month (1-12, *, */3, jan-jun, etc.)';

-- ============================================================================
-- 3. Periodic Task (main task definition)
-- ============================================================================
CREATE TABLE IF NOT EXISTS celery_periodic_task (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    task VARCHAR(200) NOT NULL,

    -- Schedule (one must be set)
    interval_id INTEGER REFERENCES celery_interval_schedule(id) ON DELETE CASCADE,
    crontab_id INTEGER REFERENCES celery_crontab_schedule(id) ON DELETE CASCADE,

    -- Task arguments (JSONB for flexibility)
    args JSONB NOT NULL DEFAULT '[]',
    kwargs JSONB NOT NULL DEFAULT '{}',

    -- Queue routing
    queue VARCHAR(200) DEFAULT NULL,
    exchange VARCHAR(200) DEFAULT NULL,
    routing_key VARCHAR(200) DEFAULT NULL,
    priority INTEGER DEFAULT NULL,

    -- Execution control
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    expires TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    expire_seconds INTEGER DEFAULT NULL,
    one_off BOOLEAN NOT NULL DEFAULT FALSE,

    -- Task limits
    max_retries INTEGER DEFAULT NULL,
    soft_time_limit INTEGER DEFAULT NULL,
    hard_time_limit INTEGER DEFAULT NULL,

    -- Metadata
    description TEXT DEFAULT NULL,

    -- Timestamps
    date_changed TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_run_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    total_run_count INTEGER NOT NULL DEFAULT 0,

    -- Constraints
    CHECK (
        (interval_id IS NOT NULL AND crontab_id IS NULL) OR
        (interval_id IS NULL AND crontab_id IS NOT NULL)
    )
);

CREATE INDEX idx_celery_periodic_task_name
ON celery_periodic_task (name);

CREATE INDEX idx_celery_periodic_task_enabled
ON celery_periodic_task (enabled);

CREATE INDEX idx_celery_periodic_task_interval
ON celery_periodic_task (interval_id);

CREATE INDEX idx_celery_periodic_task_crontab
ON celery_periodic_task (crontab_id);

CREATE INDEX idx_celery_periodic_task_last_run
ON celery_periodic_task (last_run_at);

COMMENT ON TABLE celery_periodic_task IS
'Periodic task definitions - scheduled tasks managed by Celery Beat';
COMMENT ON COLUMN celery_periodic_task.name IS
'Unique human-readable name for the task';
COMMENT ON COLUMN celery_periodic_task.task IS
'Celery task name (e.g., "sii.sync_documents")';
COMMENT ON COLUMN celery_periodic_task.args IS
'Positional arguments as JSON array (e.g., ["arg1", "arg2"])';
COMMENT ON COLUMN celery_periodic_task.kwargs IS
'Keyword arguments as JSON object (e.g., {"session_id": "123", "months": 1})';
COMMENT ON COLUMN celery_periodic_task.one_off IS
'If true, task runs once and is disabled automatically';
COMMENT ON COLUMN celery_periodic_task.total_run_count IS
'Counter incremented each time the task is triggered';

-- ============================================================================
-- 4. Periodic Task Changed (change tracking for scheduler reload)
-- ============================================================================
CREATE TABLE IF NOT EXISTS celery_periodic_task_changed (
    id SERIAL PRIMARY KEY,
    last_update TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Insert initial record
INSERT INTO celery_periodic_task_changed (last_update)
VALUES (NOW())
ON CONFLICT DO NOTHING;

COMMENT ON TABLE celery_periodic_task_changed IS
'Change tracker - Beat checks this to detect when to reload schedules';
COMMENT ON COLUMN celery_periodic_task_changed.last_update IS
'Timestamp of last change to periodic tasks';

-- ============================================================================
-- 5. Task Result (optional execution history)
-- ============================================================================
CREATE TABLE IF NOT EXISTS celery_task_result (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255) DEFAULT NULL,
    task_args JSONB DEFAULT NULL,
    task_kwargs JSONB DEFAULT NULL,

    -- Execution info
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    worker VARCHAR(100) DEFAULT NULL,
    content_type VARCHAR(128) DEFAULT 'application/json',
    content_encoding VARCHAR(64) DEFAULT 'utf-8',

    -- Result/Error
    result JSONB DEFAULT NULL,
    traceback TEXT DEFAULT NULL,
    meta JSONB DEFAULT NULL,

    -- Timestamps
    date_created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    date_done TIMESTAMP WITH TIME ZONE DEFAULT NULL
);

CREATE INDEX idx_celery_task_result_task_id
ON celery_task_result (task_id);

CREATE INDEX idx_celery_task_result_status
ON celery_task_result (status);

CREATE INDEX idx_celery_task_result_date_created
ON celery_task_result (date_created);

CREATE INDEX idx_celery_task_result_date_done
ON celery_task_result (date_done);

CREATE INDEX idx_celery_task_result_task_name
ON celery_task_result (task_name);

COMMENT ON TABLE celery_task_result IS
'Task execution history - stores results and status of completed tasks';
COMMENT ON COLUMN celery_task_result.task_id IS
'Unique task execution ID (UUID)';
COMMENT ON COLUMN celery_task_result.status IS
'Task status: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED';
COMMENT ON COLUMN celery_task_result.result IS
'Task return value as JSON';
COMMENT ON COLUMN celery_task_result.traceback IS
'Exception traceback if task failed';

-- ============================================================================
-- Trigger: Update celery_periodic_task_changed on task modifications
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_periodic_task_change()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE celery_periodic_task_changed
    SET last_update = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_periodic_task_changed
AFTER INSERT OR UPDATE OR DELETE ON celery_periodic_task
FOR EACH STATEMENT
EXECUTE FUNCTION notify_periodic_task_change();

COMMENT ON FUNCTION notify_periodic_task_change() IS
'Automatically updates celery_periodic_task_changed.last_update when tasks are modified';

-- ============================================================================
-- Example Data (commented out - uncomment to test)
-- ============================================================================

-- Example 1: Interval schedule - every 30 minutes
-- INSERT INTO celery_interval_schedule (every, period)
-- VALUES (30, 'minutes')
-- RETURNING id;

-- Example 2: Crontab schedule - daily at midnight Chile time
-- INSERT INTO celery_crontab_schedule (minute, hour, day_of_week, day_of_month, month_of_year, timezone)
-- VALUES ('0', '0', '*', '*', '*', 'America/Santiago')
-- RETURNING id;

-- Example 3: Periodic task using interval
-- INSERT INTO celery_periodic_task (
--     name,
--     task,
--     interval_id,
--     kwargs,
--     queue,
--     enabled,
--     description
-- )
-- VALUES (
--     'sync-documents-company-123',
--     'sii.sync_documents',
--     1, -- interval_id from example 1
--     '{"session_id": "uuid-here", "months": 1}'::jsonb,
--     'low',
--     true,
--     'Sync last month documents for company 123'
-- );

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- List all periodic tasks with their schedules:
-- SELECT
--     pt.id,
--     pt.name,
--     pt.task,
--     pt.enabled,
--     pt.last_run_at,
--     pt.total_run_count,
--     CASE
--         WHEN pt.interval_id IS NOT NULL
--         THEN 'Every ' || i.every || ' ' || i.period
--         WHEN pt.crontab_id IS NOT NULL
--         THEN 'Cron: ' || c.minute || ' ' || c.hour || ' * * *'
--     END as schedule
-- FROM celery_periodic_task pt
-- LEFT JOIN celery_interval_schedule i ON pt.interval_id = i.id
-- LEFT JOIN celery_crontab_schedule c ON pt.crontab_id = c.id
-- ORDER BY pt.name;

-- List recent task executions:
-- SELECT
--     task_name,
--     status,
--     date_created,
--     date_done,
--     (date_done - date_created) as duration
-- FROM celery_task_result
-- ORDER BY date_created DESC
-- LIMIT 20;
