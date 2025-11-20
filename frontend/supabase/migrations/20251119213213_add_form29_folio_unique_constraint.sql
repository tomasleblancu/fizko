-- Add unique constraint for company_id + folio in form29 table
-- This allows upsert operations based on folio without needing to parse period
-- Migration: 20251119000001_add_form29_folio_unique_constraint

ALTER TABLE form29
ADD CONSTRAINT form29_company_folio_unique UNIQUE (company_id, folio);
