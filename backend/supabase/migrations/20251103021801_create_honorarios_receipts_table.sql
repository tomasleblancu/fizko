-- Migration: Create honorarios_receipts table
-- Description: Tabla para almacenar boletas de honorarios (recibidas y emitidas)

-- Tabla para almacenar boletas de honorarios (recibidas y emitidas)
CREATE TABLE IF NOT EXISTS honorarios_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Tipo de boleta (recibida o emitida)
    receipt_type TEXT NOT NULL CHECK (receipt_type IN ('received', 'issued')),

    -- Identificación de la boleta
    folio INTEGER,
    issue_date DATE NOT NULL,
    emission_date DATE,

    -- Información del emisor (quien presta el servicio)
    issuer_rut TEXT,
    issuer_name TEXT,

    -- Información del receptor (quien recibe el servicio)
    recipient_rut TEXT,
    recipient_name TEXT,

    -- Montos financieros
    gross_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
    issuer_retention NUMERIC(15, 2) NOT NULL DEFAULT 0,
    recipient_retention NUMERIC(15, 2) NOT NULL DEFAULT 0,
    net_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,

    -- Estado de la boleta
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled', 'vigente', 'anulada')),

    -- Datos adicionales
    is_professional_society BOOLEAN DEFAULT FALSE,
    is_manual BOOLEAN DEFAULT FALSE,
    emission_user TEXT,

    -- Referencia a contacto (opcional)
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,

    -- Integración con SII
    sii_track_id TEXT,

    -- Datos adicionales flexibles
    extra_data JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Constraints
    CONSTRAINT honorarios_receipts_gross_amount_check CHECK (gross_amount >= 0),
    CONSTRAINT honorarios_receipts_net_amount_check CHECK (net_amount >= 0)
);

-- Índices para consultas eficientes
CREATE INDEX IF NOT EXISTS ix_honorarios_receipts_company_id ON honorarios_receipts(company_id);
CREATE INDEX IF NOT EXISTS ix_honorarios_receipts_company_type ON honorarios_receipts(company_id, receipt_type);
CREATE INDEX IF NOT EXISTS ix_honorarios_receipts_company_date ON honorarios_receipts(company_id, issue_date);
CREATE INDEX IF NOT EXISTS ix_honorarios_receipts_issuer_rut ON honorarios_receipts(issuer_rut);
CREATE INDEX IF NOT EXISTS ix_honorarios_receipts_recipient_rut ON honorarios_receipts(recipient_rut);
CREATE INDEX IF NOT EXISTS ix_honorarios_receipts_contact_id ON honorarios_receipts(contact_id);
CREATE INDEX IF NOT EXISTS ix_honorarios_receipts_status ON honorarios_receipts(status);

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_honorarios_receipts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_honorarios_receipts_updated_at
    BEFORE UPDATE ON honorarios_receipts
    FOR EACH ROW
    EXECUTE FUNCTION update_honorarios_receipts_updated_at();

-- Comentarios para documentación
COMMENT ON TABLE honorarios_receipts IS 'Boletas de honorarios recibidas y emitidas por la empresa';
COMMENT ON COLUMN honorarios_receipts.receipt_type IS 'Tipo: received (recibida) o issued (emitida)';
COMMENT ON COLUMN honorarios_receipts.folio IS 'Número de folio de la boleta';
COMMENT ON COLUMN honorarios_receipts.gross_amount IS 'Monto bruto de honorarios';
COMMENT ON COLUMN honorarios_receipts.issuer_retention IS 'Retención aplicada por el emisor';
COMMENT ON COLUMN honorarios_receipts.recipient_retention IS 'Retención aplicada por el receptor (típicamente 10%)';
COMMENT ON COLUMN honorarios_receipts.net_amount IS 'Monto neto (líquido) a pagar/cobrar';
COMMENT ON COLUMN honorarios_receipts.is_professional_society IS 'Si la boleta es de sociedad profesional';
COMMENT ON COLUMN honorarios_receipts.is_manual IS 'Si la boleta fue ingresada manualmente';
