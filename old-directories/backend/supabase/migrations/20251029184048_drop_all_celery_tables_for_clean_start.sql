-- Drop all manually created Celery tables in public schema
DROP TABLE IF EXISTS public.celery_periodic_task CASCADE;
DROP TABLE IF EXISTS public.celery_interval_schedule CASCADE;
DROP TABLE IF EXISTS public.celery_crontab_schedule CASCADE;
DROP TABLE IF EXISTS public.celery_periodic_task_changed CASCADE;
DROP TABLE IF EXISTS public.celery_task_result CASCADE;

-- Drop everything in celery_schema and recreate it fresh
DROP SCHEMA IF EXISTS celery_schema CASCADE;
CREATE SCHEMA celery_schema;

-- Grant permissions so Celery Beat can create tables
GRANT ALL ON SCHEMA celery_schema TO postgres, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA celery_schema TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA celery_schema TO postgres, service_role;

-- Allow service_role to create tables in celery_schema
ALTER DEFAULT PRIVILEGES IN SCHEMA celery_schema GRANT ALL ON TABLES TO postgres, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA celery_schema GRANT ALL ON SEQUENCES TO postgres, service_role;