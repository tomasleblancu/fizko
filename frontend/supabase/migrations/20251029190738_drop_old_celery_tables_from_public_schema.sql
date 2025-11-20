-- Drop old Celery tables from public schema
-- These are no longer used since we moved everything to celery_schema

DROP TABLE IF EXISTS public.celery_periodictask CASCADE;
DROP TABLE IF EXISTS public.celery_intervalschedule CASCADE;
DROP TABLE IF EXISTS public.celery_crontabschedule CASCADE;
DROP TABLE IF EXISTS public.celery_periodictaskchanged CASCADE;
DROP TABLE IF EXISTS public.celery_clockedschedule CASCADE;
DROP TABLE IF EXISTS public.celery_solarschedule CASCADE;