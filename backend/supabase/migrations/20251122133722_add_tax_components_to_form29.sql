-- =====================================================================
-- Migration: Add tax component fields to form29
-- Date: 2025-11-22
-- =====================================================================
-- Description: Adds fields for complete tax calculation breakdown
--              to match the tax calculation widget requirements.
--
-- Fields added:
-- - overdue_iva_credit: IVA fuera de plazo (can't be recovered)
-- - ppm: Pago Provisional Mensual (0.125% of net revenue)
-- - retencion: Retención from honorarios receipts
-- - reverse_charge_withholding: Retención Cambio de Sujeto (código 46)
-- - impuesto_trabajadores: Tax from employee payroll (for future use)
-- =====================================================================

-- Add tax component columns to form29
ALTER TABLE form29
ADD COLUMN IF NOT EXISTS overdue_iva_credit NUMERIC(15, 2) DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS ppm NUMERIC(15, 2) DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS retencion NUMERIC(15, 2) DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS reverse_charge_withholding NUMERIC(15, 2) DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS impuesto_trabajadores NUMERIC(15, 2) DEFAULT 0 NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN form29.overdue_iva_credit IS 'IVA fuera de plazo - IVA from overdue documents that cannot be recovered. Always adds to tax burden.';
COMMENT ON COLUMN form29.ppm IS 'Pago Provisional Mensual - Provisional monthly payment for annual income tax (0.125% of net revenue excluding documents with overdue IVA).';
COMMENT ON COLUMN form29.retencion IS 'Retención from honorarios receipts - Tax withholding from professional services invoices (typically 12.25%).';
COMMENT ON COLUMN form29.reverse_charge_withholding IS 'Retención Cambio de Sujeto - Reverse charge withholding (document code 46) where buyer pays seller''s IVA obligation.';
COMMENT ON COLUMN form29.impuesto_trabajadores IS 'Impuesto de trabajadores - Tax from employee payroll (for future payroll integration).';

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_form29_overdue_iva
ON form29(company_id, period_year, period_month)
WHERE overdue_iva_credit > 0;

CREATE INDEX IF NOT EXISTS idx_form29_ppm
ON form29(company_id, period_year, period_month)
WHERE ppm > 0;

-- =====================================================================
-- END OF MIGRATION
-- =====================================================================
