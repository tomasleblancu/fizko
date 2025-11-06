-- Migration: Phone Verification System
-- Description: Creates table for storing phone verification codes sent via WhatsApp
-- Author: Claude
-- Date: 2025-10-28

-- Create phone_verifications table
CREATE TABLE IF NOT EXISTS phone_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    phone_number TEXT NOT NULL,
    code TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    expires_at TIMESTAMPTZ NOT NULL,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX idx_phone_verifications_user_id ON phone_verifications(user_id);
CREATE INDEX idx_phone_verifications_phone_number ON phone_verifications(phone_number);
CREATE INDEX idx_phone_verifications_created_at ON phone_verifications(created_at);
CREATE INDEX idx_phone_verifications_expires_at ON phone_verifications(expires_at);

-- Add RLS policies
ALTER TABLE phone_verifications ENABLE ROW LEVEL SECURITY;

-- Users can only see their own verification codes
CREATE POLICY "Users can view own verification codes"
    ON phone_verifications
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own verification codes
CREATE POLICY "Users can create own verification codes"
    ON phone_verifications
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own verification codes
CREATE POLICY "Users can update own verification codes"
    ON phone_verifications
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Add comment
COMMENT ON TABLE phone_verifications IS 'Stores verification codes for phone number verification via WhatsApp';
