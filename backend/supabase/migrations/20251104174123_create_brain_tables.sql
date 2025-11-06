-- Migration: Create UserBrain and CompanyBrain tables for Mem0 memory tracking
-- Description: Creates tables to track memories stored in Mem0, enabling updates instead of duplicates

-- ============================================================================
-- USER BRAIN TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_brain (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_id VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    extra_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS ix_user_brain_user_id ON public.user_brain(user_id);
CREATE INDEX IF NOT EXISTS ix_user_brain_memory_id ON public.user_brain(memory_id);
CREATE INDEX IF NOT EXISTS ix_user_brain_slug ON public.user_brain(slug);
CREATE INDEX IF NOT EXISTS ix_user_brain_created ON public.user_brain(created_at);

-- Unique constraint for user_id + slug
CREATE UNIQUE INDEX IF NOT EXISTS ix_user_brain_user_slug ON public.user_brain(user_id, slug);

-- Comments
COMMENT ON TABLE public.user_brain IS 'Tracks user-specific memories stored in Mem0';
COMMENT ON COLUMN public.user_brain.memory_id IS 'Mem0 memory ID returned from API';
COMMENT ON COLUMN public.user_brain.slug IS 'Descriptive slug to identify the memory (e.g., user_tax_regime_preference)';
COMMENT ON COLUMN public.user_brain.content IS 'The actual memory content stored in Mem0';
COMMENT ON COLUMN public.user_brain.extra_metadata IS 'Additional metadata stored with the memory';

-- ============================================================================
-- COMPANY BRAIN TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.company_brain (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
    memory_id VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    extra_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS ix_company_brain_company_id ON public.company_brain(company_id);
CREATE INDEX IF NOT EXISTS ix_company_brain_memory_id ON public.company_brain(memory_id);
CREATE INDEX IF NOT EXISTS ix_company_brain_slug ON public.company_brain(slug);
CREATE INDEX IF NOT EXISTS ix_company_brain_created ON public.company_brain(created_at);

-- Unique constraint for company_id + slug
CREATE UNIQUE INDEX IF NOT EXISTS ix_company_brain_company_slug ON public.company_brain(company_id, slug);

-- Comments
COMMENT ON TABLE public.company_brain IS 'Tracks company-wide memories stored in Mem0';
COMMENT ON COLUMN public.company_brain.memory_id IS 'Mem0 memory ID returned from API';
COMMENT ON COLUMN public.company_brain.slug IS 'Descriptive slug to identify the memory (e.g., company_tax_regime)';
COMMENT ON COLUMN public.company_brain.content IS 'The actual memory content stored in Mem0';
COMMENT ON COLUMN public.company_brain.extra_metadata IS 'Additional metadata stored with the memory';

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_brain_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to user_brain
DROP TRIGGER IF EXISTS user_brain_updated_at ON public.user_brain;
CREATE TRIGGER user_brain_updated_at
    BEFORE UPDATE ON public.user_brain
    FOR EACH ROW
    EXECUTE FUNCTION update_brain_updated_at();

-- Apply trigger to company_brain
DROP TRIGGER IF EXISTS company_brain_updated_at ON public.company_brain;
CREATE TRIGGER company_brain_updated_at
    BEFORE UPDATE ON public.company_brain
    FOR EACH ROW
    EXECUTE FUNCTION update_brain_updated_at();

-- ============================================================================
-- RLS (Row Level Security) POLICIES
-- ============================================================================

-- Enable RLS
ALTER TABLE public.user_brain ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_brain ENABLE ROW LEVEL SECURITY;

-- User Brain: Users can only access their own memories
CREATE POLICY "Users can view their own brain memories"
    ON public.user_brain
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own brain memories"
    ON public.user_brain
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own brain memories"
    ON public.user_brain
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own brain memories"
    ON public.user_brain
    FOR DELETE
    USING (auth.uid() = user_id);

-- Company Brain: Users with active sessions can access company memories
CREATE POLICY "Users can view company brain memories for their companies"
    ON public.company_brain
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.sessions
            WHERE sessions.user_id = auth.uid()
            AND sessions.company_id = company_brain.company_id
            AND sessions.is_active = true
        )
    );

CREATE POLICY "Users can insert company brain memories for their companies"
    ON public.company_brain
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.sessions
            WHERE sessions.user_id = auth.uid()
            AND sessions.company_id = company_brain.company_id
            AND sessions.is_active = true
        )
    );

CREATE POLICY "Users can update company brain memories for their companies"
    ON public.company_brain
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.sessions
            WHERE sessions.user_id = auth.uid()
            AND sessions.company_id = company_brain.company_id
            AND sessions.is_active = true
        )
    );

CREATE POLICY "Users can delete company brain memories for their companies"
    ON public.company_brain
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.sessions
            WHERE sessions.user_id = auth.uid()
            AND sessions.company_id = company_brain.company_id
            AND sessions.is_active = true
        )
    );
