-- Migration: Personnel Management System (Simplified)
-- Description: Creates tables for managing employees and their payroll
-- Author: Fizko System
-- Date: 2025-10-27

-- ============================================================================
-- PEOPLE TABLE (Empleados)
-- ============================================================================
CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Personal Information
    rut VARCHAR(20) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    birth_date DATE,

    -- Position and Contract
    position_title VARCHAR(100),
    contract_type VARCHAR(50), -- indefinido, plazo_fijo, honorarios
    hire_date DATE,

    -- Salary Information
    base_salary NUMERIC(15, 2) NOT NULL DEFAULT 0,

    -- AFP (Pension)
    afp_provider VARCHAR(100),
    afp_percentage NUMERIC(5, 2) DEFAULT 10.49, -- Default AFP rate

    -- Health Insurance
    health_provider VARCHAR(100), -- Fonasa, Isapre name
    health_plan VARCHAR(100),
    health_percentage NUMERIC(5, 2), -- For Isapre
    health_fixed_amount NUMERIC(15, 2), -- For Isapre UF amount

    -- Bank Information
    bank_name VARCHAR(100),
    bank_account_type VARCHAR(50), -- cuenta corriente, cuenta vista, cuenta ahorro
    bank_account_number VARCHAR(50),

    -- Employment Status
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, inactive, terminated
    termination_date DATE,
    termination_reason TEXT,

    -- Additional Data
    notes TEXT,
    photo_url TEXT,
    extra_data JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Constraints
    CONSTRAINT people_status_check CHECK (status IN ('active', 'inactive', 'terminated')),
    CONSTRAINT people_contract_type_check CHECK (contract_type IS NULL OR contract_type IN ('indefinido', 'plazo_fijo', 'honorarios', 'por_obra', 'part_time')),
    CONSTRAINT people_company_rut_unique UNIQUE (company_id, rut)
);

-- Indexes for people
CREATE INDEX idx_people_company_id ON people(company_id);
CREATE INDEX idx_people_rut ON people(rut);
CREATE INDEX idx_people_status ON people(status);
CREATE INDEX idx_people_hire_date ON people(hire_date);

COMMENT ON TABLE people IS 'Stores employee information for payroll management';
COMMENT ON COLUMN people.afp_percentage IS 'AFP contribution percentage (typically 10-13%)';
COMMENT ON COLUMN people.health_percentage IS 'Health insurance percentage for Isapre';
COMMENT ON COLUMN people.health_fixed_amount IS 'Fixed UF amount for Isapre plans';

-- ============================================================================
-- PAYROLL TABLE (Liquidaciones de Sueldo)
-- ============================================================================
CREATE TABLE IF NOT EXISTS payroll (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    -- Period Information
    period_month INTEGER NOT NULL, -- 1-12
    period_year INTEGER NOT NULL,
    payment_date DATE,
    worked_days NUMERIC(5, 2) DEFAULT 30,

    -- Base Salary
    base_salary NUMERIC(15, 2) NOT NULL DEFAULT 0,

    -- HABERES IMPONIBLES (Taxable Income)
    -- These are stored as JSONB array: [{name: "Gratificación", amount: 209396}, ...]
    taxable_income_items JSONB DEFAULT '[]'::jsonb,
    total_taxable_income NUMERIC(15, 2) DEFAULT 0,

    -- HABERES NO IMPONIBLES (Non-taxable Income)
    -- These are stored as JSONB array: [{name: "Colación", amount: 300000}, ...]
    non_taxable_income_items JSONB DEFAULT '[]'::jsonb,
    total_non_taxable_income NUMERIC(15, 2) DEFAULT 0,

    -- TOTAL HABERES
    total_income NUMERIC(15, 2) DEFAULT 0,

    -- DESCUENTOS LEGALES (Legal Deductions)
    afp_deduction NUMERIC(15, 2) DEFAULT 0, -- Cotiz. Previ. Obligatoria (AFP)
    health_deduction NUMERIC(15, 2) DEFAULT 0, -- Cotiz. Salud Obligatoria (7% or Isapre)
    unemployment_insurance NUMERIC(15, 2) DEFAULT 0, -- Seguro de Cesantía
    income_tax NUMERIC(15, 2) DEFAULT 0, -- Impuesto Único (segunda categoría)
    total_legal_deductions NUMERIC(15, 2) DEFAULT 0,

    -- OTROS DESCUENTOS (Other Deductions)
    -- These are stored as JSONB array: [{name: "Préstamo", amount: 50000}, ...]
    other_deductions_items JSONB DEFAULT '[]'::jsonb,
    total_other_deductions NUMERIC(15, 2) DEFAULT 0,

    -- TOTAL DESCUENTOS
    total_deductions NUMERIC(15, 2) DEFAULT 0,

    -- BASES IMPONIBLES (For reference/calculation)
    pension_base NUMERIC(15, 2) DEFAULT 0, -- IMP. PREV./SALUD
    unemployment_base NUMERIC(15, 2) DEFAULT 0, -- IMP. CESANTÍA
    taxable_base NUMERIC(15, 2) DEFAULT 0, -- BASE TRIBUTABLE

    -- NET SALARY
    net_salary NUMERIC(15, 2) DEFAULT 0, -- LÍQUIDO A RECIBIR

    -- Payment Information
    payment_method VARCHAR(50) DEFAULT 'bank_transfer', -- bank_transfer, cash, check
    payment_reference VARCHAR(100),
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending, paid, failed

    -- Documents
    payslip_document_url TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- draft, approved, paid, closed

    -- Additional Data
    notes TEXT,
    extra_data JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Constraints
    CONSTRAINT payroll_payment_method_check CHECK (payment_method IN ('bank_transfer', 'cash', 'check')),
    CONSTRAINT payroll_payment_status_check CHECK (payment_status IN ('pending', 'paid', 'failed')),
    CONSTRAINT payroll_status_check CHECK (status IN ('draft', 'approved', 'paid', 'closed')),
    CONSTRAINT payroll_month_check CHECK (period_month >= 1 AND period_month <= 12),
    CONSTRAINT payroll_year_check CHECK (period_year >= 2020 AND period_year <= 2100),
    CONSTRAINT payroll_person_period_unique UNIQUE (person_id, period_month, period_year)
);

