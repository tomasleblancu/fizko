-- Migration: Add phone verification fields to profiles table
-- Description: Adds phone_verified and phone_verified_at columns to track phone number verification status
-- Date: 2025-10-22

-- Add phone_verified column (boolean, default false)
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN NOT NULL DEFAULT false;

-- Add phone_verified_at column (timestamp, nullable)
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS phone_verified_at TIMESTAMP WITH TIME ZONE NULL;

-- Add comments to document the columns
COMMENT ON COLUMN profiles.phone_verified IS 'Whether the user''s phone number has been verified';
COMMENT ON COLUMN profiles.phone_verified_at IS 'Timestamp when the phone number was verified';

-- Create index on phone_verified for faster queries
CREATE INDEX IF NOT EXISTS idx_profiles_phone_verified ON profiles(phone_verified);