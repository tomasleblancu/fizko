-- Add missing schedule types that sqlalchemy-celery-beat expects

-- Solar schedule (for sunrise/sunset based tasks)
CREATE TABLE IF NOT EXISTS celery_schema.celery_solarschedule (
    id SERIAL PRIMARY KEY,
    event VARCHAR(24) NOT NULL,
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL
);

-- Clocked schedule (for one-time tasks at specific datetime)
CREATE TABLE IF NOT EXISTS celery_schema.celery_clockedschedule (
    id SERIAL PRIMARY KEY,
    clocked_time TIMESTAMPTZ NOT NULL
);

-- Grant permissions
GRANT ALL ON celery_schema.celery_solarschedule TO postgres, service_role;
GRANT ALL ON celery_schema.celery_clockedschedule TO postgres, service_role;
GRANT ALL ON SEQUENCE celery_schema.celery_solarschedule_id_seq TO postgres, service_role;
GRANT ALL ON SEQUENCE celery_schema.celery_clockedschedule_id_seq TO postgres, service_role;