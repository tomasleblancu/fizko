-- Migration: Add phone verification columns to profiles
-- Created: 2025-10-22
-- Purpose: Add phone_verified and phone_verified_at columns to profiles table

-- Add phone_verified column (boolean, default false)
ALTER TABLE profiles
ADD COLUMN phone_verified BOOLEAN NOT NULL DEFAULT false;

-- Add phone_verified_at column (nullable timestamp)
ALTER TABLE profiles
ADD COLUMN phone_verified_at TIMESTAMP WITH TIME ZONE;

-- Add comment for documentation
COMMENT ON COLUMN profiles.phone_verified IS 'Whether the user phone number has been verified';
COMMENT ON COLUMN profiles.phone_verified_at IS 'Timestamp when the phone number was verified';
