/**
 * Tax Summary types for Chilean tax calculations
 */

export interface TaxSummary {
  id: string
  company_id: string
  period_start: string
  period_end: string
  total_revenue: number
  total_expenses: number
  iva_collected: number
  iva_paid: number
  net_iva: number
  income_tax: number
  previous_month_credit: number | null
  overdue_iva_credit: number
  ppm: number | null
  retencion: number | null
  reverse_charge_withholding: number | null
  impuesto_trabajadores: number | null
  monthly_tax: number
  generated_f29: GeneratedForm29 | null
  form29_sii_download: Form29SiiDownload | null
  created_at: string
  updated_at: string
}

export interface GeneratedForm29 {
  id: string
  company_id: string
  period_year: number
  period_month: number
  total_sales: number
  taxable_sales: number
  exempt_sales: number
  sales_tax: number
  total_purchases: number
  taxable_purchases: number
  purchases_tax: number
  iva_to_pay: number
  iva_credit: number
  net_iva: number
  status: string
  extra_data: Record<string, any> | null
  submitted_at: string | null
  created_at: string
  updated_at: string
}

export interface Form29SiiDownload {
  id: string
  company_id: string
  form29_id: string | null
  sii_folio: string
  sii_id_interno: string | null
  period_year: number
  period_month: number
  period_display: string
  contributor_rut: string
  submission_date: string | null
  status: string
  amount_cents: number
  pdf_storage_url: string | null
  pdf_download_status: string
  pdf_download_error: string | null
  pdf_downloaded_at: string | null
  extra_data: Record<string, any> | null
  created_at: string
  updated_at: string
}

// Sales document types that ADD to totals
export const SALES_POSITIVE_TYPES = [
  'factura_venta',
  'boleta',
  'boleta_exenta',
  'factura_exenta',
  'comprobante_pago',
  'liquidacion_factura',
  'nota_debito_venta'
] as const

// Sales document types that SUBTRACT from totals
export const SALES_CREDIT_TYPES = ['nota_credito_venta'] as const

// Purchase document types that ADD to totals
export const PURCHASES_POSITIVE_TYPES = [
  'factura_compra',
  'factura_exenta_compra',
  'liquidacion_factura',
  'nota_debito_compra',
  'declaracion_ingreso'
] as const

// Purchase document types that SUBTRACT from totals
export const PURCHASES_CREDIT_TYPES = ['nota_credito_compra'] as const
