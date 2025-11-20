/**
 * Company Settings types
 */

export interface CompanySettings {
  id: string
  company_id: string
  has_formal_employees: boolean | null
  has_imports: boolean | null
  has_exports: boolean | null
  has_lease_contracts: boolean | null
  has_bank_loans: boolean | null
  business_description: string | null
  is_initial_setup_complete: boolean
  initial_setup_completed_at: string | null
  created_at: string
  updated_at: string
}

export interface CompanySettingsRequest {
  has_formal_employees?: boolean | null
  has_imports?: boolean | null
  has_exports?: boolean | null
  has_lease_contracts?: boolean | null
  has_bank_loans?: boolean | null
  business_description?: string | null
}

export interface CompanySettingsResponse {
  data: CompanySettings
  message?: string
}
