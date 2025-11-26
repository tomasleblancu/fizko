-- Phone Verification Codes for WhatsApp OTP Authentication
-- Stores temporary verification codes sent via WhatsApp

CREATE TABLE IF NOT EXISTS phone_verification_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT NOT NULL,
    code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    verified_at TIMESTAMPTZ,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    metadata JSONB DEFAULT '{}'::JSONB
);

-- Index for fast lookup by phone number
CREATE INDEX idx_phone_verification_codes_phone ON phone_verification_codes(phone_number);

-- Index for cleanup of expired codes
CREATE INDEX idx_phone_verification_codes_expires ON phone_verification_codes(expires_at);

-- Index for active (non-verified, non-expired) codes
CREATE INDEX idx_phone_verification_codes_active ON phone_verification_codes(phone_number, verified_at, expires_at)
WHERE verified_at IS NULL;

-- RLS Policies (restrictive - only backend should access)
ALTER TABLE phone_verification_codes ENABLE ROW LEVEL SECURITY;

-- Only service role can access verification codes
CREATE POLICY "Service role can manage verification codes"
ON phone_verification_codes
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Function to cleanup expired codes (run periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_verification_codes()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM phone_verification_codes
    WHERE expires_at < NOW() - INTERVAL '1 hour';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON TABLE phone_verification_codes IS 'Temporary verification codes for WhatsApp OTP authentication';
COMMENT ON COLUMN phone_verification_codes.phone_number IS 'Phone number in E.164 format (e.g., +56912345678)';
COMMENT ON COLUMN phone_verification_codes.code IS 'Six-digit verification code';
COMMENT ON COLUMN phone_verification_codes.expires_at IS 'Code expiration time (typically 5-10 minutes from creation)';
COMMENT ON COLUMN phone_verification_codes.verified_at IS 'Timestamp when code was successfully verified (NULL if not verified)';
COMMENT ON COLUMN phone_verification_codes.attempts IS 'Number of verification attempts made';
COMMENT ON COLUMN phone_verification_codes.max_attempts IS 'Maximum allowed attempts before code is invalidated';
