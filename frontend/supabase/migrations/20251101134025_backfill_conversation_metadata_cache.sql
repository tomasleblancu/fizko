-- Migration: Backfill auth cache in existing WhatsApp conversations
-- Purpose: Add user_id and company_id to metadata of existing conversations
-- Date: 2025-11-01

-- Description:
-- This migration adds cached authentication data to existing WhatsApp conversations
-- that were created before the optimization was implemented. New conversations
-- automatically get this cache, but old ones need to be backfilled.

-- Step 1: Add user_id to metadata for all WhatsApp conversations without it
UPDATE conversations
SET metadata = jsonb_set(
    metadata,
    '{user_id}',
    to_jsonb(user_id::text)
)
WHERE metadata->>'channel' = 'whatsapp'
  AND metadata->>'user_id' IS NULL;

-- Step 2: Add company_id to metadata by joining with sessions table
-- We get the most recent company_id for each user
WITH user_companies AS (
  SELECT DISTINCT ON (user_id)
    user_id,
    company_id
  FROM sessions
  WHERE company_id IS NOT NULL
  ORDER BY user_id, created_at DESC
)
UPDATE conversations c
SET metadata = jsonb_set(
    c.metadata,
    '{company_id}',
    to_jsonb(uc.company_id::text)
)
FROM user_companies uc
WHERE c.user_id = uc.user_id
  AND c.metadata->>'channel' = 'whatsapp'
  AND c.metadata->>'company_id' IS NULL;

-- Verification query (run manually to check results):
-- SELECT
--     COUNT(*) as total_whatsapp_convs,
--     COUNT(*) FILTER (WHERE metadata->>'user_id' IS NOT NULL) as with_user_cache,
--     COUNT(*) FILTER (WHERE metadata->>'company_id' IS NOT NULL) as with_company_cache,
--     COUNT(*) FILTER (WHERE metadata->>'user_id' IS NOT NULL AND metadata->>'company_id' IS NOT NULL) as with_full_cache
-- FROM conversations
-- WHERE metadata->>'channel' = 'whatsapp';
