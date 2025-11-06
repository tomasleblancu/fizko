-- Clean up duplicate conversations
-- Keep only the most recent conversation for each (chatkit_session_id, user_id) combination

WITH ranked_conversations AS (
  SELECT
    id,
    chatkit_session_id,
    user_id,
    created_at,
    ROW_NUMBER() OVER (
      PARTITION BY chatkit_session_id, user_id
      ORDER BY created_at DESC
    ) as rn
  FROM conversations
  WHERE chatkit_session_id IS NOT NULL
),
duplicates_to_delete AS (
  SELECT id
  FROM ranked_conversations
  WHERE rn > 1
)
DELETE FROM conversations
WHERE id IN (SELECT id FROM duplicates_to_delete);

-- Add unique index to prevent future duplicates
-- Using partial unique index instead of constraint (more flexible)
DROP INDEX IF EXISTS idx_conversations_chatkit_session_user_unique;

CREATE UNIQUE INDEX idx_conversations_chatkit_session_user_unique
ON conversations(chatkit_session_id, user_id)
WHERE chatkit_session_id IS NOT NULL;