-- Indexes for payroll
CREATE INDEX idx_payroll_company_id ON payroll(company_id);
CREATE INDEX idx_payroll_person_id ON payroll(person_id);
CREATE INDEX idx_payroll_period ON payroll(period_year, period_month);
CREATE INDEX idx_payroll_status ON payroll(status);
CREATE INDEX idx_payroll_payment_status ON payroll(payment_status);

COMMENT ON TABLE payroll IS 'Stores monthly payroll calculations (liquidaciones de sueldo)';
COMMENT ON COLUMN payroll.taxable_income_items IS 'Array of taxable income items like bonuses, gratification';
COMMENT ON COLUMN payroll.non_taxable_income_items IS 'Array of non-taxable income items like colación, movilización';
COMMENT ON COLUMN payroll.other_deductions_items IS 'Array of other deductions like loans, advances';
COMMENT ON COLUMN payroll.pension_base IS 'Base for pension and health calculations (IMP. PREV./SALUD)';
COMMENT ON COLUMN payroll.unemployment_base IS 'Base for unemployment insurance (IMP. CESANTÍA)';
COMMENT ON COLUMN payroll.taxable_base IS 'Base for income tax calculation (BASE TRIBUTABLE)';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_people_updated_at BEFORE UPDATE ON people FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payroll_updated_at BEFORE UPDATE ON payroll FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate payroll totals (can be called from application or trigger)
CREATE OR REPLACE FUNCTION calculate_payroll_totals()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate total taxable income
    NEW.total_taxable_income := NEW.base_salary + COALESCE(
        (SELECT SUM((item->>'amount')::numeric)
         FROM jsonb_array_elements(NEW.taxable_income_items) AS item),
        0
    );

    -- Calculate total non-taxable income
    NEW.total_non_taxable_income := COALESCE(
        (SELECT SUM((item->>'amount')::numeric)
         FROM jsonb_array_elements(NEW.non_taxable_income_items) AS item),
        0
    );

    -- Calculate total income (haberes)
    NEW.total_income := NEW.total_taxable_income + NEW.total_non_taxable_income;

    -- Calculate total legal deductions
    NEW.total_legal_deductions := NEW.afp_deduction + NEW.health_deduction +
                                   NEW.unemployment_insurance + NEW.income_tax;

    -- Calculate total other deductions
    NEW.total_other_deductions := COALESCE(
        (SELECT SUM((item->>'amount')::numeric)
         FROM jsonb_array_elements(NEW.other_deductions_items) AS item),
        0
    );

    -- Calculate total deductions
    NEW.total_deductions := NEW.total_legal_deductions + NEW.total_other_deductions;

    -- Calculate net salary
    NEW.net_salary := NEW.total_income - NEW.total_deductions;

    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-calculate payroll totals
CREATE TRIGGER calculate_payroll_totals_trigger
    BEFORE INSERT OR UPDATE ON payroll
    FOR EACH ROW
    EXECUTE FUNCTION calculate_payroll_totals();
