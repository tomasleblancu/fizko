/**
 * Type definitions for IVA Summary Edge Function
 */

export interface Document {
  tax_amount: number | null;
  total_amount: number | null;
  net_amount: number | null;
  overdue_iva_credit: number | null;
}

export interface IvaSummary {
  debito_fiscal: number;
  credito_fiscal: number;
  balance: number;
  previous_month_credit: number;
  overdue_iva_credit: number;
  ppm: number;
  retencion: number;
  reverse_charge_withholding: number;
  sales_count: number;
  purchases_count: number;
}

export interface IvaSummaryRequest {
  company_id: string;
  period?: string; // Format: YYYY-MM
}
