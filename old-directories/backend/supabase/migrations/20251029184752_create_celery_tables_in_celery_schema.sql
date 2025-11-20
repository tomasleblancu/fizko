-- Create tables in celery_schema with names expected by sqlalchemy-celery-beat
-- These match our updated models exactly

-- 1. celery_intervalschedule
CREATE TABLE IF NOT EXISTS celery_schema.celery_intervalschedule (
    id SERIAL PRIMARY KEY,
    every INTEGER NOT NULL,
    period VARCHAR(24) NOT NULL
);

-- 2. celery_crontabschedule
CREATE TABLE IF NOT EXISTS celery_schema.celery_crontabschedule (
    id SERIAL PRIMARY KEY,
    minute VARCHAR(64) NOT NULL DEFAULT '*',
    hour VARCHAR(64) NOT NULL DEFAULT '*',
    day_of_week VARCHAR(64) NOT NULL DEFAULT '*',
    day_of_month VARCHAR(64) NOT NULL DEFAULT '*',
    month_of_year VARCHAR(64) NOT NULL DEFAULT '*',
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC'
);

-- 3. celery_periodictaskchanged
CREATE TABLE IF NOT EXISTS celery_schema.celery_periodictaskchanged (
    id SERIAL PRIMARY KEY,
    last_update TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. celery_taskresult
CREATE TABLE IF NOT EXISTS celery_schema.celery_taskresult (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255),
    periodic_task_name VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    worker VARCHAR(100),
    content_type VARCHAR(128) NOT NULL DEFAULT 'application/json',
    content_encoding VARCHAR(64) NOT NULL DEFAULT 'utf-8',
    result JSONB,
    traceback TEXT,
    date_created TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    date_done TIMESTAMPTZ,
    runtime DOUBLE PRECISION,
    company_id UUID REFERENCES companies(id)
);

-- 5. celery_periodictask
CREATE TABLE IF NOT EXISTS celery_schema.celery_periodictask (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    task VARCHAR(200) NOT NULL,
    interval_id INTEGER REFERENCES celery_schema.celery_intervalschedule(id) ON DELETE CASCADE,
    crontab_id INTEGER REFERENCES celery_schema.celery_crontabschedule(id) ON DELETE CASCADE,
    args JSONB NOT NULL DEFAULT '[]'::jsonb,
    kwargs JSONB NOT NULL DEFAULT '{}'::jsonb,
    queue VARCHAR(200),
    exchange VARCHAR(200),
    routing_key VARCHAR(200),
    headers TEXT NOT NULL DEFAULT '{}',
    priority SMALLINT,
    expires TIMESTAMPTZ,
    expire_seconds INTEGER,
    one_off BOOLEAN NOT NULL DEFAULT FALSE,
    start_time TIMESTAMPTZ,
    max_retries INTEGER,
    soft_time_limit INTEGER,
    hard_time_limit INTEGER,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    total_run_count INTEGER NOT NULL DEFAULT 0,
    discriminator VARCHAR(20) NOT NULL,
    schedule_id INTEGER NOT NULL,
    date_changed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT,
    company_id UUID REFERENCES companies(id),
    CONSTRAINT check_schedule CHECK (
        (interval_id IS NOT NULL AND crontab_id IS NULL) OR
        (interval_id IS NULL AND crontab_id IS NOT NULL)
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_periodictask_enabled ON celery_schema.celery_periodictask(enabled);
CREATE INDEX IF NOT EXISTS idx_periodictask_company ON celery_schema.celery_periodictask(company_id);
CREATE INDEX IF NOT EXISTS idx_taskresult_company ON celery_schema.celery_taskresult(company_id);
CREATE INDEX IF NOT EXISTS idx_taskresult_status ON celery_schema.celery_taskresult(status);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA celery_schema TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA celery_schema TO postgres, service_role;