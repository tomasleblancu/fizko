-- Create sales_leads table for contact form submissions
CREATE TABLE IF NOT EXISTS sales_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    company_name TEXT,
    message TEXT,
    source TEXT DEFAULT 'landing_page',
    status TEXT DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sales_leads_status_check CHECK (status IN ('new', 'contacted', 'qualified', 'converted', 'rejected'))
);

-- Create index on email for lookups
CREATE INDEX IF NOT EXISTS idx_sales_leads_email ON sales_leads(email);

-- Create index on status for filtering
CREATE INDEX IF NOT EXISTS idx_sales_leads_status ON sales_leads(status);

-- Create index on created_at for sorting
CREATE INDEX IF NOT EXISTS idx_sales_leads_created_at ON sales_leads(created_at DESC);

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_sales_leads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sales_leads_updated_at
    BEFORE UPDATE ON sales_leads
    FOR EACH ROW
    EXECUTE FUNCTION update_sales_leads_updated_at();

-- Enable RLS (Row Level Security)
ALTER TABLE sales_leads ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read all leads (for admin panel)
CREATE POLICY "Authenticated users can read sales leads"
    ON sales_leads
    FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Authenticated users can update leads (for admin panel)
CREATE POLICY "Authenticated users can update sales leads"
    ON sales_leads
    FOR UPDATE
    USING (auth.uid() IS NOT NULL);

-- Anyone can insert (contact form is public)
CREATE POLICY "Anyone can submit contact form"
    ON sales_leads
    FOR INSERT
    WITH CHECK (true);

COMMENT ON TABLE sales_leads IS 'Stores contact form submissions from the landing page';
COMMENT ON COLUMN sales_leads.source IS 'Source of the lead (landing_page, referral, etc.)';
COMMENT ON COLUMN sales_leads.status IS 'Lead status: new, contacted, qualified, converted, rejected';
