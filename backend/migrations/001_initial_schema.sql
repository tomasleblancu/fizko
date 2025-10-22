-- =====================================================================
-- Fizko Database Migration - Initial Schema
-- =====================================================================
-- Description: Creates all tables for Fizko tax/accounting platform
-- Version: 1.0
-- Date: 2025-01-20
--
-- Architecture:
-- - Users can access multiple companies via Sessions
-- - Company data split: basic info (companies) + tax data (company_tax_info)
-- - Tax documents separated: purchases vs sales
-- - Form29 for monthly IVA declarations
-- =====================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- USER TABLES
-- =====================================================================

-- Profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    company_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    name TEXT DEFAULT ''::text,
    lastname TEXT DEFAULT ''::text,
    rol TEXT DEFAULT ''::text
);

-- Enable RLS on profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- =====================================================================
-- COMPANY TABLES
-- =====================================================================

-- Companies table (basic company information)
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rut TEXT UNIQUE NOT NULL,
    business_name TEXT NOT NULL,
    trade_name TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Company tax info table (tax-specific information)
CREATE TABLE IF NOT EXISTS company_tax_info (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID UNIQUE NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    tax_regime TEXT DEFAULT 'regimen_general'::text NOT NULL,
    sii_activity_code TEXT,
    sii_activity_name TEXT,
    legal_representative_rut TEXT,
    legal_representative_name TEXT,
    start_of_activities_date DATE,
    accounting_start_month INTEGER DEFAULT 1 NOT NULL,
    extra_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT company_tax_info_tax_regime_check
        CHECK (tax_regime = ANY (ARRAY['regimen_general'::text, 'regimen_simplificado'::text, 'pro_pyme'::text, '14_ter'::text])),
    CONSTRAINT company_tax_info_accounting_start_month_check
        CHECK (accounting_start_month >= 1 AND accounting_start_month <= 12)
);

-- Enable RLS on companies and company_tax_info
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_tax_info ENABLE ROW LEVEL SECURITY;

-- =====================================================================
-- SESSION TABLE (User-Company Link)
-- =====================================================================

-- Sessions table (links users to companies)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true NOT NULL,
    cookies JSONB DEFAULT '{}'::jsonb,
    resources JSONB DEFAULT '{}'::jsonb,
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Unique constraint: one session per user-company pair
    CONSTRAINT sessions_user_company_unique UNIQUE (user_id, company_id)
);

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS ix_sessions_user_company ON sessions(user_id, company_id);
CREATE INDEX IF NOT EXISTS ix_sessions_company_active ON sessions(company_id, is_active);

-- Enable RLS on sessions
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for sessions (users can only see their own sessions)
CREATE POLICY "Users can view own sessions"
    ON sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions"
    ON sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions"
    ON sessions FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions"
    ON sessions FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for companies (users can view companies they have sessions for)
CREATE POLICY "Users can view companies via sessions"
    ON companies FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = companies.id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

CREATE POLICY "Users can update companies via sessions"
    ON companies FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = companies.id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- RLS Policies for company_tax_info
CREATE POLICY "Users can view company tax info via sessions"
    ON company_tax_info FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = company_tax_info.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

CREATE POLICY "Users can update company tax info via sessions"
    ON company_tax_info FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = company_tax_info.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- =====================================================================
-- TAX DOCUMENT TABLES (Separated by type)
-- =====================================================================

-- Purchase documents table (facturas de compra - received)
CREATE TABLE IF NOT EXISTS purchase_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    folio INTEGER,
    issue_date DATE NOT NULL,
    sender_rut TEXT,
    sender_name TEXT,
    net_amount NUMERIC(15, 2) NOT NULL,
    tax_amount NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    exempt_amount NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    total_amount NUMERIC(15, 2) NOT NULL,
    status TEXT DEFAULT 'pending'::text NOT NULL,
    dte_xml TEXT,
    sii_track_id TEXT,
    file_url TEXT,
    extra_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT purchase_documents_document_type_check
        CHECK (document_type = ANY (ARRAY['factura_compra'::text, 'nota_credito_compra'::text, 'nota_debito_compra'::text])),
    CONSTRAINT purchase_documents_status_check
        CHECK (status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, 'cancelled'::text])),
    CONSTRAINT purchase_documents_total_amount_check
        CHECK (total_amount >= 0)
);

-- Indexes for purchase_documents
CREATE INDEX IF NOT EXISTS ix_purchase_documents_company_type ON purchase_documents(company_id, document_type);
CREATE INDEX IF NOT EXISTS ix_purchase_documents_company_date ON purchase_documents(company_id, issue_date);

-- Enable RLS on purchase_documents
ALTER TABLE purchase_documents ENABLE ROW LEVEL SECURITY;

-- Sales documents table (facturas de venta - issued)
CREATE TABLE IF NOT EXISTS sales_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    folio INTEGER,
    issue_date DATE NOT NULL,
    recipient_rut TEXT,
    recipient_name TEXT,
    net_amount NUMERIC(15, 2) NOT NULL,
    tax_amount NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    exempt_amount NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    total_amount NUMERIC(15, 2) NOT NULL,
    status TEXT DEFAULT 'pending'::text NOT NULL,
    dte_xml TEXT,
    sii_track_id TEXT,
    file_url TEXT,
    extra_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT sales_documents_document_type_check
        CHECK (document_type = ANY (ARRAY['factura_venta'::text, 'boleta'::text, 'nota_credito_venta'::text, 'nota_debito_venta'::text, 'factura_exenta'::text])),
    CONSTRAINT sales_documents_status_check
        CHECK (status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, 'cancelled'::text])),
    CONSTRAINT sales_documents_total_amount_check
        CHECK (total_amount >= 0)
);

