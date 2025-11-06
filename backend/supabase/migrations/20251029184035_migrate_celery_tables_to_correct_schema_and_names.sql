-- Create celery_schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS celery_schema;

-- Create new tables with correct names in celery_schema
-- These match what sqlalchemy-celery-beat expects

-- 1. celery_intervalschedule (no underscore between words)
CREATE TABLE IF NOT EXISTS celery_schema.celery_intervalschedule (
    id SERIAL PRIMARY KEY,
    every INTEGER NOT NULL,
    period VARCHAR(24) NOT NULL
);

-- 2. celery_crontabschedule (no underscore between words)
CREATE TABLE IF NOT EXISTS celery_schema.celery_crontabschedule (
    id SERIAL PRIMARY KEY,
    minute VARCHAR(64) NOT NULL DEFAULT '*',
    hour VARCHAR(64) NOT NULL DEFAULT '*',
    day_of_week VARCHAR(64) NOT NULL DEFAULT '*',
    day_of_month VARCHAR(64) NOT NULL DEFAULT '*',
    month_of_year VARCHAR(64) NOT NULL DEFAULT '*',
    timezone VARCHAR(63) NOT NULL DEFAULT 'UTC'
);

-- 3. celery_periodictaskchanged (no underscore between words)
CREATE TABLE IF NOT EXISTS celery_schema.celery_periodictaskchanged (
    id INTEGER PRIMARY KEY DEFAULT 1,
    last_update TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. celery_taskresult (no underscore between words)
CREATE TABLE IF NOT EXISTS celery_schema.celery_taskresult (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(155) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL,
    result TEXT,
    date_done TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    traceback TEXT,
    name VARCHAR(155),
    args TEXT,
    kwargs TEXT,
    worker VARCHAR(155),
    retries INTEGER DEFAULT 0,
    queue VARCHAR(155)
);

-- 5. celery_periodictask (no underscore between words) - last due to FK dependencies
CREATE TABLE IF NOT EXISTS celery_schema.celery_periodictask (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    task VARCHAR(255) NOT NULL,
    interval_id INTEGER REFERENCES celery_schema.celery_intervalschedule(id) ON DELETE CASCADE,
    crontab_id INTEGER REFERENCES celery_schema.celery_crontabschedule(id) ON DELETE CASCADE,
    args TEXT NOT NULL DEFAULT '[]',
    kwargs TEXT NOT NULL DEFAULT '{}',
    queue VARCHAR(255),
    exchange VARCHAR(255),
    routing_key VARCHAR(255),
    priority INTEGER,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    expires TIMESTAMPTZ,
    expire_seconds INTEGER,
    one_off BOOLEAN NOT NULL DEFAULT FALSE,
    max_retries INTEGER,
    soft_time_limit INTEGER,
    hard_time_limit INTEGER,
    description TEXT DEFAULT '',
    date_changed TIMESTAMPTZ DEFAULT NOW(),
    last_run_at TIMESTAMPTZ,
    total_run_count INTEGER NOT NULL DEFAULT 0,
    company_id UUID,
    start_time TIMESTAMPTZ,
    headers TEXT DEFAULT '{}',
    discriminator VARCHAR(20) NOT NULL,
    schedule_id INTEGER NOT NULL,
    CONSTRAINT check_schedule CHECK (
        (interval_id IS NOT NULL AND crontab_id IS NULL) OR
        (interval_id IS NULL AND crontab_id IS NOT NULL)
    )
);

-- Copy data from old tables to new tables
INSERT INTO celery_schema.celery_intervalschedule (id, every, period)
SELECT id, every, period 
FROM public.celery_interval_schedule
ON CONFLICT DO NOTHING;

INSERT INTO celery_schema.celery_crontabschedule (id, minute, hour, day_of_week, day_of_month, month_of_year, timezone)
SELECT id, minute, hour, day_of_week, day_of_month, month_of_year, timezone
FROM public.celery_crontab_schedule
ON CONFLICT DO NOTHING;

-- Copy periodic tasks with discriminator and schedule_id fields
INSERT INTO celery_schema.celery_periodictask (
    id, name, task, interval_id, crontab_id, args, kwargs, queue, exchange, 
    routing_key, priority, enabled, expires, expire_seconds, one_off, 
    max_retries, soft_time_limit, hard_time_limit, description, date_changed,
    last_run_at, total_run_count, company_id,
    discriminator, schedule_id
)
SELECT 
    id, name, task, interval_id, crontab_id, args, kwargs, queue, exchange,
    routing_key, priority, enabled, expires, expire_seconds, one_off,
    max_retries, soft_time_limit, hard_time_limit, description, date_changed,
    last_run_at, total_run_count, company_id,
    -- Set discriminator based on which schedule type is used
    CASE 
        WHEN interval_id IS NOT NULL THEN 'intervalschedule'
        WHEN crontab_id IS NOT NULL THEN 'crontabschedule'
    END as discriminator,
    -- Set schedule_id to the appropriate FK value
    COALESCE(interval_id, crontab_id) as schedule_id
FROM public.celery_periodic_task
ON CONFLICT (name) DO NOTHING;

-- Update sequence values to match
SELECT setval('celery_schema.celery_intervalschedule_id_seq', 
    COALESCE((SELECT MAX(id) FROM celery_schema.celery_intervalschedule), 1));
    
SELECT setval('celery_schema.celery_crontabschedule_id_seq', 
    COALESCE((SELECT MAX(id) FROM celery_schema.celery_crontabschedule), 1));
    
SELECT setval('celery_schema.celery_periodictask_id_seq', 
    COALESCE((SELECT MAX(id) FROM celery_schema.celery_periodictask), 1));

-- Grant necessary permissions
GRANT USAGE ON SCHEMA celery_schema TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA celery_schema TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA celery_schema TO postgres, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA celery_schema TO anon, authenticated;