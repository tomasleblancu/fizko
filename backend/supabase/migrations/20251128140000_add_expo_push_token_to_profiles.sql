-- =====================================================================
-- Add Expo Push Token Support
-- =====================================================================
-- Description: Adds expo_push_token field to profiles for mobile push notifications
-- Date: 2025-11-28
-- =====================================================================

-- Add expo_push_token column to profiles
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS expo_push_token TEXT;

-- Add index for faster lookups when sending notifications
CREATE INDEX IF NOT EXISTS idx_profiles_expo_push_token
ON profiles(expo_push_token)
WHERE expo_push_token IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN profiles.expo_push_token IS 'Expo push notification token for mobile app (format: ExponentPushToken[...])';
