/**
 * Types for SII integration
 */

export interface SIILoginRequest {
  rut: string;
  password: string;
}

export interface SIILoginResponse {
  success: boolean;
  message: string;
  session_active: boolean;
  cookies: SIICookie[];
  company_id?: string;
  session_id?: string;
  needs_setup?: boolean;
}

export interface SIICookie {
  name: string;
  value: string;
  domain?: string;
  path?: string;
  expires?: number;
  httpOnly?: boolean;
  secure?: boolean;
}

export interface SessionWithCompany {
  id: string;
  user_id: string;
  company_id: string;
  is_active: boolean;
  cookies: any;
  resources?: any;
  last_accessed_at: string;
  created_at: string;
  updated_at: string;
  company: {
    id: string;
    rut: string;
    business_name: string;
    trade_name?: string;
    settings?: {
      id?: string;
      is_initial_setup_complete: boolean;
      has_formal_employees?: boolean | null;
      has_imports?: boolean | null;
      has_exports?: boolean | null;
      has_lease_contracts?: boolean | null;
      has_bank_loans?: boolean | null;
      business_description?: string | null;
    };
  };
}

export interface ActiveSessionsResponse {
  hasActiveSessions: boolean;
  sessions: SessionWithCompany[];
  error?: string;
}
