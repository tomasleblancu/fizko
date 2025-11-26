/**
 * TypeScript types for Company Setup Edge Function
 */

/**
 * Company settings values from setup questions
 */
export interface CompanySettingsInput {
  has_formal_employees?: boolean | null;
  has_lease_contracts?: boolean | null;
  has_imports?: boolean | null;
  has_exports?: boolean | null;
  has_bank_loans?: boolean | null;
  business_description?: string | null;
}

/**
 * Request payload for company setup
 */
export interface CompanySetupRequest {
  company_id: string;
  settings: CompanySettingsInput;
  selected_template_ids?: string[]; // Optional: specific event templates to enable (in addition to mandatory)
}

/**
 * Response from company setup
 */
export interface CompanySetupResponse {
  success: boolean;
  settings_id?: string;
  company_events_created?: number;
  message?: string;
  error?: string;
}

/**
 * Company settings record from database
 */
export interface CompanySettings {
  id: string;
  company_id: string;
  has_formal_employees: boolean | null;
  has_lease_contracts: boolean | null;
  has_imports: boolean | null;
  has_exports: boolean | null;
  has_bank_loans: boolean | null;
  business_description: string | null;
  is_initial_setup_complete: boolean;
  initial_setup_completed_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Event template from database
 */
export interface EventTemplate {
  id: string;
  code: string;
  name: string;
  is_mandatory: boolean;
}

/**
 * Company event record
 */
export interface CompanyEvent {
  id: string;
  company_id: string;
  event_template_id: string;
  is_enabled: boolean;
  created_at: string;
}
