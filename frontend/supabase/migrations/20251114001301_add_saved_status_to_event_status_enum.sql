-- Add 'saved' value to event_status enum (for production sync via deploy)
-- This fixes the error: invalid input value for enum event_status: "saved"
ALTER TYPE event_status ADD VALUE IF NOT EXISTS 'saved';