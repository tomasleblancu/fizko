export interface Company {
  id: string;
  rut: string;
  business_name: string;
  trade_name?: string;
  address?: string;
  phone?: string;
  email?: string;
  tax_regime?: string;
  sii_activity_code?: string;
  created_at: string;
  session_id?: string;
}

export interface TaxSummary {
  id: string;
  company_id: string;
  period_start: string;
  period_end: string;
  total_revenue: number;
  total_expenses: number;
  iva_collected: number;
  iva_paid: number;
  net_iva: number;
  income_tax: number;
  created_at: string;
}

export interface PayrollRecord {
  id: string;
  company_id: string;
  employee_name: string;
  employee_rut: string;
  gross_salary: number;
  afp_deduction: number;
  isapre_deduction: number;
  other_deductions: number;
  net_salary: number;
  employer_contributions: number;
  period: string;
  created_at: string;
}

export interface PayrollSummary {
  period: string;
  total_employees: number;
  total_gross_salary: number;
  total_deductions: number;
  total_net_salary: number;
  total_employer_contributions: number;
}

export interface TaxDocument {
  id: string;
  company_id: string;
  document_type: string;
  document_number: string;
  issue_date: string;
  amount: number;
  tax_amount?: number;
  status: string;
  description?: string;
  created_at: string;
}
