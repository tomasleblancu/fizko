/**
 * F29 Form types for monthly tax declarations
 *
 * Re-exports the database type with stricter typing for status fields
 */

import type { Database } from './database'
import type { SIIFormStatus } from './f29-sii-downloads'

export type FormType = 'monthly' | 'annual'
export type F29Status = 'draft' | 'pending' | 'submitted' | 'accepted' | 'rejected'

// Combined status type for UI display
export type CombinedF29Status = F29Status | SIIFormStatus

// Re-export base type from database with stricter status typing
export type F29Form = Omit<Database['public']['Tables']['form29']['Row'], 'status'> & {
  status: F29Status
}

// API response types
export interface F29FormsResponse {
  data: F29Form[]
  total: number
}

export interface F29FormsParams {
  companyId: string
  formType?: FormType
  year?: number
  month?: number
}

// Combined form type for UI - can be from either source
export interface CombinedF29Form {
  id: string
  period_year: number
  period_month: number
  status: CombinedF29Status
  amount: number
  submission_date: string | null
  created_at: string
  source: 'local' | 'sii'
  // Optional fields from F29
  net_iva?: number
  total_sales?: number
  total_purchases?: number
  // Optional fields from SII
  sii_folio?: string
  pdf_storage_url?: string | null
  pdf_download_status?: string
}