-- Indexes for sales_documents
CREATE INDEX IF NOT EXISTS ix_sales_documents_company_type ON sales_documents(company_id, document_type);
CREATE INDEX IF NOT EXISTS ix_sales_documents_company_date ON sales_documents(company_id, issue_date);

-- Enable RLS on sales_documents
ALTER TABLE sales_documents ENABLE ROW LEVEL SECURITY;

-- RLS Policies for purchase_documents
CREATE POLICY "Users can view purchase documents via sessions"
    ON purchase_documents FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = purchase_documents.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

CREATE POLICY "Users can manage purchase documents via sessions"
    ON purchase_documents FOR ALL
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = purchase_documents.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- RLS Policies for sales_documents
CREATE POLICY "Users can view sales documents via sessions"
    ON sales_documents FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = sales_documents.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

CREATE POLICY "Users can manage sales documents via sessions"
    ON sales_documents FOR ALL
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = sales_documents.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- =====================================================================
-- FORM 29 TABLE (Monthly IVA Declaration)
-- =====================================================================

CREATE TABLE IF NOT EXISTS form29 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,
    total_sales NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    taxable_sales NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    exempt_sales NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    sales_tax NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    total_purchases NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    taxable_purchases NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    purchases_tax NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    iva_to_pay NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    iva_credit NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    net_iva NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    status TEXT DEFAULT 'draft'::text NOT NULL,
    submission_date TIMESTAMPTZ,
    folio TEXT,
    extra_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Unique constraint: one Form29 per company per period
    CONSTRAINT form29_company_period_unique UNIQUE (company_id, period_year, period_month),

    -- Constraints
    CONSTRAINT form29_period_month_check
        CHECK (period_month >= 1 AND period_month <= 12),
    CONSTRAINT form29_status_check
        CHECK (status = ANY (ARRAY['draft'::text, 'submitted'::text]))
);

-- Index for form29
CREATE INDEX IF NOT EXISTS ix_form29_company_period ON form29(company_id, period_year, period_month);

-- Enable RLS on form29
ALTER TABLE form29 ENABLE ROW LEVEL SECURITY;

-- RLS Policies for form29
CREATE POLICY "Users can view form29 via sessions"
    ON form29 FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = form29.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

CREATE POLICY "Users can manage form29 via sessions"
    ON form29 FOR ALL
    USING (EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.company_id = form29.company_id
        AND sessions.user_id = auth.uid()
        AND sessions.is_active = true
    ));

-- =====================================================================
-- CHAT TABLES (ChatKit integration)
-- =====================================================================

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    chatkit_session_id TEXT,
    title TEXT DEFAULT 'Nueva conversación'::text NOT NULL,
    status TEXT DEFAULT 'active'::text NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT conversations_status_check
        CHECK (status = ANY (ARRAY['active'::text, 'archived'::text, 'completed'::text]))
);

-- Enable RLS on conversations
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own conversations"
    ON conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own conversations"
    ON conversations FOR ALL
    USING (auth.uid() = user_id);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT messages_role_check
        CHECK (role = ANY (ARRAY['user'::text, 'assistant'::text, 'system'::text]))
);

-- Enable RLS on messages
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view messages from own conversations"
    ON messages FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM conversations
        WHERE conversations.id = messages.conversation_id
        AND conversations.user_id = auth.uid()
    ));

CREATE POLICY "Users can create messages in own conversations"
    ON messages FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM conversations
        WHERE conversations.id = conversation_id
        AND conversations.user_id = auth.uid()
    ));

-- ChatKit attachments table
CREATE TABLE IF NOT EXISTS attachments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    thread_id TEXT,
    upload_url TEXT,
    preview_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =====================================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_company_tax_info_updated_at BEFORE UPDATE ON company_tax_info
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_purchase_documents_updated_at BEFORE UPDATE ON purchase_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sales_documents_updated_at BEFORE UPDATE ON sales_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_form29_updated_at BEFORE UPDATE ON form29
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attachments_updated_at BEFORE UPDATE ON attachments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- COMMENTS (Documentation)
-- =====================================================================

COMMENT ON TABLE profiles IS 'User profiles extending Supabase auth.users';
COMMENT ON TABLE companies IS 'Basic company information (RUT, name, contact)';
COMMENT ON TABLE company_tax_info IS 'Tax-specific company information (regime, SII data)';
COMMENT ON TABLE sessions IS 'User-company sessions (many-to-many link with cookies/resources)';
COMMENT ON TABLE purchase_documents IS 'Purchase documents (facturas de compra, received from suppliers)';
COMMENT ON TABLE sales_documents IS 'Sales documents (facturas de venta, issued to clients)';
COMMENT ON TABLE form29 IS 'Monthly IVA declarations (Form 29)';
COMMENT ON TABLE conversations IS 'ChatKit conversation threads';
COMMENT ON TABLE messages IS 'Messages within ChatKit conversations';
COMMENT ON TABLE attachments IS 'ChatKit file attachments metadata';

-- =====================================================================
-- END OF MIGRATION
-- =====================================================================
